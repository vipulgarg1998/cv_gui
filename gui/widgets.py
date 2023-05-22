from PySide6.QtCore import Qt, Slot
import pyqtgraph as pg

from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QIntValidator

from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QSlider,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QFileDialog,
                               QLineEdit, QFormLayout, QScrollArea, QCheckBox,
                               QStackedWidget, QGridLayout)

from cv_gui.utils.flags import DATASET_TYPE
        
class ImageNameSaveWidget(QWidget):
    def __init__(self, on_save = None, parent=None, default_enabled = False):
        QWidget.__init__(self, parent=parent)
        
        self.default_enabled = default_enabled
        self.on_save = on_save
        self.auto_record = False
        self.on_auto_record_checkbox_state_change = None
        
        self.image_name_text_box = QLineEdit(self)
        self.image_save_button = QPushButton("Save")
        self.auto_record_checkbox = QCheckBox("Auto Rec", self)
        self.auto_record_checkbox.setChecked(self.default_enabled)
        
        self.image_save_layout = QHBoxLayout()
        self.image_save_layout.addWidget(self.auto_record_checkbox, 20)
        self.image_save_layout.addWidget(self.image_name_text_box, 60)
        self.image_save_layout.addWidget(self.image_save_button, 20)
        
        
        self.image_save_button.clicked.connect(self.on_save_)
        self.auto_record_checkbox.stateChanged.connect(self.on_auto_record_checkbox_state_change_)
        
        self.setLayout(self.image_save_layout)
        
    def set_image_name(self, name, auto_update = False):
        if(not self.image_name_text_box.underMouse()):
            self.image_name_text_box.setText(name)
            
    def set_on_save(self, func):
        self.on_save = func
        
    def on_auto_record_checkbox_state_change_(self, state):
        self.auto_record = state
        
    @Slot()
    def on_save_(self):
        file_name = self.image_name_text_box.text()
        
        if(file_name != ""):
            self.on_save(file_name)
            
    def reset(self):
        # Clear the name
        self.set_image_name(name="", auto_update=True)
        # Reset the checkbox
        self.auto_record_checkbox.setChecked(self.default_enabled)
            
      
class ImageWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        
        # Create a label for the display camera
        self.image = QLabel(self)
        self.image.setFixedSize(640, 480)
        
        self.image_layout = QVBoxLayout()
        self.image_layout.addWidget(self.image)
        
        self.setLayout(self.image_layout)

    def set_image(self, img, img_format_type):
        # Creating and scaling QImage
        h, w, ch = self.get_img_dim(img)
        qt_img = QImage(img.data, w, h, ch * w, img_format_type.value)
        scaled_img = qt_img.scaled(640, 480, Qt.KeepAspectRatio)
        
        self.image.setPixmap(QPixmap.fromImage(scaled_img))
        
    def get_img_dim(self, img):
        ch = 1
        if(len(img.shape) == 2):
            h, w = img.shape
        else:
            h, w, ch = img.shape
        
        return h, w, ch
    
    def reset(self):
        print("Reseting Images")
        self.image.setPixmap(QPixmap())
        self.image.clear()
        
class ImageSaveWidget(QWidget):
    def __init__(self, on_save = None, parent=None):
        QWidget.__init__(self, parent=parent)
        
        self.image_save_widget = ImageNameSaveWidget(on_save=on_save)
        
        self.image_widget = ImageWidget()
        
        self.image_save_layout = QVBoxLayout()
        self.image_save_layout.addWidget(self.image_save_widget)
        self.image_save_layout.addWidget(self.image_widget)
        
        self.setLayout(self.image_save_layout)
        
    def set_on_save(self, func):
        self.image_save_widget.set_on_save(func)
        
    def set_image(self, img, img_format_type, image_name, auto_update = False, forcefully_save_img=False):
        self.image_widget.set_image(img, img_format_type)
        
        self.image_save_widget.set_image_name(image_name, auto_update=auto_update)
        
        if((auto_update or forcefully_save_img) and self.image_save_widget.auto_record):
            self.image_save_widget.on_save_()
    
    def reset(self):
        self.image_save_widget.reset()
        self.image_widget.reset()
        
        
class TimestampWidget(QWidget):
    def __init__(self, parent=None, on_export = None):
        QWidget.__init__(self, parent=parent)
        
        self.on_export = on_export
        
        self.timestamp_label_widget = QLabel("timestamp")
        self.timestamp_text_widget = QLabel("")
        self.timestamp_export_button = QPushButton("export")
        
        self.timestamp_layout = QHBoxLayout()
        self.timestamp_layout.addWidget(self.timestamp_label_widget)
        self.timestamp_layout.addWidget(self.timestamp_text_widget)
        self.timestamp_layout.addWidget(self.timestamp_export_button)
        
        self.timestamp_export_button.clicked.connect(self.on_export_)
        
        self.setLayout(self.timestamp_layout)
        
    def set_on_export(self, func):
        self.on_export = func
        
    def set_timestamp(self, timestamp):
        self.timestamp_text_widget.setText(f"{timestamp}")
        
    def reset(self):
        self.timestamp_text_widget.setText("")
        
    def on_export_(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, 
            "Save File", "times.txt", "Text Files(*.txt)", options = options)
        if fileName and self.on_export is not None:
            self.on_export(fileName)
            

class DynamicParameterWidget(QWidget):
    def __init__(self, parameter_name, callback, parent=None, default_value = ""):
        QWidget.__init__(self, parent=parent)
        
        self.parameter_name = parameter_name
        self.param_default_value = default_value
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
        
    @Slot()
    def on_button_click(self):
        input_data = self.input_box.text()
        self.callback(input_data)
        
    def reset(self):
        self.input_box.setText(self.param_default_value)
        

class VideoControlWidget(QWidget):
    def __init__(self, is_enabled = False, is_playing = False, init_frame_number = 0, parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        self.default_is_playing = is_playing
        self.default_is_enabled = is_enabled
        self.default_init_frame_number = init_frame_number
        
        self.is_playing = is_playing
        self.is_enabled = is_enabled
        
        self.current_frame_number = init_frame_number
        self.maximum_frame_count = -1
        
        # Create a slider to interact with the dataset
        self.play_pause_button = QPushButton("Play" if not is_playing else "Pause")
        self.play_pause_button.setEnabled(self.is_enabled)
        
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.frame_number_label = QLabel(f"{self.current_frame_number}")
        
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
        
        self.setLayout(self.slider_layout)
        
        # Callback functions
        self.on_next_frame = None
        self.on_prev_frame = None
        self.on_play_pause = None
        self.on_frame_jump = None
        self.on_slider_moved = None
        self.on_slider_value_changed = None
        
        self.frame_number_jump_button.clicked.connect(self.on_frame_jump_)
        self.play_pause_button.clicked.connect(self.on_play_pause_)
        self.prev_frame_button.clicked.connect(self.on_prev_frame_)
        self.next_frame_button.clicked.connect(self.on_next_frame_)
        self.slider.valueChanged.connect(self.on_slider_value_changed_)
        self.slider.sliderMoved.connect(self.on_slider_moved_)
    
    def reset(self):        
        # Reset the variables
        self.is_playing = self.default_is_playing
        self.is_enabled = self.default_is_enabled
        
        self.current_frame_number = self.default_init_frame_number
        self.maximum_frame_count = -1
        
        # Reset the play pause button
        self.play_pause_button.setText("Play" if not self.is_playing else "Pause")
        self.set_play_pause_enabled_state(self.is_enabled)
        
        # Reset the frame label text
        self.set_frame_label(self.current_frame_number)
        
        # Reset the slider
        self.update_slider_pos_(frame_number = self.current_frame_number, block_signals = True)
        
    
    def set_play_pause_enabled_state(self, is_enabled):
        self.is_enabled = is_enabled
        self.play_pause_button.setEnabled(self.is_enabled)
        
    def set_on_next_frame(self, func):
        self.on_next_frame = func
        
    def set_on_prev_frame(self, func):
        self.on_prev_frame = func
        
    def set_on_play_pause(self, func):
        self.on_play_pause = func
        
    def set_on_frame_jump(self, func):
        self.on_frame_jump = func
        
    def set_on_slider_moved(self, func):
        self.on_slider_moved = func
        
    def set_on_slider_value_changed(self, func):
        self.on_slider_value_changed = func

    def set_pause(self):
        self.is_playing = False
        self.play_pause_button.setText("Play" if not self.is_playing else "Pause")
        self.on_play_pause(self.is_playing)
        
    def set_play(self):
        self.is_playing = True
        self.play_pause_button.setText("Play" if not self.is_playing else "Pause")
        self.on_play_pause(self.is_playing)
        
    @Slot()
    def on_play_pause_(self):
        self.is_playing = not self.is_playing
        
        self.play_pause_button.setText("Play" if not self.is_playing else "Pause")
        self.on_play_pause(self.is_playing)
        
    @Slot()
    def on_frame_jump_(self):
        frame_number = int(self.frame_number_text_box.text())
        
        self.on_frame_jump(frame_number)
        
        # Update slider
        self.update_slider_pos_(frame_number=frame_number)
        
    @Slot()
    def on_slider_value_changed_(self, frame_number):
        # Update the text
        self.set_frame_label(frame_number)
        
        self.on_slider_value_changed(frame_number)
        
    @Slot()
    def on_slider_moved_(self, frame_number):
        # Update the text
        self.set_frame_label(frame_number)
        
        self.on_slider_moved(frame_number)
        
    @Slot()
    def on_next_frame_(self, frame_number):
        frame_number = min(self.current_frame_number + 1, self.maximum_frame_count - 1)

        self.on_next_frame(frame_number)
        
        # Update slider
        self.update_slider_pos_(frame_number=frame_number)
        
    @Slot()
    def on_prev_frame_(self, frame_number):
        frame_number = max(self.current_frame_number - 1, 0)
        
        self.on_prev_frame(frame_number)
        
        # Update slider
        self.update_slider_pos_(frame_number=frame_number)
        
    def update_slider_pos_(self, frame_number = -1, block_signals = False):
        if(block_signals):
            self.slider.blockSignals(True)         
               
        # Update the slider position and the text box
        frame_number = self.current_frame_number if frame_number == -1 else frame_number
        
        # Update the slider position
        self.slider.setValue(frame_number)
        
        # Update the text
        self.set_frame_label(frame_number)
        
        if(block_signals):
            self.slider.blockSignals(False)
        
    def set_frame_label(self, frame_number):
        # Update the text
        self.frame_number_label.setText(f"{frame_number}")
        
    def update(self, frame_number, block_signals = False):
        self.current_frame_number = frame_number
        
        # Update slider
        self.update_slider_pos_(frame_number=frame_number, block_signals=block_signals)
        
    def set_maximum_frame_count(self, frame_count):
        self.maximum_frame_count = frame_count - 1
        
        self.slider.setMaximum(self.maximum_frame_count)
        # Set the maximum number of frame to the input text box
        self.frame_number_text_box.setValidator(QIntValidator(0, self.maximum_frame_count))
        
        
class SaveMenuWidget(QWidget):
    def __init__(self, parent=None, default_save_path = None, default_use_jpeg = True, default_use_pdf = False, default_use_date_prefix = False):
        
        QWidget.__init__(self, parent=parent)
        
        self.default_save_path = default_save_path
        self.default_use_jpeg = default_use_jpeg
        self.default_use_pdf = default_use_pdf
        self.default_use_date_prefix = default_use_date_prefix
        
        self.save_path = self.default_save_path
        
        # File Save Menu
        self.save_menu_layout = QHBoxLayout()

        self.select_save_file_button = QPushButton("Select Save Directory")
        self.file_name_prefix_checkbox = QCheckBox("Date Prefix", self)
        self.file_name_prefix_checkbox.setChecked(self.default_use_date_prefix)
        self.use_jpeg_ext_checkbox = QCheckBox("Use .jpeg", self)
        self.use_jpeg_ext_checkbox.setChecked(self.default_use_jpeg)
        self.use_pdf_ext_checkbox = QCheckBox("Use .pdf", self)
        self.use_pdf_ext_checkbox.setChecked(self.default_use_pdf)
        
        self.save_menu_layout.addWidget(QLabel("Save Dir:"), 10)
        self.save_menu_layout.addWidget(self.select_save_file_button, 70)
        self.save_menu_layout.addWidget(self.file_name_prefix_checkbox, 10)
        self.save_menu_layout.addWidget(self.use_jpeg_ext_checkbox, 10)
        self.save_menu_layout.addWidget(self.use_pdf_ext_checkbox, 10)
        
        self.setLayout(self.save_menu_layout)
        
        self.on_save_dir_selected = None
        self.on_file_name_prefix_checkbox_state_change = None
        self.on_use_jpeg_ext_checkbox_state_change = None
        self.on_use_pdf_ext_checkbox_state_change = None
        
        self.select_save_file_button.clicked.connect(self.on_save_dir_selected_)
        self.file_name_prefix_checkbox.stateChanged.connect(self.on_file_name_prefix_checkbox_state_change_)
        self.use_jpeg_ext_checkbox.stateChanged.connect(self.on_use_jpeg_ext_checkbox_state_change_)
        self.use_pdf_ext_checkbox.stateChanged.connect(self.on_use_pdf_ext_checkbox_state_change_)
        
    def reset(self):
        self.save_path = self.default_save_path
        self.file_name_prefix_checkbox.setChecked(self.default_use_date_prefix)
        self.use_jpeg_ext_checkbox.setChecked(self.default_use_jpeg)
        self.use_pdf_ext_checkbox.setChecked(self.default_use_pdf)
        
    def set_on_save_dir_selected(self, func):
        self.on_save_dir_selected = func
        
    def set_on_use_jpeg_ext_checkbox_state_change(self, func):
        self.on_use_jpeg_ext_checkbox_state_change = func
        
    def set_on_use_pdf_ext_checkbox_state_change(self, func):
        self.on_use_pdf_ext_checkbox_state_change = func
        
    def set_on_file_name_prefix_checkbox_state_change(self, func):
        self.on_file_name_prefix_checkbox_state_change = func
        
    @Slot()
    def on_save_dir_selected_(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        self.save_path = dialog.getExistingDirectory()
        self.select_save_file_button.setText(self.save_path)
        
        self.on_save_dir_selected(self.save_path)
        
    @Slot()
    def on_file_name_prefix_checkbox_state_change_(self, state):
        self.on_file_name_prefix_checkbox_state_change(state)
        
    @Slot()
    def on_use_jpeg_ext_checkbox_state_change_(self, state):
        self.on_use_jpeg_ext_checkbox_state_change(state)

    @Slot()
    def on_use_pdf_ext_checkbox_state_change_(self, state):
        self.on_use_pdf_ext_checkbox_state_change(state)
        
class ZEDDatasetWidget(QWidget):
    def __init__(self, parent=None, default_dataset_file_path = "/home/vipul/Documents/ZED/loop_closure_zeabuz.svo",
                 default_label_folder_path = "/home/vipul/Documents/ZED/loop_closure_dataset/env_seg"):
        
        QWidget.__init__(self, parent=parent)
        
        self.default_dataset_file_path = default_dataset_file_path
        self.default_label_folder_path = default_label_folder_path
        
        self.zed_dataset_file_path = self.default_dataset_file_path
        self.zed_label_folder_path = self.default_label_folder_path
        
        # Create UI for ZED
        self.zed_dataset_file_label = QLabel("File")
        self.zed_dataset_file_button = QPushButton("Select SVO FIle")
        self.zed_dataset_file_button.setText(self.default_dataset_file_path)
        self.zed_label_folder_label = QLabel("Label folder")
        self.zed_label_folder_button = QPushButton("Select Label Folder")
        self.zed_label_folder_button.setText(self.zed_label_folder_path)
        
        self.zed_layout = QHBoxLayout()
        self.zed_layout.addWidget(self.zed_dataset_file_label, 10)
        self.zed_layout.addWidget(self.zed_dataset_file_button, 40)
        self.zed_layout.addWidget(self.zed_label_folder_label, 10)
        self.zed_layout.addWidget(self.zed_label_folder_button, 40)
        
        self.setLayout(self.zed_layout)
        
        self.zed_dataset_file_button.clicked.connect(self.select_zed_file)
        self.zed_label_folder_button.clicked.connect(self.select_label_folder)
            
    def reset(self):
        self.zed_dataset_file_path = self.default_dataset_file_path
        self.zed_label_folder_path = self.default_label_folder_path
        
        self.zed_dataset_file_button.setText(self.default_dataset_file_path)
        self.zed_label_folder_button.setText(self.zed_label_folder_button)
        
            
    @Slot()
    def select_zed_file(self):
        self.zed_dataset_file_path = QFileDialog.getOpenFileName()[0]
        self.zed_dataset_file_button.setText(self.zed_dataset_file_path.split('/')[-1])
        
    @Slot()
    def select_label_folder(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.zed_label_folder_path = dataset_path
        self.zed_label_folder_button.setText(dataset_path.split('/')[-1])
                
class KITTIDatasetWidget(QWidget):
    def __init__(self, parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        self.kitti_left_folder_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_color/dataset/sequences/00/image_2"
        self.kitti_right_folder_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_color/dataset/sequences/00/image_3"
        self.kitti_label_folder_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_color/dataset/sequences/00/env_seg"
        self.kitti_calib_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_calib/dataset/sequences/00/calib.txt"
        self.kitti_time_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_calib/dataset/sequences/00/times.txt"
        self.kitti_poses_file_path = "/home/vipul/Documents/projects/zb_vslam/data/data_odometry_poses/dataset/poses/00.txt"
        
        # Create UI for KITTI
        self.kitti_left_folder_label = QLabel("Left Images")
        self.kitti_left_folder_button = QPushButton("Select Folder")
        self.kitti_right_folder_label = QLabel("Right Images")
        self.kitti_right_folder_button = QPushButton("Select Folder")
        self.kitti_label_folder_label = QLabel("Labeled Images")
        self.kitti_label_folder_button = QPushButton("Select Folder")
        self.kitti_dataset_poses_label = QLabel("Pose File")
        self.kitt_dataset_poses_file_button = QPushButton("Select Pose FIle")
        self.kitti_dataset_calib_label = QLabel("Calibration File")
        self.kitt_dataset_calib_file_button = QPushButton("Select Calibration FIle")
        self.kitti_dataset_time_label = QLabel("Timestamps File")
        self.kitt_dataset_time_file_button = QPushButton("Select Timestamps FIle")
        
        self.kitti_layout = QGridLayout()
        self.kitti_layout.addWidget(self.kitti_left_folder_label, 0, 0)
        self.kitti_layout.addWidget(self.kitti_left_folder_button, 0, 1)
        self.kitti_layout.addWidget(self.kitti_right_folder_label, 0, 2)
        self.kitti_layout.addWidget(self.kitti_right_folder_button, 0, 3)
        self.kitti_layout.addWidget(self.kitti_label_folder_label, 0, 4)
        self.kitti_layout.addWidget(self.kitti_label_folder_button, 0, 5)
        self.kitti_layout.addWidget(self.kitti_dataset_poses_label, 1, 0)
        self.kitti_layout.addWidget(self.kitt_dataset_poses_file_button, 1, 1)
        self.kitti_layout.addWidget(self.kitti_dataset_calib_label, 1, 2)
        self.kitti_layout.addWidget(self.kitt_dataset_calib_file_button, 1, 3)
        self.kitti_layout.addWidget(self.kitti_dataset_time_label, 1, 4)
        self.kitti_layout.addWidget(self.kitt_dataset_time_file_button, 1, 5)
        
        self.setLayout(self.kitti_layout)
        
        self.kitti_left_folder_button.clicked.connect(self.select_kitti_left_folder)
        self.kitti_right_folder_button.clicked.connect(self.select_kitti_right_folder)
        self.kitti_label_folder_button.clicked.connect(self.select_kitti_label_folder)
        self.kitt_dataset_time_file_button.clicked.connect(self.select_kitti_time_file)
        self.kitt_dataset_calib_file_button.clicked.connect(self.select_kitti_calib_file)
        self.kitt_dataset_poses_file_button.clicked.connect(self.select_kitti_poses_file)
        
    @Slot()
    def select_kitti_left_folder(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.kitti_left_folder_path = dataset_path
        self.kitti_left_folder_button.setText(dataset_path.split('/')[-1])
        
    @Slot()
    def select_kitti_right_folder(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.kitti_right_folder_path = dataset_path
        self.kitti_right_folder_button.setText(dataset_path.split('/')[-1])
        
    @Slot()
    def select_kitti_label_folder(self):
        dialog = QFileDialog(self, windowTitle='Select directory')
        dialog.setFileMode(dialog.Directory)
        dataset_path = dialog.getExistingDirectory()
        self.kitti_label_folder_path = dataset_path
        self.kitti_label_folder_button.setText(dataset_path.split('/')[-1])

    @Slot()
    def select_kitti_time_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.kitti_time_file_path = file_path
        self.kitt_dataset_time_file_button.setText(file_path.split('/')[-1])
    
    @Slot()
    def select_kitti_calib_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.kitti_calib_file_path = file_path
        self.kitt_dataset_calib_file_button.setText(file_path.split('/')[-1])
    
    @Slot()
    def select_kitti_poses_file(self):
        file_path = QFileDialog.getOpenFileName()[0]
        self.kitti_poses_file_path = file_path
        self.kitt_dataset_poses_file_button.setText(file_path.split('/')[-1])
    
class VideoDatasetWidget(QWidget):
    def __init__(self, parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        # Create UI for Videos
        self.video_dataset_file_label = QLabel("Video File")
        self.video_dataset_file_button = QPushButton("Wait for Future Updates")
        
        self.video_layout = QHBoxLayout()
        
        self.setLayout(self.video_layout)
        

class DatasetWidget(QWidget):
    def __init__(self, dataset_type = DATASET_TYPE.KITTI, parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        self.default_dataset_type = dataset_type
        self.dataset_type = self.default_dataset_type
        
        # Dataset type
        self.dataset_type_list_widget = QComboBox()
        self.dataset_type_list_widget.addItems([DATASET_TYPE.ZED.name, DATASET_TYPE.KITTI.name, DATASET_TYPE.VIDEO.name])
        self.dataset_type_list_widget.setCurrentText(self.dataset_type.name)
        
        # Dataset Widgets
        self.zed_dataset_widget = ZEDDatasetWidget(default_dataset_file_path="", default_label_folder_path="")
        self.kitti_dataset_widget = KITTIDatasetWidget()
        self.video_dataset_widget = VideoDatasetWidget()
        
        # Layout for dataset menu and dataset ui
        self.stacked_widget =  QStackedWidget()
        self.stacked_widget.addWidget(self.zed_dataset_widget)
        self.stacked_widget.addWidget(self.kitti_dataset_widget)
        self.stacked_widget.addWidget(self.video_dataset_widget)
        self.stacked_widget.setCurrentIndex(self.dataset_type.value)
        
        self.dataset_layout = QHBoxLayout()
        self.dataset_layout.addWidget(self.dataset_type_list_widget, 10)
        self.dataset_layout.addWidget(self.stacked_widget, 90)
        
        self.setLayout(self.dataset_layout)
        
        self.dataset_type_list_widget.activated.connect(self.on_dataset_type_changed)
        
    def reset(self):
        self.dataset_type = self.default_dataset_type
        self.dataset_type_list_widget.setCurrentText(self.dataset_type.name)
        
    @Slot()
    def on_dataset_type_changed(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        if(index == DATASET_TYPE.ZED.value):
            self.dataset_type = DATASET_TYPE.ZED
        if(index == DATASET_TYPE.KITTI.value):
            self.dataset_type = DATASET_TYPE.KITTI
        if(index == DATASET_TYPE.VIDEO.value):
            self.dataset_type = DATASET_TYPE.VIDEO
            

class StartStopResetWidget(QWidget):
    def __init__(self, parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        self.is_start_enabled = True
        
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Quit")
        self.reset_button = QPushButton("Reset")
        
        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.start_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.reset_button)
        
        self.setLayout(self.buttons_layout)
        
        self.on_start = None
        self.on_stop = None
        self.on_reset = None
        
        
        self.start_button.clicked.connect(self.on_start_)
        self.stop_button.clicked.connect(self.on_stop_)
        self.reset_button.clicked.connect(self.on_reset_)
    
    def reset(self):
        self.is_start_enabled = True
        self.start_button.setEnabled(self.is_start_enabled)
        
    def set_on_start(self, func):
        self.on_start = func
        
    def set_on_stop(self, func):
        self.on_stop = func
        
    def set_on_reset(self, func):
        self.on_reset = func
    
    @Slot()
    def on_start_(self):
        self.is_start_enabled = not self.is_start_enabled
        
        self.start_button.setEnabled(self.is_start_enabled)
        
        self.on_start()
        
    @Slot()
    def on_stop_(self):
        self.on_stop()
        
    @Slot()
    def on_reset_(self):
        self.on_reset()
        
class PlotWidget(QWidget):
    def __init__(self, x_label = 'Time (seconds)', y_label = 'Rotation (Degrees)',parent=None):
        
        QWidget.__init__(self, parent=parent)
        
        # Create a plot
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_widget.setBackground('w')
        
        #Add legend
        self.graph_widget.addLegend()
        styles = {'color':'r', 'font-size':'20px'}
        self.graph_widget.setLabel('left', y_label, **styles)
        self.graph_widget.setLabel('bottom', x_label, **styles)
        
        # Set plots
        self.r_plot = self.graph_widget.plot([], [], "Roll", 'r')
        self.y_plot = self.graph_widget.plot([], [], "Pitch", 'b')
        self.p_plot = self.graph_widget.plot([], [], "Yaw", 'g')
        
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.graph_widget)
        
        self.setLayout(self.layout)
        
    def reset(self):
        self.clear_plot()
        
    def clear_plot(self):
        self.plot_(self.r_plot, [], [], "Roll", 'r')
        self.plot_(self.p_plot, [], [], "Pitch", 'b')
        self.plot_(self.y_plot, [], [], "Yaw", 'g')

    def plot_(self, plt, x, y, plotname, color):
        pen = pg.mkPen(color=color, width=5)
        plt.setData(x, y, name=plotname, pen=pen, symbol='star', symbolSize=1, symbolBrush=(color))
        self.graph_widget.addLegend()
        
    def update_rpy_plot(self, timestamp, r, p, y, filter = None):
        if(filter is not None):
            r = filter(r)
            p = filter(p)
            y = filter(y)
        
        self.plot_(self.r_plot, timestamp, r, "Roll", 'r')
        self.plot_(self.p_plot, timestamp, p, "Pitch", 'b')
        self.plot_(self.y_plot, timestamp, y, "Yaw", 'g')
    