from database import Milvus, BGE
from pprint import pprint
import requests
import json
from collections.abc import Iterable
from config import get_document_dict
from api import api_llm,send_request

doc_dict = get_document_dict('config/documents.yaml')

class MilvusResults():
    def __init__(self,dbname=None,collection_name=None,results=None) -> None:
        self.results=[]
        if dbname and collection_name and results:
            for result in results:
                for entry in result:
                    entry_dict={}
                    page = entry.entity.get("page")
                    if page>0:
                        entry_dict['page'] = '{0}-第{1}页'.format(doc_dict[dbname][collection_name],page)
                    else:
                        entry_dict['page'] = '{0}'.format(doc_dict[dbname][collection_name])
                    entry_dict['context'] = entry.entity.get("context")
                    entry_dict['distance'] = entry.distance
                    self.results.append(entry_dict)
            self.sorted()
            print("sorted:",self.results)
            self.results = [self.results[0]] + [res for res in self.results[1:] if res['distance'] <= 0.75]
            print(self.results)
    
    def __add__(self,other):
        res = MilvusResults()
        res.results = self.results+other.results
        res.sorted()
        return res
    
    def sorted(self):
        return self.results.sort(key=lambda x:x['distance'])
    
    def perfect_contexts(self,top_k:int=3,*args,**kw):
        contexts=[]
        for i,res in enumerate(self.results):
            if i >= top_k:
                break
            contexts.append(res['context'])
        return contexts
    
    @property
    def perfect_page(self):
        return self.results[0]['page'],self.results[0]['distance']

def clip(x,min,max):
    if x<min:
        x=min
    if x>max:
        x=max
    return x
    
def search(db_name, collection_name, input, img_prompt:list=None):
    if isinstance(collection_name,str):
        collection_name=[collection_name]
    assert isinstance(collection_name,list)
    input = str(input)
    milvus = Milvus(db_name=db_name)
    results = MilvusResults()
    # page = 0 
    # distance = 9999
    for collection in collection_name:
        milvus.load_collection(collection)    # 一个中文占三位
        current = MilvusResults(db_name, collection, milvus.search_text('为这个句子生成表示以用于检索相关文章：'+input, top_k=3))
        # print(milvus.search_text('为这个句子生成表示以用于检索相关文章：'+input, top_k=5))
        # current_page,current_distance=current.perfect_page
        # if current_distance<distance:
        #     distance = current_distance
        #     page = current_page
        results += current

    # prompts = results.perfect_contexts(top_k=clip(len(collection_name)*2,3,6))
    prompts = results.perfect_contexts(top_k=3)

    # new_prompts = [prompts[0]]
    # for p in prompts[1:]:
    #     print(p)
    # if img_prompt:
    # #     img_prompt.extend(prompts)
    # #     prompts = img_prompt
    #     prompts.extend(img_prompt)
    prompts = str(prompts)
    img_prompt = str(img_prompt)
    # prompts = prompts[:2048] if len(prompts)>2048 else prompts
    page,distance = results.perfect_page
    print('Question:',input,end='\n\n')
    print('prompt:',prompts, end='\n\n')
    print('img_prompt',img_prompt, end='\n\n')
    print('distance:',distance, end='\n\n')


    limit = '你是一个电子信息专业数字图像处理课程的助教，给出至多300字的解答内容，不要回答与专业或课程无关的问题。'
    input = '以下是检索到课本中的相关内容：{1}\n重要信息：{3}\n问题：{0}\n{2}'.format(input,prompts,limit,img_prompt)
    # output,history = send_request(query = input)
    output = api_llm(input=input)  
    if page and results.results[0]['distance']<= 0.65:
        citation = page
    else:
        citation = None
    print("A:",output,end='\n\n')
    return output, citation


if __name__=='__main__':
    # input = '低通滤波可以用于图像锐化吗？'
    # params = {'input': "问题：{0}\n回答:".format(input),
    #             'history': []}
    # rl = requests.get('http://58.199.163.176:34503/chat', params=params)
    # info = json.loads(rl.text)
    # print(info['output'])
    
    res = search(db_name = 'shutu',collection_name = ['book1'],
           input = 'DFT是什么?')
    print(res)