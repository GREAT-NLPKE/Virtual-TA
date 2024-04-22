from wechaty import Contact, FileBox, Message, Wechaty, ScanStatus
from wechaty_puppet import MessageType
from api import api_pptable,api_ppocr,api_embed
from PIL import Image
import os

async def process_image(msg: Message, api_ppocr):
    # 从消息中获取 FileBox
    image_file_box = await msg.to_file_box()

    # 指定文件的保存路径和名称
    file_path = './image.jpg'

    # 将文件保存到本地并打开图片
    await image_file_box.to_file(file_path, overwrite=True)
    img = Image.open(file_path)

    # 调用ocr并存入图片信息
    prompt = api_ppocr(img)
    prompt = [line[1][0] for line in prompt[0]]
    prompt = ''.join(prompt)

    # 检查文件是否存在，然后删除
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f'File {file_path} has been deleted.')
    else:
        print(f'File {file_path} does not exist.')

    return prompt
