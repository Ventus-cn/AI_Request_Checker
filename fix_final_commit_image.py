from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import zipfile, hashlib

REPORT=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\软工2班-24111302102-许文涛-实验4-软件基础功能开发.docx')
IMAGE=Path(r'C:\Users\34856\AppData\Local\Temp\codex-clipboard-0b3ecd11-f0f8-4250-b6c4-55e7751c0ebf.png')
doc=Document(str(REPORT))
anchor=next(p._p for p in doc.paragraphs if p.text.strip().startswith('3.2 '))
# Remove the old commit caption and its immediately preceding drawing paragraph.
for p in list(doc.paragraphs):
    if p.text.strip().startswith('图3-2 GitHub 修订版 Commit'):
        prev=p._p.getprevious()
        p._element.getparent().remove(p._element)
        if prev is not None and prev.xpath('.//w:drawing'):
            prev.getparent().remove(prev)
        break
# Add directly to the original package so the relationship points to this image.
doc.add_picture(str(IMAGE), width=Inches(6.2))
pic_para=next(p for p in reversed(doc.paragraphs) if p._p.xpath('.//w:drawing'))
pic_para.alignment=WD_ALIGN_PARAGRAPH.CENTER
pic_para.paragraph_format.space_after=Pt(3)
anchor.addprevious(pic_para._p)
cap=doc.add_paragraph()
cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_after=Pt(8)
r=cap.add_run('图3-2 GitHub 修订版 Commit f5af077：错误数据处理、界面优化和千问模型接入。')
r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string('555555')
anchor.addprevious(cap._p)
doc.save(str(REPORT))
with zipfile.ZipFile(REPORT) as z:
    h=hashlib.sha256(IMAGE.read_bytes()).hexdigest()
    matches=[n for n in z.namelist() if n.startswith('word/media/') and hashlib.sha256(z.read(n)).hexdigest()==h]
    if not matches: raise SystemExit('commit image hash verification failed')
    print('verified',matches)
