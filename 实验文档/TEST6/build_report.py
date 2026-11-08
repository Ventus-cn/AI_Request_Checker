# -*- coding: utf-8 -*-
"""按前几次实验报告的格式生成实验6 报告：
   第 1、2 部分与作业 md 一致；第 3 部分按 2.1—2.6 逐项记录操作、截图、日志；
   第 4 部分为实验小结。"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(r'D:\deepseek harness workspace\AI_Request_check')
TEST6 = ROOT / '实验文档' / 'TEST6'
SHOTS = TEST6 / '截图'
OUT = TEST6 / '软工2班-24111302102-许文涛-实验6-工具调用、Agent与Harness实现.docx'

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.6), Cm(27.9)
sec.left_margin = sec.right_margin = Cm(1.9)
sec.top_margin = sec.bottom_margin = Cm(1.7)

normal = doc.styles['Normal']
normal.font.name = '微软雅黑'
normal.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
normal.font.size = Pt(10.5)

for name, size, before in [('Heading 1', 15, 24), ('Heading 2', 12.5, 10), ('Heading 3', 11, 10)]:
    st = doc.styles[name]
    st.font.name = '微软雅黑'
    st.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(6)

title_style = doc.styles['Title']
title_style.font.name = '微软雅黑'
title_style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
title_style.font.size = Pt(20)
title_style.font.bold = True
title_style.font.color.rgb = RGBColor(0, 0, 0)
title_style.paragraph_format.space_after = Pt(15)


def title(text):
    p = doc.add_paragraph(style='Title')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(text)


def h1(text):
    return doc.add_heading(text, level=1)


def h2(text):
    return doc.add_heading(text, level=2)


def h3(text):
    return doc.add_heading(text, level=3)


def para(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run(text)
    return p


def bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text)
    return p


def tabcap(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.font.size = Pt(9)
    r.bold = True
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    r.font.name = '微软雅黑'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')


def figcap(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    r.font.name = '微软雅黑'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')


def shade(p, color='F2F3F5'):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color)
    pPr.append(shd)


def code_block(text, size=8.5):
    for line in text.rstrip('\n').split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(12)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        shade(p)
        r = p.add_run(line if line else ' ')
        r.font.name = 'Consolas'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        r.font.size = Pt(size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def table(headers, rows, widths=None, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(font_size)
        r.font.name = '微软雅黑'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:fill'), 'E8EEF7')
        tcPr.append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ''
            p = cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(str(text))
            r.font.size = Pt(font_size)
            r.font.name = '微软雅黑'
            r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, cap, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(str(SHOTS / name), width=Cm(width_cm))
    figcap(cap)


# ===================== 标题 =====================
title('实验6 工具调用、Agent与Harness实现 实验报告')

# ===================== 学习通提交说明 =====================
h2('学习通提交说明')
bullet('提交平台：只向学习通对应的作业上传一份PDF文件。')
bullet('文件命名：班级-学号-姓名-实验6-工具调用、Agent与Harness实现.pdf。')
bullet('PDF内容：任务说明、工具接口、Agent、Harness、执行日志和实验小结，附仓库链接与Commit。')
bullet('截止时间：以学习通作业设置为准。')

# ===================== 1. 实验目的 =====================
h2('1. 实验目的')
bullet('掌握工具接口定义、参数验证、权限边界和结果反馈。')
bullet('实现一个由模型根据任务和工具结果决定下一步操作、运行状态可查看且能够终止的单Agent。')
bullet('编写运行时Harness，完成上下文组织、工具执行、结果检查、停止控制和日志记录。')

# ===================== 2. 实验内容 =====================
h2('2. 实验内容')

h3('2.1 任务选择与边界')
bullet('结合个人软件选择一个范围较小、结果能够检查的任务，如查询样例数据后生成统计结果；不适合接入个人软件时，可独立完成练习。')
bullet('列出任务目标、可用数据、工具、停止条件和成功标准，并给出一组输入及预期结果。本实验实现单Agent，由模型根据目标和工具结果决定下一步操作；说明哪些步骤由程序预设，哪些由模型决定。')
bullet('说明哪些操作允许自动执行，哪些必须用户确认，哪些明确禁止。')

h3('2.2 工具接口与参数约束')
bullet('实现至少2个可实际运行的工具，如读取样例文件、查询数据或执行统计计算，说明名称、用途、输入字段、类型、必填项、返回结果和错误信息。输入格式及字段约束也称Schema。')
bullet('建立允许调用的工具列表，执行前由程序检查工具名称、参数和访问范围，例如数值范围、允许的文件目录或可访问的数据；不能直接执行模型生成的任意函数名或命令。')
bullet('说明工具的最长等待时间、是否修改数据，以及重复调用是否会产生重复修改；在接入Agent前，直接测试至少一次正确参数和一次错误参数。')

h3('2.3 Agent循环与状态')
bullet('绘制“接收目标—模型提出调用请求—程序检查并执行工具—回传工具结果—模型继续或给出最终回答”的循环图，标出参数校验、人工确认和停止检查的位置。')
bullet('接入支持工具调用的模型接口，或约定可由程序解析的JSON调用格式，实际运行模型与工具之间的循环。模型提出工具名称和参数，程序负责执行；将调用请求和对应工具结果按接口要求加入后续上下文，不能只把结果打印出来。')
bullet('设置最大执行步数、模型与工具调用超时、总运行时限及重试上限，说明一步如何计数，并由程序执行限制。模型给出最终回答后，还应检查结果是否满足2.1的成功标准，不能仅凭模型声称完成就判定成功。')

h3('2.4 运行时Harness设计与实现')
bullet('将组织模型与工具运行的外围程序作为本实验的运行时Harness，说明任务输入、上下文、执行、结果检查和日志分别由哪些函数或模块负责，不要求拆成多个独立服务。')
bullet('实现模型调用、工具分发、参数与权限检查、结果回传和停止控制；保留当前任务需要的输入、调用记录及工具结果。关键限制必须由程序执行，不能只写在提示词中。')
bullet('工具失败或结果不符合要求时，将错误信息反馈给模型进行有限次修正，或结束任务并说明原因。可以使用开发框架或自行编写代码，但须说明实际控制流程，不要求多Agent或复杂框架。')

h3('2.5 失败处理与可观测性')
bullet('为每次运行设置任务编号，记录时间、调用的工具与参数摘要、工具结果、错误类型、执行步数、耗时和最终状态；密钥和个人信息须遮挡或省略。')
bullet('处理参数错误、工具异常、超时和达到步数上限等情况，返回明确状态和原因。超时可能只是停止等待，不代表后台工具已停止，应说明实际取消能力；可能修改数据的调用状态不明时，先核对执行结果，不得直接重试。')
bullet('对需要确认的操作，在执行前展示操作内容与影响，由用户明确同意后执行；拒绝或等待超时则不执行。')

h3('2.6 测试与结果分析')
bullet('至少测试5类情况：正常完成、参数错误、工具异常、达到步数或时间限制、人工确认。其中人工确认分别检查同意与拒绝；异常与边界情况可模拟触发，正常流程必须实际调用模型和工具。')
bullet('用表格记录输入、预期行为、实际结果和判断依据，检查任务是否完成、错误是否正确反馈、停止与确认规则是否生效；未符合预期时，分析问题出在模型决策、参数、工具、检查规则还是控制流程。')
bullet('说明Agent及运行时Harness是否用于个人软件，以及当前局限和改进计划；在个人GitHub/Gitee仓库保存工具、Agent、Harness、测试代码和运行说明，报告注明路径及对应Commit。')

# ===================== 3. 操作记录 =====================
h2('3. 操作记录')
para('本节按 2.1—2.6 的顺序记录实际操作：先说明做法，再给出表格、代码、截图和日志证据。截图均来自真实运行的前后端（Spring Boot 3.3.5，端口 8080；Vite，端口 5173；模型 qwen-plus），编号与正文一致。')
para('实验环境：Windows，JDK 17.0.16，Maven 3.9.10，Node.js 24.16.0，H2 文件数据库，千问 qwen-plus（OpenAI 兼容 tools 接口）。')

# -------- 3.1 --------
h2('3.1 任务选择与边界')
para('本实验在个人软件“AI 需求歧义审查器”上实现“审查档案分析助手”：用户用自然语言询问审查档案的风险情况，Agent 通过只读工具查询 H2 中的真实档案和内置知识库，给出数字可核对的结论；删除档案是唯一的写操作，用于验证人工确认。选择这个任务，是因为范围小、结果可判定（统计数字必须与数据库聚合一致），并且直接复用个人软件已有的数据，不需要另造样例。')

tabcap('表3-1 任务卡')
table(['项目', '内容'], [
    ['任务目标', '用自然语言查询档案风险分布、单条档案详情和知识库规则，给出可核对的结论'],
    ['典型提问', '① 现在有多少份档案，风险分布如何？② 最近一条档案最严重的问题是什么？③ 知识库里文件上传有什么限制？④ 删除某条测试档案'],
    ['输入', '自然语言问题（≤500 字符）+ 会话内工具结果'],
    ['输出', '中文回答：先结论数字，再给依据（工具统计或知识库片段编号），最后给建议'],
    ['可用数据', 'H2 档案库（实验前 28 条历史档案）、rag/knowledge.json（10 个片段）'],
    ['停止条件', '① 回答通过程序检查；② 达到最大步数；③ 超过总时限；④ 等待确认被拒绝或超时；⑤ 发生不可恢复错误'],
    ['成功标准', '回答中的总数与高/中/低风险数量与 compute_risk_stats 逐项相等；引用知识库必须带片段编号；删除未经确认不执行'],
], widths=[3.2, 14.2])

tabcap('表3-2 输入与预期结果')
table(['编号', '提问', '预期工具调用', '预期结果'], [
    ['Q1', '现在有多少份档案，风险分布如何？', 'compute_risk_stats(mode=all)', '给出总数与三档计数，数字与工具一致'],
    ['Q2', '最近一条档案讲了什么，最严重的问题是什么？', 'list_reviews(limit=3) → get_review_detail(id)', '指出档案 ID 与问题，不编造内容'],
    ['Q3', '知识库里文件上传有什么限制？', 'search_knowledge(q=…, k=3)', '有结果时给出片段编号；无结果时说明资料不足'],
    ['Q4', '删除某条测试档案', 'delete_review(id) → 暂停等待确认', '未确认不执行；确认后删除并回报'],
    ['Q5', '帮我查一下服务器磁盘占用', '无工具可满足', '明确说明无法执行，并建议可用问题'],
], widths=[1.6, 5.6, 5.4, 4.8])

tabcap('表3-3 自动执行、必须确认与明确禁止')
table(['类别', '内容'], [
    ['自动执行', 'list_reviews、compute_risk_stats、get_review_detail、search_knowledge——只读、幂等、无副作用'],
    ['必须人工确认', 'delete_review：执行前展示档案 ID、创建时间、摘要和“不可恢复”提示；拒绝或 5 分钟未响应则不执行'],
    ['明确禁止', '执行模型生成的任意函数名、SQL 或 shell 命令；访问项目目录外文件；把 API Key 写入上下文或日志；批量删除；绕过确认直接写库；对写操作重复调用“碰运气”'],
], widths=[3.4, 14.0])

tabcap('表3-4 程序预设与模型决定的边界')
table(['环节', '由谁决定', '实现位置'], [
    ['调用哪个工具、传什么参数', '模型（输出 tool_calls）', 'QwenAgentModelClient'],
    ['工具是否存在、参数是否合法', '程序（白名单 + Schema 校验）', 'ToolRegistry、ArgumentValidator'],
    ['工具执行与超时', '程序（Future 限时）', 'AgentHarness.executeTool'],
    ['是否继续循环、何时收尾', '模型（无 tool_calls 即给出回答）', 'AgentHarness.loop'],
    ['步数、总时限、重答次数', '程序（到达即终止，模型无权延长）', 'AgentHarness、AnswerChecker'],
    ['删除是否需要确认', '程序（写工具强制挂起）', 'AgentRunStore'],
    ['回答是否达标', '程序（数字与引用核对）', 'AnswerChecker'],
], widths=[5.8, 6.4, 5.2])

para('操作步骤：① 先备份数据库 backend/data/ambiguity.mv.db 到 实验文档/TEST6/备份/；② 为验证删除流程，临时创建 2 条测试档案；③ 启动前后端，从首页进入“档案分析”。首页侧边栏已新增入口，如图3-1。')
figure('图3-1-首页.png', '图3-1 首页：侧边栏新增“档案分析”入口（真实运行截图）', 15.5)

tabcap('表3-5 仓库与版本证据')
table(['项目', '内容'], [
    ['仓库地址', 'https://github.com/Ventus-cn/AI_Request_Checker'],
    ['实验6 Commit', '7fe4988（完整哈希 7fe49885cc8fc927bafde32925ccdae817ecd0ec），报告与截图见 a07d337、6a9611f'],
    ['提交说明', '实验6：新增审查档案分析 Agent（工具调用、Harness、测试与运行日志）'],
    ['推送结果', 'f5af077..7fe4988、7fe4988..a07d337、a07d337..6a9611f（main -> main）'],
    ['代码路径', 'backend/src/main/java/com/example/ambiguity/agent 与 backend/src/test/java/com/example/ambiguity/agent'],
    ['运行说明', '实验文档/TEST6/运行说明.md'],
], widths=[3.4, 14.0])

# -------- 3.2 --------
h2('3.2 工具接口与参数约束')
para('系统实现 5 个工具：4 个只读、1 个写操作。所有工具都由 Spring 注入后注册进 ToolRegistry，形成唯一白名单；模型给出的函数名不在白名单内会直接返回 ARG_INVALID，程序不会反射调用任意方法，也不执行模型生成的命令。')
para('工具的最长等待时间为 5 秒；只读工具可重复调用且不产生副作用；delete_review 会修改数据，确认后只执行一次；若执行后出现异常则记为 STATE_UNKNOWN，要求人工核对，不自动重试。')

tabcap('表3-6 工具清单')
table(['工具名', '用途', '输入', '返回', '超时', '修改数据'], [
    ['list_reviews', '列出档案摘要', 'limit 1–20；riskLevel 枚举', 'id、时间、摘要、风险、计数', '5s', '否'],
    ['compute_risk_stats', '风险统计', 'mode 枚举', 'total、high、medium、low、byType', '5s', '否'],
    ['get_review_detail', '单条档案详情', 'id（UUID）', '档案字段与问题明细（截断）', '5s', '否'],
    ['search_knowledge', '检索知识库', 'q 2–100 字符；k 1–5', 'resultCount、chunks（含编号）', '5s', '否'],
    ['delete_review', '删除档案', 'id（UUID）', 'deleted、id', '5s', '是（需确认）'],
], widths=[3.6, 2.8, 4.2, 4.2, 1.2, 1.4], font_size=8.5)

para('参数采用 OpenAI function 的 JSON Schema 结构，程序按 Schema 校验类型、范围、枚举、格式和多余字段。以 list_reviews 为例：')
code_block('''{
  "type": "object",
  "properties": {
    "limit":     {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
    "riskLevel": {"type": "string", "enum": ["all","high","medium","low"], "default": "all"}
  },
  "required": [], "additionalProperties": false
}''')

para('其余四个工具的参数定义如下（完整结构同 list_reviews，均为 additionalProperties=false）：')
code_block('''compute_risk_stats
{"type":"object","properties":{
  "mode":{"type":"string","enum":["all","全面审查","可测试性","安全与权限"],"default":"all"}},
 "required":[],"additionalProperties":false}

get_review_detail / delete_review
{"type":"object","properties":{
  "id":{"type":"string","pattern":"^[0-9a-fA-F-]{36}$"}},
 "required":["id"],"additionalProperties":false}

search_knowledge
{"type":"object","properties":{
  "q":{"type":"string","minLength":2,"maxLength":100},
  "k":{"type":"integer","minimum":1,"maximum":5,"default":3}},
 "required":["q"],"additionalProperties":false}''')

tabcap('表3-7 参数校验规则')
table(['检查项', '规则', '失败反馈（回传模型）'], [
    ['工具名', '必须命中 ToolRegistry 白名单', 'ARG_INVALID：未知工具，并列出可用工具'],
    ['类型', 'integer 必须是整数，string 必须是字符串', 'ARG_INVALID：需要整数/字符串'],
    ['范围', 'limit 1–20、k 1–5、q 2–100 字符', 'ARG_INVALID：不能大于 20，收到 999'],
    ['枚举', 'riskLevel、mode 必须命中枚举', 'ARG_INVALID：只能取 all/high/…'],
    ['格式', 'id 必须匹配 36 位 UUID', 'ARG_INVALID：id 格式不正确'],
    ['多余字段', 'additionalProperties=false', 'ARG_INVALID：不支持的参数 xxx'],
    ['执行超时', '单次工具 5 秒', 'TIMEOUT：已停止等待，状态可能未知'],
], widths=[3.0, 7.8, 6.6])

para('接入 Agent 之前先做了直接测试：正确参数 list_reviews({"limit":3}) 返回 3 条真实档案；错误参数 list_reviews({"limit":999}) 被 ArgumentValidator 拒绝，回传“list_reviews.limit 不能大于 20，收到：999”，查询没有执行。两组结果也固化为自动化测试（ToolRegistryTest 与 AgentHarnessTest）。')

tabcap('表3-8 工具直接测试记录')
table(['编号', '调用', '预期', '实际结果'], [
    ['T-1', 'list_reviews {"limit":3}', '返回 3 条，按时间倒序', '返回 3 条；后续在真实运行中再次验证'],
    ['T-2', 'list_reviews {"limit":999}', '拒绝，不执行查询', 'ARG_INVALID：不能大于 20，收到：999'],
    ['T-3', 'get_review_detail {"id":"not-a-uuid"}', '拒绝', 'ARG_INVALID：id 格式不正确'],
    ['T-4', 'delete_all {}', '未知工具拒绝', 'ARG_INVALID：未知工具，并列出 5 个可用工具'],
], widths=[1.4, 6.2, 4.6, 5.2], font_size=8.5)

# -------- 3.3 --------
h2('3.3 Agent循环与状态')
para('Agent 采用单轮循环：模型提出工具调用，程序负责校验、执行、回传和终止。循环图如下图 3-2，其中参数校验、人工确认和停止检查的位置都已标出。')
figure('图2-1-Agent循环.png', '图3-2 Agent 循环与状态（参数校验、人工确认、停止检查的位置）', 12.0)

para('调用请求与工具结果必须写回上下文，而不是只打印。assistant 的 tool_calls 原样回填，每个结果按 tool_call_id 对应一条 role=tool 消息：')
code_block('''[system]    角色、任务边界、可用工具与禁止事项
[user]      现在有多少份档案，风险分布如何？
[assistant] tool_calls=[{id:"call_1", function:{name:"compute_risk_stats",
                                                arguments:"{\\"mode\\":\\"all\\"}"}}]
[tool]      {"tool_call_id":"call_1","name":"compute_risk_stats",
             "content":"{\\"total\\":28,\\"high\\":21,\\"medium\\":6,\\"low\\":1,...}"}
[assistant] 目前共有 28 份档案，其中高风险 21 份、中风险 6 份、低风险 1 份……''')

para('一步定义为模型的一次响应：无论这次响应发起 1 个还是多个工具调用都只计一步；工具执行不单独计步，但计入总时限；单步最多 3 个工具调用，超出部分拒绝。这样计数可以避免模型用并行调用绕过步数限制。结果检查由程序执行：调用过 compute_risk_stats 时回答必须包含总数和高/中/低四个数字且与工具结果相等；调用过 search_knowledge 且有结果时必须出现 KB 编号；没有检索却引用 KB 编号视为无依据引用，要求删除或重新检索。')

tabcap('表3-9 程序级运行限制')
table(['参数', '取值', '到达后的行为'], [
    ['最大步数', '6 步', '终止并说明“已达最大步数，结论不完整”'],
    ['模型超时', '30 秒/次', '本次调用失败，不再重试，返回 FAILED'],
    ['工具超时', '5 秒/次', '向模型回传 TIMEOUT，允许换工具或说明原因'],
    ['总时限', '60 秒/次运行', '下一步开始前检查，超时立即终止'],
    ['重答次数', '2 次', '仍不合格则 CHECK_FAILED'],
    ['单步工具数', '3 个', '超出部分拒绝并回报'],
    ['确认有效期', '5 分钟', '超时不执行，任务失效'],
], widths=[3.6, 4.2, 9.6])

para('实际运行：从首页进入“档案分析”页（图3-3），输入统计问题后点击“开始分析”。模型调用 compute_risk_stats，程序执行后把结果写回上下文，模型据此作答（图3-4）。该次运行任务编号为 20261108-162656-e75830，工具返回总数 30、高风险 21、中风险 6、低风险 3，回答中的数字与之一致。')
figure('图3-2-分析页初始.png', '图3-3 档案分析页：问题输入、示例问题与运行按钮', 15.5)
figure('图3-3-正常分析.png', '图3-4 正常分析：回答给出 30 份档案与高/中/低风险数量，下方为工具轨迹', 15.5)

# -------- 3.4 --------
h2('3.4 运行时Harness设计与实现')
para('Harness 负责组织模型和工具之间的每一次交互：任务输入、上下文、执行、结果检查和日志分别由不同类承担，模块关系如图3-5。')
figure('图2-2-Harness模块.png', '图3-5 运行时 Harness 模块与依赖', 14.6)

tabcap('表3-10 Harness 模块职责')
table(['类', '职责'], [
    ['AgentController', 'REST 入口，校验问题长度与确认参数，统一返回 400/404'],
    ['AgentService', '任务编排入口：启动运行、恢复确认'],
    ['AgentHarness', '循环控制、预算检查、工具分发、确认挂起与恢复、错误回传、终止'],
    ['ToolRegistry', '白名单：未命中的工具名直接拒绝'],
    ['ArgumentValidator', '按 JSON Schema 校验类型、范围、枚举、格式和多余字段'],
    ['AgentModelClient', '模型通道抽象；QwenAgentModelClient 调用 qwen-plus'],
    ['AnswerChecker', '数字一致性、知识库引用与无依据引用检查'],
    ['AgentRunLogger', '逐事件写 JSONL；参数与结果截断，密钥不落盘'],
    ['AgentRunStore', '保存等待确认的运行，5 分钟 TTL'],
], widths=[5.0, 12.4])

para('上下文组织遵循“数据必须来自工具”的原则：系统提示只写角色、边界和输出要求，不放任何示例数字；历史工具结果按 tool_call_id 排列；单条工具结果进入上下文前截断到 2000 字符。确认流程被建模成显式状态：写操作不直接执行，Harness 先返回 NEED_CONFIRM 和影响说明，用户同意后才从断点继续，拒绝则直接以 DENIED 结束并明确“未删除任何档案”。')
para('实际操作：在分析页输入“请删除档案 f1e24e91-011c-4519-b92d-bdd014c48706，这是一条测试档案”。模型调用 delete_review，弹出确认框（图3-6），展示档案摘要和“删除后不可恢复”；点击“允许执行”后工具执行、模型收尾（图3-7），档案从列表消失。')
figure('图3-4-确认弹窗.png', '图3-6 删除档案前的人工确认弹窗（展示影响，等待用户决定）', 15.5)
figure('图3-5-删除完成.png', '图3-7 确认执行后：档案被删除，运行状态为“已完成”', 15.5)

# -------- 3.5 --------
h2('3.5 失败处理与可观测性')
para('每次运行生成任务编号，逐事件写入 backend/logs/agent-runs/<taskId>.jsonl。日志只记录工具名、参数摘要、结果摘要、错误类型、步数、耗时和最终状态；不记录 API Key、完整需求文本或完整外部响应。报告引用的 6 份日志同时复制到 实验文档/TEST6/运行日志/。')

tabcap('表3-11 运行日志字段')
table(['字段', '说明'], [
    ['taskId', 'yyyyMMdd-HHmmss-6 位随机，与前端展示一致'],
    ['ts / step / phase', '时间；步号；context/model/tool/confirm/check/finish'],
    ['tool / args / result', '工具名；参数摘要（≤120 字）；结果摘要（≤200 字）'],
    ['status / errorType', 'ok 或 error；ARG_INVALID、NOT_FOUND、TOOL_EXCEPTION、TIMEOUT、STATE_UNKNOWN 等'],
    ['durationMs / tokens', '本事件耗时；模型返回的 prompt/completion token'],
    ['finalStatus', 'SUCCESS、DENIED、STEP_LIMIT、TIMEOUT、CHECK_FAILED、FAILED'],
], widths=[4.2, 13.2])

para('一次真实运行的日志（节选自任务 20261108-162558-c8c0a9）：')
code_block('''{"taskId":"20261108-162558-c8c0a9","step":0,"phase":"context","status":"ok",
 "tools":"compute_risk_stats,delete_review,get_review_detail,list_reviews,search_knowledge"}
{"taskId":"20261108-162558-c8c0a9","step":1,"phase":"model","status":"ok","durationMs":900}
{"taskId":"20261108-162558-c8c0a9","step":1,"phase":"tool","tool":"compute_risk_stats",
 "status":"ok","durationMs":27,"result":"{\\"total\\":28,\\"high\\":21,...}"}
{"taskId":"20261108-162558-c8c0a9","step":2,"phase":"model","status":"ok","durationMs":2486}
{"taskId":"20261108-162558-c8c0a9","step":2,"phase":"check","status":"ok","result":"ok"}
{"taskId":"20261108-162558-c8c0a9","step":2,"phase":"finish","status":"ok","finalStatus":"SUCCESS"}''')

tabcap('表3-12 错误分类与用户可见反馈')
table(['情形', '内部状态', '页面/回答'], [
    ['参数错误', 'ARG_INVALID 回传模型', '模型换参数重试；仍失败则说明参数不合法并停止'],
    ['工具异常/记录不存在', 'TOOL_EXCEPTION / NOT_FOUND', '说明查不到该档案，不编造数据'],
    ['工具或模型超时', 'TIMEOUT', '已停止等待；后台可能仍在执行，状态未知，请核对'],
    ['达到步数上限', 'STEP_LIMIT', '结论不完整，并给出已获得的工具结果'],
    ['用户拒绝确认', 'DENIED', '已取消，未删除任何档案'],
    ['写操作执行后异常', 'STATE_UNKNOWN', '结果不确定，请到列表核对；不自动重试'],
    ['结果校验失败', 'CHECK_FAILED', '统计数字与工具结果不一致，已终止'],
], widths=[4.4, 4.8, 8.2])

para('超时的实际取消能力：程序用 Future 限时，超时后调用 cancel(true) 中断线程并停止等待，但这不代表后台数据库操作一定已回滚；因此日志标记 TIMEOUT，回答提示“状态未知，请核对”。拒绝确认的演练：同样输入删除请求，在弹窗中点击“拒绝”，运行以 DENIED 结束（图3-8），档案仍可查询。')
figure('图3-6-拒绝删除.png', '图3-8 拒绝确认：状态为“已取消”，回答说明未删除任何档案', 15.5)

# -------- 3.6 --------
h2('3.6 测试与结果分析')
para('后端共 33 个自动化测试全部通过，其中本实验新增 17 个：AgentHarnessTest 11 个（模型用测试桩，覆盖失败与边界）、ToolRegistryTest 6 个（白名单与参数 Schema）；原有 16 个测试不受影响。除自动化测试外，真实流程执行 5 次，全部调用 qwen-plus 与实际工具。')

tabcap('表3-13 五类测试覆盖与结果')
table(['编号', '类别', '输入/操作', '实际结果'], [
    ['TA-01', '正常完成（真实模型）', '询问档案风险分布', 'SUCCESS；调用 compute_risk_stats；回答 30 份、高 21、中 6、低 3，与工具一致'],
    ['TA-02', '参数错误（测试桩）', '模型传 limit=999', '程序拒绝并回传 ARG_INVALID，查询未执行；模型改口径后结束'],
    ['TA-03', '工具异常（测试桩）', '查询不存在的 UUID', '返回 NOT_FOUND，回答说明查不到，不编造'],
    ['TA-04', '步数上限（测试桩）', 'max-steps=1，模型继续请求工具', 'STEP_LIMIT，回答说明结论不完整'],
    ['TA-05', '时间限制（测试桩）', '慢工具 + 50ms 工具超时', 'TIMEOUT 回传模型，运行继续并收尾'],
    ['TA-06', '人工确认-同意（真实）', '删除测试档案并确认', '执行删除，档案从列表消失（图3-7）'],
    ['TA-07', '人工确认-拒绝（真实）', '删除测试档案并拒绝', 'DENIED，回答“未删除”，档案仍可查询（图3-8）'],
    ['TA-08', '结果校验（测试桩）', '回答写错数字 / 无依据引用', '触发重答；仍错则 CHECK_FAILED；引用被要求删除'],
    ['TA-09', '未知工具（测试桩）', '调用 delete_all', 'ARG_INVALID：未知工具，拒绝执行'],
], widths=[1.6, 4.4, 5.4, 6.0], font_size=8.5)

tabcap('表3-14 真实运行记录')
table(['任务编号', '问题', '工具调用', '最终状态'], [
    ['20261108-162656-e75830', '档案总数与风险分布', 'compute_risk_stats', 'SUCCESS'],
    ['20261108-162700-2bdd63', '删除测试档案 f1e24e91', 'delete_review（确认后）', 'SUCCESS'],
    ['20261108-162705-94bcdc', '删除测试档案 8b1d538f', 'delete_review（拒绝）', 'DENIED'],
    ['20261108-162818-968b42', '知识库文件上传限制', 'search_knowledge（0 条）', 'SUCCESS（资料不足）'],
    ['20261108-162820-5fcb93', '最近 3 条档案摘要', 'list_reviews(limit=3)', 'SUCCESS'],
], widths=[5.2, 5.4, 4.2, 2.6], font_size=8.5)

para('说明：为验证删除流程，实验前临时创建了 2 条测试档案，因此统计运行显示 30 份；确认删除后剩 29 份，被拒绝删除的一条保留，档案列表如图3-9。')
figure('图3-7-档案列表.png', '图3-9 审查档案列表：被删除的档案不再出现，拒绝删除的档案仍在', 15.5)

tabcap('表3-15 开发与测试中发现的问题')
table(['编号', '问题', '处理'], [
    ['P-1', '对 Map<?,?> 调用 getOrDefault 触发泛型捕获编译错误', '先取 Object 再判空，重新编译通过'],
    ['P-2', 'lambda 捕获被重新赋值的局部变量，编译报“必须是最终变量”', '改用独立变量承接解析结果'],
    ['P-3', '测试 Schema 的 riskLevel 未写 default，断言失败', '补默认值后通过'],
    ['P-4', '单例 Harness 的预算字段被前一个用例改小，后续用例误判超时', '每个用例前重置预算'],
    ['P-5', 'target/test-classes 残留旧 class，出现 NoClassDefFoundError', '执行 mvn clean 后恢复'],
    ['P-6', '真实模型未检索却附带 [KB-003] 编号', '补充“无检索不得引用”的检查规则'],
    ['P-7', '提示词要求“先说明再调用”，模型改为反问用户要 ID，删除流程走不通', '改为用户明确要求后直接调用，由程序弹出确认'],
    ['P-8', '知识库按整段汉字匹配，“文件上传限制”检索 0 条（未修复）', '模型按规则回答“资料不足”不编造；列入改进计划'],
], widths=[1.4, 8.4, 7.6], font_size=8.5)

para('测试覆盖了要求的 5 类情况，人工确认分别验证了同意与拒绝；正常流程实际调用了模型和工具，异常与边界用测试桩稳定复现。从定位看，问题分别落在参数（P-3）、工具（P-5、P-8）、检查规则（P-6）、控制流程（P-4）和模型决策（P-7）五个层面，说明“让模型自己保证正确”并不可靠，程序侧的校验和状态管理才是可测试的部分。')
para('Agent 与运行时 Harness 已用于个人软件：入口在侧边栏“档案分析”，接口为 POST /api/agent/runs 与 POST /api/agent/runs/{taskId}/confirm，代码位于 backend/src/main/java/com/example/ambiguity/agent，测试位于 backend/src/test/java/com/example/ambiguity/agent，运行说明见 实验文档/TEST6/运行说明.md，对应 Commit 为 7fe4988。')
para('当前局限与改进计划：知识库仍是整段汉字匹配，口语化提问召回不足，计划改为二字词或向量检索；上下文只做截断，计划增加摘要压缩；工具串行执行，计划利用并行调用；前端仍是单文件页面，计划把“档案分析”拆成独立组件；多人使用时需要补充鉴权与审计落库。')

# ===================== 4. 实验小结 =====================
h1('4. 实验小结')
para('本次实验在 AI 需求歧义审查器上完成了“审查档案分析助手”：5 个白名单工具、单 Agent 循环、运行时 Harness、人工确认、结果检查和 JSONL 运行日志，并通过 33 个自动化测试和 5 次真实运行验证。Agent 已经作为产品的一个页面和接口使用，不是独立练习。')
para('实现过程中体会最深的是三点。第一，能用程序做的事不要交给提示词：白名单、Schema、步数、超时和确认流程一旦写进代码，模型就无法绕过，测试也才有稳定的断言对象。第二，人工确认必须建模成显式状态，而不是让模型在回答里“请用户确认”，否则无法保证写操作真的没有执行。第三，日志和结果检查是排错的核心：真实运行中出现过无依据引用和检索 0 条的情况，正是日志里的阶段、错误类型和检查结果让问题可定位。')
para('当前局限也很明确：知识库仍用整段汉字匹配，口语化提问召回不足；上下文只做了截断，没有摘要压缩；工具串行执行，尚未利用并行调用；前端仍是单文件页面结构。后续计划把检索改为二字词或向量匹配、为长上下文增加摘要、把“档案分析”拆成独立组件，并在需要多人使用时补充鉴权和审计落库。')

# ===================== 页脚页码 =====================
footer_p = doc.sections[0].footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = footer_p.add_run('第 ')
r1.font.size = Pt(9)
fld_begin = OxmlElement('w:fldChar')
fld_begin.set(qn('w:fldCharType'), 'begin')
instr = OxmlElement('w:instrText')
instr.set(qn('xml:space'), 'preserve')
instr.text = 'PAGE'
fld_end = OxmlElement('w:fldChar')
fld_end.set(qn('w:fldCharType'), 'end')
r2 = footer_p.add_run()
r2.font.size = Pt(9)
r2._r.append(fld_begin)
r2._r.append(instr)
r2._r.append(fld_end)
r3 = footer_p.add_run(' 页')
r3.font.size = Pt(9)

doc.save(str(OUT))
print(OUT)
print('size', OUT.stat().st_size)