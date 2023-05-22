import sys
import time
from PySide6.QtCore import QThread, Signal
import numpy as np

import cv_gui.utils.flags as cv_gui


class Process(QThread):
    updateFrame1 = Signal(np.ndarray, cv_gui.IMAGE_TYPES, str, bool)
    updateFrame2 = Signal(np.ndarray, cv_gui.IMAGE_TYPES, str, bool)
    updateFrame3 = Signal(np.ndarray, cv_gui.IMAGE_TYPES, str, bool)
    updateTimestamp= Signal(str)

    def __init__(self, parent=None, add_extra_image_window = False):
        QThread.__init__(self, parent)
        
        self.default_add_extra_image_window = add_extra_image_window
        self.add_extra_image_window = add_extra_image_window
        
        self.do_nothing = True
        self.trained_file = None
        self.status = True
        self.cap = True
        self.current_frame_number = 0
        self.is_playing = False
        self.current_img1 = None
        self.current_img2 = None
        self.tracking_mode = False
        self.data = {}
        
        # Callbacks
        self.on_start = None
        self.on_eof = None
        self.img1_callback = None
        self.img2_callback = None
        self.img3_callback = None
        self.timestamp_callback = None
        self.send_data_to_camera = None
        
        # Objects
        self.camera = None
        
    def reset_process(self):
        self.do_nothing = True
        self.requestInterruption()
        self.camera = None
        self.add_extra_image_window = self.default_add_extra_image_window
        
        self.trained_file = None
        self.status = True
        self.cap = True
        self.current_frame_number = 0
        self.is_playing = False
        
    def start_process(self):
        # Start the thread
        self.start()
        self.do_nothing = False
        
    def run(self):
        while self.status:
            if(self.do_nothing):
                time.sleep(0.001)
                continue
            self.status, data = self.camera.get_next_stereo_images()
            # If no data is left
            if(self.status == cv_gui.ERROR.END_OF_FILE):
                self.on_eof()
                while(not self.is_playing):
                    time.sleep(0.001)
                    
                continue
            # Update the frame number
            self.current_frame_number = data["index"]
            
            # Store Data
            self.data = data
            
            # Send this data to process
            self.send_data_to_camera(data, old_frame = False)
            
            # Update the frame
            self.update(data=data)
            time.sleep(0.1)
            
            # print(self.current_frame_number)
            while(not self.is_playing):
                # Do not send new data to the camera
                # if(self.tracking_mode):
                # Send this data to process
                self.send_data_to_camera(self.data, old_frame = True)
                # print("In While LOOP")
                self.update(data=self.data, old_frame = True)
                time.sleep(0.1)
                # time.sleep(1)
                continue
        sys.exit(-1)

    def update(self, data = {}, old_frame = False):
        # Current image on display
        # self.current_img = data['left_img']
        self.current_img1, img1_format_type, img1_name = self.img1_callback(data)
        self.current_img2, img2_format_type, img2_name = self.img2_callback(data)
        self.timestamp = self.timestamp_callback(data)
        # print(old_frame, img1_name)
        forcefully_save_img = not old_frame
        # Emit signal
        self.updateFrame1.emit(self.current_img1, img1_format_type, img1_name, forcefully_save_img)
        self.updateFrame2.emit(self.current_img2, img2_format_type, img2_name, forcefully_save_img)
        self.updateTimestamp.emit(self.timestamp)
        
        if(self.add_extra_image_window):
            self.current_img3, img3_format_type, img3_name = self.img3_callback(data)
            self.updateFrame3.emit(self.current_img3, img3_format_type, img3_name, forcefully_save_img)
        
    def get_img_dim(self, img):
        ch = 1
        if(len(img.shape) == 2):
            h, w = img.shape
        else:
            h, w, ch = img.shape
        
        return h, w, ch

    def jump_to_frame(self, frame_number):
        self.camera.jump_to(frame_number)
        self.current_frame_number = frame_number
        # Update the GUI if the player is paused
        if(not self.is_playing):
            # Get the data
            self.status, data = self.camera.get_next_stereo_images()
            # Update the frame number
            self.current_frame_number = data["index"]
            # Store Data
            self.data = data
            # Send this data to process
            self.send_data_to_camera(data, old_frame = False)
            # print("Jump to frame")
            # Update the GUI
            self.update(data)

    def close(self):
        self.camera.close()
        
    def toggle_play_pause_state(self):
        self.is_playing = not self.is_playing
    