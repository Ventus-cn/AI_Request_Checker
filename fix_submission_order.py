from docx import Document
from pathlib import Path
p=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
d=Document(str(p))
heading=next(x for x in d.paragraphs if x.text.strip()=='学习通提交说明')
heading.style='Heading 1'
first_bullet=next(x for x in d.paragraphs if x.text.strip().startswith('提交平台：'))
first_section=next(x for x in d.paragraphs if x.text.strip().startswith('1. '))
# Move the heading before the first submission bullet; retain the four bullets immediately before section 1.
first_bullet._p.addprevious(heading._p)
d.save(str(p))
print('fixed order and heading style')
for x in d.paragraphs[:10]: print(x.text, x.style.name)
