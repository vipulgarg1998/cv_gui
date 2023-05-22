from datetime import datetime
import cv2
from PIL import Image


class Recorder:
    def __init__(self):
        self.add_date_prefix_to_file_name = False
        self.use_jpeg_file_ext = True
        self.use_pdf_file_ext = False
        self.save_dir_name = None
        
        self.img1 = None
        self.img2 = None
        self.img3 = None
        self.timestamps = []
        
    def reset(self):
        self.add_date_prefix_to_file_name = False
        self.use_jpeg_file_ext = True
        self.use_pdf_file_ext = False
        self.save_dir_name = None
        
        self.img1 = None
        self.img2 = None
        self.img3 = None
        self.timestamps = []
        
    def save_figure(self, img_name, img_idx):
        prefix = ""
        if(self.add_date_prefix_to_file_name):
            prefix = datetime.today().strftime("%Y%m%d") + "-"
            
        if(img_idx == 1):
            img = self.img1
        if(img_idx == 2):
            img = self.img2
        if(img_idx == 3):
            img = self.img3
            
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
        
    def add_timestamp(self, timestamp):
        if(len(self.timestamps) > 0):
            if(self.timestamps[-1] != timestamp):
                self.timestamps.append(timestamp)
                
            return
        self.timestamps.append(timestamp)
        
    def save_timestamps(self, filename):
        with open(filename, 'w') as file:
            file.write('\n'.join(i for i in self.timestamps))
    