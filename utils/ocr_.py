'''
处理ppocr和ppstructure的结果
'''
from copy import deepcopy
import requests
import json
from utils.convert import image2bytes
from collections.abc import Iterable
from PIL import Image
from .latex import LatexImage

ORDER = '([{（【「'
UNORDER = '●'
ARRANGE = ORDER + UNORDER
REST = '.!…。！'

def ppocr(image:Image.Image):
    file = {'image': image2bytes(image)}
    rl = requests.post('http://127.0.0.1:34510/ppocr', files=file)
    info = json.loads(rl.text)
    return info['output']

def ppstructure(image:Image.Image):
    file = {'image': image2bytes(image)}
    rl = requests.post('http://127.0.0.1:34510/ppstructure', files=file)
    info = json.loads(rl.text)
    return info['output']

class Line():
    def __init__(self,line) -> None:
        self.box,self.text=line
        self.text,self.confidence = self.text
    
    def __str__(self) -> str:
        return self.context
    
    @property
    def bbox(self):
        p1,p2,p3,p4=self.box
        x1,y1 = p1
        x2,y2 = p3
        return x1,y1,x2,y2
    @property
    def left(self):
        return self.bbox[0]
    @property
    def right(self):
        return self.bbox[2]
    @property
    def top(self):
        return self.bbox[1]
    @property
    def bottom(self):
        return self.bbox[3]
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

class Area():
    def __init__(self,region,ocrs) -> None:
        self.bbox = region['bbox']
        self.type = region['type']
        self.lines:Iterable[Line] = []
        for ocr in ocrs:
            for line in ocr:
                _line = Line(line)
                if self.is_in(_line):
                    self.lines.append(_line)
    
    def __str__(self) -> str:
        return self.type,self.lines
    
    @property
    def center(self):
        return ((self.bbox[1]+self.bbox[3])//2,(self.bbox[0]+self.bbox[2])//2)

    def is_in(self,line:Line):
        x1,y1,x2,y2=self.bbox
        c_x,c_y=line.center
        if x1<=c_x<=x2 and y1<=c_y<=y2:
            return True
        return False
    
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

class Paragraph():
    def __init__(self,title=None) -> None:
        self.title=title
        self.lines:Iterable[Line] = []
        
    def __bool__(self):
        return True if self.lines else False
    
    def __len__(self):
        return len(self.titleandcontext)
    
    def __add__(self,preview):
        res = Paragraph()
        if preview.title:
            res.title = preview.title
        elif self.title:
            res.title = self.title
        res.lines = preview.lines + self.lines
        return res
    
    def add(self,line):
        self.lines.append(line)
    
    @property
    def context(self):
        t = ''
        for line in self.lines:
            t+=line.context
        return t
    
    @property
    def titleandcontext(self):
        t = self.title
        for line in self.lines:
            t+=line.context
        return t
        

class Page():
    def __init__(self,structs,ocrs) -> None:
        self.areas:Iterable[Area] =[Area(region,ocrs) for region in structs]
        self.areas.sort(key=lambda x:x.center)
    
    @property
    def watershed_left(self,shift_pixel=10):
        t = 9999
        for p in self.areas:
            for l in p.lines:
                if l.left < t:
                    t = l.left
        t += shift_pixel
        return t
    
    @property
    def paragraphs(self):
        paragraphs:Iterable[Paragraph]= []
        paragraph = Paragraph()
        title=''
        for area in self.areas:
            for line in area.lines:
                if area.type=='text':
                    if line.left>self.watershed_left and paragraph and paragraph.context[0] not in ARRANGE:
                        paragraphs.append(paragraph)
                        paragraph = Paragraph(title)
                    paragraph.add(line)
                elif area.type=='title':
                    title += line.context
                else:
                    pass
        paragraphs.append(paragraph)
        return paragraphs
    
    @property
    def header(self)->Paragraph:
        paragraph = Paragraph()
        for area in self.areas:
            for line in area.lines:
                if area.type=='header':
                    paragraph.add(line)
        return paragraph

    @property
    def footer(self)->Paragraph:
        paragraph = Paragraph()
        for area in self.areas:
            for line in area.lines:
                if area.type=='footer':
                    paragraph.add(line)
        return paragraph
    
    @property
    def reference(self)->Paragraph:
        paragraph = Paragraph()
        for area in self.areas:
            for line in area.lines:
                if area.type=='reference':
                    paragraph.add(line)
        return paragraph

class OCR():
    def __init__(self, max_length:int = 200) -> None:
        self.buf = None
        self.headandfooter=[]
        self.max_length = max_length
        self.latex = LatexImage('/nvme01/lmj/virtual-ta/latexocr')
    
    def steam(self,image):
        self.image = image
        ocrs = ppocr(image)
        structs = ppstructure(image)
        page = Page(structs=structs, ocrs=ocrs)
        
        header = page.header
        if header.context in self.headandfooter:
            self.headandfooter.append(header.context)
        footer = page.footer
        if footer.context in self.headandfooter:
            self.headandfooter.append(footer.context)
        reference = page.reference
        if reference.context in self.headandfooter:
            self.headandfooter.append(reference.context)
            
        paragraphs = page.paragraphs
        for paragraph in paragraphs:
            if paragraph.context in self.headandfooter:
                paragraphs.remove(paragraph)
                
        if self.buf:
            page.paragraphs[0] += self.buf
            self.buf = None
        if page.paragraphs[-1].context[-1] not in REST:
            self.buf = page.paragraphs.pop(-1)
          
        

'''
处理每一页ocr的结果
'''
class OcrKit():
    def __init__(self, max_length:int = 200) -> None:
        self.buf = ''
        self.headandfooter=[]
        self.max_length = max_length
        self.title = ''
        self.latex = LatexImage('/nvme01/lmj/virtual-ta/latexocr')
        self.reset()
        
    def reset(self):
        self.results = []
    
    def ocrinfer(self,image):
        self.image = image
        ocr = ppocr(image)
        struct = ppstructure(image)
        
        self.reset()
        # 整理结构，文本框排序
        self.results = self.sort_struct(struct)
        self.add_ocr(ocr)

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
                        if ocrline(line).bbox[0] > watershed_left and ocrline(line).context[0] not in '([{（【「●' and (i and ocrline(res[i-1]).context[-1] not in ':：,，;；'):
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
    
    # def merge_text(self,contexts:list[str]):
    #     result=[]
    #     for res in contexts:
    #         if self.has_context and res['type']in ['title']:
    #             for title in res['context']:
    #                 if title[-1] not in ',.?!;，。？！；…':
    #                     result.append(title+'.')
    #                 else:
    #                     result.append(title)
    #         elif res['type']in ['text']:
    #             result.extend(res['context'])
    #     # result=[''.join(res['context']) for res in contexts if res['type']in ['text','title']]
    #     for i,res in enumerate(result):
    #         if res[-1] not in '。.!！?？;；…'and res!=result[-1]:
    #             result[i+1] = res+result[i+1]
    #             result.remove(res)
    #     return result
    
    def merge_text(self,contexts:list[str]):
        result=[]
        for res in contexts:
            if res['type']in ['title']:
                for title in res['context']:
                    self.title = title
                    if title[-1] not in ',.?!;，。？！；…':
                        self.title+=':'
            elif res['type']in ['text']:
                for text in res['context']:
                    if text in self.headandfooter:
                        continue
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
                    elif i+1>self.max_length and r:
                        result.append(s[:self.max_length])
                        s = s[self.max_length:]
                    else:
                        result.append(r)
                        r=''
                result.append(r)
            else:
                result.append(sentence)
        return result
