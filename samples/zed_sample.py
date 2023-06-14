from cv_gui.dataset_handlers.zed import ZED, ZEDDepthMode, ZEDDepthUnit, ZEDResolution, ZEDSensingMode
from cv_gui.gui.application import Application
import cv_gui.utils.flags as cv_gui

class ZEDGUISample:
    def __init__(self):    
        
        # GUI
        self.gui = Application(add_extra_image_window=False)
        self.gui.on_frame_jump_callback = self.on_frame_jump
        self.gui.set_send_data_to_camera(self.on_data_receive)
        self.gui.set_img1_callback(self.return_left_image)
        self.gui.set_img2_callback(self.return_right_image)
        self.gui.set_timestamp_callback(self.return_timestamp)
        self.gui.set_on_close(self.on_close)
        
        self.gray = True
        self.color = True

        self.depth_min = 10
        self.depth_max = 200
        
        # Point Cloud is not working on mm yet.
        self.camera = ZED(depth_unit=ZEDDepthUnit.METER, depth_mode=ZEDDepthMode.NEURAL, resolution=ZEDResolution.HD1080, 
                        depth_min_dist=self.depth_min, depth_max_dist=self.depth_max, gray=self.gray, color=self.color, use_rectified=True)

        # Set camera to gui
        self.gui.set_camera(self.camera)
        self.gui.set_on_start(self.on_zed_start)
        
        self.data = {}
        
    def on_data_receive(self, data, old_frame = False):
        self.data = data
        
        # Do some processing if needed
        
    def on_close(self):
        pass
    
    def return_timestamp(self, data):
        return f"{data['t']}"
    
    def return_left_image(self, data):
        file_name = f"Seq001Fr{str(data['index']).zfill(8)}L"
        return data['left_color_img'], cv_gui.IMAGE_TYPES.BGR, file_name
        
    def return_right_image(self, data):
        file_name = f"Seq001Fr{str(data['index']).zfill(8)}R"
        return data['right_color_img'], cv_gui.IMAGE_TYPES.BGR, file_name

    def on_zed_start(self, filepath, label_path = "", config_file = ""):
        print(label_path)
        self.camera.set_from_svo_file(filepath)
        self.camera.set_label_folder(label_path)
        self.camera.set_config_file(config_file)
        self.setup_stereo()
        self.camera.set_runtime_parameters(sensing_mode=ZEDSensingMode.FILL, confidence_th=100, textureness_confidence_th=100)
        
    def setup_stereo(self):
        self.camera.init()
        self.camera.set_base_camera_type_for_intrinsics(camera_type=cv_gui.CAMERA_TYPE.LEFT_RGB)
        
    def on_frame_jump(self, frame_number):
        # DO something if required
        pass
     
if __name__ == "__main__":
    gui_test = ZEDGUISample()
    gui_test.gui.show()
    gui_test.gui.exit()