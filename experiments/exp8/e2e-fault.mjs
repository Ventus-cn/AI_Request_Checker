// 实验8 故障与恢复用例：模型不可用、模型超时、后端重启后状态与已保存结果仍在。
// 需按阶段在不同配置下启动后端后分别执行：
//   node experiments/exp8/e2e-fault.mjs unavailable   # 启动后端时不提供 DASHSCOPE_API_KEY
//   node experiments/exp8/e2e-fault.mjs timeout        # ACCEPTANCE_TIMEOUT_MS=1 + 正常 Key
//   node experiments/exp8/e2e-fault.mjs restart        # 恢复正常配置并重启后执行
import fs from "node:fs";
import path from "node:path";
import { launchChrome, openPage, APP, ROOT, sleep, api, jsonPost, waitFor } from "./lib/cdp.mjs";

const SHOTS = path.join(ROOT, "实验文档", "TEST8", "截图");
const RESULTS = path.join(ROOT, "experiments", "exp8", "results");
fs.mkdirSync(RESULTS, { recursive: true });
const CONTEXT = path.join(RESULTS, "fault-context.json");
const OUTPUT = path.join(RESULTS, "e2e-fault.json");
const phase = process.argv[2] || "unavailable";
const context = fs.existsSync(CONTEXT) ? JSON.parse(fs.readFileSync(CONTEXT, "utf8")) : {};
const results = fs.existsSync(OUTPUT) ? JSON.parse(fs.readFileSync(OUTPUT, "utf8")) : [];

const TEXT = "用户可以在设置页修改昵称和头像，昵称长度 2-20 个字符。保存后立即生效并提示成功；保存失败时保留原值并提示原因。";

function record(id, title, preconditions, steps, expected, actual, ok, evidence) {
  results.push({ id, title, preconditions, steps, expected, actual, status: ok ? "PASS" : "FAIL", evidence, at: new Date().toISOString() });
  fs.writeFileSync(OUTPUT, JSON.stringify(results, null, 2));
  console.log(`  ${ok ? "PASS" : "FAIL"} ${id} ${actual}`);
}
function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const chrome = await launchChrome();
const page = await openPage(SHOTS);

async function text(selector) { return page.text(selector); }
async function status() { return (await page.text(".acceptance-integration .status-chip")) || ""; }
async function taskId() { return ((await page.text(".integration-task")).match(/AC\d{14}-[0-9a-f]{4}/) || [])[0] || ""; }
async function click(selector) {
  const ok = await page.eval(`(() => { const b = document.querySelector(${JSON.stringify(selector)}); if (!b || b.disabled) return false; b.click(); return true; })()`);
  assert(ok, "无法点击 " + selector);
}
async function clickText(selector, label) {
  const ok = await page.eval(`(() => { const b = [...document.querySelectorAll(${JSON.stringify(selector)})].find(x => (x.textContent || '').includes(${JSON.stringify(label)})); if (!b) return false; b.click(); return true; })()`);
  assert(ok, "未找到按钮：" + label);
}
async function openArchive(reviewId) {
  const short = reviewId.slice(0, 8);
  await page.clickText(".side-link", "审查档案");
  await sleep(700);
  await waitFor(async () => (await page.eval("document.querySelectorAll('.archive-row').length")) > 0, 15_000);
  const ok = await page.eval(`(() => {
    const row = [...document.querySelectorAll('.archive-row')].find(r => (r.textContent || '').includes(${JSON.stringify(short)}));
    if (!row) return false;
    row.querySelector('.icon-btn[aria-label="查看档案"]')?.click();
    return true;
  })()`);
  assert(ok, "未找到档案 " + short);
  await sleep(1200);
}
async function waitTerminal(timeout = 60_000) {
  return waitFor(async () => {
    const value = await status();
    return ["已生成", "生成失败", "校验未通过", "已拒绝", "已取消"].includes(value) ? value : null;
  }, timeout, 600);
}
async function createArchive() {
  const res = await api("/reviews", jsonPost({ text: TEXT, mode: "全面审查", promptVersion: "revised" }));
  assert(res.ok, "创建档案失败：" + JSON.stringify(res.data).slice(0, 160));
  return res.data.id;
}

try {
  await page.navigate(APP);
  await sleep(1200);

  if (phase === "unavailable") {
    const reviewId = await createArchive();
    await openArchive(reviewId);
    await click(".acceptance-integration .integration-run");
    const final = await waitTerminal(90_000);
    assert(final === "生成失败", "期望生成失败，实际 " + final);
    const id = await taskId();
    const detail = (await api(`/acceptance/tasks/${id}`)).data;
    assert(detail.errorCode === "MODEL_UNAVAILABLE", "错误码应为 MODEL_UNAVAILABLE，实际 " + detail.errorCode);
    assert(detail.actions.includes("fallback") && detail.actions.includes("handoff"), "失败后应提供规则流程/转人工");
    await page.shotElement(".acceptance-integration", "图3-16-模型不可用.png");

    await clickText(".integration-actions button, .error-actions button", "规则流程");
    await sleep(1500);
    const fallbackTask = (await api(`/acceptance/tasks?reviewId=${reviewId}`)).data.find((t) => t.degraded && t.mode === "rule");
    assert(fallbackTask, "未创建规则降级任务");
    const fb = (await api(`/acceptance/tasks/${fallbackTask.taskId}`)).data;
    assert(fb.degraded === true && fb.mode === "rule" && fb.model === "rule-baseline", "降级任务标记不正确");
    await page.shotElement(".acceptance-integration", "图3-17-规则降级.png");
    await clickText(".integration-actions button, .run-btn", "保存到档案");
    await waitFor(async () => (await text(".saved-note")).includes("已保存到档案"), 10_000);
    const saved = (await api(`/reviews/${reviewId}/acceptance`)).data;
    assert(saved.saved === true && saved.acceptance.degraded === true, "降级结果未按“非 AI”保存");
    record("E2E-12", "模型不可用：提示错误码并可规则降级后保存", "后端以 AI_MODE=qwen、无 DASHSCOPE_API_KEY 启动", "打开档案 → 生成 → 规则流程 → 保存到档案", "任务失败并给出 MODEL_UNAVAILABLE 与重试/规则/人工入口；规则结果显示非 AI 标注并可保存",
      `任务 ${id} MODEL_UNAVAILABLE；规则任务 ${fb.taskId} degraded=true、model=rule-baseline；已保存到档案`, true,
      ["图3-16-模型不可用.png", "图3-17-规则降级.png"]);
    context.reviewId = reviewId;
    context.degradedTaskId = fb.taskId;
    fs.writeFileSync(CONTEXT, JSON.stringify(context, null, 2));
  }

  if (phase === "timeout") {
    const reviewId = await createArchive();
    await openArchive(reviewId);
    await click(".acceptance-integration .integration-run");
    const final = await waitTerminal(90_000);
    assert(final === "生成失败", "期望生成失败（超时），实际 " + final);
    const id = await taskId();
    const detail = (await api(`/acceptance/tasks/${id}`)).data;
    assert(detail.errorCode === "MODEL_TIMEOUT", "错误码应为 MODEL_TIMEOUT，实际 " + detail.errorCode);
    assert(detail.errorMessage && detail.errorMessage.toLowerCase().includes("timed out"), "错误信息应说明超时：" + detail.errorMessage);
    await page.shotElement(".acceptance-integration", "图3-18-模型超时.png");
    record("E2E-13", "模型超时：真实读超时被识别为 MODEL_TIMEOUT", "后端 ACCEPTANCE_TIMEOUT_MS=1，Key 正常", "打开档案 → 生成 → 等待失败", "任务为生成失败，错误码 MODEL_TIMEOUT，页面给出重试/规则/人工入口",
      `任务 ${id} MODEL_TIMEOUT：${String(detail.errorMessage).slice(0, 80)}`, true, ["图3-18-模型超时.png"]);
    context.timeoutReviewId = reviewId;
    context.timeoutTaskId = id;
    fs.writeFileSync(CONTEXT, JSON.stringify(context, null, 2));
  }

  if (phase === "restart") {
    assert(context.degradedTaskId && context.timeoutTaskId, "缺少前两个阶段的任务编号");
    const degraded = (await api(`/acceptance/tasks/${context.degradedTaskId}`)).data;
    assert(degraded.status === "SUCCEEDED" && degraded.saved === true, "重启后降级任务状态或保存标记丢失");
    const timeout = (await api(`/acceptance/tasks/${context.timeoutTaskId}`)).data;
    assert(timeout.status === "FAILED" && timeout.errorCode === "MODEL_TIMEOUT", "重启后失败任务状态丢失");
    await openArchive(context.reviewId);
    await waitFor(async () => (await text(".integration-saved")).includes("已保存的验收标准"), 15_000);
    await page.shotElement(".acceptance-integration", "图3-22-重启后恢复.png");
    const savedText = await text(".integration-saved");
    assert(savedText.includes("已保存的验收标准"), "重启后未从档案恢复已保存结果：" + savedText.slice(0, 120));
    record("E2E-14", "服务重启：任务状态与已保存结果仍可恢复", "后端恢复正常配置并重启", "重启后查询任务 → 重新打开档案", "任务状态、错误码、保存标记与已保存结果与重启前一致",
      `降级任务 ${degraded.taskId} 仍为已保存；超时任务 ${timeout.taskId} 仍为 FAILED/MODEL_TIMEOUT；档案页恢复已保存结果`, true,
      ["图3-22-重启后恢复.png"]);
  }
} finally {
  chrome.kill();
}