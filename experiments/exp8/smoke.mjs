// 集成层冒烟测试：真实调用后端与模型，验证“档案 → 任务 → 结果 → 编辑 → 保存”主链路。
// 用法：node experiments/exp8/smoke.mjs
const API = "http://localhost:8080/api";

const REQUIREMENT = "用户可以在需求审查页上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB。"
  + "上传后系统解析正文和内嵌图片，解析时间不超过 60 秒。文件超过 10MB 或格式不支持时，页面提示具体原因并拒绝上传。"
  + "扫描版 PDF 需要视觉模型识别，识别失败的页面应在结果中标注未识别范围。";

async function call(path, options = {}) {
  const res = await fetch(API + path, options);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) {
    const error = new Error(data.error || `HTTP ${res.status}`);
    error.code = data.code;
    error.status = res.status;
    throw error;
  }
  return data;
}

const json = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

const step = (name, extra = "") => console.log(`[${new Date().toISOString().slice(11, 19)}] ${name}${extra ? " " + extra : ""}`);

const review = await call("/reviews", json({ text: REQUIREMENT, mode: "全面审查", promptVersion: "revised" }));
step("审查档案已创建", review.id);

const started = Date.now();
const task = await call("/acceptance/tasks", json({ reviewId: review.id, promptVersion: "revised", mode: "model" }));
step("任务已提交", `${task.taskId} ${task.status} ${task.phase}`);

let view = task;
const seen = [];
while (view.status === "QUEUED" || view.status === "RUNNING") {
  await new Promise((r) => setTimeout(r, 1000));
  view = await call(`/acceptance/tasks/${task.taskId}`);
  if (seen.at(-1) !== view.phase) { seen.push(view.phase); step("阶段", view.phase); }
  if (Date.now() - started > 150_000) throw new Error("等待任务超时");
}
step("任务结束", `${view.status} ${view.durationMs}ms 尝试 ${view.attempts} 次 Token ${view.promptTokens + view.completionTokens}`);

if (view.status !== "SUCCEEDED") {
  console.log(JSON.stringify({ status: view.status, errorCode: view.errorCode, error: view.errorMessage }, null, 2));
  process.exit(1);
}
console.log("验收标准:", view.report.acceptanceCriteria.map((a) => `${a.id} ${a.title}`).join(" | "));
console.log("测试样例:", view.report.testSamples.map((t) => `${t.id}/${t.kind}`).join(" "));
console.log("检查:", JSON.stringify(view.checks));

const edited = structuredClone(view.report);
edited.acceptanceCriteria[0].title = edited.acceptanceCriteria[0].title + "（人工补充）";
const afterEdit = await call(`/acceptance/tasks/${task.taskId}/result`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ report: edited }),
});
step("人工修改已保存", `edited=${afterEdit.edited} grounding=${afterEdit.checks?.groundingOk}`);

const applied = await call(`/acceptance/tasks/${task.taskId}/apply`, { method: "POST" });
step("已保存到档案", `saved=${applied.task.saved} savedAt=${applied.task.savedAt}`);

const saved = await call(`/reviews/${review.id}/acceptance`);
step("档案读取验收标准", `saved=${saved.saved} task=${saved.acceptance?.taskId} 标题=${saved.acceptance?.report?.acceptanceCriteria?.[0]?.title}`);

const tasks = await call(`/acceptance/tasks?reviewId=${review.id}`);
step("档案任务列表", tasks.map((t) => `${t.taskId}/${t.status}`).join(", "));