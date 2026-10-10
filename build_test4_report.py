from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
import re, shutil

root=Path(r'D:\deepseek harness workspace\AI_Request_check')
template=root/'实验文档'/'TEST3'/'软工2班-24111302102-许文涛-实验3-软件架构与界面设计.docx'
source=root/'实验文档'/'TEST4'/'实验4-软件基础功能开发.md'
out=root/'实验文档'/'TEST4'/'实验四报告.docx'

doc=Document(str(template))
# clear body but preserve section properties
body=doc._element.body
for child in list(body):
    if child.tag != qn('w:sectPr'):
        body.remove(child)

sec=doc.sections[0]
sec.top_margin=Inches(0.75); sec.bottom_margin=Inches(0.75); sec.left_margin=Inches(0.85); sec.right_margin=Inches(0.85)

# Helpers

def set_cell_shading(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=tcPr.find(qn('w:shd'))
    if shd is None: shd=OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'),fill)

def set_cell_border(cell, color='D9D9D9', sz='6'):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr(); borders=tcPr.first_child_found_in('w:tcBorders')
    if borders is None: borders=OxmlElement('w:tcBorders'); tcPr.append(borders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        tag='w:'+edge; el=borders.find(qn(tag))
        if el is None: el=OxmlElement(tag); borders.append(el)
        el.set(qn('w:val'),'single'); el.set(qn('w:sz'),sz); el.set(qn('w:color'),color)

def fmt_run(run, size=10.5, bold=False, color='000000'):
    run.font.name='宋体'; run._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); run.font.size=Pt(size); run.bold=bold; run.font.color.rgb=RGBColor.from_string(color)

def add_para(text='', style='Normal', bold_prefix=None):
    p=doc.add_paragraph(style=style)
    p.paragraph_format.space_after=Pt(5); p.paragraph_format.line_spacing=1.25
    if bold_prefix and text.startswith(bold_prefix):
        r=p.add_run(bold_prefix); fmt_run(r,bold=True); r2=p.add_run(text[len(bold_prefix):]); fmt_run(r2)
    else:
        r=p.add_run(text); fmt_run(r)
    return p

def add_heading(text, level=1):
    p=doc.add_paragraph(style=f'Heading {level}'); p.paragraph_format.space_before=Pt(10 if level==1 else 7); p.paragraph_format.space_after=Pt(5)
    r=p.add_run(text); fmt_run(r, size=15 if level==1 else 12, bold=True)
    return p

def add_bullet(text, level=0):
    p=doc.add_paragraph(style='List Bullet' if level==0 else 'List Bullet 2'); p.paragraph_format.space_after=Pt(3); p.paragraph_format.line_spacing=1.2
    r=p.add_run(text); fmt_run(r)
    return p

def add_number(text):
    p=doc.add_paragraph(style='List Number'); p.paragraph_format.space_after=Pt(3); r=p.add_run(text); fmt_run(r); return p

def add_table(headers, rows, widths=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=''; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(h); fmt_run(r,9.5,True,'FFFFFF'); set_cell_shading(c,'2F5D62'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_border(c)
    for ridx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            c=cells[i]; c.text=''; p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(str(val)); fmt_run(r,9); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_border(c); set_cell_shading(c,'F5F8F5' if ridx%2 else 'FFFFFF')
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t

# title block
p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('实验四报告'); fmt_run(r,22,True,'000000')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('项目：AI 需求歧义审查器'); fmt_run(r,12,False,'444444')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('测试修订版需求分析、实现与验证'); fmt_run(r,11,False,'666666')
add_para('说明：本报告沿用实验三报告的章节层级和表格风格。第一、第二部分依据实验四写作要求原文整理；第三部分记录本次修订版实现和测试过程。截图、Commit/Tag 和运行日志等现场证据以“待补材料”标出，请在完成实际演示后补入。')

# parse source sections 1 and 2 exactly
lines=source.read_text(encoding='utf-8').splitlines()
section=0
for line in lines:
    if line.startswith('## 1.'):
        section=1; add_heading('1. 实验目的',1); continue
    if line.startswith('## 2.'):
        section=2; add_heading('2. 实验内容',1); continue
    if line.startswith('## 3.'):
        section=3; break
    if section not in (1,2): continue
    if line.startswith('### '): add_heading(line[4:],2)
    elif line.startswith('- '): add_bullet(line[2:])
    elif line.strip(): add_para(line)

# third
add_heading('3. 操作记录',1)
add_para('本部分记录测试修订版对第二部分要求的实现、运行步骤、测试结果和证据位置。以下结果中，前端生产构建已在本地执行通过；后端 Maven 测试因依赖下载环境受限，需在可访问 Maven Central 的环境补跑并填入最终日志。')
add_heading('3.1 迭代计划与版本证据',2)
add_table(['版本','实现内容','完成条件','证据'],[
['可运行初版','文本审查、DOCX/PDF 解析、Mock/Qwen、报告展示、追问、历史记录','项目可启动并完成一次审查保存','待补：初版 Commit/Tag 截图与链接'],
['测试修订版','增加服务端输入/模式/文件/追问/删除校验、404反馈、日志；优化界面样式与交互状态','异常输入不崩溃，错误有反馈，前端构建通过','待补：修订版 Commit/Tag、复测日志']])
add_para('操作说明：先在 backend 目录设置 AI_MODE=mock 并启动后端，再在 frontend 目录执行 npm run dev。浏览器访问 http://localhost:5173。')
add_para('待补材料：图3-1 初版启动与首页；图3-2 测试修订版 Git 提交记录；图3-3 后端启动日志。')

add_heading('3.2 项目骨架与修订内容',2)
add_para('后端继续按 Controller、Service、Repository、Entity/DTO 分层，前端采用 Vue 单页面工作台。测试修订版主要修改 ReviewController、ReviewService、DocumentService 和前端 App.vue/style.css。')
add_table(['模块','修订内容','对应需求'],[
['ReviewService','校验空文本、20000 字符上限、审查模式；追问 2000 字符上限；删除前检查记录存在性；记录保存、追问、删除日志','2.2、2.5、2.6'],
['ReviewController','上传文件空值/大小/空文本校验；不存在记录返回 404；追问请求体校验','2.3、2.5'],
['DocumentService','拦截空文件，保持 DOCX/PDF 类型限制','2.2、2.3'],
['前端界面','上传大小提前提示；文本长度提示；重复审查后重置筛选；更新色彩、字体、卡片和按钮交互','2.3、2.5']])
add_para('待补材料：图3-4 目录结构与关键代码；图3-5 修订前后差异或 Commit diff。')

add_heading('3.3 核心业务闭环操作',2)
add_para('测试输入采用具有真实业务含义的电商活动报名需求：')
add_para('“系统需要尽快上线一个电商活动报名功能。用户填写姓名、联系方式和报名商品后，可以方便地提交报名信息。系统应当合理安排报名顺序，并在活动页面友好地展示报名结果。运营人员可以查看报名列表，必要时调整报名状态。报名数据需要保存下来，后续可以继续使用。系统应支持大量报名请求，并保证页面访问流畅。对于重复报名、信息不完整、数据无法保存以及活动结束后的报名操作，请按照实际情况进行处理。”')
add_number('启动 Mock 模式后打开审查页，粘贴上述需求。')
add_number('选择“全面审查”，点击“开始审查”。')
add_number('查看风险摘要、问题引用、缺失条件、待确认问题和验收标准。')
add_number('在“继续追问”输入“哪一个问题最可能导致后期返工？请说明原因？”，发送并观察版本更新。')
add_number('进入历史记录，打开详情并确认记录可回看。')
add_para('预期结果：Mock 规则识别“尽快、方便、合理、友好、大量”等模糊表达，识别角色权限缺口，并识别异常处理不完整问题。高风险、中风险计数应与问题明细一致。')
add_para('待补材料：图3-6 输入页面；图3-7 审查结果页面；图3-8 追问后版本页面；图3-9 历史记录页面。')

add_heading('3.4 异常处理与测试记录',2)
add_table(['编号','测试场景','预期结果','初版结果','修订版结果'],[
['TC-01','正常文本审查','报告保存并展示','通过','待补复测截图/日志'],
['TC-02','空文本或空格','提示需求文本不能为空','前端提示，服务端原先未统一校验','已增加前后端校验；待补截图'],
['TC-03','超过 20000 字符','拒绝提交并提示限制','前端存在长度控件但服务端未限制','已增加服务端限制；待补复测'],
['TC-04','正常 DOCX/PDF','解析并回填文本','通过','已保留并增加空文件/空文本校验'],
['TC-05','非法/空文件','明确提示文件错误','部分情况反馈不统一','已增加校验；待补复测'],
['TC-06','空筛选/无问题','显示空状态而非白屏','通过','已保留'],
['TC-07','空追问','不发请求并提示错误','前端拦截','增加服务端校验'],
['TC-08','不存在记录','返回 404 语义错误','统一 400','已增加 404 异常处理'],
['TC-09','追问版本','旧报告进入 versions，新报告成为当前报告','通过','增加长度校验和日志'],
['TC-10','AI 输出异常','不保存无效报告并反馈','已有结构校验','待补异常桩/日志'],
['TC-11','历史与删除','倒序显示，删除后移除','通过','删除不存在 ID 会明确反馈'],
['TC-12','重复点击','仅产生一次有效提交','前端有 loading','保留并待补演示']])
add_para('前端验证结果：执行 npm run build，Vite 构建成功。后端验证：需在可下载 Maven 依赖的环境执行 mvn test 或 run-local.ps1，补充成功日志和测试截图。')
add_para('待补材料：图3-10 前端构建成功终端；图3-11 后端测试成功终端；图3-12 TC-02/TC-05/TC-08/TC-10 的错误反馈与日志。')

add_heading('3.5 AI 辅助编码审查',2)
add_para('本次修订围绕 AI 初版代码进行人工审查，重点检查不存在的接口、无用依赖、异常遗漏、输入边界和敏感信息泄露。审查结论是：原有核心接口和 Mock 流程可用，但服务端对输入长度、文件大小、空文件、追问长度及删除不存在记录的处理不完整。')
add_table(['阶段','记录'],[
['AI 初稿/初版问题','ReviewService 直接调用 AI 和保存；上传接口直接解析文件；Controller 对所有异常统一返回 400；删除不存在 ID 时没有明确反馈。'],
['人工修正','加入文本/模式/追问长度校验、文件大小和空文本校验、NoSuchElementException 的 404 处理、删除前存在性判断和 SLF4J 操作日志。'],
['测试验证','前端构建已通过；空输入、超长文本、非法文件、不存在记录和删除异常需在运行环境复测并补图。']])
add_para('待补材料：图3-13 AI 初稿代码；图3-14 人工修正代码 diff；图3-15 修正后测试通过日志。')

add_heading('3.6 结果与材料清单',2)
add_para('已完成材料：测试修订版需求规格书、后端校验与日志代码、前端界面优化、前端 npm run build 成功记录。')
add_para('需要由实验者补入的现场材料：实际运行截图、后端 Maven 测试日志、初版与修订版 Commit/Tag、仓库链接、真实 AI 协作记录，以及根据实际运行结果填写 TC-01 至 TC-12 的“修订版结果”。')

add_heading('4. 实验小结',1)
add_para('本次实验在已有可运行初版基础上，围绕需求输入、文件解析、AI 输出、追问版本和历史记录等环节补充了服务端校验、异常反馈和日志记录，并对前端工作台进行了视觉和交互优化。通过测试用例可以把需求中的正常流程、空数据和错误输入转化为可复测证据。后续需要在可访问 Maven 依赖的环境完成后端测试，并补齐运行截图、版本提交记录和现场日志，使报告证据与实现结果完全对应。')

# footer
for section in doc.sections:
    footer=section.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    rr=footer.add_run('实验四报告 · AI 需求歧义审查器'); fmt_run(rr,9,False,'777777')

doc.save(str(out))
print(out)
