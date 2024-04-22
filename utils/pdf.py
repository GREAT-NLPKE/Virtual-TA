import sys
import fitz
import numpy as np
from utils.iterable import Iterable
from utils.ocr import OcrKit
from PIL import Image

class PDF(Iterable):
    def __init__(self,path:str, max_length:int, onlyocr:bool=False) -> None:
        super().__init__()
        self.pdfDoc = fitz.open(path)
        self.onlyocr=onlyocr
        self.ocrkit = OcrKit(max_length=max_length)
    
    def __len__(self):
        return self.pdfDoc.page_count
    
    def __getitem__(self,index):
        page = self.pdfDoc[index]
        try:
            image = self.pdf2img(page)
        except:
            print('Failed to decode JPX image')
            return None
        else:
            self.ocrkit.ocrinfer(image=image,onlyocr=self.onlyocr)
            buf_filter_text = self.ocrkit.buf_filter_text if not self.ocrkit.is_content and self.ocrkit.has_context else []
            return buf_filter_text
    
    def pdf2img(self,page):
        zoom_x = 1.5 # horizontal zoom
        zomm_y = 1.5 # vertical zoom
        mat = fitz.Matrix(zoom_x, zomm_y) # zoom factor 2 in each dimension

        pix = page.get_pixmap(matrix=mat)
        image_array = np.frombuffer(buffer=pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
        image = Image.fromarray(image_array)
        return image
    

if __name__=='__main__':
    pdf = PDF(path='/nvme01/lmj/virtual-ta/data/book.pdf',
              max_length=250)
    for i in range(45,len(pdf)):
        print(pdf[i])
        