// 把截图与示意图统一重命名为报告中的图号，并同步改写脚本里的文件名。
// 目的：报告里图 3-1…图 3-22 与磁盘文件名一致，后续复跑也生成同一套编号。
import fs from "node:fs";
import path from "node:path";

const ROOT = "D:\\deepseek harness workspace\\AI_Request_check";
const SHOTS = path.join(ROOT, "实验文档", "TEST8", "截图");

const MAP = [
  ["图3-1-集成顺序图.png", "图3-1-集成顺序图.png"],
  ["图3-2-任务状态图.png", "图3-9-任务状态图.png"],
  ["图3-1-集成入口.png", "图3-2-集成入口.png"],
  ["图3-2-处理中.png", "图3-3-处理中.png"],
  ["图3-3-生成完成与检查.png", "图3-4-生成完成与检查.png"],
  ["图3-4-保存到档案.png", "图3-5-保存到档案.png"],
  ["图3-5-重新打开档案已保存.png", "图3-6-重新打开档案已保存.png"],
  ["图3-6-重复提交.png", "图3-10-重复提交.png"],
  ["图3-7-取消请求.png", "图3-12-取消请求.png"],
  ["图3-8-已取消.png", "图3-13-已取消.png"],
  ["图3-9-刷新恢复.png", "图3-11-刷新恢复.png"],
  ["图3-10-输入超长.png", "图3-15-输入超长.png"],
  ["图3-11-信息不足.png", "图3-7-信息不足.png"],
  ["图3-12-超出范围.png", "图3-8-超出范围.png"],
  ["图3-13-两任务交错.png", "图3-14-两任务交错.png"],
  ["图3-14-人工修改.png", "图3-19-人工修改.png"],
  ["图3-15-放弃结果.png", "图3-20-放弃结果.png"],
  ["图3-16-转人工保存.png", "图3-21-转人工保存.png"],
  ["图3-17-模型不可用.png", "图3-16-模型不可用.png"],
  ["图3-18-规则降级.png", "图3-17-规则降级.png"],
  ["图3-19-模型超时.png", "图3-18-模型超时.png"],
  ["图3-20-重启后恢复.png", "图3-22-重启后恢复.png"],
];

// 两阶段改名，避免 a→b 与 b→c 相互覆盖
const staged = [];
for (const [from, to] of MAP) {
  const src = path.join(SHOTS, from);
  if (!fs.existsSync(src)) continue;
  const tmp = path.join(SHOTS, "__rename__" + staged.length + ".png");
  fs.renameSync(src, tmp);
  staged.push([tmp, path.join(SHOTS, to)]);
}
for (const [tmp, to] of staged) fs.renameSync(tmp, to);
console.log("renamed", staged.length);

// 同步脚本中的文件名（先长后短，避免前缀误替换）
const scripts = [
  path.join(ROOT, "experiments", "exp8", "e2e-normal.mjs"),
  path.join(ROOT, "experiments", "exp8", "e2e-fault.mjs"),
  path.join(ROOT, "experiments", "exp8", "shoot-figures.mjs"),
];
for (const file of scripts) {
  let content = fs.readFileSync(file, "utf8");
  for (const [from, to] of [...MAP].sort((a, b) => b[0].length - a[0].length)) {
    content = content.split(from).join(to);
  }
  fs.writeFileSync(file, content);
}
console.log("scripts updated");