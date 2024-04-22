MILVUS_IP = "58.199.161.165"
MILVUS_PORT = "19530"

from PIL import Image
import requests
import json
import io
from collections.abc import Iterable
from typing import Optional,Union

def image2bytes(image:Image.Image):
    img_bytes = io.BytesIO()
    image = image.convert("RGB")
    image.save(img_bytes, format="JPEG")
    data = img_bytes.getvalue()
    return data

def api_ppocr(image:Image.Image):
    file = {'image': image2bytes(image)}
    rl = requests.post('http://127.0.0.1:34510/ppocr', files=file)
    info = json.loads(rl.text)
    return info['output']

def api_ppstructure(image:Image.Image):
    file = {'image': image2bytes(image)}
    rl = requests.post('http://127.0.0.1:34510/ppstructure', files=file)
    info = json.loads(rl.text)
    return info['output']

def api_pptable(image:Image.Image):
    file = {'image': image2bytes(image)}
    rl = requests.post('http://10.0.0.20:34510/pptable', files=file)
    info = json.loads(rl.text)
    return info['output']

def api_embed(input:Union[str,list]):
    data = {'input':input}
    embeddings = requests.post('http://127.0.0.1:34510/embed', data=json.dumps(data))
    embeddings = json.loads(embeddings.text)['output']
    return embeddings

def api_llm(input:str,history:list=[]):
    params = {'input': input,
              'history': history}
    rl = requests.get('http://10.0.0.24:8003/chat', params=params)
    info = json.loads(rl.text)
    output = info['output']
    return output

def send_request(query, user='user', history=[],max_new_tokens= 256):
    ## json 可传参数system_prompt、role、query、history、max_new_tokens
    data = json.dumps({"user":user, "query":query, "history":history,"max_new_tokens":max_new_tokens})
    rl = requests.post("http://58.199.161.165:8001/chat", data=data)
    # print(res)    
    response = json.loads(rl.text)["response"]
    history = json.loads(rl.text)["history"]
    return response, history
