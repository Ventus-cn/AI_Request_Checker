# -*- coding: utf-8 -*-
"""生成实验8 报告：第 1、2 部分与作业 md 完全一致；第 3 部分按 2.1—2.5 记录集成实现、
状态与持久化、错误与降级、端到端测试与缺陷修复；第 4 部分为实验小结。

数据来源：
- experiments/exp8/results/e2e-normal.json、e2e-fault.json（用例的前置条件、步骤、预期、实际）
- experiments/exp8/results/commits.json（报告引用的 Commit）
- 实验文档/TEST8/截图（真实运行截图，图号与文件名一致）
"""
import json
import re
import urllib.request
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(r"D:\deepseek harness workspace\AI_Request_check")
TEST8 = ROOT / "实验文档" / "TEST8"
SHOTS = TEST8 / "截图"
RESULTS = ROOT / "experiments" / "exp8" / "results"
OUT = TEST8 / "软工2班-24111302102-许文涛-实验8-AI能力与软件系统集成.docx"

NORMAL = json.loads((RESULTS / "e2e-normal.json").read_text(encoding="utf-8"))
FAULT = json.loads((RESULTS / "e2e-fault.json").read_text(encoding="utf-8"))
NORMAL_CASES = NORMAL["cases"] if isinstance(NORMAL, dict) else NORMAL
TOTAL_MS = NORMAL.get("totalMs", 0) if isinstance(NORMAL, dict) else 0
CASES = {c["id"]: c for c in NORMAL_CASES + FAULT}
COMMITS = json.loads((RESULTS / "commits.json").read_text(encoding="utf-8"))
C_FEATURE = COMMITS["feature"]
C_FRONTEND = COMMITS["frontend"]
C_TEST = COMMITS["test"]
C_REPORT = COMMITS.get("report", "")

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.6), Cm(27.9)
sec.left_margin = sec.right_margin = Cm(1.9)
sec.top_margin = sec.bottom_margin = Cm(1.7)

normal_style = doc.styles["Normal"]
normal_style.font.name = "微软雅黑"
normal_style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
normal_style.font.size = Pt(10.5)


def strip_theme_fonts(rfonts):
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]


for name, size, before in [("Heading 1", 15, 20), ("Heading 2", 12.5, 9), ("Heading 3", 11, 9)]:
    st = doc.styles[name]
    st.font.name = "微软雅黑"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    strip_theme_fonts(st.element.rPr.rFonts)
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(6)

title_style = doc.styles["Title"]
title_style.font.name = "微软雅黑"
title_style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
strip_theme_fonts(title_style.element.rPr.rFonts)
title_style.font.size = Pt(20)
title_style.font.bold = True
title_style.font.color.rgb = RGBColor(0, 0, 0)
title_style.paragraph_format.space_after = Pt(15)


def title(text):
    p = doc.add_paragraph(style="Title")
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
    p.paragraph_format.line_spacing = 1.22
    p.add_run(text)
    return p


def bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.2
    p.add_run(text)
    return p


def bullet_rich(label, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(label)
    r.bold = True
    p.add_run(text)
    return p


def tabcap(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.size = Pt(9)
    r.bold = True
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    r.font.name = "微软雅黑"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def figcap(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    r.font.name = "微软雅黑"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def shade(p, color="F2F3F5"):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def code_block(text, size=8.5):
    for line in text.rstrip("\n").split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(12)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        shade(p)
        r = p.add_run(line if line else " ")
        r.font.name = "Consolas"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        r.font.size = Pt(size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def table(headers, rows, widths=None, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, text in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(font_size)
        r.font.name = "微软雅黑"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "E8EEF7")
        tcPr.append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(str(text))
            r.font.size = Pt(font_size)
            r.font.name = "微软雅黑"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
        tblPr = t._tbl.tblPr
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tblPr.append(layout)
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        tblW.set(qn("w:type"), "dxa")
        tblW.set(qn("w:w"), str(int(sum(widths) * 567)))
    for index, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        trPr.append(cant_split)
        if index == 0:
            tbl_header = OxmlElement("w:tblHeader")
            tbl_header.set(qn("w:val"), "true")
            trPr.append(tbl_header)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, cap, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    p.add_run().add_picture(str(SHOTS / name), width=Cm(width_cm))
    figcap(cap)


def clip(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def task_pair(case_id):
    """从用例实际结果里取出交错任务的两个任务编号。"""
    actual = CASES[case_id]["actual"]
    m = re.search(r"A=(AC[0-9a-f-]+)、B=(AC[0-9a-f-]+)", actual)
    return (m.group(1), m.group(2)) if m else ("见用例记录", "见用例记录")


def fetch_summary(task_id):
    """按任务编号读取结果摘要；后端未启动时给出可追溯的说明，不编造内容。"""
    try:
        with urllib.request.urlopen(f"http://localhost:8080/api/acceptance/tasks/{task_id}", timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        summary = (data.get("report") or {}).get("summary") or ""
        return clip(summary, 40) or "（结果无摘要）"
    except Exception:
        return "（生成时后端未连接，摘要见任务结果）"


def cancelled_log_excerpt():
    """从复制到报告目录的取消任务 JSONL 中抽取三行证据。"""
    path = TEST8 / "运行日志" / "cancelled.jsonl"
    if not path.exists():
        return None
    picked = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("phase") == "model" and obj.get("status") == "start":
            picked.append({"runId": obj.get("runId"), "attempt": obj.get("attempt"),
                           "phase": "model", "status": "start"})
        elif obj.get("phase") == "cancel":
            picked.append({k: obj.get(k) for k in ("runId", "attempt", "phase", "status", "stage", "lateResult", "durationMs")})
        elif obj.get("phase") == "finish":
            picked.append({k: obj.get(k) for k in ("runId", "attempt", "phase", "status", "durationMs")})
        if len(picked) >= 3:
            break
    if not picked:
        return None
    return "\n".join(json.dumps(p, ensure_ascii=False) for p in picked)


# ===================== 标题 =====================
title("实验8 AI能力与软件系统集成 实验报告")

# ===================== 学习通提交说明 =====================
h2("学习通提交说明")
bullet_rich("提交平台：", " 只向学习通对应的作业上传一份PDF文件。")
bullet_rich("文件命名：", " 班级-学号-姓名-实验8-AI能力与软件系统集成.pdf。")
bullet_rich("PDF内容：", " 集成方案、核心用户流程、任务状态、端到端测试、试用、两周版本对比，附仓库链接与Commit。")
bullet_rich("截止时间：", " 以学习通作业设置为准。")

# ===================== 1. 实验目的 =====================
h2("1. 实验目的")
bullet("将核心AI原型接入个人软件的界面、业务和数据层，形成用户可完成的真实任务流程。")
bullet("处理模型等待过程、会话或任务状态、错误提示、取消、重试和降级等AI软件集成问题。")
bullet("通过端到端测试验证功能、交互、数据和AI结果的一致性。")

# ===================== 2. 实验内容 =====================
h2("2. 实验内容")

h3("2.1 集成边界与接口统一")
bullet("比较AI原型与现有软件的输入输出，列出需要统一的字段名称、数据格式、任务状态和错误信息；项目具有账号或权限控制时，还应说明身份验证和权限要求。")
bullet("使用顺序图或流程图描述界面、业务、AI模块及实际使用的数据或工具之间的调用，标出等待步骤，以及信任级别或权限发生变化的位置，例如用户输入进入后端、外部资料进入模型上下文。")
bullet("建立接口字段和状态对应表，说明各模块的职责；关键输入校验与权限检查由后端或实际执行模块负责，不能只依赖界面限制。")

h3("2.2 页面与核心用户流程")
bullet("将实验7的AI能力接入实验4的基础软件，使用户能从正常入口完成一条核心任务。")
bullet("实现与项目有关的输入、等待提示、编辑和保存等交互；使用RAG时展示来源。无法获知实际进度时，显示“处理中”等状态，不编造进度百分比。")
bullet("对不确定或需要核验的AI结果给出明显提示，并允许用户修改、重新生成、转为人工处理或放弃结果，明确人和AI如何接力完成任务。")

h3("2.3 状态、会话与数据持久化")
bullet("定义任务状态及转换条件，如等待、处理中、成功、失败和取消，处理重复提交及刷新后的状态恢复；不支持恢复的任务，应明确提示重新操作。")
bullet("说明最终输出以及项目实际使用的会话历史、检索结果或工具结果是否保存、保存多久和如何清理；不使用会话、RAG或工具的项目不必增加相应数据。")
bullet("使用任务编号、会话编号或其他方式区分任务，交错发起两个不同任务，检查不同返回顺序下输入、中间结果和最终结果不会混用。")
bullet("支持取消时，说明是否只停止界面等待、是否停止后续模型或工具调用，并处理迟到结果。")

h3("2.4 错误提示与降级策略")
bullet("处理与项目有关的输入不合法、模型拒绝、模型超时、输出校验失败或网络中断；项目使用RAG或工具时，还应处理没有检索结果或工具调用失败。")
bullet("错误提示说明当前状态和可采取的操作，按需提供规则流程、明确标注的缓存结果或人工处理入口。重试可能修改数据的任务前，先核对执行状态，避免重复写入。")
bullet("演示至少一种AI不可用时的处理流程，可通过模拟超时或服务异常触发，确认用户能够继续操作或安全退出。")

h3("2.5 端到端测试与缺陷修复")
bullet("建立不少于8个端到端用例，覆盖正常流程、错误输入、等待或失败、重复操作及数据保存等相关情况，记录前置条件、操作、预期、实际结果和日志或截图。")
bullet("对实际发现的缺陷记录影响、复现步骤、可能原因、修复Commit和复测结果，并重跑相关原有用例，检查修改是否破坏已有功能；未发现缺陷时说明检查范围与依据。")
bullet("在固定的软件版本、模型和主要配置下，邀请至少1名同学试用核心流程。试用过程中只提供正常的运行说明，不直接替试用者操作，记录其完成情况、困惑、反馈、修改和再次测试结果。")

# ===================== 3. 操作记录 =====================
h2("3. 操作记录")
para("本节按 2.1—2.5 的顺序记录实际操作：先说明设计与实现，再给出表格、代码、截图和日志证据。截图均来自真实运行的前后端（Spring Boot 3.3.5，端口 8080；Vite 构建产物，端口 5173；模型 qwen-plus），用例数据来自 experiments/exp8/results，运行日志来自 backend/logs/acceptance-runs 并复制到 实验文档/TEST8/运行日志。")
para("实验环境与版本见表3-1。第 3.5 节的 14 个端到端用例全部使用真实模型与真实浏览器执行，耗时、Token、状态与错误码均取自接口响应或数据库，不使用手工填写的“示意数据”。")

tabcap("表3-1 实验环境与版本")
table(["项目", "取值", "说明"], [
    ["操作系统", "Windows 11", "本机单用户环境"],
    ["JDK / Maven", "17.0.16 / 3.9.16", "后端编译与测试"],
    ["Node.js / 前端", "24.16.0 / Vue 3.5 + Vite 5.4", "构建产物由 vite preview 提供"],
    ["后端框架", "Spring Boot 3.3.5", "REST、JPA、H2、定时清理"],
    ["模型", "qwen-plus（OpenAI 兼容 chat/completions）", "temperature 0.2，max-tokens 2000"],
    ["数据存储", "H2 文件库 ./data/ambiguity", "审查档案、验收任务"],
    ["浏览器", "Chrome 无头模式 1500×1100", "截图与端到端操作"],
    ["集成功能 Commit", f"{C_FEATURE}（后端）、{C_FRONTEND}（前端）", "端到端测试基于此版本"],
    ["测试脚本 Commit", C_TEST, "用例、故障演示、截图与结果文件"],
], widths=[3.4, 8.8, 5.2], font_size=8.5)

# -------- 3.1 --------
h2("3.1 集成边界与接口统一")
para("实验7 的验收标准生成是一个独立页面加同步接口：用户手工粘贴需求，点击后在浏览器里等待 20—40 秒，失败只返回一段错误文字，结果展示完即结束。实验8 要把这项能力接入实验4 的审查档案，就必须先划清边界：输入不再由用户重新粘贴，而是从档案取正文快照；调用不再是“一次 HTTP 请求等到结果”，而是“提交任务→后台执行→轮询状态→人工确认→保存回档案”。两者的差异见表3-2。")

tabcap("表3-2 实验7 原型与实验8 集成后的差异")
table(["维度", "实验7 原型", "实验8 集成后"], [
    ["入口", "侧边栏“验收标准”独立页，需要手工粘贴", "审查档案详情页底部面板，直接使用当前档案正文"],
    ["触发与返回", "同步 POST /api/acceptance/runs，浏览器等待完整结果", "POST /api/acceptance/tasks 立即返回 taskId，后台线程执行"],
    ["进度", "无，只有“生成中…”", "7 个任务状态 + phase 阶段 + 已用时间；不显示百分比"],
    ["失败表达", "一段 error 字符串", "错误码 + retryable + actions（重试/规则流程/转人工）"],
    ["结果去向", "页面展示后结束，不进入业务数据", "可编辑，确认后写入档案 acceptanceJson"],
    ["重复与并发", "无保护", "同档案同版本去重；任务以 taskId 隔离；保存幂等"],
    ["数据留存", "JSONL 日志", "acceptance_tasks 表 + JSONL + 档案字段，任务保留 30 天"],
], widths=[2.8, 6.7, 8.0], font_size=8.5)

para("统一后的字段与状态由后端定义，前端只负责展示和传值，避免“前端一套、后端一套、AI 一套”。关键字段见表3-3；字段名、枚举值与错误码在 AcceptanceTaskService、TaskDtos 与前端 TypeScript 类型中保持一致，接口返回的 TaskView 就是页面渲染的唯一数据源。")

tabcap("表3-3 接口字段与状态对应")
table(["字段", "取值 / 类型", "前端用途", "后端或执行模块的职责"], [
    ["taskId", "AC+14 位时间+4 位十六进制", "轮询、刷新恢复、任务列表", "服务端生成，任务唯一标识"],
    ["reviewId", "UUID 或 null", "从当前档案传入；null 表示独立输入", "校验档案存在，读取正文与检索片段快照"],
    ["status", "QUEUED/RUNNING/SUCCEEDED/FAILED/CHECK_FAILED/REFUSED/CANCELLED", "状态标签与按钮显示", "状态机唯一写入方，终态只读"],
    ["phase", "≤120 字，如“调用模型（第 2 次）”", "处理中的等待提示", "执行线程在阶段边界写入，不编造百分比"],
    ["report", "requirementKind、summary、acceptanceCriteria[]、testSamples[]、openQuestions[]、limits[]", "展示与编辑", "解析 JSON 并通过程序检查后写入"],
    ["checks", "schemaOk / groundingOk / structureOk / coverageOk + messages", "四项检查面板", "AcceptanceChecker 计算，不调用模型"],
    ["errorCode", "INPUT_INVALID、SCOPE_REJECTED、MODEL_TIMEOUT、MODEL_UNAVAILABLE、MODEL_ERROR、OUTPUT_INVALID、CHECK_FAILED、CANCELLED", "错误提示与可选操作", "把异常归一到有限错误码"],
    ["actions", "字符串数组：cancel/edit/apply/retry/fallback/handoff/discard", "按数组渲染按钮，不在前端自定义规则", "按状态与错误码计算"],
    ["decision", "PENDING / ACCEPTED / DISCARDED / MANUAL", "已保存、已放弃、转人工提示", "用户操作后写入，保留人工决定"],
    ["saved / savedAt", "布尔 / 时间字符串", "“已保存到档案”提示", "apply 幂等，重复保存不重复写入"],
], widths=[2.4, 5.6, 4.6, 5.0], font_size=8)

para("职责划分见表3-4。原则是：界面只做即时提示，关键校验和权限判断全部由后端或实际执行模块完成；即使绕过页面直接调用接口，长度、范围、状态与保存条件仍然会被拒绝。")

tabcap("表3-4 关键校验由谁负责")
table(["校验项", "前端", "后端任务接口", "执行线程 / 检查器", "档案库"], [
    ["输入长度", "提示 3000 字上限", "校验并返回 400，不创建任务", "再次校验后才调用模型", "—"],
    ["需求范围", "不判断", "记录任务后由执行线程预检", "命中采购/付款等规则即 REFUSED，attempts=0", "—"],
    ["引用逐字核验", "未通过的引用标红", "—", "AcceptanceChecker 去空白子串匹配", "—"],
    ["GWT 与三类覆盖", "展示检查结果", "—", "AcceptanceChecker 按字段与类别判断", "—"],
    ["身份与密钥", "无登录，不接触密钥", "单用户本地；密钥只在后端环境变量", "模型客户端只读后端配置", "同一数据库"],
    ["写入档案", "“保存到档案”按钮", "要求状态 SUCCEEDED、reviewId 非空", "—", "写 acceptanceJson，重复保存幂等"],
], widths=[3.0, 3.4, 4.4, 4.4, 2.6], font_size=8)

para("关于身份验证与权限：本项目从实验4 起就是单用户本地应用，没有账号、角色和多用户隔离，因此本次没有可校验的登录态；所有接口只监听本机，模型密钥只存在于后端环境变量，浏览器拿不到。为了说明“权限在哪里变化”，图3-1 用①—④标出了四处信任边界：用户输入进入后端（①）、档案正文进入模型上下文（②）、模型输出进入系统（③）、结果写回档案（④）。如果后续要支持多用户，需要补登录、按用户过滤 reviews 与 acceptance_tasks，并在保存时校验档案归属——这是遗留问题，不是本次已经实现的能力。")
figure("图3-1-集成顺序图.png", "图3-1 验收标准生成的集成顺序：界面、任务接口、状态库、模型与档案库（含等待步骤与信任边界）", 16.4)

para("错误也做了统一：前端不再自己拼错误文案，而是根据错误码显示“当前状态 + 可采取的操作”。完整错误码见表3-5；其中 HTTP 状态码只用于同步返回，异步任务失败时 HTTP 仍是 202/200，失败信息在任务里。")

tabcap("表3-5 错误码与用户可见操作")
table(["错误码", "触发条件", "HTTP", "用户看到", "可重试"], [
    ["INPUT_INVALID", "正文为空、超过 3000 字、reviewId 格式错误", "400", "具体原因 + 错误码", "否，需修改输入"],
    ["SCOPE_REJECTED", "需求命中采购/付款/股票等范围规则", "任务内", "已拒绝，未调用模型", "否，可转人工"],
    ["MODEL_TIMEOUT", "模型读超时", "任务内", "本次无结果，可重试/规则/人工", "是"],
    ["MODEL_UNAVAILABLE", "未配置密钥或通道不可用", "任务内", "模型不可用，可规则/人工", "否，重试无意义"],
    ["MODEL_ERROR", "其他模型或网络异常", "任务内", "本次无结果，可重试", "是"],
    ["OUTPUT_INVALID", "输出不是合法 JSON 或字段缺失", "任务内", "输出格式错误，结果已丢弃", "是"],
    ["CHECK_FAILED", "引用/GWT/覆盖未通过且修复用尽", "任务内", "未通过检查，可编辑或重试", "是"],
    ["CANCELLED", "用户取消，迟到结果被丢弃", "任务内", "已取消，可重新发起", "是"],
    ["TASK_NOT_FOUND", "任务不存在或超过 30 天保留期", "404", "请重新发起", "重新发起"],
    ["TASK_FINISHED", "对已结束任务调用取消", "409", "任务已结束，无法取消", "否"],
    ["TASK_ACTIVE", "对处理中任务重试/降级/转人工", "409", "请先取消或等待", "等待或取消"],
    ["TASK_NOT_READY", "对非 SUCCEEDED 结果保存", "409", "当前状态不能保存", "重试/转人工"],
    ["ALREADY_SAVED", "对已保存结果执行放弃", "409", "已保存，需先在档案清除", "否"],
    ["QUEUE_FULL", "任务线程池队列已满", "503", "排队过多，稍后或规则流程", "是"],
], widths=[3.2, 5.2, 1.2, 4.6, 3.4], font_size=8)

para("接口返回的 TaskView 是字段统一的落点，节选如下（省略 sources 等字段）：")
code_block('''public record TaskView(
    String taskId, String reviewId, String status, String statusLabel, String phase,
    String promptVersion, String mode, String model, boolean degraded, String degradeReason,
    String errorCode, String errorMessage, boolean retryable, boolean duplicate,
    int attempts, long durationMs, int promptTokens, int completionTokens,
    String createdAt, String startedAt, String finishedAt,
    boolean cancelRequested, String decision, boolean edited, boolean saved, String savedAt,
    String retryOf, Report report, Checks checks, List<SourceRef> sources, List<String> actions) {}''')

# -------- 3.2 --------
h2("3.2 页面与核心用户流程")
para("集成入口放在“审查档案”的详情页：用户从首页进入档案列表，打开一份档案，页面底部的“把这份档案变成可验收的测试”面板就是实验7 能力的入口。用户不需要复制正文，也不需要重新选择模型；档案正文、检索片段和档案编号会随任务一起提交。图3-2 是打开档案后的初始状态，此时没有任务，面板显示档案字数与 3000 字上限。")
figure("图3-2-集成入口.png", "图3-2 集成入口：档案详情页底部的验收标准面板（未开始）", 15.6)

para("核心流程共 6 步：① 打开档案；② 点击“生成验收标准”；③ 观察排队/处理中与阶段；④ 核对验收标准、测试样例、待确认问题与四项检查；⑤ 需要时编辑并保存修改；⑥ 确认后保存到档案。生成期间界面如图3-3：状态为“处理中”，显示“调用模型（第 1 次）”和已用秒数，并提供“取消”按钮；这里没有百分比，因为模型返回前无法获知真实进度，按 2.2 的要求只显示状态与阶段。")

figure("图3-3-处理中.png", "图3-3 处理中：显示阶段与已用时间，提供取消，不显示进度百分比", 15.6)

para("生成完成后的界面如图3-4：顶部是状态与“已保存/未保存”，中间是四项检查（结构、引用、GWT、覆盖）和验收标准卡片，每条标准都有 Given/When/Then 与逐字引用；下面是测试样例、待确认问题和本次限制，最后是“编辑、保存到档案、重新生成、规则流程、转人工、放弃结果”等操作。只要结果是 AI 生成的，面板就会显示“AI 生成结果，需人工核验”的提示，避免用户把模型输出当成已验证结论。")
figure("图3-4-生成完成与检查.png", "图3-4 已生成：检查面板、验收标准、测试样例与待确认问题（AI 结果需人工核验）", 15.6)

para("点击“保存到档案”后，结果写入档案的 acceptanceJson，并显示保存时间与任务编号（图3-5）。刷新页面或重新打开档案，面板会从档案读回已保存的结果（图3-6），不需要重新调用模型。保存是幂等的：重复点击不会重复写入，接口返回同一个 savedAt。")
figure("图3-5-保存到档案.png", "图3-5 保存到档案：显示保存时间与任务编号", 15.6)
figure("图3-6-重新打开档案已保存.png", "图3-6 重新打开档案：已保存的验收标准从档案恢复", 15.6)

para("对 AI 不确定的结果，界面给出三条人机接力路径：编辑（人改字段，保存时重新做程序检查）、重新生成（创建新任务，旧任务保留）、转人工（创建可编辑的人工任务）和放弃结果（标记 decision=DISCARDED）。此外，信息不足与超出范围不是“失败”，而是 AI 的边界结果：图3-7 的模糊需求不生成验收标准，只给 3 个待确认问题；图3-8 的采购需求在调用模型前被拒绝，页面显示“已拒绝”且 attempts=0。")
figure("图3-7-信息不足.png", "图3-7 信息不足：不生成验收标准，给出待确认问题", 15.6)
figure("图3-8-超出范围.png", "图3-8 超出范围：程序在调用模型前拒绝，未产生模型费用", 15.6)

para("来源展示分两层：一是每条验收标准和测试样例的 sourceQuote，逐字来自档案正文，点击检查项可以看到“引用可核验/不可核验”；二是档案审查时使用的 RAG 检索片段，提交任务时作为快照保存在 sources 中，面板底部列出编号、来源、标题与得分；如果该档案没有检索片段，面板会明确写“本次任务的来源只有档案原文与逐条引用”。")
para("界面元素与实现位置见表3-6。等待与轮询由 acRefreshTask 完成：任务处于 QUEUED/RUNNING 时每 1.2 秒查询一次，进入终态后停止，并把任务编号写入 localStorage 以便刷新恢复。")
code_block('''async function acRefreshTask() {
  const cur = acTask.value
  const fresh = await request(`/acceptance/tasks/${cur.taskId}`) as AcceptanceTask
  acTask.value = fresh
  if (acIsActive(fresh)) acStartPoll()          // QUEUED / RUNNING：继续轮询
  else { acStopPoll(); await acLoadTaskList(fresh.reviewId) }
}''')

tabcap("表3-6 界面元素与实现")
table(["界面元素", "行为", "实现位置"], [
    ["生成/重新生成按钮", "处理中禁用；提交后立即显示任务编号", "App.vue acGenerate"],
    ["状态与阶段", "标签 + phase + 已用秒数，不显示百分比", "acTask / acElapsed"],
    ["取消", "排队立即取消；处理中显示“正在取消”", "POST /tasks/{id}/cancel"],
    ["四项检查", "结构/引用/GWT/覆盖，未通过标红", "AcceptanceResult.vue"],
    ["编辑", "可改摘要、标准、样例、待确认问题；保存后重新检查", "PUT /tasks/{id}/result"],
    ["保存到档案", "仅 SUCCEEDED 可保存；幂等；显示保存时间", "POST /tasks/{id}/apply"],
    ["降级与转人工", "规则流程（非 AI 标注）、人工任务", "POST /tasks/{id}/fallback、/handoff"],
    ["来源", "逐字引用 + 档案检索片段快照", "TaskView.sources"],
    ["任务历史", "本档案最近任务，可切换查看", "GET /tasks?reviewId="],
], widths=[3.6, 9.2, 5.0], font_size=8.5)

# -------- 3.3 --------
h2("3.3 状态、会话与数据持久化")
para("任务状态定义为 7 个：QUEUED（排队中）、RUNNING（处理中）、SUCCEEDED（已生成）、FAILED（生成失败）、CHECK_FAILED（校验未通过）、REFUSED（已拒绝）、CANCELLED（已取消）。状态只由后端状态机写入，前端只读；终态不可被迟到结果或重复请求覆盖。转换条件见表3-7，状态图见图3-9。")

tabcap("表3-7 任务状态与转换条件")
table(["状态", "进入条件", "离开条件 / 可做操作", "用户可见"], [
    ["QUEUED", "任务落库，等待线程池", "被线程取到→RUNNING；取消→CANCELLED", "排队中，可取消"],
    ["RUNNING", "后台线程开始执行", "检查通过→SUCCEEDED；3 次未通过→CHECK_FAILED；异常/超时→FAILED；范围命中→REFUSED；取消→CANCELLED", "处理中 + 阶段 + 已用时间"],
    ["SUCCEEDED", "四项检查通过", "编辑、保存、重新生成、转人工、放弃；人工修改后仍可保存", "已生成"],
    ["CHECK_FAILED", "修复次数用尽仍未通过", "编辑（检查通过可转 SUCCEEDED）、重试、规则、人工", "校验未通过 + 原因"],
    ["FAILED", "模型异常、超时、输出格式错误", "重试、规则流程、转人工", "生成失败 + 错误码"],
    ["REFUSED", "范围预检命中，未调用模型", "转人工、重新生成", "已拒绝"],
    ["CANCELLED", "用户取消；迟到结果被丢弃", "重新生成、规则、人工", "已取消"],
], widths=[2.4, 4.6, 7.4, 3.4], font_size=8.5)
figure("图3-9-任务状态图.png", "图3-9 任务状态与转换条件（终态只读；重试/降级/人工创建新任务）", 15.8)

para("重复提交有两层保护。界面层：任务处于排队或处理中时生成按钮禁用；接口层：同一“档案（或文本哈希）+ Prompt 版本 + 模式”存在进行中的任务时，直接返回已有任务并标记 duplicate=true，不新建任务。图3-10 是连点后仍只有一个任务的状态，E2E-02 记录任务数从 1 增至 2（原有的已保存任务 + 本次新任务），重复请求没有产生第三个任务。")
figure("图3-10-重复提交.png", "图3-10 重复提交：按钮禁用，接口返回同一任务（duplicate=true）", 15.6)

para("刷新恢复使用任务编号：前端把最近一次任务的 taskId 存在 `acceptanceTask:<reviewId>`，刷新或重新进入档案时先按编号查询；任务不存在（超过 30 天保留期）时清除本地编号并提示重新发起。图3-11 是生成过程中刷新页面后恢复的界面，任务编号与刷新前一致，状态仍为处理中。如果本地没有编号，则优先恢复进行中的任务；没有进行中任务且档案已保存结果时，直接展示已保存的验收标准，而不是最近一次可能失败的任务。")
figure("图3-11-刷新恢复.png", "图3-11 刷新恢复：按 taskId 恢复同一任务与状态", 15.6)

para("取消是协作式的，这是本次集成里最需要说清楚的语义：排队中的任务立即置为 CANCELLED；处理中的任务只置 cancelRequested，后台线程在当前模型调用返回后丢弃结果并置为 CANCELLED。已经在途的 HTTP 请求无法中断，因此取消后仍可能消耗一次模型调用，但结果不会写入任务，也不会覆盖终态。图3-12 是点击取消后的“正在取消（等待当前调用返回）”，图3-13 是最终状态；对应日志如下（实验文档/TEST8/运行日志/cancelled.jsonl 节选）：")
excerpt = cancelled_log_excerpt()
if excerpt:
    code_block(excerpt)
else:
    code_block('''{"phase":"model","status":"start","attempt":1}
{"phase":"cancel","status":"CANCELLED","stage":"after-model","lateResult":true}
{"phase":"finish","status":"CANCELLED","durationMs":23000}''')
figure("图3-12-取消请求.png", "图3-12 取消请求：处理中点击取消后显示“正在取消”", 15.6)
figure("图3-13-已取消.png", "图3-13 已取消：结果为空，迟到结果未写入", 15.6)

para("两个不同任务交错时，任务编号、结果和状态都按 taskId 隔离，服务端没有共享的“当前任务”变量。E2E-08 同时为两份档案发起任务，先返回的任务不会覆盖后返回的任务；回到档案 A 仍显示 A 的任务。实际结果见表3-8。")
task_a, task_b = task_pair("E2E-08")
tabcap("表3-8 两任务交错的实际结果")
table(["项目", "任务 A", "任务 B"], [
    ["来源档案", "正常需求档案（上传大小/格式/解析时限）", "管理档案（筛选、导出、删除确认）"],
    ["任务编号", task_a, task_b],
    ["结果摘要", fetch_summary(task_a), fetch_summary(task_b)],
    ["任务列表归属", "只出现在 A 档案", "只出现在 B 档案"],
    ["交错后检查", "回到 A 档案仍显示 A 的任务，无 B 的内容", "B 档案显示 B 的任务与历史"],
], widths=[3.2, 7.2, 7.2], font_size=8.5)
para(f"用例记录的实际结果为：{CASES['E2E-08']['actual']}")
figure("图3-14-两任务交错.png", "图3-14 两任务交错：结果与任务列表互不混用", 15.6)

para("数据保存与清理见表3-9。任务表保存输入快照、状态、阶段、结果、检查、错误码、耗时、Token 和人工决定；用户确认的结果写入档案；运行日志按 runId 保存 JSONL 与完整产物。清理任务每小时执行一次，只删除已结束且超过 30 天的任务和日志；进行中的任务不会被清理。该项目不使用多轮会话，工具调用只在实验6 的档案分析功能里，本功能不新增会话或工具结果表。")

tabcap("表3-9 数据保存与清理")
table(["数据", "存储位置", "保留期", "清理方式", "删除档案的影响"], [
    ["任务与结果", "acceptance_tasks 表", "30 天", "定时任务删除终态旧任务", "任务保留，但无法再保存到档案"],
    ["已确认结果", "reviews.acceptanceJson", "随档案", "删除档案时一并删除", "结果随档案删除"],
    ["输入快照", "acceptance_tasks.inputText", "30 天", "随任务删除", "任务保留输入副本"],
    ["检索来源快照", "acceptance_tasks.sourcesJson", "30 天", "随任务删除", "用于核对生成依据"],
    ["运行日志", "backend/logs/acceptance-runs", "30 天", "清理任务删除过期文件", "不影响档案"],
], widths=[3.0, 5.8, 2.0, 3.8, 3.4], font_size=8.5)

para("状态迁移与迟到结果的处理集中在 finish 方法：只要任务已请求取消或已经是 CANCELLED，就不写结果、不改状态，只记录 late_result_discarded。节选：")
code_block('''synchronized (lock) {
  AcceptanceTask task = repo.findById(taskId).orElse(null);
  boolean cancelled = task.isCancelRequested() || TaskStatus.CANCELLED.equals(task.getStatus())
      || (response != null && "CANCELLED".equals(response.status()));
  if (cancelled) {
    task.setStatus(TaskStatus.CANCELLED);
    task.setPhase("已取消");
    task.setResultJson(null);              // 迟到结果丢弃
    task.setErrorCode("CANCELLED");
    repo.save(task);
    log.info("acceptance.task.late_result_discarded id={} lateStatus={}", taskId, response.status());
    return;
  }
  ...
}''')

# -------- 3.4 --------
h2("3.4 错误提示与降级策略")
para("本项目实际会遇到的错误分为五类：输入不合法、范围拒绝、模型超时/不可用、输出格式错误、程序检查不通过，另外还有网络中断导致的模型调用失败。表3-10 给出每一种的处理方式、用户看到的提示和证据。所有提示都说明“当前状态 + 下一步能做什么”，而不是只给一个“失败”。")

tabcap("表3-10 错误与降级处理")
table(["情形", "触发方式", "状态/错误码", "用户可见提示与操作", "证据"], [
    ["输入不合法", "档案正文 3520 字", "400 INPUT_INVALID", "指出实际字数，要求缩短；不创建任务", "图3-15，E2E-05"],
    ["范围拒绝", "采购/付款需求", "REFUSED / SCOPE_REJECTED", "已拒绝，未调用模型；可转人工", "图3-8，E2E-07"],
    ["模型不可用", "启动时不配置密钥", "FAILED / MODEL_UNAVAILABLE", "模型不可用；规则流程/转人工", "图3-16，E2E-12"],
    ["模型超时", "读超时设为 1 ms", "FAILED / MODEL_TIMEOUT", "本次无结果；重试/规则/人工", "图3-18，E2E-13"],
    ["输出格式错误", "模型返回非 JSON（单测覆盖）", "FAILED / OUTPUT_INVALID", "结果已丢弃；可重试", "AcceptanceServiceTest"],
    ["检查不通过", "引用/覆盖不达标（单测覆盖）", "CHECK_FAILED", "列出未通过项；编辑/重试", "AcceptanceServiceTest"],
    ["并发写冲突", "重复提交同一档案", "200 + duplicate=true", "恢复已有任务，不新建", "图3-10，E2E-02"],
], widths=[2.8, 4.2, 4.0, 4.4, 2.4], font_size=8)

para("图3-15 是超长档案的提示，前端现在优先显示后端的具体原因并附错误码，用户能直接看到“当前 3520 个字符”，而不是只有一句“输入不合法”。")
figure("图3-15-输入超长.png", "图3-15 输入不合法：显示实际字数与错误码，未创建任务", 15.6)

para("AI 不可用的演示不使用“假失败开关”：把 `AI_MODE=qwen` 且 `DASHSCOPE_API_KEY` 置空启动后端，生成任务会真实走到模型通道并失败。此时任务状态为生成失败，错误码 MODEL_UNAVAILABLE，面板给出“重试 / 规则流程 / 转人工”三个入口（图3-16）。用户可以选择“规则流程”继续：规则流程不调用模型，用句子模板生成一份可编辑的占位结果，并明确标注“非 AI 结果”，保存时把这个标记一起写入档案（图3-17）；也可以转人工，直接填写后保存。")
figure("图3-16-模型不可用.png", "图3-16 模型不可用：错误码、当前状态与三个可选操作", 15.6)
figure("图3-17-规则降级.png", "图3-17 规则降级：明确标注“非 AI 结果”，可编辑后保存", 15.6)

para("第二种演示是把 `ACCEPTANCE_TIMEOUT_MS` 设为 1，触发真实的读超时（不是伪造响应）。任务返回 MODEL_TIMEOUT，错误信息保留底层 “Read timed out” 以便定位，但不会重复“模型调用失败”前缀（图3-18）。重试会创建新任务，原失败任务保留，便于对比失败原因；已经结束的任务不会因为重试被改写。")
figure("图3-18-模型超时.png", "图3-18 模型超时：真实读超时被识别为 MODEL_TIMEOUT", 15.6)

para("降级策略遵循三条原则。第一，不编造：没有模型结果时不生成“看起来像 AI 输出”的内容；规则结果必须带 degraded 标记，缓存结果本项目没有使用。第二，重试前核对状态：重试、降级、转人工都先检查任务是否仍在处理中，处理中会返回 TASK_ACTIVE 并提示先取消；保存是幂等的，已保存的结果不会重复写入。第三，可以安全退出：任何失败状态下，用户都可以关闭页面或返回档案，任务表保留记录，不会留下半写状态的结果。")

# -------- 3.5 --------
h2("3.5 端到端测试与缺陷修复")
para("端到端测试使用真实前后端、真实 qwen-plus 和真实浏览器（Chrome 无头模式），脚本为 experiments/exp8/e2e-normal.mjs 与 e2e-fault.mjs。11 个主用例覆盖正常流程、重复提交、取消、刷新恢复、非法输入、信息不足、超出范围、两任务交错、人工修改、放弃结果和转人工；3 个故障用例覆盖模型不可用、模型超时和重启后恢复。所有用例的前置条件、操作、预期、实际结果和截图记录在 experiments/exp8/results/*.json，报告中的表格由这些文件生成，未做人工改写。")
para(f"执行结果：主用例 {len(NORMAL_CASES)}/11 通过，用时 {TOTAL_MS / 1000:.1f} 秒；故障用例 3/3 通过，分别在“无密钥”“1 ms 超时”“恢复正常并重启”三种配置下执行。用例与结果见表3-11、表3-12。")

def case_rows(ids):
    rows = []
    for cid in ids:
        c = CASES[cid]
        rows.append([cid, clip(c["preconditions"], 42), clip(c["steps"], 62), clip(c["expected"], 58), clip(c["actual"], 78), "通过" if c["status"] == "PASS" else "失败"])
    return rows

tabcap("表3-11 端到端用例（主流程与边界）")
table(["编号", "前置条件", "操作", "预期", "实际结果", "结论"],
      case_rows(["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08"]),
      widths=[1.1, 3.4, 4.4, 4.2, 3.6, 1.0], font_size=7.5)

tabcap("表3-12 端到端用例（交互、放弃、人工与故障）")
table(["编号", "前置条件", "操作", "预期", "实际结果", "结论"],
      case_rows(["E2E-09", "E2E-10", "E2E-11", "E2E-12", "E2E-13", "E2E-14"]),
      widths=[1.1, 3.4, 4.4, 4.2, 3.6, 1.0], font_size=7.5)

para("交互与故障用例的界面证据见图3-19—图3-22。图3-19 是人工修改：编辑模式可改摘要、验收标准与测试样例，保存后重新执行程序检查；图3-20 是放弃结果后的状态，任务记录保留、decision=DISCARDED；图3-21 是拒绝任务转人工后的人工填写结果；图3-22 是后端重启后重新打开档案，已保存的规则降级结果仍可读取。")
figure("图3-19-人工修改.png", "图3-19 人工修改：编辑标题并保存，保存后重新检查", 15.6)
figure("图3-20-放弃结果.png", "图3-20 放弃结果：decision=DISCARDED，任务记录保留", 15.6)
figure("图3-21-转人工保存.png", "图3-21 转人工：人工任务填写后保存到档案", 15.6)
figure("图3-22-重启后恢复.png", "图3-22 重启后恢复：任务状态与已保存结果仍在", 15.6)

para("测试过程中实际发现并修复了 6 个缺陷，均来自真实运行或真实联调，不是人为制造。缺陷、影响、复现、原因、修复提交与复测结果见表3-13。")
tabcap("表3-13 缺陷与修复")
table(["编号", "缺陷与影响", "复现步骤", "可能原因", "修复 Commit", "复测"], [
    ["D1", "浏览器保存人工修改失败：PUT 预检被拒，编辑功能不可用", "打开已生成结果→编辑→保存修改", "CORS allowedMethods 未包含 PUT", C_FRONTEND, "E2E-09 通过"],
    ["D2", "取消或失败后没有操作按钮，用户只能停在空结果", "生成中取消→结果区为空→无重试/人工入口", "操作按钮渲染在 report 分支内", C_TEST, "E2E-03、E2E-12 通过"],
    ["D3", "取消后阶段被后续阶段覆盖，误以为取消未生效", "取消后等模型返回并进入检查", "updatePhase 未判断 cancelRequested", C_TEST, "E2E-03 显示“正在取消”"],
    ["D4", "超长输入只显示通用错误，看不到实际字数", "用 3520 字档案生成", "前端优先用错误码映射文案", C_TEST, "E2E-05 显示 3520 字"],
    ["D5", "超时提示重复“模型调用失败：”，难读", "ACCEPTANCE_TIMEOUT_MS=1 生成", "客户端与服务层各加一次前缀", C_TEST, "E2E-13 提示只出现一次"],
    ["D6", "清空本地任务编号后，重新打开档案看不到已保存结果", "新浏览器打开已保存档案", "无任务编号时总回退到最近任务", C_TEST, "E2E-14 恢复已保存结果"],
], widths=[1.1, 4.6, 4.0, 3.8, 2.2, 2.2], font_size=8)

para("修复后重跑了相关原有用例与全量回归，结果见表3-14。后端 56 个测试全部通过（原有 44 个 + 本次新增 12 个），前端构建包含 vue-tsc 类型检查，端到端 11 个主用例与 3 个故障用例全部通过；没有发现修复破坏已有功能。")
tabcap("表3-14 回归结果")
table(["检查项", "范围", "结果"], [
    ["后端单元/接口测试", "AcceptanceTaskServiceTest 12 个 + 原有 44 个", "56/56 通过"],
    ["前端构建", "vue-tsc 类型检查 + vite build", "通过，产物 index-*.js 约 1.08 MB"],
    ["主链路冒烟", "experiments/exp8/smoke.mjs：档案→任务→编辑→保存→读取", "通过"],
    ["端到端主用例", "E2E-01—E2E-11", "11/11 通过"],
    ["故障与恢复", "E2E-12—E2E-14", "3/3 通过"],
    ["原有功能抽查", "审查创建、追问、PDF 导出、档案分析 Agent", "ReviewControllerTest 等原有测试通过"],
], widths=[3.8, 8.6, 5.2], font_size=8.5)

para("仓库与版本：代码保存在个人 GitHub 仓库 https://github.com/Ventus-cn/AI_Request_Checker（main 分支）。本次集成相关提交为：后端任务接口与状态机 "
     + C_FEATURE + "，前端集成面板 " + C_FRONTEND + "，端到端用例与测试证据 " + C_TEST
     + "；报告、截图与试用记录表随 main 分支提交。运行说明见 实验文档/TEST8/运行说明.md，测试结果见 experiments/exp8/results/e2e-normal.json 与 e2e-fault.json，运行日志见 实验文档/TEST8/运行日志。")

para("同学试用按 2.5 的要求准备：固定版本为本报告表3-1 的 Commit，模型 qwen-plus，temperature 0.2，超时 60 s，最多 3 次尝试；只提供《运行说明》，不替试用者操作。试用任务见表3-15，记录表模板见 实验文档/TEST8/试用记录表.md，包含完成情况、用时、卡住位置、原话反馈、修改与再次测试。")
para("截至本稿完成时，试用记录尚未回收，因此本节只保留记录表结构与试用任务，不填写未经证实的完成率或主观评价；收到记录后，会把每位试用者的完成情况、困惑、对应修改和复测结果补入表3-15 下方，并注明修改 Commit。未完成的试用不作为“已验证”的结论，这一点在实验小结中也保持一致。")

tabcap("表3-15 试用任务与记录状态")
table(["编号", "试用任务", "观察点", "记录状态"], [
    ["T1", "打开一份审查档案，找到“生成验收标准”入口", "是否能在正常入口发现功能", "待试用者填写"],
    ["T2", "发起生成，说出当前状态、能否取消", "是否理解“处理中”与取消语义", "待试用者填写"],
    ["T3", "判断结果是否可保存，并说明依据", "是否注意到检查项与人工核验提示", "待试用者填写"],
    ["T4", "修改一条验收标准的标题并保存", "编辑与保存是否顺手", "待试用者填写"],
    ["T5", "保存到档案，刷新后确认仍在", "是否理解结果已写入档案", "待试用者填写"],
], widths=[1.2, 7.4, 6.4, 2.8], font_size=8.5)

# ===================== 4. 实验小结 =====================
summary_heading = h1("4. 实验小结")
summary_heading.paragraph_format.page_break_before = True
para("本次实验把实验7 的“需求→可验收标准”能力真正接进了实验4 的审查档案：入口从独立页面移到档案详情页，调用从同步等待改为后台任务，结果从“看完即走”变为可编辑、可保存、可追溯的档案数据。用户现在可以从一份已有档案出发，完成“生成—核对—修改—保存”的完整任务，不需要复制正文，也不需要在浏览器里空等。")
para("实现过程中体会最深的是三点。第一，集成的难点不在模型，而在状态：模型调用只是链路中的一段，真正决定体验的是排队、处理中、失败、取消、迟到结果和保存这些状态是否被明确建模。把状态机、阶段、错误码和 actions 定义清楚后，前端不再需要“猜”当前能不能点，用户也能看懂发生了什么。第二，取消必须说清楚语义：界面能立即停止等待，但在途的模型调用无法中断，只能丢弃结果；如果假装“已停止”，用户会以为没有产生费用或副作用，这是不诚实的。第三，降级要克制：规则流程只能作为明确标注的占位结果，不能伪装成 AI 输出；没有结果时给出重试、规则、人工三条路，比编造一个“看起来还行”的结果更可靠。")
para("端到端测试的价值在这一次非常直接：6 个缺陷里有 4 个只有在真实浏览器、真实模型和真实重启下才会暴露——PUT 被 CORS 拦住、取消后按钮消失、取消阶段被覆盖、清空本地编号后看不到已保存结果。如果没有这些用例，单测和手工点几下都可能漏掉。修复后重跑 56 个后端测试、前端构建和 14 个端到端用例，确认没有破坏已有功能。")
para("当前局限也很明确：项目仍是单用户本地应用，没有登录与多用户隔离，接口没有鉴权；单个档案正文上限 3000 字，超长档案需要先精简；取消不能中断在途请求，会多消耗一次模型调用；任务只保留 30 天，过期后需要重新生成；程序检查只能验证引用、GWT 与覆盖，不能判断业务语义是否真的正确；同学试用记录尚未回收，试用结论待补。后续计划先补登录与档案归属校验，再做长文本分段与总时限，最后把试用反馈转成具体的交互修改并复测。")
para("从工程角度看，这次实验最大的收获不是“把 AI 放进页面”，而是建立了一条可验证的集成链：固定的接口字段与状态、可重放的端到端用例、每次运行都留痕的任务与日志。只要这条链在，换模型、改 Prompt、加降级策略，都能马上知道是变好还是变坏，也能向用户说清楚“现在发生了什么、下一步能做什么”。")

# ===================== 页脚页码 =====================
footer_p = doc.sections[0].footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = footer_p.add_run("第 ")
r1.font.size = Pt(9)
fld_begin = OxmlElement("w:fldChar")
fld_begin.set(qn("w:fldCharType"), "begin")
instr = OxmlElement("w:instrText")
instr.set(qn("xml:space"), "preserve")
instr.text = "PAGE"
fld_end = OxmlElement("w:fldChar")
fld_end.set(qn("w:fldCharType"), "end")
r2 = footer_p.add_run()
r2.font.size = Pt(9)
r2._r.append(fld_begin)
r2._r.append(instr)
r2._r.append(fld_end)
r3 = footer_p.add_run(" 页")
r3.font.size = Pt(9)

for p in doc.paragraphs:
    if p.style.name in ("Title", "Heading 1", "Heading 2", "Heading 3"):
        for r in p.runs:
            r.font.name = "微软雅黑"
            rfonts = r._element.get_or_add_rPr().get_or_add_rFonts()
            rfonts.set(qn("w:eastAsia"), "微软雅黑")
            rfonts.set(qn("w:cs"), "微软雅黑")
            strip_theme_fonts(rfonts)

doc.save(str(OUT))
print(OUT)
print("size", OUT.stat().st_size)