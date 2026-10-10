from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

ROOT=Path(r'D:\deepseek harness workspace\AI_Request_check')
src=ROOT/'实验文档'/'TEST3'/'24111302102-许文涛.docx'
out=ROOT/'实验文档'/'TEST3'/'24111302102-许文涛-最终版.docx'

def remove_paragraph(p):
    p._element.getparent().remove(p._element)

def set_run_font(run, size=None, bold=None):
    run.font.name='微软雅黑'; run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'微软雅黑')
    if size: run.font.size=Pt(size)
    if bold is not None: run.bold=bold

doc=Document(src)
# Keep all existing wording in sections 1 and 2 unchanged; apply only font formatting.
for style_name in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
    try:
        st=doc.styles[style_name]
        st.font.name='微软雅黑'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑')
    except KeyError:
        pass
for p in doc.paragraphs:
    if p.style.name in {'Title','Heading 1','Heading 2','Heading 3'}:
        for r in p.runs: set_run_font(r)

# Add a concise section 4 while preserving all existing report content.
heading = next((p for p in doc.paragraphs if p.style.name == 'Heading 1' and p.text.startswith('4.')), None)
if heading is None:
    heading = doc.add_paragraph('4. 实验小结', style='Heading 1')
    for r in heading.runs:
        set_run_font(r, 14, True)

texts = [
    '本实验完成了从需求分析到软件架构、模块、数据、接口和界面原型的设计。',
    '通过类图、顺序图和原型图，明确了系统主要模块及其交互关系。',
    '当前设计可作为后续编码实现的依据，Mock 模式、OCR 和权限等功能还需继续完善。',
    '项目已提交 GitHub，提交记录见第 3.6 节图 10。'
]
anchor = heading
for text in texts:
    np = doc.add_paragraph(text)
    anchor._p.addnext(np._p)
    anchor = np
    for r in np.runs:
        set_run_font(r, 10.5)

doc.save(out)
print(out)
