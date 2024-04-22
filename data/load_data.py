import sys
sys.path.append('/server24/VirtualTA')
from utils import PDF,PPT
from database import Milvus, BGE
from tqdm import tqdm
import json
import sys

SENTENCE_MAX_LENGTH = 500
DIM = 1024
COLLECTION_NAME = 'book1'

# model = BGE(model = 'BAAI/bge-large-zh',
#             path = '/nvme01/lmj/virtual-ta/model',
#             device = 'cuda:0')

milvus = Milvus(db_name='shutu')
milvus.drop_collection(COLLECTION_NAME)
milvus.create_collection(COLLECTION_NAME, type='text', dimension = DIM, max_length=SENTENCE_MAX_LENGTH * 3)    # 一个中文占三位

def load_pdf(path):
    pdf = PDF(path = path, max_length = SENTENCE_MAX_LENGTH,onlyocr=False)
    with tqdm(total=len(pdf),desc='loading',ncols=80) as bar:
        for idx, contexts in enumerate(pdf):
            page = idx + 1
            if contexts:
                milvus.load_text(contexts, page)
            print(contexts)
            bar.update(1)

def load_pdf_jiexi(path):
    results=''
    pdf = PDF(path = path, max_length = SENTENCE_MAX_LENGTH,onlyocr=True)
    with tqdm(total=len(pdf),desc='loading',ncols=80) as bar:
        with open('','w+') as file:
            for idx, contexts in enumerate(pdf):
                page = idx + 1
                contexts = ''.join(contexts)
                print(contexts)
                results+=contexts
                # file.write(contexts)
                # if contexts:
                #     milvus.load_text(contexts, page)
                bar.update(1)
            results = results.split('【解析】')
            for result in results:
                file.write(result[:result.find('章：')]+'\n')

def load_ppt(path):
    ppt = PPT(path,max_length = SENTENCE_MAX_LENGTH)
    with tqdm(total=len(ppt),desc='loading',ncols=80) as bar:
        for contexts,page in ppt:
            print(contexts)
            bar.update(1)

def load_txt(path):
    with open(path,'r') as file:
        contexts = file.readlines()
        milvus.load_text(contexts, 0)
        
            
if __name__=='__main__':
    load_pdf('/server24/VirtualTA/data/数图/book.pdf')
    # load_ppt(path='/nvme01/lmj/virtual-ta/data/数图习题2023.pptx')