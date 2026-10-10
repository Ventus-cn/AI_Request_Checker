from docx import Document
from pathlib import Path
p=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
d=Document(str(p))
heading=next(x for x in d.paragraphs if x.text.strip()=='学习通提交说明')
labels=['提交平台：','文件命名：','PDF 内容：','截止时间：']
found=[]
for label in labels:
    para=next((x for x in d.paragraphs if x.text.strip().startswith(label)),None)
    if para:
        para.style='List Bullet'; found.append(para)
insert=heading._p
for para in found:
    insert.addnext(para._p)
    insert=para._p
d.save(str(p))
print([(x.text,x.style.name) for x in d.paragraphs[:12]])
