// 通过 Chrome DevTools Protocol 驱动真实页面（无需额外依赖），供实验8 端到端脚本复用。
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

export const ROOT = path.resolve("D:\\deepseek harness workspace\\AI_Request_check");
export const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
export const PORT = 9223;
export const APP = "http://127.0.0.1:5173";
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function launchChrome() {
  const profile = path.join(ROOT, ".chrome-profile");
  fs.rmSync(profile, { recursive: true, force: true });
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
    "--no-first-run", "--no-default-browser-check", "--disable-extensions",
    "--remote-allow-origins=*", `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`, "--window-size=1500,1100", "about:blank",
  ], { stdio: "ignore" });
  for (let i = 0; i < 80; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (res.ok) return chrome;
    } catch { }
    await sleep(250);
  }
  throw new Error("Chrome 调试端口未就绪");
}

class Page {
  constructor(ws, shots) {
    this.ws = ws;
    this.shots = shots;
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
      }, 90000);
    });
  }
  async eval(expression) {
    const result = await this.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "页面脚本异常");
    return result.result?.value;
  }
  async navigate(url) {
    await this.send("Page.navigate", { url });
    for (let i = 0; i < 150; i++) {
      try {
        if (await this.eval("document.readyState === 'complete'")) return;
      } catch { }
      await sleep(200);
    }
  }
  async reload() {
    await this.send("Page.reload");
    await sleep(1200);
    for (let i = 0; i < 100; i++) {
      try {
        if (await this.eval("document.readyState === 'complete'")) return;
      } catch { }
      await sleep(200);
    }
  }
  async clickText(selector, text) {
    return this.eval(`(() => {
      const el = [...document.querySelectorAll(${JSON.stringify(selector)})]
        .find(e => (e.textContent || '').includes(${JSON.stringify(text)}));
      if (!el) return false;
      el.click();
      return true;
    })()`);
  }
  async text(selector) {
    return this.eval(`document.querySelector(${JSON.stringify(selector)})?.textContent?.trim() || ''`);
  }
  async shot(name, opts = {}) {
    const metrics = await this.send("Page.getLayoutMetrics");
    const content = metrics.cssContentSize || metrics.contentSize;
    const width = 1500;
    const maxHeight = opts.maxHeight || 4200;
    const height = Math.min(Math.max(Math.ceil(content.height), 900), maxHeight);
    await this.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
    await sleep(400);
    const { data } = await this.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false, fromSurface: true });
    fs.writeFileSync(path.join(this.shots, name), Buffer.from(data, "base64"));
    console.log("  截图", name, `${width}x${height}`);
    await this.send("Emulation.setDeviceMetricsOverride", { width: 1500, height: 1100, deviceScaleFactor: 1, mobile: false });
  }

  /** 只截某个元素：先滚动到可见区域，再按页面坐标裁剪，适合报告里的局部界面图。 */
  async shotElement(selector, name, maxHeight = 1600) {
    const rect = await this.eval(`(() => {
      const el = document.querySelector(${JSON.stringify(selector)});
      if (!el) return null;
      el.scrollIntoView({ block: 'start' });
      const r = el.getBoundingClientRect();
      return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height };
    })()`);
    if (!rect) throw new Error("元素不存在：" + selector);
    await sleep(450);
    const h = Math.min(Math.max(rect.h, 120), maxHeight);
    const { data } = await this.send("Page.captureScreenshot", {
      format: "png", fromSurface: true, captureBeyondViewport: false,
      clip: { x: rect.x, y: rect.y, width: rect.w, height: h, scale: 1 },
    });
    fs.writeFileSync(path.join(this.shots, name), Buffer.from(data, "base64"));
    console.log("  截图", name, `${Math.round(rect.w)}x${Math.round(h)}`);
  }
}

export async function openPage(shotsDir) {
  fs.mkdirSync(shotsDir, { recursive: true });
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const target = list.find((t) => t.type === "page");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });
  const page = new Page(ws, shotsDir);
  await page.send("Page.enable");
  await page.send("Runtime.enable");
  await page.send("Emulation.setDeviceMetricsOverride", { width: 1500, height: 1100, deviceScaleFactor: 1, mobile: false });
  return page;
}

export async function api(path, options = {}) {
  const res = await fetch("http://localhost:8080/api" + path, options);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  return { ok: res.ok, status: res.status, data };
}

export const jsonPost = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export async function waitFor(fn, timeoutMs, intervalMs = 500) {
  const deadline = Date.now() + timeoutMs;
  let last;
  while (Date.now() < deadline) {
    last = await fn();
    if (last) return last;
    await sleep(intervalMs);
  }
  throw new Error("等待条件超时");
}