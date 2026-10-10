from docx import Document
from pathlib import Path
p=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
d=Document(str(p))
main={'3.4 ','3.5 ','3.6 '}
sub=('3.4.1 ','3.4.2 ','3.5.1 ','3.5.2 ','3.6.1 ','3.6.2 ')
for para in d.paragraphs:
    if any(para.text.startswith(x) for x in main): para.style='Heading 2'
    elif any(para.text.startswith(x) for x in sub): para.style='Heading 3'
d.save(str(p))
print('updated heading styles')
for para in d.paragraphs:
    if para.text.startswith(('3.4','3.5','3.6')): print(para.text, para.style.name)
