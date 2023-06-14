from cv_gui.dataset_handlers.camera import Camera

import numpy as np
import cv2 as cv

import cv_gui.utils.flags as cv_gui
from cv_gui.utils.data_parsers import get_frame_numbers_from_config_file


class StereoCamera(Camera):
    def __init__(self, dataset = cv_gui.DATASET_TYPE.KITTI, config_file = ""):
        super().__init__(dataset = dataset)

        self.base_camera_type = None
        self.basic_calibration_params = {}
        
        self.config_file = config_file
        
        self.frame_numbers = []
        
    def set_config_file(self, config_file):
        self.config_file = config_file

    def process_config_file(self, config_file):
        self.frame_numbers = get_frame_numbers_from_config_file(config_file)
        
    def get_next_index(self, idx):
        if(self.frame_numbers == []):
            return idx + 1
        
        return self.frame_numbers.pop(0)

    def get_disparity_img(self, left_img, right_img, fill = False, gray = True):

        if(not gray):
            left_img = cv.cvtColor(left_img, cv.COLOR_RGB2GRAY)
            right_img = cv.cvtColor(right_img, cv.COLOR_RGB2GRAY)

        # StereoSGBM Parameters
        sad_window = 6
        num_disparities = sad_window*16
        block_size = 11
        
        stereo = cv.StereoSGBM_create  (   numDisparities=num_disparities,
                                            minDisparity=0,
                                            blockSize=block_size,
                                            P1 = 8 * 3 * sad_window ** 2,
                                            P2 = 32 * 3 * sad_window ** 2,
                                            mode=cv.STEREO_SGBM_MODE_SGBM_3WAY
                                        )

        disparity_img = stereo.compute(left_img, right_img).astype(np.float32)/16.0

        if(fill):
            # Avoid instability and division by zero
            disparity_img = np.where(disparity_img == 0.0, 10000, disparity_img)
            disparity_img = np.where(disparity_img == -1.0, 10000, disparity_img)

        return disparity_img

    def get_depth_img_from_stereo_img(self, left_img, right_img, fill = False, convert_to_gray = True):
        disparity_img = self.get_disparity_img(left_img, right_img, fill = fill, convert_to_gray = convert_to_gray)
        
        return self._get_depth_image(disparity_img)
    
    def get_depth_img_from_disparity_img(self, disparity_img):
        return self._get_depth_image(disparity_img)

    def _get_depth_image(self, disparity_img):
        # Make empty depth map then fill with depth
        depth_map = np.ones(disparity_img.shape)
        fx = self.basic_calibration_params["fx"]
        baseline = self.basic_calibration_params["b"]

        depth_map = fx * baseline / disparity_img        
        
        return depth_map
    
    def set_base_camera_type_for_intrinsics(self, camera_type):
        self.base_camera_type = camera_type

        self.basic_calibration_params = self.get_basic_calib_params(camera_type = camera_type)
        
    def get_disparity_values(self, kps, disparity_img):
        return disparity_img[kps[:, 0, 1].astype(int), kps[:, 0, 0].astype(int)]
    
    def get_depth_values(self, kps, depth_img):
        return depth_img[kps[:, 0, 1].astype(int), kps[:, 0, 0].astype(int)]
    
    def get_corresponding_pixels_from_disparity(self, kps, disparities):
        correspondings_kps = kps.copy()
        
        # Add the disparity to the x coordinate
        correspondings_kps[:, 0, 0] = correspondings_kps[:, 0, 0] - disparities
        
        return correspondings_kps
        

    def get_L1_norm_for_kps(self, kps1, kps2, img1, img2, patch_size = 3):
        mean_l1_norm = []
        for kp1, kp2 in zip(kps1, kps2):
            patch1 = cv.getRectSubPix(img1, (patch_size, patch_size), (kp1[0, 1], kp1[0, 0]))
            patch2 = cv.getRectSubPix(img2, (patch_size, patch_size), (kp2[0, 1], kp2[0, 0]))
            
            # Compute the L1 Norm
            l1_norm = np.mean(np.abs(patch1 - patch2))
            mean_l1_norm.append(l1_norm)
            
        return np.array(mean_l1_norm)