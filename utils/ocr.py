'''
处理ppocr和ppstructure的结果
'''
from copy import deepcopy
from .latex import LatexImage
from api import api_ppocr,api_ppstructure

class ocrline():
    def __init__(self,line) -> None:
        self.box,self.text=line
        self.text,self.confidence = self.text  
    @property
    def bbox(self):
        p1,p2,p3,p4=self.box
        x1,y1 = p1
        x2,y2 = p3
        return x1,y1,x2,y2
    @property
    def height(self):
        x1,y1,x2,y2=self.bbox
        return y2-y1
    @property
    def center(self):
        x1,y1,x2,y2=self.bbox
        return (x1+x2)//2,(y1+y2)//2
    @property
    def center_horizion(self):
        x1,y1,x2,y2=self.bbox
        return (x1+x2)//2
    @property
    def context(self):
        return self.text

'''
处理每一页ocr的结果
'''
class OcrKit():
    def __init__(self, max_length:int = 200, is_title='unused') -> None:
        self.buf = ''
        self.headandfooter=[]
        self.max_length = max_length
        self.title = ''
        assert is_title in ['alone','attached','unused']
        self.is_title = is_title
        self.latex = LatexImage('/server24/VirtualTA/latexocr')
        self.reset()
        
    def reset(self):
        self.results = []
    
    def ocrinfer(self,image,onlyocr=False):
        self.image = image
        self.reset()
        if not onlyocr:
            # 整理结构，文本框排序
            struct = api_ppstructure(image)
            self.results = self.sort_struct(struct)
        else:
            self.results  = self.no_struct()
        ocr = api_ppocr(image)
        self.add_ocr(ocr)

    def no_struct(self):
        results=[{'bbox':[0,0,9999,9999],'type':'text','context':[[]]}]
        return results
    def sort_struct(self,struct):
        results=[]
        for region in struct:
            results.append({'bbox':region['bbox'],'type':region['type'],'context':[[]]})
        results.sort(key=lambda x:(x['bbox'][1]+x['bbox'][3],x['bbox'][0]+x['bbox'][2]))
        return results
    
    def add_ocr(self,ocr):
        # 判断是否缩进
        x0 = [9999]
        for res in ocr:
            for i,line in enumerate(res):
                for region in self.results:
                    if region['type']=='text' and self.intersection(region['bbox'],ocrline(line).bbox):
                        x0.append(ocrline(line).bbox[0])
        watershed_left = min(x0)+10
        # unused
        x1 = [0]
        for res in ocr:
            for i,line in enumerate(res):
                x1.append(ocrline(line).bbox[2])
        watershed_right = max(x1)-5
        watershed_middle = (watershed_left+watershed_right)//2
    
        for res in ocr:
            for j,region in enumerate(self.results):
                # if region['type'] == 'equation':
                #     latex:str = self.latex.img2latex(self.image.crop(region['bbox']))
                #     if not latex.startswith(r'\begin'):
                #         latex=latex+';'
                #         if j==0:
                #             self.results[j]['context'].append([latex])
                #         else:
                #             self.results[j-1]['context'][-1].append(latex)
                #     continue
                for i,line in enumerate(res):
                    bbox = region['bbox']
                    if self.intersection(bbox,ocrline(line).bbox):
                        if ocrline(line).bbox[0] > watershed_left and ocrline(line).context[0] not in '([{（【「●①②③④⑤⑥⑦⑧⑨' and ocrline(line).context[:2] not in 'A.B.C.D.E.F.1）2）3）4）5）6）7）8）9）' and (i and ocrline(res[i-1]).context[-1] not in ':：,，;；'):
                            self.results[j]['context'].append([ocrline(line).context])
                        else:
                            self.results[j]['context'][-1].append(ocrline(line).context)
        for i,res in enumerate(self.results):
            self.results[i]['context'] = list(filter(None, self.results[i]['context']))
            for j in range(len(self.results[i]['context'])):
                self.results[i]['context'][j]=''.join(res['context'][j])

    # 判断两个框是否有交集
    def intersection(self,rec1,rec2):
        x11,y11,x12,y12=rec1
        x21,y21,x22,y22=rec2
        x1 = max(x11,x21)
        y1 = max(y11,y21)
        x2 = min(x12,x22)
        y2 = min(y12,y22)
        if x2>x1 and y2>y1:
            return True
        else:
            return False
    @property
    def is_content(self):
        r = [''.join(res['context']) for res in self.results if res['type'] in ['header','title']]
        r=''.join(r)
        return True if '目录' in r or '第0章' in r or 'content' in r else False
    @property
    def has_context(self):
        t = [res['context'] for res in self.results if res['type']=='text']
        return True if t else False
    
    def merge_text(self,contexts:list[str]):
        result=[]
        for res in contexts:
            if res['type']in ['title']:
                for title in res['context']:
                    self.title = title
                    if title[-1] not in ',.?!;，。？！；…':
                        self.title+=':'
                    if self.is_title == 'alone':
                        result.append(title)
            elif res['type']in ['text']:
                for text in res['context']:
                    if text in self.headandfooter:
                        continue                     
                    if self.is_title == 'attached':
                        result.append(self.title + text)
                    else:
                        result.append(text)
                    # self.title=''
            elif res['type']in ['header','footer','reference']:
                if res['context'] not in self.headandfooter:
                    self.headandfooter.extend(res['context'])
        for i,res in enumerate(result):
            if res[-1] not in '。.!！…' and res!=result[-1]:
                result[i+1] = res+result[i+1]
                result.remove(res)
        return result
    @property
    def buf_filter_text(self):
        merged_text = self.merge_text(self.results)
        if self.buf != '':
            if merged_text:
                merged_text[0] = self.buf + merged_text[0]
            else:
                merged_text.append(self.buf)
            self.buf=''
        if merged_text:
            if merged_text[-1][-1] not in '。.！!；;…':
                self.buf = merged_text[-1]
                merged_text.pop(-1)
        if merged_text:
            merged_text = self.clip_max_length(merged_text)
        return merged_text
    
    def clip_max_length(self,sentences:list[str]):
        result=[]
        for sentence in sentences:
            if len(sentence)>self.max_length:
                r=''
                s = deepcopy(sentence)
                while s:
                    i=[s.index(signal) for signal in '.;。；…！!？?' if signal in s]
                    i.append(len(s)-1)
                    i = min(i)
                    if len(r)+i+1 <= self.max_length:
                        r += s[:i+1]
                        s = s[i+1:] if i+1 != len(s) else []
                    elif i+1>self.max_length and r=='':
                        result.append(s[:self.max_length])
                        s = s[self.max_length:]
                    else:
                        result.append(r)
                        r=''
                result.append(r)
            else:
                result.append(sentence)
        return result
