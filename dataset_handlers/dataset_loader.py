import os
import cv2 as cv
import numpy as np
from enum import Enum
from scripts.camera import CameraType
from scripts.flags import ERROR
from scripts.stereo_camera import StereoCamera
from scripts.utils import DatasetType

class DatasetLoader(StereoCamera):
    def __init__(self, left_path = "", right_path = "", label_path = "", dataset_type = DatasetType.KITTI, pose_file = "", timestamp_file = "", 
                 calib_file = "", gray = True, color = True):
        super().__init__(dataset=dataset_type)
        
        self.dataset_type = dataset_type
        
        self.left_path = left_path
        self.right_path = right_path
        self.label_path = label_path
        self.pose_file = pose_file
        self.calib_file = calib_file
        self.timestamp_file = timestamp_file
        
        self.gray = gray
        self.color = color
        
        self.initial_pose = None
        self.idx = 0

    def set_left_folder(self, path):
        self.left_path = path
        
    def set_right_folder(self, path):
        self.right_path = path
        
    def set_label_folder(self, path):
        self.label_path = path
        
    def set_calib_file_path(self, path):
        self.calib_file = path
        
    def set_timestamp_file_path(self, path):
        self.timestamp_file = path
        
    def set_pose_file_path(self, path):
        self.pose_file = path

    def init(self):
        if(self.dataset_type == DatasetType.KITTI):
            left_img_folder = self.left_path
            right_img_folder = self.right_path
            label_img_foler = self.label_path

            self.left_img_files = self.get_img_files_from_dir(left_img_folder)
            self.right_img_files = self.get_img_files_from_dir(right_img_folder)

            self.img_count = len(self.left_img_files)
            # Read timestamps
            if(self.timestamp_file):
                self.timestamps = self._load_timestamps(self.timestamp_file)
                
            # Load calibration params
            if(self.calib_file):
                self.load_caliberation_paramters(calib_file=self.calib_file)
                
            # Read poses
            if(self.pose_file):
                self.poses, self.poses_right_cam = self._load_poses(self.pose_file)
                self.initial_pose = self.poses[self.idx]
                self.initial_pose_right = self.poses_right_cam[self.idx]
                
            # Load Label Files
            if(self.label_path):  
                self.label_img_files = self.get_img_files_from_dir(label_img_foler)

    def get_img_files_from_dir(self, dir):
        files = os.listdir(dir)
        img_files = [(dir +'/'+ ff) for ff in files if (ff.endswith('.png') or ff.endswith('.jpg') or ff.endswith('.jpeg'))]
        img_files.sort()

        return img_files
    
    def _load_poses(self, pose_file):
        """Load ground truth poses (T_w_cam0) from file."""

        # Read and parse the poses
        poses = []
        poses_right_cam = []
        try:
            with open(pose_file, 'r') as f:
                lines = f.readlines()

                for line in lines:
                    T_w_cam0 = np.fromstring(line, dtype=float, sep=' ')
                    T_w_cam0 = T_w_cam0.reshape(3, 4)
                    T_w_cam0 = np.vstack((T_w_cam0, [0, 0, 0, 1]))
                    poses.append(T_w_cam0)

                    # The transformation of right camera w.r.t left camera
                    R = self.cam_parameters[CameraType.RIGHT_GRAY.name]["r"]
                    t = self.cam_parameters[CameraType.RIGHT_GRAY.name]["t"][0:3]
                    T_w_cam_right = np.vstack((np.hstack((R, t)), [0, 0, 0, 1]))

                    poses_right_cam.append(T_w_cam0@T_w_cam_right)
                    
        except FileNotFoundError:
            print('Ground truth poses are not available for sequence')

        return poses, poses_right_cam
    
    def _load_timestamps(self, timestamp_file):
        """Load timestamps from file."""

        # Read and parse the timestamps
        timestamps = []
        try:
            with open(timestamp_file, 'r') as f:
                lines = f.readlines()

                for line in lines:
                    timestamp = np.fromstring(line, dtype=float, sep=' ')
                    timestamps.append(timestamp)


        except FileNotFoundError:
            print('Time stamps are not available for sequence')

        return timestamps

    
    def get_next_stereo_images(self, gray = True, color = True):
        self.gray = gray
        self.color = color
        data = {}
        
        assert gray or color, "Either gray or color frag should be true"

        if(self.idx == self.img_count):
            return ERROR.END_OF_FILE, data

        
        left_color_img = cv.imread(self.left_img_files[self.idx])
        right_color_img = cv.imread(self.right_img_files[self.idx])
        
        data["image_loc"] = self.left_img_files[self.idx]
        
        if(gray):
            left_img = cv.cvtColor(left_color_img, cv.COLOR_RGB2GRAY)
            right_img = cv.cvtColor(right_color_img, cv.COLOR_RGB2GRAY)
            data["left_img"] = left_img
            data["right_img"] = right_img
            
        if(color):
            data["left_color_img"] = left_color_img
            data["right_color_img"] = right_color_img
        
        data["index"] = self.idx

        if(self.pose_file):
            # For the left camera
            data["abs_pose"] = self.poses[self.idx]
            
            # For the right camera
            data["abs_pose_right"] = self.poses_right_cam[self.idx]
            
            if(self.idx > 0):
                data["rel_pose"] = np.linalg.inv(self.poses[self.idx - 1])@self.poses[self.idx]
                data["rel_pose_right"] = np.linalg.inv(self.poses_right_cam[self.idx - 1])@self.poses_right_cam[self.idx]
                
        if(self.timestamp_file):
            data["t"] = self.timestamps[self.idx][0]
        if(self.label_path):
            data["label_img"] = cv.imread(self.label_img_files[self.idx])
            
        self.idx = self.idx + 1
        
        return ERROR.SUCCESS, data
    
    def get_frame_count(self):
        return self.img_count
        
    def jump_to(self, frame_number):
        # Jump to the frame number. The next call to grab() will read the provided frame number.
        self.idx = frame_number
        
    def close(self):
        return
    
    def __str__(self):
        return f"The number of images found are {self.img_count} \n {super().__str__()}"
