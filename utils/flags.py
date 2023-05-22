from PySide6.QtGui import QImage

from enum import Enum

class CAMERA_TYPE(Enum):
    LEFT_GRAY = 0
    RIGHT_GRAY = 1
    LEFT_RGB = 2
    RIGHT_RGB = 3
    
    
class IMAGE_TYPES(Enum):
    RGB = QImage.Format_RGB888 # The image is stored using a 24-bit RGB format (8-8-8).
    BGR = QImage.Format_BGR888 # The image is stored using a 24-bit BGR format (8-8-8).
    GRAY8 = QImage.Format_Grayscale8 # The image is stored using an 8-bit grayscale format. 
    GRAY16 = QImage.Format_Grayscale16 # The image is stored using an 16-bit grayscale format. 

class DATASET_TYPE(Enum):
    ZED = 0
    KITTI = 1
    VIDEO = 2
    
class ERROR(Enum):
    SUCCESS = 0,
    NO_DATA_FOUND = 1,
    NO_FILE_FOUND = 2,
    END_OF_FILE = 3,
    FAILURE = 4,