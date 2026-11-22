// 用 Chrome DevTools Protocol 真实操作页面并截图（无需额外 npm 依赖）。
// 用法：node shoot.mjs ui|figures|github
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve("..", "..");
const SHOTS = path.join(ROOT, "实验文档", "TEST7", "截图");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9223;
const APP = "http://localhost:5173";
const profile = path.join(ROOT, ".chrome-profile");
fs.mkdirSync(SHOTS, { recursive: true });
fs.rmSync(profile, { recursive: true, force: true });

const testset = JSON.parse(fs.readFileSync(path.join(ROOT, "experiments", "exp7", "testset.json"), "utf8"));
const samples = Object.fromEntries(testset.samples.map((s) => [s.id, s]));

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
  "--no-first-run", "--no-default-browser-check", "--disable-extensions",
  "--remote-allow-origins=*", `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`, "--window-size=1500,1100", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForChrome() {
  for (let i = 0; i < 80; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (res.ok) return;
    } catch {}
    await sleep(250);
  }
  throw new Error("Chrome 调试端口未就绪");
}

class Page {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    };
  }
  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`${method} 超时`));
        }
      }, 60000);
    });
  }
  async eval(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression, awaitPromise: true, returnByValue: true,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result?.value;
  }
  async navigate(url) {
    await this.send("Page.navigate", { url });
    for (let i = 0; i < 120; i++) {
      try {
        if (await this.eval("document.readyState === 'complete'")) return;
      } catch {}
      await sleep(200);
    }
  }
  async shot(name) {
    const metrics = await this.send("Page.getLayoutMetrics");
    const content = metrics.cssContentSize || metrics.contentSize;
    const width = 1500;
    const height = Math.min(Math.max(Math.ceil(content.height), 900), 4200);
    await this.send("Emulation.setDeviceMetricsOverride", {
      width, height, deviceScaleFactor: 1, mobile: false,
    });
    await sleep(350);
    const { data } = await this.send("Page.captureScreenshot", {
      format: "png", captureBeyondViewport: false, fromSurface: true,
    });
    fs.writeFileSync(path.join(SHOTS, name), Buffer.from(data, "base64"));
    console.log("saved", name, `${width}x${height}`);
    await this.send("Emulation.setDeviceMetricsOverride", {
      width: 1500, height: 1100, deviceScaleFactor: 1, mobile: false,
    });
  }
}

async function openPage() {
  await waitForChrome();
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const target = list.find((t) => t.type === "page");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });
  const page = new Page(ws);
  await page.send("Page.enable");
  await page.send("Runtime.enable");
  await page.send("Emulation.setDeviceMetricsOverride", {
    width: 1500, height: 1100, deviceScaleFactor: 1, mobile: false,
  });
  return page;
}

async function clickText(page, selector, text) {
  return page.eval(`(() => {
    const el = [...document.querySelectorAll(${JSON.stringify(selector)})]
      .find(e => e.textContent.includes(${JSON.stringify(text)}));
    if (!el) return false;
    el.click();
    return true;
  })()`);
}

async function runAcceptance(page, text, shotName, waitText = "已生成") {
  await page.eval(`(() => {
    const el = document.querySelector('.acceptance-input textarea');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(el, ${JSON.stringify(text)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return el.value.length;
  })()`);
  await sleep(300);
  await page.eval("document.querySelector('.acceptance-run-btn').click()");
  await sleep(600);
  const finals = ["已生成", "生成失败", "校验未通过", "超出范围", "已拒绝"];
  let status = "";
  for (let i = 0; i < 240; i++) {
    const busy = await page.eval(
      "document.querySelector('.acceptance-run-btn')?.textContent?.includes('生成中') || false");
    status = await page.eval(
      "document.querySelector('.acceptance-result .status-chip')?.textContent?.trim() || ''");
    if (!busy && finals.includes(status)) break;
    await sleep(1000);
  }
  if (!finals.includes(status)) throw new Error(`等待结果超时：${shotName}，status=${status}`);
  await sleep(800);
  await page.eval("window.scrollTo(0, 0)");
  await page.shot(shotName);
}

async function ui(page) {
  await page.navigate(APP);
  await sleep(1200);
  await clickText(page, ".side-link", "验收标准");
  await sleep(900);
  await page.shot("图3-1-验收标准页.png");

  await runAcceptance(page, samples["AC-02"].text, "图3-2-正常生成.png");
  await runAcceptance(page, samples["AC-06"].text, "图3-3-信息不足.png");
  await runAcceptance(page, samples["AC-08"].text, "图3-4-超出范围.png");
  await runAcceptance(page, samples["AC-11"].text, "图3-5-提示注入.png");
  await runAcceptance(page, samples["AC-10"].text, "图3-6-长需求冲突.png");
}

async function figures(page) {
  const diagram = path.join(ROOT, "实验文档", "TEST7", "图", "数据流图.html");
  const dashboard = path.join(ROOT, "实验文档", "TEST7", "图", "评测看板.html");
  await page.navigate("file:///" + diagram.replaceAll("\\", "/"));
  await sleep(900);
  await page.shot("图3-7-数据流图.png");
  await page.navigate("file:///" + dashboard.replaceAll("\\", "/"));
  await sleep(900);
  await page.shot("图3-8-评测看板.png");
}

async function github(page) {
  const url = process.argv[3];
  if (!url) throw new Error("缺少 GitHub 地址");
  await page.navigate(url);
  await sleep(3000);
  await page.shot("图3-9-仓库与版本.png");
}

try {
  const mode = process.argv[2] || "ui";
  const page = await openPage();
  if (mode === "ui") await ui(page);
  else if (mode === "figures") await figures(page);
  else if (mode === "github") await github(page);
  else throw new Error("未知模式：" + mode);
} finally {
  chrome.kill();
}