from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

REPORT=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
IMG=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验报告3.3的截图')
doc=Document(str(REPORT))
anchor=next((p._p for p in doc.paragraphs if p.text.strip().startswith('3.4 ')), None)
if anchor is None: raise SystemExit('3.4 anchor not found')
if any('主要接口与模块调用说明' in p.text for p in doc.paragraphs):
    print('already updated'); raise SystemExit(0)

tmp=Document()
def fmt(r,size=10.5,bold=False,color='000000'):
    r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(size); r.bold=bold; r.font.color.rgb=RGBColor.from_string(color)
def para(text='', bold=False, center=False):
    p=tmp.add_paragraph(); p.paragraph_format.space_after=Pt(5); p.paragraph_format.line_spacing=1.25
    if center: p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(text); fmt(r,bold=bold); return p
def table(headers, rows):
    t=tmp.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=''; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(h); fmt(r,9,True,'FFFFFF'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'2F5D62'); c._tc.get_or_add_tcPr().append(shd)
    for ridx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            c=cells[i]; c.text=''; p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(str(val)); fmt(r,8.5); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx%2==0:
                shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F5F8F5'); c._tc.get_or_add_tcPr().append(shd)
    return t

para('主要接口与模块调用说明', True)
para('核心业务从前端输入开始，经接口层、业务层和 AI 审查模块处理，最后写入 H2 数据库并返回结果页面。主要调用的输入、输出和校验规则如下：')
table(['接口/模块','输入','输出','主要校验规则'],[
('POST /api/reviews','ReviewRequest：text、mode','ReviewResponse：id、原文、模式、时间、report、versions','text 非空且不超过 20000 字符；mode 只能为全面审查、可测试性、安全与权限；报告必须有 issues 数组'),
('POST /api/reviews/upload','multipart file：.docx 或文字型 .pdf','ParseResponse：fileName、text、characters','文件非空、不超过 10MB；扩展名受限；提取文本不能为空；解析失败返回错误'),
('POST /api/reviews/{id}/follow-up','路径 id、question','更新后的 ReviewResponse，新报告和旧版本','记录必须存在；question 非空且不超过 2000 字符；旧报告追加到 versions'),
('GET /api/reviews / {id}','无参数或 UUID','HistoryItem[] 或 ReviewResponse','UUID 格式有效；记录不存在返回 404；历史按创建时间倒序'),
('DELETE /api/reviews/{id}','路径 id','HTTP 204 空响应','删除前检查记录存在；不存在返回 404；删除失败记录日志'),
('AiReviewService.review','需求原文、审查模式','结构化报告 Map','Mock/Qwen 输出必须包含 issues；问题类型和风险等级限制在约定枚举；非法 JSON 不保存'),
('ReviewRepository / H2','Review 实体','持久化记录','id 唯一；reportJson 和 versionsJson 必须可解析；保存失败返回明确错误')])
para('接口正常调用时，页面显示报告摘要、风险数量和问题证据；空数据时返回空数组并显示空状态；错误输入时由前端即时校验，服务端再次校验并返回错误信息。')

para('3.3 操作截图与结果证据', True)
para('以下截图来自本次核心业务操作，分别对应输入、空数据、错误输入、审查结果和历史档案。截图编号可直接用于实验报告第三部分的操作记录。')
images=[('输入界面.png','图3-6 需求输入界面：用户粘贴真实业务需求，选择审查模式后提交。'),('空数据输入界面.png','图3-7 空数据输入界面：未输入需求时，系统提示先输入或上传需求文本。'),('输入错误数据界面.png','图3-8 错误数据反馈界面：输入不符合要求时，页面显示错误提示且不生成无效报告。'),('审查结果界面.png','图3-9 审查结果界面：展示风险等级、问题证据、缺失条件、待确认问题和验收标准。'),('历史记录界面.png','图3-10 历史记录界面：审查记录按时间展示，可打开详情或删除档案。')]
for name,caption in images:
    path=IMG/name
    if not path.exists(): raise SystemExit(f'missing image: {path}')
    p=tmp.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(3); r=p.add_run(); r.add_picture(str(path), width=Inches(6.2))
    p=tmp.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(9); r=p.add_run(caption); fmt(r,9,False,'555555')

for child in list(tmp._element.body):
    if child.tag != qn('w:sectPr'): anchor.addprevious(deepcopy(child))
doc.save(str(REPORT))
print('updated', REPORT)
