// 把实验8 的 SVG 示意图渲染为 PNG（供报告插图）。
import fs from "node:fs";
import path from "node:path";
import { launchChrome, openPage, ROOT, sleep } from "./lib/cdp.mjs";

const FIG = path.join(ROOT, "实验文档", "TEST8", "图");
const SHOTS = path.join(ROOT, "实验文档", "TEST8", "截图");
const chrome = await launchChrome();
try {
  const page = await openPage(SHOTS);
  const items = [
    { file: "集成顺序图.svg", out: "图3-1-集成顺序图.png", w: 1560, h: 1220 },
    { file: "任务状态图.svg", out: "图3-9-任务状态图.png", w: 1500, h: 900 },
  ];
  for (const item of items) {
    await page.send("Emulation.setDeviceMetricsOverride", { width: item.w, height: item.h, deviceScaleFactor: 1, mobile: false });
    await page.navigate("file:///" + path.join(FIG, item.file).replaceAll("\\", "/"));
    await sleep(700);
    const { data } = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    fs.writeFileSync(path.join(SHOTS, item.out), Buffer.from(data, "base64"));
    console.log("saved", item.out);
  }
} finally {
  chrome.kill();
}