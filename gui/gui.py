import os
import sys
import time
from PIL import Image

from datetime import datetime
import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
import numpy as np
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QIntValidator
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QSlider,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QFileDialog,
                               QLineEdit, QFormLayout, QScrollArea, QCheckBox)


from enum import Enum

class GUImageTypes(Enum):
    RGB = QImage.Format_RGB888 # The image is stored using a 24-bit RGB format (8-8-8).
    BGR = QImage.Format_BGR888 # The image is stored using a 24-bit BGR format (8-8-8).
    GRAY8 = QImage.Format_Grayscale8 # The image is stored using an 8-bit grayscale format. 
    GRAY16 = QImage.Format_Grayscale16 # The image is stored using an 16-bit grayscale format. 

class DATASET_TYPE(Enum):
    ZED = 0
    KITTI = 1
    VIDEO = 2

class Thread(QThread):
    updateFrame1 = Signal(QImage, str)
    updateFrame2 = Signal(QImage, str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.trained_file = None
        self.status = True
        self.cap = True
        self.save_dir_name = None
        self.current_frame_number = 0
        self.is_playing = False
        self.current_img1 = None
        self.current_img2 = None
        self.add_date_prefix_to_file_name = False
        self.use_jpeg_file_ext = True
        self.use_pdf_file_ext = False
        self.tracking_mode = False
        self.data = {}
        
        # Datasets
        self.zed_dataset_file_path = "/home/vipul/Documents/ZED/loop_closure_zeabuz.svo"
        self.kitti_dataset_folder_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_color/dataset/sequences/00"
        self.kitti_calib_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_calib/dataset/sequences/00/calib.txt"
        self.kitti_time_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_calib/dataset/sequences/00/times.txt"
        self.kitti_poses_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_poses/dataset/poses/00.txt"
        
        # Callbacks
        self.on_start = None
        self.img1_callback = None
        self.img2_callback = None
        self.send_data_to_camera = None
        
        # Objects
        self.camera = None

    def set_zed_file(self, fname):
        self.zed_dataset_file_path = fname
        
    def set_save_dir(self, dir_name):
        self.save_dir_name = dir_name
        print(dir_name)

    def run(self):
        while self.status:
            
            self.status, data = self.camera.get_next_stereo_images()
            
            # If no data is left
            if(not self.status):
                break
            
            # Update the frame number
            self.current_frame_number = data["index"]
            
            # Store Data
            self.data = data
            
            # Send this data to process
            self.send_data_to_camera(data, old_frame = False)
            
            # Update the frame
            self.update(data=data)
            
            # print(self.current_frame_number)
            while(not self.is_playing):
                # Do not send new data to the camera
                if(self.tracking_mode):
                    time.sleep(0.001)
                    continue
                # print(self.current_frame_number)
                # Send this data to process
                self.send_data_to_camera(self.data, old_frame = True)
                self.update(data=self.data)
                # time.sleep(1)
                continue
        sys.exit(-1)

    def update(self, data = {}):
        # Current image on display
        # self.current_img = data['left_img']
        self.current_img1, img1_format_type, img1_name = self.img1_callback(data)
        self.current_img2, img2_format_type, img2_name = self.img2_callback(data)
        
        # Creating and scaling QImage
        h, w, ch = self.get_img_dim(self.current_img1)
        img1 = QImage(self.current_img1.data, w, h, ch * w, img1_format_type.value)
        scaled_img1 = img1.scaled(640, 480, Qt.KeepAspectRatio)
        
        # Creating and scaling QImage
        h, w, ch = self.get_img_dim(self.current_img2)
        img2 = QImage(self.current_img2.data, w, h, ch * w, img2_format_type.value)
        scaled_img2 = img2.scaled(640, 480, Qt.KeepAspectRatio)

        # Emit signal
        self.updateFrame1.emit(scaled_img1, img1_name)
        self.updateFrame2.emit(scaled_img2, img2_name)
        
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
            # Update the GUI
            self.update(data)

    def close(self):
        self.camera.close()
        
    def toggle_play_pause_state(self):
        self.is_playing = not self.is_playing
        
    def save_figure(self, img_name, img_idx):
        prefix = ""
        suffix = ""
        if(self.add_date_prefix_to_file_name):
            prefix = datetime.today().strftime("%Y%m%d") + "-"
            
        if(img_idx == 1):
            img = self.current_img1
        if(img_idx == 2):
            img = self.current_img2
            
        if(self.use_jpeg_file_ext):
            final_path = f"{self.save_dir_name}/{prefix}{img_name}.jpeg"
            cv2.imwrite(final_path, img)
        
        if(self.use_pdf_file_ext):
            final_path = f"{self.save_dir_name}/{prefix}{img_name}.pdf"
            
            fr = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            pdf_img = Image.fromarray(fr)
            pdf_img = pdf_img.convert('RGB')
            pdf_img.save(final_path)
        
        print(final_path)

class DynamicParameterWidget(QWidget):
    def __init__(self, parameter_name, callback, parent=None):
        QWidget.__init__(self, parent=parent)
        
        self.parameter_name = parameter_name
        self.callback = callback
        
        # self.label = QLabel(parameter_name)
        self.input_box = QLineEdit(self)
        self.set_button = QPushButton("Set")
        
        self.layout = QHBoxLayout()
        
        # self.layout.addWidget(self.label, 40)
        self.layout.addWidget(self.input_box, 60)
        self.layout.addWidget(self.set_button, 40)
        
        self.set_button.clicked.connect(self.on_button_click)
        
        self.setLayout(self.layout)
        
    def on_button_click(self):
        input_data = self.input_box.text()
        self.callback(input_data)

class Window(QMainWindow):
    def __init__(self):        
        self.app = QApplication()
        super().__init__()
        
        # Params
        self.init_file_name1 = False
        self.init_file_name2 = False
        self.rolls = []
        self.pitchs = []
        self.yaws = []
        self.timestamps = []
        self.selected_dataset_type = DATASET_TYPE.ZED
        self.on_frame_jump = None
        
        # Title and dimensions
        self.setWindowTitle("Sequencer 2.0")
        # self.setGeometry(0, 0, 800, 500)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=qApp.aboutQt)
        self.menu_about.addAction(about)

        # Create an input box to enter the filename of the image to be saved
        self.image1_name_text_box = QLineEdit(self)
        self.image1_save_button = QPushButton("Save")
        self.image1_save_layout = QHBoxLayout()
        self.image1_save_layout.addWidget(self.image1_name_text_box, 80)
        self.image1_save_layout.addWidget(self.image1_save_button, 20)
        
        # Create a label for the display camera
        self.image1 = QLabel(self)
        self.image1.setFixedSize(640, 480)
        
        # Single image layout
        self.image1_layout = QVBoxLayout()
        self.image1_layout.addLayout(self.image1_save_layout)
        self.image1_layout.addWidget(self.image1)
        
        
        # Create an input box to enter the filename of the image to be saved
        self.image2_name_text_box = QLineEdit(self)
        self.image2_save_button = QPushButton("Save")
        self.image2_save_layout = QHBoxLayout()
        self.image2_save_layout.addWidget(self.image2_name_text_box, 80)
        self.image2_save_layout.addWidget(self.image2_save_button, 20)
        
        # Create a label for the display camera
        self.image2 = QLabel(self)
        self.image2.setFixedSize(640, 480)
        
        # Single image layout
        self.image2_layout = QVBoxLayout()
        self.image2_layout.addLayout(self.image2_save_layout)
        self.image2_layout.addWidget(self.image2)
        
        # Multiple Images layout
        self.images_layout = QHBoxLayout()
        self.images_layout.addLayout(self.image1_layout)
        self.images_layout.addLayout(self.image2_layout)

        ## Create dynamic parameters
        self.dynamic_paramters = {}
        # self.dynamic_parameters_layout = QVBoxLayout()
        
        # scroll area widget contents - layout
        self.dynamic_parameters_layout = QFormLayout()

        # scroll area widget contents
        self.scrollWidget = QWidget()
        self.scrollWidget.setLayout(self.dynamic_parameters_layout)

        # scroll area
        # self.scrollArea = QScrollArea()
        # self.scrollArea.setWidgetResizable(True)
        # self.scrollArea.setWidget(self.scrollWidget)

        # Central Window Layout
        self.image_param_layout = QHBoxLayout()
        self.image_param_layout.addLayout(self.images_layout)
        self.image_param_layout.addWidget(self.scrollWidget)
        # self.image_param_layout.addLayout(self.dynamic_parameters_layout, 20)
        

        # Create a slider to interact with the dataset
        self.is_playing = False
        self.play_pause_button = QPushButton("Play")
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.frame_number_label = QLabel("")
        
        # Create button to jump to prev and next frame
        self.next_frame_button = QPushButton("Next")
        self.prev_frame_button = QPushButton("Prev")
        
        # Create an input box to enter the frame number
        self.frame_number_text_box = QLineEdit(self)
        self.frame_number_jump_button = QPushButton("Go To")
        self.frame_number_layout = QHBoxLayout()
        self.frame_number_layout.addWidget(self.frame_number_text_box, 50)
        self.frame_number_layout.addWidget(self.frame_number_jump_button, 50)
        
        # Slider layout
        self.slider_layout = QHBoxLayout()

        self.slider_layout.addWidget(self.play_pause_button, 10)
        self.slider_layout.addWidget(self.slider, 70)
        self.slider_layout.addWidget(self.prev_frame_button, 5)
        self.slider_layout.addWidget(self.next_frame_button, 5)
        self.slider_layout.addWidget(self.frame_number_label, 5)
        self.slider_layout.addLayout(self.frame_number_layout, 5)

        # Thread in charge of updating the image
        self.th = Thread(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame1.connect(self.setImage1)
        self.th.updateFrame2.connect(self.setImage2)

        # File Save Menu
        self.save_menu_layout = QHBoxLayout()

        self.select_save_file_button = QPushButton("Select Save Directory")
        self.file_name_prefix_checkbox = QCheckBox("Date Prefix", self)
        self.use_jpeg_ext_checkbox = QCheckBox("Use .jpeg", self)
        self.use_jpeg_ext_checkbox.setChecked(True)
        self.use_pdf_ext_checkbox = QCheckBox("Use .pdf", self)
        self.save_menu_layout.addWidget(QLabel("Save Dir:"), 10)
        self.save_menu_layout.addWidget(self.select_save_file_button, 70)
        self.save_menu_layout.addWidget(self.file_name_prefix_checkbox, 10)
        self.save_menu_layout.addWidget(self.use_jpeg_ext_checkbox, 10)
        self.save_menu_layout.addWidget(self.use_pdf_ext_checkbox, 10)
        
        # Dataset type
        self.dataset_type_list_widget = QComboBox()
        self.dataset_type_list_widget.addItems([DATASET_TYPE.ZED.name, DATASET_TYPE.KITTI.name, DATASET_TYPE.VIDEO.name])
        
        # Create a group for datasets
        self.dataset_group_model = QGroupBox("Dataset Selection")
        self.dataset_group_model.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Create UI for ZED
        self.zed_dataset_file_label = QLabel("File")
        self.zed_dataset_file_button = QPushButton("Select SVO FIle")
        
        self.zed_layout = QHBoxLayout()
        self.zed_layout.addWidget(self.zed_dataset_file_label, 10)
        self.zed_layout.addWidget(self.zed_dataset_file_button, 90)
        
        self.zed_layout_widget = QWidget()
        self.zed_layout_widget.setLayout(self.zed_layout)
        
        # Create UI for KITTI
        self.kitti_dataset_file_label = QLabel("Images Folder")
        self.kitt_dataset_folder_button = QPushButton("Select Folder")
        self.kitti_dataset_poses_label = QLabel("Pose File")
        self.kitt_dataset_poses_file_button = QPushButton("Select Pose FIle")
        self.kitti_dataset_calib_label = QLabel("Calibration File")
        self.kitt_dataset_calib_file_button = QPushButton("Select Calibration FIle")
        self.kitti_dataset_time_label = QLabel("Timestamps File")
        self.kitt_dataset_time_file_button = QPushButton("Select Timestamps FIle")
        
        self.kitti_layout = QHBoxLayout()
        self.kitti_layout.addWidget(self.kitti_dataset_file_label, 7)
        self.kitti_layout.addWidget(self.kitt_dataset_folder_button, 18)
        self.kitti_layout.addWidget(self.kitti_dataset_poses_label, 7)
        self.kitti_layout.addWidget(self.kitt_dataset_poses_file_button, 18)
        self.kitti_layout.addWidget(self.kitti_dataset_calib_label, 7)
        self.kitti_layout.addWidget(self.kitt_dataset_calib_file_button, 18)
        self.kitti_layout.addWidget(self.kitti_dataset_time_label, 7)
        self.kitti_layout.addWidget(self.kitt_dataset_time_file_button, 18)
        
        self.kitti_layout_widget = QWidget()
        self.kitti_layout_widget.setLayout(self.kitti_layout)
        
        # Layout for dataset menu and dataset ui
        self.dataset_layout = QHBoxLayout()
        self.dataset_layout.addWidget(self.dataset_type_list_widget, 10)
        self.dataset_layout.addWidget(self.zed_layout_widget, 90)
        self.dataset_layout.addWidget(self.kitti_layout_widget, 90)
        
        if(self.dataset_type_list_widget.currentIndex() == DATASET_TYPE.ZED.value):
            self.selected_dataset_type = DATASET_TYPE.ZED
            self.kitti_layout_widget.hide()
        if(self.dataset_type_list_widget.currentIndex() == DATASET_TYPE.KITTI.value):
            self.selected_dataset_type = DATASET_TYPE.KITTI
            self.zed_layout_widget.hide()

        # Add dataset to dataset group
        self.dataset_group_model.setLayout(self.dataset_layout)
        
        # File Selection Menu
        # self.group_model = QGroupBox("Dataset Filepath")
        # self.group_model.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # model_layout = QHBoxLayout()

        # model_layout.addWidget(self.dataset_type_list_widget)
        # self.select_file_button = QPushButton("Select File")
        
        # model_layout.addWidget(QLabel("File:"), 10)
        # model_layout.addWidget(self.select_file_button, 90)
        # self.group_model.setLayout(model_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop/Close")
        # self.start_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # self.stop_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.start_button)

        right_layout = QHBoxLayout()
        right_layout.addWidget(self.dataset_group_model, 1)
        right_layout.addLayout(buttons_layout, 1)

        
        # Create a plot
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        #Add legend
        self.graph_widget.addLegend()
        styles = {'color':'r', 'font-size':'20px'}
        self.graph_widget.setLabel('left', 'Rotation (Degrees)', **styles)
        self.graph_widget.setLabel('bottom', 'Time (seconds)', **styles)
        
        # Set plots
        self.r_plot = self.graph_widget.plot(self.timestamps, self.rolls, "Roll", 'r')
        self.y_plot = self.graph_widget.plot(self.timestamps, self.pitchs, "Pitch", 'b')
        self.p_plot = self.graph_widget.plot(self.timestamps, self.yaws, "Yaw", 'g')
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(self.save_menu_layout)
        # layout.addLayout(self.images_layout)
        layout.addLayout(self.image_param_layout)
        layout.addWidget(self.graph_widget)
        # layout.addLayout(self.image_save_layout)
        # layout.addWidget(self.label)
        layout.addLayout(self.slider_layout)
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.kill_thread)
        self.stop_button.setEnabled(False)
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.clicked.connect(self.play_pause_video)
        self.zed_dataset_file_button.clicked.connect(self.select_zed_file)
        self.kitt_dataset_folder_button.clicked.connect(self.select_kitti_dataset_folder)
        self.kitt_dataset_time_file_button.clicked.connect(self.select_kitti_time_file)
        self.kitt_dataset_calib_file_button.clicked.connect(self.select_kitti_calib_file)
        self.kitt_dataset_poses_file_button.clicked.connect(self.select_kitti_poses_file)
        self.select_save_file_button.clicked.connect(self.select_save_dir)
        self.image1_save_button.clicked.connect(self.save_image1)
        self.image2_save_button.clicked.connect(self.save_image2)
        self.frame_number_jump_button.clicked.connect(self.jumpt_to_frame)
        self.slider.valueChanged.connect(self.update_frame_number)
        self.slider.sliderMoved.connect(self.clear_plot)
        self.prev_frame_button.clicked.connect(self.jump_to_prev_frame)
        self.next_frame_button.clicked.connect(self.jump_to_next_frame)
        self.file_name_prefix_checkbox.stateChanged.connect(self.on_file_name_prefix_checkbox_state_change)
        self.use_jpeg_ext_checkbox.stateChanged.connect(self.on_use_jpeg_ext_checkbox_state_change)
        self.use_pdf_ext_checkbox.stateChanged.connect(self.on_use_pdf_ext_checkbox_state_change)
        self.dataset_type_list_widget.activated.connect(self.on_dataset_type_changed)

    @Slot()
    def select_kitti_dataset_folder(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.th.kitti_dataset_folder_path = dataset_path
        self.kitt_dataset_folder_button.setText(dataset_path.split('/')[-1])

    @Slot()
    def select_kitti_time_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.th.kitti_time_file_path = file_path
        self.kitt_dataset_time_file_button.setText(file_path.split('/')[-1])
    
    @Slot()
    def select_kitti_calib_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.th.kitti_calib_file_path = file_path
        self.kitt_dataset_calib_file_button.setText(file_path.split('/')[-1])
    
    @Slot()
    def select_kitti_poses_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.th.kitti_poses_file_path = file_path
        self.kitt_dataset_poses_file_button.setText(file_path.split('/')[-1])
    
    @Slot()
    def select_zed_file(self):
        dataset_path = QFileDialog.getOpenFileName()[0]
        self.th.set_zed_file(dataset_path)
        self.zed_dataset_file_button.setText(dataset_path.split('/')[-1])
        
    @Slot()
    def on_dataset_type_changed(self, index):
        if(index == DATASET_TYPE.ZED.value):
            self.selected_dataset_type = DATASET_TYPE.ZED
            self.kitti_layout_widget.hide()
            self.zed_layout_widget.show()
        if(index == DATASET_TYPE.KITTI.value):
            self.selected_dataset_type = DATASET_TYPE.KITTI
            self.kitti_layout_widget.show()
            self.zed_layout_widget.hide()
            

    @Slot()
    def on_file_name_prefix_checkbox_state_change(self, state):
        self.th.add_date_prefix_to_file_name = state

    @Slot()
    def on_use_jpeg_ext_checkbox_state_change(self, state):
        self.th.use_jpeg_file_ext = state
        self.use_pdf_ext_checkbox.setChecked(not state)

    @Slot()
    def on_use_pdf_ext_checkbox_state_change(self, state):
        self.th.use_pdf_file_ext = state
        self.use_jpeg_ext_checkbox.setChecked(not state)

    @Slot()
    def play_pause_video(self):
        self.is_playing = not self.is_playing
        
        self.play_pause_button.setText("Pause" if self.is_playing else "Play")
        self.th.toggle_play_pause_state()

    @Slot()
    def save_image1(self):
        file_name = self.image1_name_text_box.text()
        if(file_name != ""):
            self.th.save_figure(file_name, 1)
            
    @Slot()
    def save_image2(self):
        file_name = self.image2_name_text_box.text()
        if(file_name != ""):
            self.th.save_figure(file_name, 2)
        
    @Slot()
    def select_save_dir(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.th.set_save_dir(dataset_path)
        self.select_save_file_button.setText(dataset_path)

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        # self.th.cap.release()
        # cv2.destroyAllWindows()
        self.th.close()
        self.status = False
        self.th.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start(self):
        print("Starting...")
        self.stop_button.setEnabled(True)
        self.play_pause_button.setEnabled(True)
        self.start_button.setEnabled(False)
        # self.th.set_file(self.combobox.currentText())
        if(self.selected_dataset_type == DATASET_TYPE.ZED):
            self.th.on_start(self.th.zed_dataset_file_path)
        elif(self.selected_dataset_type == DATASET_TYPE.KITTI):
            self.th.on_start(self.th.kitti_dataset_folder_path, self.th.kitti_calib_file_path, self.th.kitti_poses_file_path, self.th.kitti_time_file_path)
        
        # Update the maximum number of frames to the slider
        frame_count = self.th.camera.get_frame_count()
        self.slider.setMaximum(frame_count)
        
        # Set the maximum number of frame to the input text box
        self.frame_number_text_box.setValidator(QIntValidator(0, frame_count))
        
        self.th.start()

    @Slot(QImage)
    def setImage1(self, image, image_name):
        self.image1.setPixmap(QPixmap.fromImage(image))
        
        if(not self.init_file_name1):
            # Update the image name to the save bar
            self.image1_name_text_box.setText(image_name)
            self.init_file_name1 = True
        # Just update the position of the slider. Dont call update_frame_number()
        self.slider.blockSignals(True)
        self.update_slider_pos()
        self.slider.blockSignals(False)
        
    @Slot(QImage)
    def setImage2(self, image, image_name):
        self.image2.setPixmap(QPixmap.fromImage(image))
        
        if(not self.init_file_name2):
            # Update the image name to the save bar
            self.image2_name_text_box.setText(image_name)
            self.init_file_name2 = True
        
    @Slot()
    def update_frame_number(self, frame_number):
        self.th.jump_to_frame(frame_number)
        self.frame_number_label.setText(f"{frame_number}")
        
    @Slot()
    def jumpt_to_frame(self):
        frame_number = int(self.frame_number_text_box.text())

        # Clear the plot
        self.clear_plot()
        # Jump the frame number in thread
        self.th.jump_to_frame(frame_number)
        
        # Update slider
        self.update_slider_pos(frame_count=frame_number)
    
    @Slot()
    def jump_to_prev_frame(self):
        frame_number = max(self.th.current_frame_number - 1, 0)

        # Clear the plot
        self.clear_plot()
        # Jump the frame number in thread
        self.th.jump_to_frame(frame_number)
        
        # Update slider
        self.update_slider_pos(frame_count=frame_number)
        
    @Slot()
    def jump_to_next_frame(self):
        frame_number = min(self.th.current_frame_number + 1, self.th.camera.get_frame_count() - 1)
        
        # Jump the frame number in thread
        self.th.jump_to_frame(frame_number)
        
        # Update slider
        self.update_slider_pos(frame_count=frame_number)
    
    def close(self):
        sys.exit(self.app.exec())
        
    def set_on_start(self, on_start):
        self.th.on_start = on_start
        
    def update_rpy_estimates(self, timestamp, r, p, y, average_filter = False):
        self.timestamps.append(timestamp)
        self.rolls.append(r)
        self.pitchs.append(p)
        self.yaws.append(y)
        
        if(average_filter):
            rolls = self.apply_box_filtering(self.rolls)
            pitchs = self.apply_box_filtering(self.pitchs)
            yaws = self.apply_box_filtering(self.yaws)

        else:
            rolls = self.rolls
            pitchs = self.pitchs
            yaws = self.yaws
        
        self._plot(self.r_plot, self.timestamps, rolls, "Roll", 'r')
        self._plot(self.p_plot, self.timestamps, pitchs, "Pitch", 'b')
        self._plot(self.y_plot, self.timestamps, yaws, "Yaw", 'g')
    
    def _plot(self, plt, x, y, plotname, color):
        pen = pg.mkPen(color=color, width=5)
        plt.setData(x, y, name=plotname, pen=pen, symbol='star', symbolSize=1, symbolBrush=(color))
        self.graph_widget.addLegend()
    
    def apply_box_filtering(self, data, kernel_size = 5):
        if(len(data) < kernel_size):
            return data
        kernel = np.ones(kernel_size) / kernel_size
        
        return np.convolve(data, kernel, mode='same')
        
    def set_camera(self, camera):
        self.th.camera = camera
        
    def set_img1_callback(self, img_callback):
        self.th.img1_callback = img_callback
        
    def set_img2_callback(self, img_callback):
        self.th.img2_callback = img_callback
        
    def set_send_data_to_camera(self, func):
        self.th.send_data_to_camera = func
        
    def update_slider_pos(self, frame_count = -1):
        # Update the slider position and the text box
        frame_count = self.th.current_frame_number if frame_count == -1 else frame_count
        
        # Update the slider position
        self.slider.setValue(frame_count)
        # Update the text
        self.frame_number_label.setText(f"{frame_count}")
        
    def add_dynamic_parameter(self, parameter_name, on_parameter_set_callback):
        self.dynamic_paramters[parameter_name] = DynamicParameterWidget(parameter_name=parameter_name, callback=on_parameter_set_callback)
        
        self.dynamic_parameters_layout.addRow(QLabel(parameter_name), self.dynamic_paramters[parameter_name])

    def clear_plot(self):
        self.rolls = []
        self.pitchs = []
        self.yaws = []
        self.timestamps = []
        self._plot(self.r_plot, self.timestamps, self.rolls, "Roll", 'r')
        self._plot(self.p_plot, self.timestamps, self.pitchs, "Pitch", 'b')
        self._plot(self.y_plot, self.timestamps, self.yaws, "Yaw", 'g')
        self.on_frame_jump()
        
    def activate_tracking_mode(self):
        self.th.tracking_mode = True

if __name__ == "__main__":
    # app = QApplication()
    w = Window()
    w.show()
    w.close()
    # sys.exit(app.exec())