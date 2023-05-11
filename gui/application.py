import os
import sys
import time
from PIL import Image

from datetime import datetime
import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
import numpy as np
import pyqtgraph as pg
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QIntValidator
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QSlider,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QFileDialog,
                               QLineEdit, QFormLayout, QScrollArea, QCheckBox)
from gui.process import Process
from gui.recorder import Recorder

from gui.utils import DATASET_TYPE
from gui.widgets import DatasetWidget, DynamicParameterWidget, ImageSaveWidget, PlotWidget, SaveMenuWidget, StartStopResetWidget, TimestampWidget, VideoControlWidget

class Application(QMainWindow):
    def __init__(self, add_extra_image_window = False, add_plotter = False):        
        self.app = QApplication()
        super().__init__()
        
        # Params
        self.add_plotter = add_plotter
        self.is_playing = False
        self.init_file_name1 = False
        self.init_file_name2 = False
        self.selected_dataset_type = DATASET_TYPE.ZED
        self.on_frame_jump_callback = None
        self.dynamic_paramters = {}
        self.add_extra_image_window = add_extra_image_window
        
        # Title and dimensions
        self.setWindowTitle("Sequencer 2.0")
        
        # Init Menu bar
        self.init_menu_bar()
        
        # Get Images Layout
        self.images_layout = self.get_images_layout(add_extra_image_window = self.add_extra_image_window) 

        # Get Dynamic Parameters Layout
        self.dynamic_parameters_layout, self.dynamic_parameters_scroll_widget = self.get_dynamic_params_layout()
        
        # Create Video Control Layout
        self.video_control_widget = VideoControlWidget(is_playing=self.is_playing)
        
        # Create Widget for Datasets
        self.dataset_widget = DatasetWidget(dataset_type=DATASET_TYPE.ZED)
        
        # Save Menu Widget
        self.save_menu_widget = SaveMenuWidget()
        
        # Timestamp Widget
        self.timestamp_widget = TimestampWidget(on_export=self.on_export_timestamp)
        
        # Start Stop Buttons Widget
        self.start_stop_reset_button_widget = StartStopResetWidget()
        
        if(self.add_plotter):
            # Create a plot widget
            self.plot_widget = PlotWidget(x_label = 'Time (seconds)', y_label = 'Rotation (Degrees)')
        
        # Init the UI
        self.init_gui()
        
        # Init the callbacks
        self.init_callbacks()
        
        # Thread in charge of updating the image
        self.process = Process(self, add_extra_image_window = add_extra_image_window)
        self.process.finished.connect(self.close)
        self.process.on_eof = self.on_eof
        self.process.updateFrame1.connect(self.setImage1)
        self.process.updateFrame2.connect(self.setImage2)
        self.process.updateTimestamp.connect(self.set_timestamp)
        
        if(add_extra_image_window):
            self.process.updateFrame3.connect(self.setImage3)
            
        # Recorder
        self.recorder = Recorder()

    def reset(self):
        self.process.reset_process()
        
        print("Reseting GUI")
        self.image1.reset()
        self.image2.reset()
        if(self.add_extra_image_window):
            self.image3.reset()
            
        self.video_control_widget.reset()
        self.dataset_widget.reset()
        self.save_menu_widget.reset()
        self.start_stop_reset_button_widget.reset()
        if(self.add_plotter):
            self.plot_widget.reset()
        self.recorder.reset()
        
        
    def init_menu_bar(self):
        # Main menu bar
        self.menu = self.menuBar()
        
        # File Option
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        # About Option
        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=qApp.aboutQt)
        self.menu_about.addAction(about)


    def get_images_layout(self, add_extra_image_window = False):
        # Create widgets for images with save box
        self.image1 = ImageSaveWidget(on_save=self.on_save_image1)
        self.image2 = ImageSaveWidget(on_save=self.on_save_image2)
            
        # Multiple Images layout
        images_layout = QHBoxLayout()
        images_layout.addWidget(self.image1, 50)
        images_layout.addWidget(self.image2, 50)
        
        if(add_extra_image_window):
            self.image3 = ImageSaveWidget(on_save=self.on_save_image3)
            images_layout.addWidget(self.image3, 50)
        
        return images_layout
        
    def get_dynamic_params_layout(self):
        # scroll area widget contents - layout
        dynamic_parameters_layout = QFormLayout()

        # scroll area widget contents
        dynamic_parameters_scroll_widget = QWidget()
        dynamic_parameters_scroll_widget.setLayout(dynamic_parameters_layout)

        return dynamic_parameters_layout, dynamic_parameters_scroll_widget
    
    def init_gui(self):
        # Save Menu and Timestamp WIdget
        self.save_menu_layout = QHBoxLayout()
        self.save_menu_layout.addWidget(self.save_menu_widget)
        self.save_menu_layout.addWidget(self.timestamp_widget)
        
        # Central Dataset and Start Stop Buttons Layout
        self.dataset_and_buttons_layout = QHBoxLayout()
        self.dataset_and_buttons_layout.addWidget(self.dataset_widget, 80)
        self.dataset_and_buttons_layout.addWidget(self.start_stop_reset_button_widget, 20)

        # Central Image and Dynamic Parameters Layout
        self.image_param_layout = QHBoxLayout()
        self.image_param_layout.addLayout(self.images_layout)
        self.image_param_layout.addWidget(self.dynamic_parameters_scroll_widget)
        
        # Main layout
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.save_menu_layout)
        self.layout.addLayout(self.image_param_layout)
        if(self.add_plotter):
            self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.video_control_widget)
        self.layout.addLayout(self.dataset_and_buttons_layout)

        # Central widget
        self.widget = QWidget(self)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def init_callbacks(self):
        # Connections
        
        self.start_stop_reset_button_widget.set_on_start(self.on_start)
        self.start_stop_reset_button_widget.set_on_stop(self.on_stop)
        self.start_stop_reset_button_widget.set_on_reset(self.on_reset)
        
        self.video_control_widget.set_on_play_pause(self.on_play_pause)
        self.video_control_widget.set_on_frame_jump(self.on_frame_jump)
        self.video_control_widget.set_on_slider_value_changed(self.on_slider_value_changed)
        self.video_control_widget.set_on_slider_moved(self.on_slider_moved)
        self.video_control_widget.set_on_next_frame(self.on_next_frame)
        self.video_control_widget.set_on_prev_frame(self.on_prev_frame)
                
        self.save_menu_widget.set_on_save_dir_selected(self.on_save_dir_selected)
        self.save_menu_widget.set_on_file_name_prefix_checkbox_state_change(self.on_file_name_prefix_checkbox_state_change)
        self.save_menu_widget.set_on_use_jpeg_ext_checkbox_state_change(self.on_use_jpeg_ext_checkbox_state_change)
        self.save_menu_widget.set_on_use_pdf_ext_checkbox_state_change(self.on_use_pdf_ext_checkbox_state_change)

    @Slot()
    def on_eof(self):
        self.video_control_widget.set_pause()

    @Slot()
    def on_save_image1(self, file_name):
        self.recorder.save_figure(file_name, 1)
        
    @Slot()
    def on_save_image2(self, file_name):
        self.recorder.save_figure(file_name, 2)
        
    @Slot()
    def on_save_image3(self, file_name):
        self.recorder.save_figure(file_name, 3)
        
    def on_export_timestamp(self, file_name):
        self.recorder.save_timestamps(file_name)

    @Slot()
    def on_start(self):
        print("Starting...")
                
        if(self.dataset_widget.dataset_type == DATASET_TYPE.ZED):
            self.process.on_start(self.dataset_widget.zed_dataset_widget.zed_dataset_file_path,
                                  self.dataset_widget.zed_dataset_widget.zed_label_folder_path)
        elif(self.dataset_widget.dataset_type == DATASET_TYPE.KITTI):
            self.process.on_start(self.dataset_widget.kitti_dataset_widget.kitti_left_folder_path, 
                                  self.dataset_widget.kitti_dataset_widget.kitti_right_folder_path, 
                                  self.dataset_widget.kitti_dataset_widget.kitti_label_folder_path, 
                                  self.dataset_widget.kitti_dataset_widget.kitti_calib_file_path, 
                                  self.dataset_widget.kitti_dataset_widget.kitti_poses_file_path, 
                                  self.dataset_widget.kitti_dataset_widget.kitti_time_file_path)
        
        # Set the frame count to Video Control GUI
        frame_count = self.process.camera.get_frame_count()
        self.video_control_widget.set_maximum_frame_count(frame_count)
        
        # Enable the play button
        self.video_control_widget.set_play_pause_enabled_state(is_enabled=True)
        
        # Start the process
        self.process.start_process()

    @Slot()
    def on_stop(self):
        print("Stopping...")
        
        # Disable the play button
        self.video_control_widget.set_play_pause_enabled_state(is_enabled=False)
        
        if(self.process.isRunning()):
            # Change the logic
            self.process.close()
            self.status = False
            self.process.terminate()
        # Give time for the thread to finish
        time.sleep(1)
        
        self.close()

    @Slot()
    def on_reset(self):
        print("Resetting...")

    @Slot()
    def on_play_pause(self, is_playing):
        self.process.toggle_play_pause_state()
        
    @Slot()
    def on_save_dir_selected(self, dir_name):
        self.recorder.save_dir_name = dir_name
        
    @Slot()
    def on_frame_jump(self, frame_number):
        # Clear the plot
        # self.clear_plot()
        self.on_frame_jump_callback(frame_number)
        # Jump the frame number in thread
        self.process.jump_to_frame(frame_number)
    
    @Slot()
    def on_slider_value_changed(self, frame_number):
        self.process.jump_to_frame(frame_number)
        
    @Slot()
    def on_slider_moved(self, frame_number):
        # self.clear_plot()
        self.on_frame_jump_callback(frame_number)
        
    
    @Slot()
    def on_prev_frame(self, frame_number):
        # Clear the plot
        # self.clear_plot()
        self.on_frame_jump_callback(frame_number)
        # Jump the frame number in thread
        self.process.jump_to_frame(frame_number)
        
    @Slot()
    def on_next_frame(self, frame_number):
        # Jump the frame number in thread
        self.process.jump_to_frame(frame_number)
        
    @Slot()
    def on_file_name_prefix_checkbox_state_change(self, state):
        self.recorder.add_date_prefix_to_file_name = state

    @Slot()
    def on_use_jpeg_ext_checkbox_state_change(self, state):
        self.recorder.use_jpeg_file_ext = state

    @Slot()
    def on_use_pdf_ext_checkbox_state_change(self, state):
        self.recorder.use_pdf_file_ext = state

    @Slot(QImage)
    def setImage1(self, image, image_type, image_name):
        # Update the frame in the recorder
        self.recorder.img1 = image
        
        # Update the frame in UI
        self.image1.set_image(image, image_type, image_name, auto_update=self.process.is_playing)
        
        # Just update the position of the slider. Dont call update_frame_number()
        self.video_control_widget.update(frame_number=self.process.current_frame_number, block_signals=True)
        
    @Slot(QImage)
    def setImage2(self, image, image_type, image_name):
        # Update the frame in the recorder
        self.recorder.img2 = image
                
        # Update the frame in UI
        self.image2.set_image(image, image_type, image_name, auto_update=self.process.is_playing)
        
    @Slot(QImage)
    def setImage3(self, image, image_type, image_name):
        # Update the frame in the recorder
        self.recorder.img3 = image
                
        # Update the frame in UI
        self.image3.set_image(image, image_type, image_name, auto_update=self.process.is_playing)
        
    @Slot(QImage)
    def set_timestamp(self, timestamp):
        # Update the frame in UI
        self.timestamp_widget.set_timestamp(timestamp)
        
        self.recorder.add_timestamp(timestamp)
        
    def close(self):
        sys.exit(self.app.exec())
        
    def set_on_start(self, on_start):
        self.process.on_start = on_start
        
    def set_on_reset(self, on_reset):
        self.start_stop_reset_button_widget.set_on_reset(on_reset)
        
    def update_rpy_estimates(self, timestamp, r, p, y, average_filter = False):
        if(self.add_plotter):
            self.plot_widget.update_rpy_plot(timestamp, r, p, y, filter if average_filter else None)
    
    def apply_box_filtering(self, data, kernel_size = 5):
        if(len(data) < kernel_size):
            return data
        kernel = np.ones(kernel_size) / kernel_size
        
        return np.convolve(data, kernel, mode='same')
        
    def set_camera(self, camera):
        self.process.camera = camera
        
    def set_img1_callback(self, img_callback):
        self.process.img1_callback = img_callback
        
    def set_img2_callback(self, img_callback):
        self.process.img2_callback = img_callback
        
    def set_img3_callback(self, img_callback):
        self.process.img3_callback = img_callback
        
    def set_timestamp_callback(self, timestamp_callback):
        self.process.timestamp_callback = timestamp_callback
        
    def set_send_data_to_camera(self, func):
        self.process.send_data_to_camera = func
        
    def add_dynamic_parameter(self, parameter_name, on_parameter_set_callback):
        self.dynamic_paramters[parameter_name] = DynamicParameterWidget(parameter_name=parameter_name, callback=on_parameter_set_callback)
        
        self.dynamic_parameters_layout.addRow(QLabel(parameter_name), self.dynamic_paramters[parameter_name])

    def clear_plot(self):
        if(self.add_plotter):
            self.plot_widget.clear_plot()
        
    def activate_tracking_mode(self):
        self.process.tracking_mode = True