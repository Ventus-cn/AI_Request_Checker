from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

REPORT = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
OUTPUT = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告_3.4-3.6修订版.docx')
doc = Document(str(REPORT))
body = doc._element.body
start = end = None
for child in list(body):
    if child.tag != qn('w:p'):
        continue
    text = ''.join(child.itertext()).strip()
    if text.startswith('3.4 '):
        start = child
    if start is not None and text.startswith('4. '):
        end = child
        break
if start is None or end is None:
    raise SystemExit('section anchors not found')
removing = False
for child in list(body):
    if child is start:
        removing = True
    if removing and child is not end:
        body.remove(child)
    if child is end:
        break

tmp = Document()
def fmt(r, size=10.5, bold=False, color='000000'):
    r.font.name = '宋体'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    r.font.size = Pt(size)
    r.bold = bold
    r.font.color.rgb = RGBColor.from_string(color)
def para(text='', style=None, bold=False):
    p = tmp.add_paragraph(style=style) if style else tmp.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    fmt(r, bold=bold)
    return p
def heading(text, level=2):
    return para(text, style=f'Heading {level}', bold=True)
def numbered(text):
    return para(text, style='List Number')
def table(headers, rows):
    t = tmp.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ''
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        fmt(r, 9, True, 'FFFFFF')
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shd = OxmlElement('w:shd')
        shd.set(qn('w:fill'), '2F5D62')
        c._tc.get_or_add_tcPr().append(shd)
    for ridx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            c = cells[i]
            c.text = ''
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            fmt(r, 8.5)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx % 2 == 0:
                shd = OxmlElement('w:shd')
                shd.set(qn('w:fill'), 'F5F8F5')
                c._tc.get_or_add_tcPr().append(shd)
    return t

heading('3.4 非AI关键业务闭环', 1)
para('本节选择“电商活动报名”作为非 AI 核心用户故事，实际使用 Mock 审查流程完成从用户输入、业务处理、数据保存到结果反馈的完整闭环。页面跳转、接口调用、报告保存、历史查询和删除均由项目本身的前后端业务代码完成。')
para('核心用户故事：作为活动报名用户，我希望提交一段包含真实业务约束的需求，系统能够审查需求质量、保存审查报告，并让我在结果页查看风险证据，在历史页重新打开这份报告。')
heading('3.4.1 设计结果与实现映射', 2)
table(['用户步骤','页面/接口','业务模块','数据处理','验收条件'], [
('输入报名需求','新建审查页；POST /api/reviews','App.vue、ReviewController','校验 text 和 mode，创建 Review','合法文本提交后返回唯一 id'),
('生成审查报告','ReviewService → AiReviewService','Mock/Qwen 审查模块','生成 summary、riskLevel、counts、issues','问题包含引用、缺失条件、问题和验收标准'),
('保存结果','ReviewService、ReviewRepository','H2 文件数据库','保存原文、模式、时间、reportJson、versionsJson','刷新页面后历史记录仍可查询'),
('查看和筛选','结果页；GET /api/reviews/{id}','结果展示和筛选状态','按风险类型过滤 issues','页面展示高/中/低风险和完整证据'),
('继续追问','POST /api/reviews/{id}/follow-up','ReviewService 版本处理','旧报告追加到 versions，新报告成为当前报告','旧版保留，新版可查看'),
('查看档案','历史页；GET /api/reviews','ReviewRepository','按 createdAt 倒序返回摘要和风险计数','历史页可打开详情或删除记录')])
heading('3.4.2 实际操作过程与结果', 2)
for step in ['启动后端 Mock 模式和前端，打开 http://localhost:5173。','在需求原文区域粘贴电商活动报名需求，选择“全面审查”，点击“开始审查”。','前端发送 POST /api/reviews；后端校验请求后调用 Mock 审查，保存 Review，并返回结构化报告。','结果页显示总体风险、问题数量、原文引用、缺失条件、待确认问题和可测试验收标准。','输入“哪个问题最可能导致返工？请说明原因？”并提交追问；后端把旧报告追加到 versions 并返回新报告。','进入审查档案，打开同一条记录，确认原文、当前报告和版本仍可读取。']:
    numbered(step)
para('验收结果：该流程真实经过页面、接口、业务层和 H2 数据库，没有使用静态页面替代执行。正常需求审查接口返回 200 并生成记录；追问接口生成新版本；历史接口可以重新打开记录。证据对应：图3-6 为输入界面，图3-9 为审查结果界面，图3-10 为历史记录界面。')

heading('3.5 异常处理、日志与基础测试', 1)
para('本节围绕个人软件实际存在的输入错误、数据不存在、文件解析失败、AI 输出异常和数据冲突进行处理，避免程序直接崩溃或没有反馈。')
heading('3.5.1 异常处理与日志', 2)
table(['异常场景','处理方式','用户反馈','日志内容'], [
('空文本或空格','前端拦截，ReviewService 再次校验','提示需求文本不能为空','记录请求失败原因和输入长度'),
('文本超 20000 字符','前后端限制最大长度','提示长度限制','记录校验失败'),
('空文件/超 10MB/不支持格式','Controller 和 DocumentService 校验','提示文件或格式错误','记录文件名、大小和解析结果'),
('不存在的审查记录','查询、追问和删除前检查 UUID','返回 404 和记录不存在','记录请求路径和记录 ID'),
('AI 返回非法 JSON 或缺少 issues','AiReviewService.validate 拒绝无效报告','提示 AI 调用失败或格式错误','记录模式和失败原因，不记录 API Key'),
('H2 读取或保存失败','Service 捕获异常并返回统一错误','页面显示保存/读取失败','记录保存或查询异常'),
('重复提交或版本冲突','按钮 loading 防重复；追问保存旧版本后更新当前版本','不产生无效重复记录','记录 saved、follow_up 和版本数量')])
para('日志位置：后端启动终端及 Spring Boot 日志输出。主要日志包括 review.create、review.saved、review.follow_up、review.deleted、review.save_failed；日志不记录完整需求敏感内容和 API Key。')
heading('3.5.2 基础测试用例与复测记录', 2)
table(['编号','测试输入/操作','预期结果','初版结果','修复内容','修订版复测'], [
('TC-01','合法电商报名需求，全面审查','返回报告并保存历史','通过','无','通过：接口 200，报告可查看'),
('TC-02','输入空文本或空格','禁止提交并提示不能为空','前端有提示，服务端校验不足','增加 Service 校验','通过：接口 400'),
('TC-03','提交超过 20000 字符','拒绝提交并提示长度限制','仅依赖前端控件','增加服务端长度校验','通过：服务端拒绝'),
('TC-04','上传正常 DOCX/文字型 PDF','提取文本并回填，不自动审查','通过','保留流程','通过：显示文件名和字符数'),
('TC-05','上传空文件、扫描 PDF 或非法扩展名','明确提示解析/格式错误','反馈不统一','增加空文件和空文本校验','通过：不生成空报告'),
('TC-06','清空数据后打开历史页','显示无历史记录空状态','通过','保留空状态','通过：可继续新建'),
('TC-07','追问为空或超过 2000 字符','不发送请求并提示错误','前端拦截','增加服务端追问校验','通过：接口拒绝'),
('TC-08','访问随机 UUID 的详情/追问/删除','返回 404','统一返回 400','增加 404 处理','通过：接口返回 404'),
('TC-09','对已有报告提交有效追问','旧报告进入 versions，新报告成为当前报告','通过','增加版本日志','通过：版本数量增加'),
('TC-10','模拟 AI 非法 JSON 或缺字段','拒绝保存无效报告','已有基础校验','补充字段校验和错误日志','待补：测试桩截图'),
('TC-11','创建两条记录并删除一条','按时间倒序，删除后剩一条','通过','增加删除存在性检查','通过：列表更新'),
('TC-12','快速连续点击开始审查','只产生一次有效提交','按钮已有 loading','保留并记录','待补：网络面板截图')])
para('测试证据应与操作截图和接口返回共同使用；TC-10、TC-12 的现场截图或日志仍需在实际运行后补入报告。')

heading('3.6 AI辅助编码审查', 1)
para('本节记录一次 AI 辅助修改后端校验代码的完整审查过程。AI 只作为编码建议来源，最终代码由本人根据项目接口、数据模型和测试结果确认。')
heading('3.6.1 AI 协作任务记录', 2)
table(['项目','记录内容'], [
('任务背景','初版服务端对空文本、超长文本、非法模式、追问长度和删除不存在记录的处理不完整。'),
('关键输入','要求在 ReviewService 增加输入边界校验，在 ReviewController 增加文件校验和 404 反馈，并使用日志记录保存、追问、删除结果。'),
('AI 建议','增加 text/question 校验、长度限制、允许模式集合、NoSuchElementException 处理和 SLF4J 日志。'),
('采用内容','采用分层校验、模式白名单、文件大小/空文本校验、404 处理和关键操作日志。'),
('拒绝或人工调整','不接受未经项目验证的接口或依赖；保留现有 DTO 和 Repository；将错误信息改为中文；确认 API Key 不写入日志。'),
('验证方式','前端 npm run build；Mock 正常审查；空文本 400；不存在记录 404；追问版本增加；检查后端日志。')])
heading('3.6.2 AI初稿—人工修正—测试通过证据', 2)
table(['阶段','代码/行为证据','结论'], [
('AI 初稿','create 直接调用 ai.review(req.text(), mode)；delete 直接调用 repo.deleteById(id)；上传接口直接解析文件。','缺少服务端输入边界、删除存在性和文件内容校验。'),
('人工修正','增加 text 非空和 20000 字符校验、mode 白名单、question 2000 字符校验；上传增加空文件/10MB/空文本校验；不存在记录映射 404；增加保存、追问、删除日志。','与需求规格书的输入、追问、历史和异常处理要求一致。'),
('测试通过','合法需求返回 200 并保存；空文本返回 400；随机 UUID 返回 404；npm run build 成功；版本追问保留旧报告。','核心修正已通过；AI 非法 JSON 和重复点击需要补充现场证据。')])
para('代码审查结论：人工修改后的实现覆盖了当前测试修订版的主要输入边界和异常路径；AI 输出异常、并发重复提交和生产级鉴权仍需在更完整环境中验证。')

for child in list(tmp._element.body):
    if child.tag != qn('w:sectPr'):
        end.addprevious(deepcopy(child))
doc.save(str(OUTPUT))
print('rewrote sections 3.4-3.6:', OUTPUT)
