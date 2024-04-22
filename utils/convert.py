import io
import base64
from PIL import Image
from io import BytesIO

def image2bytes(image:Image.Image):
    img_bytes = io.BytesIO()
    image = image.convert("RGB")
    image.save(img_bytes, format="JPEG")
    data = img_bytes.getvalue()
    return data

def bytes2image(bytes):
    # str 转 bytes
    byte_data = base64.b64decode(bytes)
    # bytes 转 BytesIO
    img_data = BytesIO(byte_data)
    # BytesIO 转 Image
    img = Image.open(img_data)

    return img

def ocr2list(ocr_result):
    res = [con for con in ocr_result]
    return res