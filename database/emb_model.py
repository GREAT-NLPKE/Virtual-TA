from transformers import AutoTokenizer, AutoModel
import torch

class Model():
    def __init__(self) -> None:
        pass
    def load(self,sentences:list[str]):
        pass
    def search(self,sentence:str):
        pass
    
class BGE(Model):
    def __init__(self,model='BAAI/bge-large-zh',
                 path='/nvme01/lmj/virtual-ta/model',
                 device='cpu') -> None:
        super().__init__()
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModel.from_pretrained(model).to(device)
       
    def load(self,sentences):
        with torch.no_grad():
            if isinstance(sentences,str):
                sentences = [sentences]
            encoded_input = self.tokenizer(sentences, padding=True, truncation=True, return_tensors='pt').to(self.device)
            model_output = self.model(**encoded_input)
            sentence_embeddings = model_output[0][:, 0]
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings.tolist()

if __name__=='__main__':
    m = BGE()
    sentences=['为这个句子生成表示以用于检索相关文章：信息基础设施包括什么？','目前，新型基础设施主要包括如下三个方面其中信息基础设施主要指基于新一代信息技术演化生成的基础设施。信息基础设施包括：①以SG、物联网、工业互联网、卫星互联网为代表的通信网络基础设施；2以人工智能、云计算、区块链等为代表的新技术基础设施；③以数据中心、智能计算中心为代表的算力基础设施等。信息基础设施凸显“技术新','为这个句子生成表示以用于检索相关文章：午饭吃什么？']
    output = m.load(sentences)
    embeddings_1,embeddings_2,embeddings_3 = output
    scores = embeddings_1 @ embeddings_2.T
    print(scores)
    scores = embeddings_1 @ embeddings_3.T
    print(scores)