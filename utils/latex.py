'''
https://github.com/RapidAI/RapidLatexOCR
'''
import os 
from rapid_latex_ocr import LatexOCR
import io
import base64
from PIL import Image

class LatexImage():
    def __init__(self,models_path) -> None:
        image_resizer_path = os.path.join(models_path,'models/image_resizer.onnx')
        encoder_path = os.path.join(models_path,'models/encoder.onnx')
        decoder_path = os.path.join(models_path,'models/decoder.onnx')
        tokenizer_json = os.path.join(models_path,'models/tokenizer.json')
        self.model = LatexOCR(image_resizer_path=image_resizer_path,
                            encoder_path=encoder_path,
                            decoder_path=decoder_path,
                            tokenizer_json=tokenizer_json)
        
    def img2latex(self,image):
        if isinstance(image,str):
            with open(image, "rb") as f:
                data = f. read()
        elif isinstance(image,Image.Image):
            img_bytes = io.BytesIO()
            image = image.convert("RGB")
            image.save(img_bytes, format="JPEG")
            data = img_bytes.getvalue()
        result, elapse = self.model(data)
        return result

            
if __name__ == '__main__':
    
    m = LatexImage('/nvme01/lmj/virtual-ta/latexocr')
    image = Image.open('/nvme01/lmj/virtual-ta/open_model_zoo/demos/formula_recognition_demo/python/sample.png')
    print(m.img2latex(image))