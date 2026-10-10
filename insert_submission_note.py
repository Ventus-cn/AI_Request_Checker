from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

path = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
doc = Document(str(path))

first = next((p._p for p in doc.paragraphs if p.text.strip().startswith('1. ')), None)
if first is None:
    raise SystemExit('section 1 not found')
if any(p.text.strip() == '学习通提交说明' for p in doc.paragraphs):
    print('submission note already exists')
    raise SystemExit(0)

tmp = Document()
heading = tmp.add_paragraph(style='Heading 1')
heading.add_run('学习通提交说明')

items = [
    ('提交平台：', '只向学习通对应的作业上传一份 PDF 文件。'),
    ('文件命名：', '班级-学号-姓名-实验4-软件基础功能开发.pdf。'),
    ('PDF 内容：', '可运行基础功能版本说明、核心业务闭环、测试与复测记录、AI 辅助编码审查，以及初版与修订版的仓库版本证据。'),
    ('截止时间：', '以学习通作业设置为准；报告中的仓库链接与 Commit 用于过程核验。'),
]
for lead, text in items:
    p = tmp.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(lead)
    r.bold = True
    r.font.name = '宋体'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    r.font.size = Pt(10.5)
    r2 = p.add_run(text)
    r2.font.name = '宋体'
    r2._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    r2.font.size = Pt(10.5)

for child in reversed(list(tmp._element.body)):
    if child.tag != qn('w:sectPr'):
        first.addprevious(child)

doc.save(str(path))
print('inserted submission note before section 1')
