from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from copy import deepcopy
from pathlib import Path

path=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
doc=Document(str(path))
anchor=None
for p in doc.paragraphs:
    if p.text.strip().startswith('3.3 核心业务闭环操作'):
        anchor=p._p; break
if anchor is None: raise SystemExit('anchor not found')

# avoid duplicate insertion
if any('目录职责' in p.text for p in doc.paragraphs):
    print('already updated'); raise SystemExit(0)

tmp=Document()

def fmt(r,size=10.5,bold=False,color='000000'):
    r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(size); r.bold=bold; r.font.color.rgb=RGBColor.from_string(color)
def para(text, bold=False):
    p=tmp.add_paragraph(); p.paragraph_format.space_after=Pt(5); p.paragraph_format.line_spacing=1.25; r=p.add_run(text); fmt(r,bold=bold); return p
def bullet(text):
    p=tmp.add_paragraph(style='List Bullet'); p.paragraph_format.space_after=Pt(3); r=p.add_run(text); fmt(r); return p
def table(headers, rows):
    t=tmp.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=''; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(h); fmt(r,9.5,True,'FFFFFF'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'2F5D62'); c._tc.get_or_add_tcPr().append(shd)
    for ridx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            c=cells[i]; c.text=''; p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(str(val)); fmt(r,9); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx%2==0:
                shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F5F8F5'); c._tc.get_or_add_tcPr().append(shd)
    return t

para('目录职责与核心数据说明', True)
para('后端和前端目录按照职责拆分，保证页面、接口、业务处理和数据保存可以分别定位。')
table(['目录/模块','承担职责','本项目对应内容'],[
('frontend/src/App.vue','页面、交互和状态管理','需求输入、文件上传、审查结果、追问和历史档案页面'),
('frontend/src/style.css','界面视觉与响应式布局','工作台布局、风险指标、证据卡片和移动端适配'),
('backend/controller','HTTP 请求入口和错误反馈','ReviewController 接收审查、上传、追问、查询和删除请求'),
('backend/service','业务规则和流程编排','ReviewService 负责保存、追问版本和历史；AiReviewService 负责 Mock/Qwen 审查；DocumentService 负责 DOCX/PDF 解析'),
('backend/repository','数据访问接口','ReviewRepository 基于 Spring Data JPA 访问 Review 实体'),
('backend/model、dto','数据模型和接口数据结构','Review 保存原文、模式、时间、当前报告和版本；ReviewDtos 定义请求/响应'),
('backend/src/main/resources','运行配置','application.yml 配置端口、H2 数据库、上传大小和 AI 参数')])
para('数据库类型、访问技术与选择理由', True)
para('本项目使用 H2 文件数据库，数据库文件位于 backend/data/ambiguity.mv.db；使用 Spring Data JPA 和 Hibernate 访问。选择 H2 文件模式是因为本项目是课程实验单机原型，需要保留审查历史但不需要单独部署 MySQL 服务，文件数据库启动成本低、可重复运行、能通过 ReviewRepository 使用统一的实体查询接口。相较于纯内存数据，H2 文件模式可以在后端重启后保留审查档案；相较于直接手写 SQL，JPA 实体映射更适合当前 Review 单表和 JSON 报告字段的结构。')
para('初始化、清空与恢复方式', True)
bullet('初始化：首次运行后端时，Spring Boot 根据 application.yml 创建 H2 文件数据库；Hibernate 的 ddl-auto=update 会创建或更新 reviews 表。第一次审查成功后写入一条 Review 记录。')
bullet('样例数据：使用电商活动报名需求作为可重复审查样例，包含“尽快、方便、合理、大量”等模糊词，并包含运营人员查看报名列表的权限场景。通过页面粘贴该文本并点击“开始审查”即可重复生成一条新的审查记录。')
bullet('清空：在历史页逐条点击删除并确认，适合保留应用运行环境；测试环境需要完全清空时，先停止后端，再备份并删除 backend/data/ambiguity.mv.db 及对应 lock 文件，重新启动后会创建空数据库。')
bullet('恢复：保留一份干净的 data 目录作为测试基线，删除当前 data 后复制基线目录；也可以重新粘贴样例需求生成数据。清空或恢复前应停止后端，避免 H2 文件被占用。')
para('数据为空、重复、格式错误与读取失败处理', True)
table(['情况','处理逻辑','用户反馈/日志'],[
('数据为空','历史列表为空时返回空数组；报告问题筛选无匹配时不抛异常','页面显示“还没有审查档案”或筛选空状态'),
('数据重复','同一需求可以重复审查形成不同历史记录；追问版本追加到 versions，不覆盖旧报告','历史记录按时间倒序；日志记录 review.saved/review.follow_up'),
('格式错误','服务端校验空文本、20000 字符上限、非法模式；上传校验扩展名、空文件、10MB上限和可提取文字；AI 输出校验 issues 数组和字段默认值','返回明确错误，避免生成无效报告；错误写入后端日志'),
('读取失败','文档解析异常、H2 查询异常或报告 JSON 解析异常由统一异常处理返回错误','页面显示可理解错误；后端记录保存/查询失败日志，不直接暴露堆栈')])
para('以上数据初始化和异常处理构成测试修订版的基础数据闭环，TC-02、TC-04、TC-05、TC-06、TC-08、TC-09 和 TC-10 分别覆盖这些情况。')

# move generated elements before anchor
insert_before=anchor
for child in list(tmp._element.body):
    if child.tag == qn('w:sectPr'): continue
    insert_before.addprevious(deepcopy(child))

doc.save(str(path))
print('updated',path)
