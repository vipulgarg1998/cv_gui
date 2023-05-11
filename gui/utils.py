from PySide6.QtGui import QAction, QImage

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
    
class ERROR(Enum):
    SUCCESS = 0,
    NO_DATA_FOUND = 1,
    NO_FILE_FOUND = 2,
    END_OF_FILE = 3,
    NO_GFTT_FOUND = 4,
    NO_FAR_GFTT_FOUND = 5,
    NO_LK_CORRESPONDENCES = 6,
    NOT_ENOUGH_CORRESPONDENCES = 7,
    NO_CORRESPONDENCES = 8,
    FAILURE = 9,