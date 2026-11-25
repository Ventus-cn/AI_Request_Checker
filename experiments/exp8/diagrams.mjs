// 生成实验8 报告用的两张示意图（纯 SVG，无外部依赖）：
// 图A 集成顺序图（含等待步骤与信任边界）；图B 任务状态机。
import fs from "node:fs";
import path from "node:path";

const ROOT = "D:\\deepseek harness workspace\\AI_Request_check";
const OUT = path.join(ROOT, "实验文档", "TEST8", "图");
fs.mkdirSync(OUT, { recursive: true });

const esc = (s) => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

function text(x, y, content, opts = {}) {
  const { size = 15, anchor = "middle", fill = "#1f2937", weight = "400", family = "Microsoft YaHei, SimHei, sans-serif" } = opts;
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}">${esc(content)}</text>`;
}

function sequenceSvg() {
  const W = 1560, H = 1220, top = 150, bottom = 1120;
  const lanes = [
    { x: 110, name: "用户", sub: "浏览器操作" },
    { x: 360, name: "前端 Vue", sub: "App.vue 集成面板" },
    { x: 650, name: "任务接口", sub: "AcceptanceTaskController" },
    { x: 900, name: "任务状态库", sub: "acceptance_tasks (H2)" },
    { x: 1130, name: "模型通道", sub: "qwen-plus /chat/completions" },
    { x: 1390, name: "审查档案库", sub: "reviews (H2)" },
  ];
  const parts = [];
  parts.push(`<rect x="0" y="0" width="${W}" height="${H}" fill="#ffffff"/>`);
  parts.push(text(W / 2, 46, "图3-1 验收标准生成的集成顺序：界面、任务、状态库、模型与档案库", { size: 24, weight: "700" }));
  parts.push(text(W / 2, 78, "实线为一次调用；虚线为轮询/重复操作；灰色区间为等待步骤；①—④ 为信任级别发生变化的位置", { size: 13.5, fill: "#4b5563" }));

  for (const lane of lanes) {
    parts.push(`<rect x="${lane.x - 92}" y="100" width="184" height="52" rx="10" fill="#eef2ff" stroke="#6366f1" stroke-width="1.4"/>`);
    parts.push(text(lane.x, 122, lane.name, { size: 15.5, weight: "700", fill: "#312e81" }));
    parts.push(text(lane.x, 142, lane.sub, { size: 11, fill: "#4b5563" }));
    parts.push(`<line x1="${lane.x}" y1="${top}" x2="${lane.x}" y2="${bottom}" stroke="#c7d2fe" stroke-width="1.4" stroke-dasharray="7 7"/>`);
  }

  const msg = (from, to, y, label, opts = {}) => {
    const { dashed = false, color = "#1f2937", note = "", noteColor = "#6b7280", bidir = false } = opts;
    const a = lanes[from].x, b = lanes[to].x;
    const dir = b > a ? 1 : -1;
    parts.push(`<line x1="${a}" y1="${y}" x2="${b - dir * 10}" y2="${y}" stroke="${color}" stroke-width="1.8" ${dashed ? 'stroke-dasharray="8 6"' : ""} marker-end="url(#arrow${color === "#b45309" ? "Warn" : color === "#0e7490" ? "Info" : ""})"/>`);
    parts.push(text((a + b) / 2, y - 9, label, { size: 13, fill: color }));
    if (note) parts.push(text((a + b) / 2, y + 18, note, { size: 11, fill: noteColor }));
  };

  const self = (lane, y, label) => {
    const x = lanes[lane].x;
    parts.push(`<path d="M ${x} ${y} h 66 v 34 h -58" fill="none" stroke="#1f2937" stroke-width="1.6" marker-end="url(#arrow)"/>`);
    parts.push(text(x + 78, y + 16, label, { size: 12.5, anchor: "start" }));
  };

  msg(0, 1, 205, "打开审查档案，点击“生成验收标准”");
  msg(1, 2, 250, "POST /api/acceptance/tasks {reviewId, promptVersion, mode}", { color: "#0e7490" });
  msg(2, 5, 300, "读取档案正文与检索片段快照（只读）", { color: "#0e7490" });
  msg(2, 3, 350, "写入任务：QUEUED + 输入快照（≤3000 字）", { color: "#0e7490" });
  msg(2, 1, 400, "202 Accepted {taskId, status}（立即返回，不等待模型）", { color: "#0e7490" });
  msg(1, 2, 455, "GET /tasks/{taskId} 轮询（1.2 s）", { dashed: true, color: "#4b5563" });
  msg(2, 3, 505, "更新 RUNNING + phase “调用模型（第 1 次）”", { color: "#0e7490" });

  parts.push(`<rect x="${lanes[2].x + 18}" y="${540}" width="${lanes[4].x - lanes[2].x - 36}" height="72" fill="#f3f4f6" stroke="#9ca3af" stroke-dasharray="6 4"/>`);
  parts.push(text((lanes[2].x + lanes[4].x) / 2, 566, "等待步骤：模型返回前无法获知真实进度", { size: 12.5, weight: "700", fill: "#374151" }));
  parts.push(text((lanes[2].x + lanes[4].x) / 2, 588, "界面只显示“处理中 + 阶段 + 已用时间”，不显示百分比；可取消", { size: 11.5, fill: "#4b5563" }));
  msg(2, 4, 630, "调用模型（读超时 60 s，最多 3 次尝试）", { color: "#b45309" });
  msg(4, 2, 675, "JSON 文本 + usage（prompt/completion tokens）", { color: "#b45309" });

  self(2, 715, "解析 JSON → 程序检查：结构 / 逐字引用 / GWT / 覆盖");

  msg(2, 3, 790, "写入终态 + 结果 + 检查 + 耗时 + 错误码", { color: "#0e7490" });
  msg(2, 1, 835, "下一次轮询返回 已生成 / 生成失败 / 已拒绝 / 已取消", { color: "#0e7490" });
  msg(1, 0, 880, "展示结果与检查项：AI 生成，需人工核验");

  msg(0, 1, 930, "编辑 / 保存到档案 / 重新生成 / 规则流程 / 转人工 / 放弃");
  msg(1, 2, 975, "PUT /tasks/{id}/result 或 POST /tasks/{id}/apply", { color: "#0e7490" });
  msg(2, 3, 1020, "保存：edited / decision=ACCEPTED / appliedAt", { color: "#0e7490" });
  msg(2, 5, 1065, "写 review.acceptanceJson（仅用户确认后，幂等）", { color: "#0e7490" });

  // 信任边界
  const tb = (laneIndex, y, n, label, align = "start") => {
    const x = lanes[laneIndex].x;
    parts.push(`<circle cx="${x}" cy="${y}" r="14" fill="#fef3c7" stroke="#b45309" stroke-width="1.6"/>`);
    parts.push(text(x, y + 5, n, { size: 13, weight: "700", fill: "#92400e" }));
    parts.push(text(x + (align === "start" ? 22 : -22), y + 5, label, { size: 11.5, anchor: align, fill: "#92400e" }));
  };
  tb(2, 250, "①", "用户输入进入后端：长度/范围/权限由后端检查", "start");
  tb(5, 320, "②", "档案正文进入模型上下文：原文只当数据", "end");
  tb(4, 700, "③", "模型输出进入系统：先解析与检查再展示", "end");
  tb(5, 1095, "④", "写档案：需状态 SUCCEEDED 且用户确认", "end");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#1f2937"/></marker>
    <marker id="arrowWarn" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#b45309"/></marker>
    <marker id="arrowInfo" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#0e7490"/></marker>
  </defs>
  ${parts.join("\n  ")}
</svg>`;
}

function stateSvg() {
  const W = 1500, H = 900;
  const p = [];
  p.push(`<rect x="0" y="0" width="${W}" height="${H}" fill="#ffffff"/>`);
  p.push(text(W / 2, 46, "图3-2 验收标准任务的状态与转换条件", { size: 24, weight: "700" }));
  p.push(text(W / 2, 78, "终态只读；重新生成、规则降级、转人工都会创建新任务并记录 retryOf，原任务保留可追溯", { size: 13.5, fill: "#4b5563" }));

  const box = (x, y, w, h, title, sub, color) => {
    p.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${color.fill}" stroke="${color.stroke}" stroke-width="1.8"/>`);
    p.push(text(x + w / 2, y + 30, title, { size: 17, weight: "700", fill: color.text }));
    p.push(text(x + w / 2, y + 52, sub, { size: 11.5, fill: "#4b5563" }));
  };
  const active = { fill: "#eef2ff", stroke: "#6366f1", text: "#312e81" };
  const ok = { fill: "#dcfce7", stroke: "#16a34a", text: "#14532d" };
  const bad = { fill: "#fee2e2", stroke: "#dc2626", text: "#7f1d1d" };
  const warn = { fill: "#fef3c7", stroke: "#d97706", text: "#78350f" };
  const grey = { fill: "#f3f4f6", stroke: "#6b7280", text: "#1f2937" };

  box(80, 140, 200, 76, "排队中 QUEUED", "已落库，等待线程", active);
  box(400, 140, 200, 76, "处理中 RUNNING", "调用模型 / 程序检查", active);
  box(80, 320, 200, 76, "新任务（重试/规则/人工）", "retryOf 指向原任务", grey);
  box(760, 120, 210, 76, "已生成 SUCCEEDED", "结果可用，可编辑/保存", ok);
  box(760, 250, 210, 76, "校验未通过 CHECK_FAILED", "引用/覆盖不达标", bad);
  box(760, 380, 210, 76, "生成失败 FAILED", "超时/异常/格式错误", bad);
  box(760, 510, 210, 76, "已拒绝 REFUSED", "范围预检，未调模型", warn);
  box(400, 510, 200, 76, "已取消 CANCELLED", "用户取消，结果丢弃", grey);

  const edge = (x1, y1, x2, y2, label, opts = {}) => {
    const { dashed = false, color = "#374151", lx = (x1 + x2) / 2, ly = (y1 + y2) / 2 } = opts;
    p.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="1.7" ${dashed ? 'stroke-dasharray="8 6"' : ""} marker-end="url(#sarrow)"/>`);
    if (label) p.push(text(lx, ly - 8, label, { size: 12, fill: color }));
  };

  edge(280, 178, 400, 178, "线程取到任务");
  edge(500, 216, 500, 510, "排队/处理中取消");
  edge(600, 170, 760, 150, "4 项检查通过");
  edge(600, 190, 760, 275, "3 次尝试仍未通过");
  edge(600, 205, 760, 405, "模型异常/超时/解析失败");
  edge(600, 220, 760, 535, "范围预检命中（不调用模型）");
  edge(400, 548, 280, 548, "取消后重新发起", { dashed: true, color: "#6b7280" });

  p.push(`<rect x="80" y="660" width="1180" height="150" rx="12" fill="#f9fafb" stroke="#d1d5db" stroke-dasharray="6 4"/>`);
  p.push(text(100, 690, "并发与一致性约定", { size: 15, weight: "700", anchor: "start", fill: "#111827" }));
  const notes = [
    "① 同一档案 + 同一 Prompt 版本 + 同一模式存在排队/处理中的任务时，重复提交返回同一任务编号（duplicate=true），不再新建。",
    "② 取消：排队任务立即置为已取消；处理中的任务只置 cancelRequested，线程在当前模型调用返回后丢弃结果并置为已取消。",
    "③ 终态不可覆盖：迟到结果、重复回调、并发保存都不会修改已结束任务的状态；重新生成必然产生新 taskId。",
    "④ 保存到档案幂等：appliedAt 非空时再次 apply 返回同一 savedAt，不重复写入；放弃已保存的结果会被拒绝（ALREADY_SAVED）。",
  ];
  notes.forEach((n, i) => p.push(text(100, 718 + i * 22, n, { size: 12, anchor: "start", fill: "#374151" })));

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs><marker id="sarrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0,0 L12,6 L0,12 z" fill="#374151"/></marker></defs>
  ${p.join("\n  ")}
</svg>`;
}

fs.writeFileSync(path.join(OUT, "集成顺序图.svg"), sequenceSvg());
fs.writeFileSync(path.join(OUT, "任务状态图.svg"), stateSvg());
console.log("written", OUT);