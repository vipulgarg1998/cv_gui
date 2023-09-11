from cv_gui.dataset_handlers.dataset_loader import DatasetLoader
from cv_gui.dataset_handlers.zed import ZED, ZEDDepthUnit, ZEDDepthMode, ZEDResolution, ZEDSensingMode
from cv_gui.utils.config_file_handler import read_config_file
from cv_gui.utils.flags import CAMERA_TYPE, DATASET_TYPE


class Stereo:
    def __init__(self):
        
        self.dataset_type = None
        # ZED Camera params
        self.zed_params = None
        self.zed_depth_unit = None
        self.zed_depth_mode = None
        self.zed_resolution = None
        self.zed_sensing_mode = None
        self.zed_min_depth = None
        self.zed_max_depth = None
        self.zed_enable_pos_tracking = None
        self.zed_use_rectified_images = None
    
        # KITTI Camera Params
        self.kitti_params = None
        self.kitti_disparity_fill = None
        self.kitti_disparity_fill_value = None
        # Camera
        self.camera = None
        
    def init_params(self, params):
        if(params is not None):
            self.zed_params = params["ZED"]
            self.zed_depth_unit = ZEDDepthUnit[self.zed_params["depth_unit"]]
            self.zed_depth_mode = ZEDDepthMode[self.zed_params["depth_mode"]]
            self.zed_resolution = ZEDResolution[self.zed_params["resolution"]]
            self.zed_sensing_mode = ZEDSensingMode[self.zed_params["sensing_mode"]]
            self.zed_min_depth = self.zed_params["min_depth"]
            self.zed_max_depth = self.zed_params["max_depth"]
            self.zed_enable_pos_tracking = self.zed_params["enable_pos_tracking"]
            self.zed_use_rectified_images = self.zed_params["use_rectified_images"]
            
            self.kitti_params = params["KITTI"]
            self.kitti_disparity_fill = self.kitti_params["disparity_fill"]
            self.kitti_disparity_fill_value = self.kitti_params["disparity_fill_value"]
            
    def init_params_from_config_file(self, param_file):
        if(param_file is not None):
            self.parameters = read_config_file(param_file)
            self.init_params(self.parameters)
            
    def init(self, config_data, seq_control_file):
        print(".............Initializing Camera ...........")
        self.dataset_type = DATASET_TYPE(config_data["dataset"])

        if(self.dataset_type == DATASET_TYPE.ZED):
            self.camera = ZED(depth_unit=self.zed_depth_unit,
                              depth_mode=self.zed_depth_mode,
                              resolution=self.zed_resolution,
                              sensing_mode=self.zed_sensing_mode,
                              depth_min_dist=self.zed_min_depth,
                              depth_max_dist=self.zed_max_depth,
                              enable_pos_tracking=self.zed_enable_pos_tracking,
                              use_rectified=self.zed_use_rectified_images)
        elif(self.dataset_type == DATASET_TYPE.KITTI):
            self.camera = DatasetLoader(dataset_type=DATASET_TYPE.KITTI,
                                        disparity_fill=self.kitti_disparity_fill,
                                        disparity_fill_value=self.kitti_disparity_fill_value)

        self.camera.set_config_data(config_data)
        self.camera.set_seq_control_file(seq_control_file)

        self.camera.init()
        self.camera.set_base_camera_type_for_intrinsics(camera_type=CAMERA_TYPE.LEFT_RGB)
        self.basic_calib_params = self.camera.get_basic_calib_params(CAMERA_TYPE.LEFT_RGB)
        
    