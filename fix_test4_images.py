from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

REPORT=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
IMG=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验报告3.3的截图')
doc=Document(str(REPORT))

# Remove the five previously inserted drawing/caption paragraphs.
captions=('图3-6 需求输入界面','图3-7 空数据输入界面','图3-8 错误数据反馈界面','图3-9 审查结果界面','图3-10 历史记录界面')
for p in list(doc.paragraphs):
    if p._p.xpath('.//w:drawing') or any(p.text.startswith(c) for c in captions):
        p._element.getparent().remove(p._element)

anchor=next((p._p for p in doc.paragraphs if p.text.strip().startswith('3.4 ')), None)
if anchor is None: raise SystemExit('3.4 anchor not found')

def fmt(r,size=9,color='555555'):
    r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color)

images=[('输入界面.png','图3-6 需求输入界面：用户粘贴真实业务需求，选择审查模式后提交。'),('空数据输入界面.png','图3-7 空数据输入界面：未输入需求时，系统提示先输入或上传需求文本。'),('输入错误数据界面.png','图3-8 错误数据反馈界面：输入不符合要求时，页面显示错误提示且不生成无效报告。'),('审查结果界面.png','图3-9 审查结果界面：展示风险等级、问题证据、缺失条件、待确认问题和验收标准。'),('历史记录界面.png','图3-10 历史记录界面：审查记录按时间展示，可打开详情或删除档案。')]
for name,caption in images:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(3); p.add_run().add_picture(str(IMG/name), width=Inches(6.2))
    c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after=Pt(9); r=c.add_run(caption); fmt(r)
    anchor.addprevious(c._p); anchor.addprevious(p._p)

doc.save(str(REPORT))
print('replaced screenshots from', IMG)
