from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import zipfile, hashlib

REPORT = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
IMG_DIR = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告3.5的截图')
doc = Document(str(REPORT))

anchor = next((p._p for p in doc.paragraphs if p.text.strip().startswith('3.6 ')), None)
if anchor is None:
    raise SystemExit('3.6 anchor not found')

# Remove only the screenshot section previously inserted before 3.6.
remove = False
for p in list(doc.paragraphs):
    if p.text.strip().startswith('3.5 测试样例截图'):
        remove = True
    if remove and p._p is not anchor:
        if p._p.xpath('.//w:drawing') or p.text.strip().startswith(('3.5 测试样例截图', '图3-11', '图3-12', '图3-13', '图3-14', '图3-15', '图3-16')):
            p._element.getparent().remove(p._element)

items = [
    ('第一个测试样例的结果.png', '图3-11 TC-01 正常需求审查结果：合法需求生成结构化报告并保存审查记录。'),
    ('第二个测试样例的结果.png', '图3-12 TC-02 空文本或无效输入结果：系统拒绝无效输入并给出错误反馈。'),
    ('第三个测试样例结果.png', '图3-13 TC-03 边界输入测试结果：系统对超长或不符合长度要求的需求进行校验。'),
    ('第四个测试样例结果.png', '图3-14 TC-04 文件解析测试结果：上传需求文档后提取文本并进入审查流程。'),
    ('第五个测试样例的结果.png', '图3-15 TC-05 异常场景测试结果：文件或数据异常时系统显示可理解的错误提示。'),
    ('第六个测试样例的结果.png', '图3-16 TC-06 空数据或历史数据测试结果：系统正确展示空状态或已保存的审查结果。'),
]

def format_caption(run):
    run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string('555555')

head = doc.add_paragraph(style='Heading 3')
head.add_run('3.5 测试样例截图')
anchor.addprevious(head._p)
for filename, caption in items:
    path = IMG_DIR / filename
    if not path.exists():
        raise SystemExit(f'missing screenshot: {path}')
    image_para = doc.add_paragraph()
    image_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_para.paragraph_format.space_after = Pt(3)
    image_para.add_run().add_picture(str(path), width=Inches(6.2))
    anchor.addprevious(image_para._p)
    caption_para = doc.add_paragraph()
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_para.paragraph_format.space_after = Pt(9)
    format_caption(caption_para.add_run(caption))
    anchor.addprevious(caption_para._p)

doc.save(str(REPORT))

# Verify the six newest embedded media hashes match the source files.
with zipfile.ZipFile(REPORT) as archive:
    media = [n for n in archive.namelist() if n.startswith('word/media/')]
    source_hashes = [hashlib.sha256((IMG_DIR / name).read_bytes()).hexdigest() for name, _ in items]
    embedded_hashes = [hashlib.sha256(archive.read(n)).hexdigest() for n in media[-6:]]
    if source_hashes != embedded_hashes:
        raise SystemExit('embedded screenshot hash verification failed')
print('replaced and verified six screenshots')
