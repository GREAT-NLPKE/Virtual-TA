import yaml
from pprint import pprint,pformat

def get_document_dict(yaml_file):
    file = open(yaml_file,'r',encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data,Loader=yaml.FullLoader)
    return config

class Config():
    def __init__(self,path='config/config.yaml') -> None:
        file = open(path,'r',encoding="utf-8")
        self.file_data = file.read()
        file.close()
        self.config = yaml.load(self.file_data,Loader=yaml.FullLoader)
        for k,v in self.config.items():
            setattr(self,k,v)
    def __call__(self):
        return self.config
    
    def __str__(self):
        return pformat(self.config)