from enum import Enum
import numpy as np
import cv2 as cv

from gui.utils import DATASET_TYPE

class CameraType(Enum):
    LEFT_GRAY = 0
    RIGHT_GRAY = 1
    LEFT_RGB = 2
    RIGHT_RGB = 3

class Camera:
    def __init__(self, dataset = DATASET_TYPE.KITTI):
        self.cam_parameters = {}
        self.dataset = dataset

    def load_caliberation_paramters(self, calib_file):
        
        if(self.dataset == DATASET_TYPE.KITTI):
            with open(calib_file) as f:
                lines = f.readlines()

                P1 = np.array(lines[CameraType.LEFT_GRAY.value].split(" ")[1:]).astype(float).reshape(3,4)
                P2 = np.array(lines[CameraType.RIGHT_GRAY.value].split(" ")[1:]).astype(float).reshape(3,4)
                P3 = np.array(lines[CameraType.LEFT_RGB.value].split(" ")[1:]).astype(float).reshape(3,4)
                P4 = np.array(lines[CameraType.RIGHT_RGB.value].split(" ")[1:]).astype(float).reshape(3,4)
                
                self.cam_parameters[CameraType.LEFT_GRAY.name] = self.decompose_projection_matrix(P1)
                self.cam_parameters[CameraType.RIGHT_GRAY.name] = self.decompose_projection_matrix(P2)
                self.cam_parameters[CameraType.LEFT_RGB.name] = self.decompose_projection_matrix(P3)
                self.cam_parameters[CameraType.RIGHT_RGB.name] = self.decompose_projection_matrix(P4)


    def set_calibration_parameters(self, camera_type, calib_params):
        self.cam_parameters[camera_type.name] = calib_params

    def get_calibration_parameters(self, camera_type):
        return self.cam_parameters[camera_type.name]

    def decompose_projection_matrix(self, projection_matrix):
        calib_params = {}

        k, r, t, _, _, _, _ = cv.decomposeProjectionMatrix(projection_matrix)
        t = t / t[3]
        calib_params["k"] = k
        calib_params["r"] = r
        calib_params["t"] = t

        return calib_params
        
    def get_basic_calib_params(self, camera_type):
        basic_calib_params = {}
        if(self.dataset == DATASET_TYPE.KITTI or self.dataset == DATASET_TYPE.ZED):
            k = self.cam_parameters[camera_type.name]['k']
            basic_calib_params["fx"] = k[0, 0]
            basic_calib_params["fy"] = k[1, 1]
            basic_calib_params["cx"] = k[0, 2]
            basic_calib_params["cy"] = k[1, 2]

            if(camera_type == CameraType.LEFT_GRAY):
                basic_calib_params["b"] = np.abs(self.cam_parameters[CameraType.RIGHT_GRAY.name]["t"][0] - self.cam_parameters[CameraType.LEFT_GRAY.name]["t"][0])
            elif(camera_type == CameraType.LEFT_RGB):
                basic_calib_params["b"] = np.abs(self.cam_parameters[CameraType.RIGHT_RGB.name]["t"][0] - self.cam_parameters[CameraType.LEFT_RGB.name]["t"][0])
        
        return basic_calib_params

    def __str__(self):
        data_str = ""
        if(self.dataset == DATASET_TYPE.KITTI):
            for cam in CameraType:
                data_str = data_str + f"The intrinsics of the {cam.name} camera are \n {self.cam_parameters[cam.name]['k']} \n" 
                data_str = data_str + f"Rotation Matrix \n {self.cam_parameters[cam.name]['r']} \n" 
                data_str = data_str + f"Translation Vector \n {self.cam_parameters[cam.name]['t']} \n"
            
        return data_str
        # return f"The calibration paramters of the camera are:\n Fx: {self.fx}\n Cx: {self.cx}\n Fy: {self.fy}\n Cy: {self.cy}\n Baseline: {self.baseline}"