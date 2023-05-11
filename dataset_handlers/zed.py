from gui.utils import ERROR
from dataset_handlers.stereo_camera import StereoCamera
from dataset_handlers.camera import CameraType

import cv2 as cv
import numpy as np
import pyzed.sl as sl
import math
import os
from enum import Enum

from gui.utils import DATASET_TYPE

class ZEDDepthUnit(Enum):
    METER = sl.UNIT.METER
    MILLIMETER = sl.UNIT.MILLIMETER

class ZEDResolution(Enum):
    VGA = sl.RESOLUTION.VGA
    HD720 = sl.RESOLUTION.HD720
    HD1080 = sl.RESOLUTION.HD1080
    HD2K = sl.RESOLUTION.HD2K

class ZEDDepthMode(Enum):
    PERFORMANCE = sl.DEPTH_MODE.PERFORMANCE
    QUALITY = sl.DEPTH_MODE.QUALITY
    ULTRA = sl.DEPTH_MODE.ULTRA
    NEURAL = sl.DEPTH_MODE.NEURAL

class ZEDSensingMode(Enum):
    STANDARD = sl.SENSING_MODE.STANDARD
    FILL = sl.SENSING_MODE.FILL

class ZED(StereoCamera):
    def __init__(self, resolution = ZEDResolution.HD2K, depth_mode = ZEDDepthMode.NEURAL, depth_unit = ZEDDepthUnit.MILLIMETER, svo_file_path = "", 
                 depth_min_dist = 0.15, depth_max_dist = 50, enable_pos_tracking = False, gray = True, color = True, label_path = "", use_rectified = True):
        super().__init__(dataset = DATASET_TYPE.ZED)
        self.zed = sl.Camera()
        
        self.gray = gray
        self.color = color
        self.use_rectified = use_rectified

        # Create a InitParameters object and set configuration parameters
        self.init_params = sl.InitParameters()
        self.init_params.depth_mode = depth_mode.value # Use PERFORMANCE depth mode
        self.init_params.coordinate_units = depth_unit.value  # Use meter units (for depth measurements)
        self.init_params.camera_resolution = resolution.value
        self.init_params.depth_minimum_distance = depth_min_dist
        self.init_params.depth_maximum_distance = depth_max_dist
        
        # Enable positional tracking with default parameters
        self.pose_tracking_enabled = enable_pos_tracking
        tracking_parameters = sl.PositionalTrackingParameters()
        if(self.pose_tracking_enabled):
            err = self.zed.zed.enable_positional_tracking(tracking_parameters)
        
        self.svo_file_path = svo_file_path
        self.label_path = label_path
        if(self.svo_file_path != ""):
            self.init_params.set_from_svo_file(self.svo_file_path)

        # Create and set RuntimeParameters after opening the camera
        self.runtime_parameters = sl.RuntimeParameters()
        # self.runtime_parameters.sensing_mode = sl.SENSING_MODE.FILL

        # Index to track the frame number
        self.idx = 0

        # Store Camera frames 
        self.gray = False
        self.color = True
        self.left_image = None
        self.right_image = None
        self.left_image_color = None
        self.right_image_color = None
        self.depth_image = None
        self.disparity_image = None
        self.point_cloud = None
        self.confidence_img = None
        self.depth_color_image = None

        self.camera_open = False
        
    def set_from_svo_file(self, filepath):
        self.svo_file_path = filepath
        self.init_params.set_from_svo_file(filepath)
        
    def set_label_folder(self, filepath):
        self.label_path = filepath

    def open_camera(self):
        # Open the camera
        err_code = self.zed.open(self.init_params)
        self.camera_open = err_code == sl.ERROR_CODE.SUCCESS

        return self.camera_open

    def init(self):
        if(not self.camera_open):
            self.open_camera()
            
        width = self.zed.get_camera_information().camera_resolution.width
        height = self.zed.get_camera_information().camera_resolution.height
        # Set Camera frames 
        self.left_image = sl.Mat(width, height, sl.MAT_TYPE.U8_C1)
        self.right_image = sl.Mat(width, height, sl.MAT_TYPE.U8_C1)
        self.left_image_color = sl.Mat(width, height, sl.MAT_TYPE.U8_C4)
        self.right_image_color = sl.Mat(width, height, sl.MAT_TYPE.U8_C4)
        self.depth_image = sl.Mat(width, height, sl.MAT_TYPE.F32_C1)
        self.point_cloud = sl.Mat(width, height, sl.MAT_TYPE.F32_C4)
        self.disparity_image = sl.Mat(width, height, sl.MAT_TYPE.F32_C1)
        self.confidence_img = sl.Mat(width, height, sl.MAT_TYPE.F32_C1)
        self.depth_color_image = sl.Mat(width, height, sl.MAT_TYPE.U8_C4)

        # Get and Update Calibration Matrix
        self.set_calibration_parameters(camera_type=CameraType.LEFT_RGB, calib_params=self.get_calib_params(camera_type=CameraType.LEFT_RGB))
        self.set_calibration_parameters(camera_type=CameraType.RIGHT_RGB, calib_params=self.get_calib_params(camera_type=CameraType.RIGHT_RGB))
    
    def get_img_files_from_dir(self, dir):
        files = os.listdir(dir)
        img_files = [(dir +'/'+ ff) for ff in files if (ff.endswith('.png') or ff.endswith('.jpg') or ff.endswith('.jpeg'))]
        img_files.sort()

        return img_files
    
    def set_runtime_parameters(self, sensing_mode = ZEDSensingMode.FILL, confidence_th = 100, textureness_confidence_th = 100):
        self.runtime_parameters.sensing_mode = sensing_mode.value  # Use sensing mode
        # Setting the depth confidence parameters
        self.runtime_parameters.confidence_threshold = confidence_th
        self.runtime_parameters.textureness_confidence_threshold = textureness_confidence_th

    def get_calib_params(self, camera_type):
        calib_params = {}
        calibration_params = self.zed.get_camera_information().camera_configuration.calibration_parameters
        if(camera_type == CameraType.LEFT_RGB):
            fx = calibration_params.left_cam.fx
            fy = calibration_params.left_cam.fy
            cx = calibration_params.left_cam.cx
            cy = calibration_params.left_cam.cy
            R = np.array([[0], [0], [0]])       # Identity Rotation as Left camera is the reference camera
            T = np.array([[0], [0], [0]])       # Null translation 

        if(camera_type == CameraType.RIGHT_RGB):
            fx = calibration_params.right_cam.fx
            fy = calibration_params.right_cam.fy
            cx = calibration_params.right_cam.cx
            cy = calibration_params.right_cam.cy
            R = calibration_params.R
            T = calibration_params.T

        k = np.array([[fx, 0, cx],
                        [0, fy, cy],
                        [0, 0, 1]])

        calib_params["k"] = k
        calib_params["r"] = R
        calib_params["t"] = T

        return calib_params
        
    def get_next_stereo_images(self, gray = True, color = True):
        assert gray or color, "Either gray or color frag should be true"
        
        self.gray = gray
        self.color = color
        
        data = {}

        err_code = self.zed.grab(self.runtime_parameters)

        if(err_code != sl.ERROR_CODE.SUCCESS):
            return ERROR.END_OF_FILE, data
        
        if(gray):
            if(self.use_rectified):
                # Retrieve left image
                self.zed.retrieve_image(self.left_image, sl.VIEW.LEFT_GRAY)
                # Retrieve left image
                self.zed.retrieve_image(self.right_image, sl.VIEW.RIGHT_GRAY)
            else:
                # Retrieve left image
                self.zed.retrieve_image(self.left_image, sl.VIEW.LEFT_UNRECTIFIED_GRAY)
                # Retrieve left image
                self.zed.retrieve_image(self.right_image, sl.VIEW.RIGHT_UNRECTIFIED_GRAY)
                
            
            # Convert from zed data type to opencv data type
            data['left_img'] = self.left_image.get_data()
            data['right_img'] = self.right_image.get_data()

        if(color):
            if(self.use_rectified):
                # Retrieve left image
                self.zed.retrieve_image(self.left_image_color, sl.VIEW.LEFT)
                # Retrieve left image
                self.zed.retrieve_image(self.right_image_color, sl.VIEW.RIGHT)
            else:
                # Retrieve left image
                self.zed.retrieve_image(self.left_image_color, sl.VIEW.LEFT_UNRECTIFIED)
                # Retrieve left image
                self.zed.retrieve_image(self.right_image_color, sl.VIEW.RIGHT_UNRECTIFIED)
                
            # Convert from zed data type to opencv data type
            data['left_color_img'] = cv.cvtColor(self.left_image_color.get_data(), cv.COLOR_BGRA2BGR)
            data['right_color_img'] = cv.cvtColor(self.right_image_color.get_data(), cv.COLOR_BGRA2BGR)
            
        if(self.label_path):
            data['label_img'] = cv.imread(f"{self.label_path}/Seq001Fr{str(self.idx).zfill(8)}M.jpeg", 0)
            # cv.imshow("Seg", data['label_img'])
            # cv.waitKey(0)
            
        data['index'] = self.idx
        
        data["t"] = self.zed.get_timestamp(sl.TIME_REFERENCE.IMAGE).get_nanoseconds()*(1e-9)  # Get the image timestamp in seconds
        # update the frame count
        self.idx = self.idx + 1

        return ERROR.SUCCESS, data
    
    def get_depth_img(self):
        # Retrieve depth map. Depth is aligned on the left image
        self.zed.retrieve_measure(self.depth_image, sl.MEASURE.DEPTH)
        return self.depth_image.get_data()
    
    def get_depth_color_img(self):
        self.zed.retrieve_image(self.depth_color_image, sl.VIEW.DEPTH)
        return self.depth_color_image.get_data()
        
    def get_translation(self):
        assert self.pose_tracking_enabled, "Pose Tracking is not Enabled"
        
        
        zed_pose = sl.Pose()
        
        state = self.zed.get_position(zed_pose, sl.REFERENCE_FRAME.WORLD)
        # Display translation and timestamp
        py_translation = sl.Translation()
        tx = round(zed_pose.get_translation(py_translation).get()[0], 3)
        ty = round(zed_pose.get_translation(py_translation).get()[1], 3)
        tz = round(zed_pose.get_translation(py_translation).get()[2], 3)
        
        return np.array([[tx], [ty], [tz]])
    
    def get_zed_disparity_img(self):
        # Retrieve depth map. Depth is aligned on the left image
        self.zed.retrieve_measure(self.disparity_image, sl.MEASURE.DISPARITY)
        return self.disparity_image.get_data()

    def get_zed_point_cloud(self):
        self.zed.retrieve_measure(self.point_cloud, sl.MEASURE.XYZRGBA)
        return self.point_cloud

    def get_zed_confidence_img(self):
        # Retrieve depth map. Depth is aligned on the left image
        self.zed.retrieve_measure(self.confidence_img, sl.MEASURE.CONFIDENCE)
        return self.confidence_img.get_data()

    def close(self):
        self.zed.close()
        
    def jump_to(self, frame_number):
        # Works only if the camera is open in SVO playback mode.
        assert self.svo_file_path != "", "SVO File Path is not set"
        
        # Jump to the frame number. The next call to grab() will read the provided frame number.
        self.zed.set_svo_position(frame_number)
        
        # Update the index of the dataframe
        self.idx = frame_number
        
    def get_frame_count(self):
        # Works only if the camera is open in SVO playback mode.
        assert self.svo_file_path != "", "SVO File Path is not set"
        
        # Returns the number of frames in the SVO file
        return self.zed.get_svo_number_of_frames()
    

def main():
    # Create a Camera object
    zed = ZED()
    zed.set_runtime_parameters()
    
    if(not zed.open_camera()):
        zed.close()
        print('Zed camera failed to open')
        return
    
    zed.init()
    print(zed.cam_parameters)
    while True:
        has_data, data = zed.get_next_stereo_images()

        if(not has_data):
            break

        cv.imshow("Image", data['depth_color_img'])
        cv.waitKey(1)

    zed.close()

if __name__ == "__main__":
    main()