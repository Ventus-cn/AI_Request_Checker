from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

REPORT = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
IMG_DIR = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告3.5的截图')
doc = Document(str(REPORT))

if any('3.5 测试样例截图' in p.text for p in doc.paragraphs):
    print('screenshots already inserted')
    raise SystemExit(0)

anchor = next((p._p for p in doc.paragraphs if p.text.strip().startswith('3.6 ')), None)
if anchor is None:
    raise SystemExit('3.6 anchor not found')

temp = Document()
items = [
    ('第一个测试样例的结果.png', '图3-11 TC-01 正常需求审查结果：合法需求生成结构化报告并保存审查记录。'),
    ('第二个测试样例的结果.png', '图3-12 TC-02 空文本或无效输入结果：系统拒绝无效输入并给出错误反馈。'),
    ('第三个测试样例结果.png', '图3-13 TC-03 边界输入测试结果：系统对超长或不符合长度要求的需求进行校验。'),
    ('第四个测试样例结果.png', '图3-14 TC-04 文件解析测试结果：上传需求文档后提取文本并进入审查流程。'),
    ('第五个测试样例的结果.png', '图3-15 TC-05 异常场景测试结果：文件或数据异常时系统显示可理解的错误提示。'),
    ('第六个测试样例的结果.png', '图3-16 TC-06 空数据或历史数据测试结果：系统正确展示空状态或已保存的审查结果。'),
]

def fmt(run, size=9, color='555555'):
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)

head = temp.add_paragraph(style='Heading 3')
head.add_run('3.5 测试样例截图').bold = True
for filename, caption in items:
    path = IMG_DIR / filename
    if not path.exists():
        raise SystemExit(f'missing screenshot: {path}')
    p = temp.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    p.add_run().add_picture(str(path), width=Inches(6.2))
    c = temp.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(9)
    r = c.add_run(caption)
    fmt(r)

for child in list(temp._element.body):
    if child.tag != qn('w:sectPr'):
        anchor.addprevious(deepcopy(child))

doc.save(str(REPORT))
print('inserted', len(items), 'screenshots from', IMG_DIR)
