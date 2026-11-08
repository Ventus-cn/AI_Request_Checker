from docx import Document
from pathlib import Path
p=Path('实验文档/TEST5/实验5-LLM、Context与RAG实现-RAG版报告.docx')
d=Document(p)
for i,x in enumerate(d.paragraphs):
    print(f'P{i}: [{x.style.name}] {x.text}')
print('TABLES',len(d.tables))
for ti,t in enumerate(d.tables):
    print('TABLE',ti)
    for row in t.rows:
      print(' | '.join(c.text for c in row.cells))
