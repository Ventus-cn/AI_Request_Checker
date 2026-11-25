// 实验8 端到端测试（正常配置）：真实前后端 + 真实 qwen-plus。
// 覆盖正常主流程、重复提交、取消、刷新恢复、输入不合法、信息不足、超出范围、
// 两任务交错、人工修改、放弃结果、转人工。结果写入 results/e2e-normal.json。
import fs from "node:fs";
import path from "node:path";
import { launchChrome, openPage, APP, ROOT, sleep, api, jsonPost, waitFor } from "./lib/cdp.mjs";

const SHOTS = path.join(ROOT, "实验文档", "TEST8", "截图");
const RESULTS = path.join(ROOT, "experiments", "exp8", "results");
fs.mkdirSync(RESULTS, { recursive: true });

const TERMINAL = ["已生成", "生成失败", "校验未通过", "已拒绝", "已取消"];
const TERMINAL_API = ["SUCCEEDED", "FAILED", "CHECK_FAILED", "REFUSED", "CANCELLED"];
const results = [];
let current = null;
const startedAll = Date.now();

const TEXTS = {
  normal: "用户可以上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB。上传后系统解析正文和内嵌图片，解析时间不超过 60 秒。"
    + "文件超过 10MB 或格式不支持时，页面提示具体原因并拒绝上传。扫描版 PDF 需要调用视觉模型识别，识别失败的页面应在结果中标注未识别范围。",
  second: "管理员可以按风险等级筛选审查档案，并导出当前版本的 PDF 报告。导出不调用模型，超过 200 条档案时提示缩小筛选范围。"
    + "普通用户只能查看本人创建的档案，删除档案需要二次确认，删除后不可恢复。",
  insufficient: "用户可以上传文件然后得到结果。",
  scope: "帮我采购 20 台服务器，要求报价最低的供应商，并在本周内完成付款审批。服务器到货后由行政部分配给各项目组。",
  long: "系统在用户提交需求后返回审查结果并保存档案。".repeat(160),
};

function startCase(id, title, preconditions, steps, expected, evidence = []) {
  current = { id, title, preconditions, steps, expected, actual: "", status: "", evidence, startedAt: Date.now() };
}
function finishCase(ok, actual, extra = {}) {
  current.actual = actual;
  current.status = ok ? "PASS" : "FAIL";
  current.durationMs = Date.now() - current.startedAt;
  Object.assign(current, extra);
  results.push(current);
  fs.writeFileSync(path.join(RESULTS, "e2e-normal.json"), JSON.stringify(results, null, 2));
  console.log(`  ${ok ? "PASS" : "FAIL"} ${current.id} ${actual}`);
  current = null;
}
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
async function runCase(id, title, preconditions, steps, expected, evidence, body) {
  startCase(id, title, preconditions, steps, expected, evidence);
  try {
    const actual = await body();
    finishCase(true, actual);
  } catch (e) {
    finishCase(false, "失败：" + e.message);
  }
}

const scenario = {};

const chrome = await launchChrome();
const page = await openPage(SHOTS);

async function status() {
  return (await page.text(".acceptance-integration .status-chip")) || "";
}
async function panelTaskId() {
  const text = await page.text(".integration-task");
  return (text.match(/AC\d{14}-[0-9a-f]{4}/) || [])[0] || "";
}
async function waitStatus(targets, timeoutMs = 180_000) {
  return waitFor(async () => {
    const value = await status();
    return targets.includes(value) ? value : null;
  }, timeoutMs, 600);
}
async function waitTerminal(timeoutMs = 180_000) {
  return waitStatus(TERMINAL, timeoutMs);
}
async function clickGenerate() {
  const ok = await page.eval(`(() => {
    const b = document.querySelector('.acceptance-integration .integration-run');
    if (!b || b.disabled) return false;
    b.click();
    return true;
  })()`);
  assert(ok, "生成按钮不可点击");
}
async function clickAction(label) {
  const ok = await page.eval(`(() => {
    const b = [...document.querySelectorAll('.integration-actions button, .error-actions button, .edit-toolbar button, .integration-bar button, .run-btn')]
      .find(x => (x.textContent || '').includes(${JSON.stringify(label)}));
    if (!b) return false;
    b.click();
    return true;
  })()`);
  assert(ok, `未找到操作按钮：${label}`);
}
async function waitTaskTerminal(taskId, timeoutMs = 200_000) {
  try {
    return await waitFor(async () => {
      const detail = await taskDetail(taskId);
      return TERMINAL_API.includes(detail.status) ? detail : null;
    }, timeoutMs, 1500);
  } catch {
    const detail = await taskDetail(taskId);
    throw new Error(`任务 ${taskId} 未在 ${Math.round(timeoutMs / 1000)} 秒内结束：status=${detail.status} error=${detail.errorCode || ""}`);
  }
}
/** 点击生成并从接口取回新任务编号，避免依赖 DOM 刷新时机。 */
async function generateAndCapture(reviewId) {
  const before = new Set((await tasksOf(reviewId)).map((t) => t.taskId));
  await clickGenerate();
  const fresh = await waitFor(async () => {
    const list = await tasksOf(reviewId);
    return list.find((t) => !before.has(t.taskId)) || null;
  }, 30_000, 500);
  return fresh.taskId;
}
async function selectTaskRow(taskId) {
  const ok = await page.eval(`(() => {
    const row = [...document.querySelectorAll('.integration-history .task-row')]
      .find(r => (r.textContent || '').includes(${JSON.stringify(taskId)}));
    if (!row) return false;
    row.click();
    return true;
  })()`);
  return ok;
}
async function clickConfirm(label) {
  const ok = await page.eval(`(() => {
    const b = [...document.querySelectorAll('.el-message-box__btns button')]
      .find(x => (x.textContent || '').includes(${JSON.stringify(label)}));
    if (!b) return false;
    b.click();
    return true;
  })()`);
  assert(ok, `未找到确认按钮：${label}`);
}
async function setField(placeholder, value) {
  const ok = await page.eval(`(() => {
    const list = [...document.querySelectorAll('.acceptance-edit input, .acceptance-edit textarea')];
    const el = list.find(e => (e.getAttribute('placeholder') || '') === ${JSON.stringify(placeholder)});
    if (!el) return false;
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, ${JSON.stringify(value)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  assert(ok, `未找到输入框：${placeholder}`);
}
async function openArchive(id) {
  const short = id.slice(0, 8);
  await page.clickText(".side-link", "审查档案");
  await sleep(700);
  await waitFor(async () => (await page.eval("document.querySelectorAll('.archive-row').length")) > 0, 15_000);
  const ok = await page.eval(`(() => {
    const rows = [...document.querySelectorAll('.archive-row')];
    const row = rows.find(r => (r.textContent || '').includes(${JSON.stringify(short)}));
    if (!row) return false;
    row.querySelector('.icon-btn[aria-label="查看档案"]')?.click();
    return true;
  })()`);
  assert(ok, `未在档案列表找到 ${short}`);
  await sleep(1200);
  await waitFor(async () => (await page.text(".dashboard-head h2")).includes("需求质量"), 15_000);
  await sleep(600);
}
async function tasksOf(reviewId) {
  const res = await api(`/acceptance/tasks?reviewId=${reviewId}`);
  return res.data;
}
async function taskDetail(taskId) {
  return (await api(`/acceptance/tasks/${taskId}`)).data;
}

// ============================ 准备数据 ============================
console.log("准备：创建端到端测试用审查档案（真实模型）");
async function createArchive(text, label) {
  const res = await api("/reviews", jsonPost({ text, mode: "全面审查", promptVersion: "revised" }));
  assert(res.ok, `创建档案失败（${label}）：${JSON.stringify(res.data).slice(0, 200)}`);
  console.log(`  ${label} -> ${res.data.id}`);
  return res.data;
}
scenario.normal = await createArchive(TEXTS.normal, "正常需求");
scenario.second = await createArchive(TEXTS.second, "交错任务B");
scenario.insufficient = await createArchive(TEXTS.insufficient, "信息不足");
scenario.scope = await createArchive(TEXTS.scope, "超出范围");
scenario.long = await createArchive(TEXTS.long, "超长需求");

await page.navigate(APP);
await sleep(1200);

// ============================ E2E-01 正常主流程 ============================
await runCase(
  "E2E-01", "正常主流程：档案入口生成验收标准并保存",
  "正常需求的审查档案已存在；前后端与 qwen-plus 可用",
  "打开档案 → 点击“生成验收标准” → 观察处理中 → 等待已生成 → 核对检查项 → 保存到档案 → 刷新后重新打开档案",
  "任务经历排队/处理中到已生成；检查项四项通过；结果保存到档案，刷新后仍可读取",
  ["图3-2-集成入口.png", "图3-3-处理中.png", "图3-4-生成完成与检查.png", "图3-5-保存到档案.png", "图3-6-重新打开档案已保存.png"],
  async () => {
    await openArchive(scenario.normal.id);
    assert((await status()) === "未开始", "新档案面板应为未开始，实际 " + (await status()));
    await page.shotElement(".acceptance-integration", "图3-2-集成入口.png");
    await clickGenerate();
    await sleep(1500);
    const running = await status();
    assert(["排队中", "处理中"].includes(running), "点击后应进入排队/处理中，实际 " + running);
    await page.shotElement(".acceptance-integration", "图3-3-处理中.png");
    const final = await waitTerminal();
    assert(final === "已生成", "期望已生成，实际 " + final);
    const taskId = await panelTaskId();
    assert(taskId, "页面未显示任务编号");
    const detail = await taskDetail(taskId);
    assert(detail.checks && detail.checks.schemaOk && detail.checks.groundingOk
      && detail.checks.structureOk && detail.checks.coverageOk, "程序检查未全部通过");
    assert(detail.report.acceptanceCriteria.length >= 1 && detail.report.testSamples.length >= 3,
      "验收标准或测试样例数量不足");
    await page.shotElement(".acceptance-integration", "图3-4-生成完成与检查.png");
    await clickAction("保存到档案");
    await waitFor(async () => (await page.text(".saved-note")).includes("已保存到档案"), 10_000);
    const saved = await api(`/reviews/${scenario.normal.id}/acceptance`);
    assert(saved.data.saved === true && saved.data.acceptance.taskId === taskId, "接口未返回已保存的验收标准");
    await page.shotElement(".acceptance-integration", "图3-5-保存到档案.png");

    await page.reload();
    await sleep(1000);
    await openArchive(scenario.normal.id);
    const note = await page.text(".saved-note");
    assert(note.includes("已保存到档案"), "刷新后未恢复已保存状态：" + note);
    await page.shotElement(".acceptance-integration", "图3-6-重新打开档案已保存.png");
    return `任务 ${taskId} 成功，${detail.report.acceptanceCriteria.length} 条标准/${detail.report.testSamples.length} 个样例，耗时 ${detail.durationMs} ms，四项检查通过，已保存并在刷新后恢复`;
  },
);

// ============================ E2E-02 重复提交 ============================
await runCase(
  "E2E-02", "重复提交：按钮禁用且接口返回同一任务",
  "档案 E2E-01 已打开，可以再次生成",
  "点击生成 → 立即再次点击（界面）→ 直接向接口重复提交同一档案",
  "处理中按钮不可点击；接口重复提交返回同一任务编号并标记 duplicate=true；任务数量不增加",
  ["图3-10-重复提交.png"],
  async () => {
    await openArchive(scenario.normal.id);
    const before = (await tasksOf(scenario.normal.id)).length;
    await clickGenerate();
    await sleep(800);
    const disabled = await page.eval("document.querySelector('.acceptance-integration .integration-run')?.disabled === true");
    assert(disabled, "处理中生成按钮应禁用");
    const taskId = await panelTaskId();
    const dup = await api("/acceptance/tasks", jsonPost({ reviewId: scenario.normal.id, promptVersion: "revised", mode: "model" }));
    assert(dup.status === 200 && dup.data.duplicate === true, "重复提交应返回 duplicate=true 且 HTTP 200，实际 " + dup.status);
    assert(dup.data.taskId === taskId, "重复提交返回了不同任务：" + dup.data.taskId + " vs " + taskId);
    await page.shotElement(".acceptance-integration", "图3-10-重复提交.png");
    const after = (await tasksOf(scenario.normal.id)).length;
    assert(after === before + 1, `任务数应从 ${before} 增至 ${before + 1}，实际 ${after}`);
    await waitTerminal();
    return `按钮禁用；接口返回同一任务 ${taskId}（duplicate=true），任务数 ${before}→${after}`;
  },
);

// ============================ E2E-03 取消与迟到结果 ============================
await runCase(
  "E2E-03", "取消任务：处理中取消，迟到结果被丢弃",
  "档案 B 尚未生成过验收标准",
  "打开档案 B → 生成 → 处理中点击取消 → 等待终态 → 再等待 5 秒复查",
  "状态先显示“正在取消”，随后为“已取消”；结果为空；模型迟到返回的结果不覆盖已取消状态",
  ["图3-12-取消请求.png", "图3-13-已取消.png"],
  async () => {
    await openArchive(scenario.second.id);
    await clickGenerate();
    await waitStatus(["处理中"], 120_000);
    await sleep(500);
    await clickAction("取消");
    await sleep(800);
    const phase = await page.text(".integration-task");
    assert(phase.includes("正在取消") || phase.includes("已取消"), "取消后阶段应显示正在取消：" + phase);
    await page.shotElement(".acceptance-integration", "图3-12-取消请求.png");
    const taskId = await panelTaskId();
    const final = await waitStatus(["已取消"], 200_000);
    const detail = await taskDetail(taskId);
    assert(detail.report == null && detail.errorCode === "CANCELLED", "取消后不应保留结果");
    await page.shotElement(".acceptance-integration", "图3-13-已取消.png");
    await sleep(5000);
    const later = await taskDetail(taskId);
    assert(later.status === "CANCELLED" && later.report == null, "迟到结果覆盖了已取消状态");
    return `任务 ${taskId} 取消成功：阶段“${phase.trim()}”，终态已取消，等待 5 秒后仍无结果（迟到结果丢弃）`;
  },
);

// ============================ E2E-04 刷新恢复 ============================
await runCase(
  "E2E-04", "刷新恢复：生成中刷新页面后恢复同一任务",
  "正常档案可再次生成",
  "打开档案 → 生成 → 处理中刷新页面 → 重新进入档案",
  "刷新后仍显示同一任务编号，状态为处理中或已生成，不出现重复任务",
  ["图3-11-刷新恢复.png"],
  async () => {
    await openArchive(scenario.normal.id);
    await clickGenerate();
    await waitStatus(["处理中", "排队中"], 120_000);
    const taskId = await panelTaskId();
    await page.reload();
    await sleep(1200);
    await openArchive(scenario.normal.id);
    const restored = await panelTaskId();
    assert(restored === taskId, `刷新后任务编号不一致：${restored} vs ${taskId}`);
    const now = await status();
    assert([...TERMINAL, "处理中", "排队中"].includes(now), "刷新后状态异常：" + now);
    await page.shotElement(".acceptance-integration", "图3-11-刷新恢复.png");
    await waitTerminal();
    return `刷新前任务 ${taskId}，刷新后恢复为同一任务，状态 ${now}`;
  },
);

// ============================ E2E-05 输入不合法 ============================
await runCase(
  "E2E-05", "输入不合法：超过 3000 字的档案被拒绝且不产生任务",
  "存在正文超过 3000 字的需求档案",
  "打开超长档案 → 点击生成",
  "界面显示长度错误；接口返回 INPUT_INVALID；该档案下没有新任务",
  ["图3-15-输入超长.png"],
  async () => {
    await openArchive(scenario.long.id);
    const before = (await tasksOf(scenario.long.id)).length;
    await clickGenerate();
    await waitFor(async () => (await page.text(".integration-error")).includes("3000"), 10_000);
    const message = await page.text(".integration-error");
    const after = (await tasksOf(scenario.long.id)).length;
    assert(after === before, "输入不合法时不应创建任务");
    await page.shotElement(".acceptance-integration", "图3-15-输入超长.png");
    return `界面提示“${message.split("\n")[0].slice(0, 60)}”，任务数保持 ${after}`;
  },
);

// ============================ E2E-06 信息不足 ============================
await runCase(
  "E2E-06", "信息不足：不生成验收标准，给出待确认问题",
  "存在只有一句模糊描述的档案",
  "打开档案 → 生成 → 等待已生成 → 查看结果",
  "requirementKind=insufficient；验收标准 0 条；待确认问题不少于 3 条",
  ["图3-7-信息不足.png"],
  async () => {
    await openArchive(scenario.insufficient.id);
    await clickGenerate();
    const final = await waitTerminal();
    assert(final === "已生成", "期望已生成，实际 " + final);
    const detail = await taskDetail(await panelTaskId());
    assert(detail.report.requirementKind === "insufficient", "类型应为 insufficient");
    assert(detail.report.acceptanceCriteria.length === 0, "信息不足时不应生成验收标准");
    assert(detail.report.openQuestions.length >= 3, "待确认问题应不少于 3 条");
    await page.shotElement(".acceptance-integration", "图3-7-信息不足.png");
    return `类型 insufficient，0 条标准，${detail.report.openQuestions.length} 个待确认问题`;
  },
);

// ============================ E2E-07 超出范围 ============================
await runCase(
  "E2E-07", "超出范围：调用模型前拒绝",
  "存在采购付款类非软件需求档案",
  "打开档案 → 生成 → 等待已拒绝",
  "状态已拒绝；attempts=0；耗时小于 1 秒；不产生模型调用费用",
  ["图3-8-超出范围.png"],
  async () => {
    await openArchive(scenario.scope.id);
    await clickGenerate();
    const final = await waitTerminal(30_000);
    assert(final === "已拒绝", "期望已拒绝，实际 " + final);
    const detail = await taskDetail(await panelTaskId());
    assert(detail.attempts === 0, "超范围不应调用模型，attempts=" + detail.attempts);
    assert(detail.durationMs < 1000, "超范围应在 1 秒内返回，实际 " + detail.durationMs);
    assert(detail.errorCode === "SCOPE_REJECTED", "错误码应为 SCOPE_REJECTED");
    await page.shotElement(".acceptance-integration", "图3-8-超出范围.png");
    return `已拒绝，attempts=0，耗时 ${detail.durationMs} ms，错误码 SCOPE_REJECTED`;
  },
);

// ============================ E2E-08 两任务交错 ============================
await runCase(
  "E2E-08", "两任务交错：不同档案的结果不混用",
  "档案 A（正常）和档案 B 都可生成",
  "打开 A 生成 → 立即打开 B 生成 → 等待两者结束 → 分别查看任务与结果",
  "两个任务编号不同；A 的任务只出现在 A 档案，B 的只在 B 档案；各自结果与原文对应",
  ["图3-14-两任务交错.png"],
  async () => {
    await openArchive(scenario.normal.id);
    const taskA = await generateAndCapture(scenario.normal.id);
    await openArchive(scenario.second.id);
    const taskB = await generateAndCapture(scenario.second.id);
    assert(taskA && taskB && taskA !== taskB, "两个任务编号应不同");
    const finalA = await waitTaskTerminal(taskA);
    const finalB = await waitTaskTerminal(taskB);
    assert(finalA.reviewId === scenario.normal.id && finalB.reviewId === scenario.second.id, "任务与档案的归属错误");
    assert(finalA.report && finalB.report, `两个任务都应有结果（A=${finalA.status}，B=${finalB.status}）`);
    assert(finalA.report.summary !== finalB.report.summary, "两个任务的结果摘要不应相同");
    const listA = (await tasksOf(scenario.normal.id)).map((t) => t.taskId);
    const listB = (await tasksOf(scenario.second.id)).map((t) => t.taskId);
    assert(listA.includes(taskA) && !listA.includes(taskB), "A 档案的任务列表混入了 B 的任务");
    assert(listB.includes(taskB) && !listB.includes(taskA), "B 档案的任务列表混入了 A 的任务");
    await page.shotElement(".acceptance-integration", "图3-14-两任务交错.png");
    await openArchive(scenario.normal.id);
    const shown = await panelTaskId();
    assert(shown === taskA, `回到 A 档案应显示任务 ${taskA}，实际 ${shown}`);
    return `A=${taskA}、B=${taskB} 并行完成，结果摘要不同，任务列表互不混用；回到 A 仍显示 A 的任务`;
  },
);

// ============================ E2E-09 人工修改 ============================
await runCase(
  "E2E-09", "人工修改：编辑标题后保存并重新检查",
  "档案 B 有已生成结果",
  "点击编辑 → 修改第一条验收标准的标题 → 保存修改",
  "编辑模式可修改字段；保存后 edited=true，标题更新，程序检查重新执行",
  ["图3-19-人工修改.png"],
  async () => {
    await openArchive(scenario.second.id);
    const taskId = await panelTaskId();
    await clickAction("编辑");
    await waitFor(async () => (await page.text(".edit-toolbar")).includes("编辑结果"), 8_000);
    await setField("标题", "人工补充：筛选与导出权限校验");
    await page.shotElement(".acceptance-integration", "图3-19-人工修改.png");
    await clickAction("保存修改");
    await waitFor(async () => !(await page.text(".edit-toolbar")).includes("编辑结果"), 10_000);
    const detail = await taskDetail(taskId);
    assert(detail.edited === true, "任务应标记为已人工修改");
    assert(detail.report.acceptanceCriteria[0].title.includes("人工补充"), "标题修改未保存");
    assert(detail.checks, "保存后应重新执行程序检查");
    return `任务 ${taskId} 人工修改保存成功，edited=true，标题=${detail.report.acceptanceCriteria[0].title}，检查 grounding=${detail.checks.groundingOk}`;
  },
);

// ============================ E2E-10 放弃结果 ============================
await runCase(
  "E2E-10", "放弃结果：未保存的结果可放弃，任务记录保留",
  "正常档案有一个未保存的已生成结果",
  "打开档案 → 放弃结果 → 确认",
  "确认后 decision=DISCARDED；任务记录仍在任务列表；结果不再作为交付内容",
  ["图3-20-放弃结果.png"],
  async () => {
    await openArchive(scenario.normal.id);
    const list = await tasksOf(scenario.normal.id);
    const target = list.find((t) => t.status === "SUCCEEDED" && !t.saved && t.decision !== "DISCARDED");
    assert(target, "没有可放弃的未保存结果");
    if ((await panelTaskId()) !== target.taskId) {
      const selected = await selectTaskRow(target.taskId);
      assert(selected, "未找到目标任务行 " + target.taskId);
      await sleep(900);
    }
    await waitStatus(["已生成"], 10_000);
    await clickAction("放弃结果");
    await sleep(600);
    await clickConfirm("放弃结果");
    await sleep(1200);
    const detail = await taskDetail(target.taskId);
    assert(detail.decision === "DISCARDED", "decision 应为 DISCARDED，实际 " + detail.decision);
    assert(detail.saved === false, "未保存的任务不应被标记为已保存");
    const after = await tasksOf(scenario.normal.id);
    assert(after.some((t) => t.taskId === target.taskId), "放弃后任务记录应保留");
    await page.shotElement(".acceptance-integration", "图3-20-放弃结果.png");
    return `任务 ${target.taskId} decision=DISCARDED，任务记录仍保留在列表`;
  },
);

// ============================ E2E-11 转人工 ============================
await runCase(
  "E2E-11", "转人工：拒绝结果转人工填写并保存",
  "超出范围档案的任务状态为已拒绝",
  "打开档案 → 转人工 → 填写摘要 → 保存修改 → 保存到档案",
  "生成 manual 任务；人工填写后可保存；保存后档案可读取人工结果",
  ["图3-21-转人工保存.png"],
  async () => {
    await openArchive(scenario.scope.id);
    const refused = (await tasksOf(scenario.scope.id)).find((t) => t.status === "REFUSED");
    assert(refused, "未找到已拒绝的任务");
    await clickAction("转人工");
    await waitFor(async () => (await page.text(".edit-toolbar")).includes("编辑结果"), 10_000);
    await setField("摘要", "人工处理：采购需求不属于软件需求，改为人工确认业务归属。");
    await clickAction("保存修改");
    await sleep(1200);
    const manual = (await tasksOf(scenario.scope.id)).find((t) => t.mode === "manual" && t.retryOf === refused.taskId);
    assert(manual, "未创建人工任务");
    await clickAction("保存到档案");
    await waitFor(async () => (await page.text(".saved-note")).includes("已保存到档案"), 10_000);
    const saved = await api(`/reviews/${scenario.scope.id}/acceptance`);
    assert(saved.data.saved === true && saved.data.acceptance.mode === "manual", "人工结果未保存到档案");
    await page.shotElement(".acceptance-integration", "图3-21-转人工保存.png");
    return `拒绝任务 ${refused.taskId} 转人工为 ${manual.taskId}，人工摘要保存并写入档案`;
  },
);

chrome.kill();

const summary = {
  runAt: new Date().toISOString(),
  totalMs: Date.now() - startedAll,
  passed: results.filter((r) => r.status === "PASS").length,
  failed: results.filter((r) => r.status === "FAIL").length,
  cases: results,
};
fs.writeFileSync(path.join(RESULTS, "e2e-normal.json"), JSON.stringify(summary, null, 2));
console.log(`\n完成：${summary.passed} 通过 / ${summary.failed} 失败，用时 ${(summary.totalMs / 1000).toFixed(1)} 秒`);
if (summary.failed > 0) process.exitCode = 1;