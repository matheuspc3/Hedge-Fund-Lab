// V7.6.2 minimal DevTools-protocol client for headless Chrome (no dependencies;
// Node >= 22 provides fetch and WebSocket). Library only; see ui_check_v762.mjs.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const CHROME =
  process.env.CHROME ||
  ["C:/Program Files/Google/Chrome/Application/chrome.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"].find((p) => fs.existsSync(p));
const RUN = "radar-2026-10-09-recovery-01";
export const PAGES = [
  ["home", "/"],
  ["radar", `/radar?run=${RUN}`],
  ["portfolio", `/portfolio?run=${RUN}`],
  ["paper", "/paper"],
  ["h2", "/h2"],
  ["logs", "/logs"],
  ["legacy", "/legacy"],
];
export const VIEWPORTS = {
  desktop: { width: 1440, height: 900, mobile: false },
  notebook: { width: 1280, height: 800, mobile: false },
  tablet: { width: 768, height: 1024, mobile: true },
  phone: { width: 390, height: 844, mobile: true },
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function launch() {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "hfl-cdp-"));
  const proc = spawn(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--hide-scrollbars",
    '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    "about:blank",
  ]);
  for (let i = 0; i < 100; i++) {
    try {
      const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return { proc, profile, url: page.webSocketDebuggerUrl };
    } catch {}
    await sleep(100);
  }
  proc.kill();
  throw new Error("chrome_devtools_unavailable");
}

class Page {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.id = 0;
    this.pending = new Map();
    this.listeners = [];
    this.requests = [];
    this.console = [];
    this.ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      } else if (msg.method) {
        if (msg.method === "Network.requestWillBeSent")
          this.requests.push({ method: msg.params.request.method, url: msg.params.request.url });
        if (msg.method === "Runtime.exceptionThrown")
          this.console.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
        if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error")
          this.console.push(msg.params.args.map((a) => a.value ?? a.description).join(" "));
        this.listeners.forEach((l) => l(msg));
      }
    };
  }
  open() {
    return new Promise((r) => (this.ws.onopen = r));
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  once(method) {
    return new Promise((r) => {
      const l = (m) => {
        if (m.method === method) {
          this.listeners = this.listeners.filter((x) => x !== l);
          r(m.params);
        }
      };
      this.listeners.push(l);
    });
  }
  async viewport(v) {
    await this.send("Emulation.setDeviceMetricsOverride", { width: v.width, height: v.height, deviceScaleFactor: 1, mobile: v.mobile });
    await this.send("Emulation.setTouchEmulationEnabled", { enabled: v.mobile });
  }
  async go(url, settle = 1800) {
    const loaded = this.once("Page.loadEventFired");
    const nav = await this.send("Page.navigate", { url });
    // A hash-only change is a same-document navigation: no loaderId, no load event.
    if (nav.loaderId) await Promise.race([loaded, sleep(20000)]);
    await sleep(nav.loaderId ? settle : 400);
  }
  async eval(expression) {
    const r = await this.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || "evaluate_failed");
    return r.result.value;
  }
  async shot(file, full = false) {
    const params = { format: "png" };
    if (full) {
      const m = await this.send("Page.getLayoutMetrics");
      const h = Math.min(Math.ceil(m.cssContentSize.height), 6000);
      params.clip = { x: 0, y: 0, width: m.cssLayoutViewport.clientWidth, height: h, scale: 1 };
      params.captureBeyondViewport = true;
    }
    const { data } = await this.send("Page.captureScreenshot", params);
    fs.writeFileSync(file, Buffer.from(data, "base64"));
  }
  async key(key, code = key, extra = {}) {
    // Enter and Space carry text, so the browser performs the native button activation.
    const text = { Enter: "\r", " ": " " }[key];
    for (const type of ["keyDown", "keyUp"])
      await this.send("Input.dispatchKeyEvent", { type: type === "keyDown" && text ? "keyDown" : type, key, code: { " ": "Space" }[key] || code, text: type === "keyDown" ? text : undefined, windowsVirtualKeyCode: { Tab: 9, Enter: 13, Escape: 27, " ": 32 }[key] || 0, ...extra });
    await sleep(100);
  }
  async tap(selector) {
    const box = await this.eval(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
    await this.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: box.x, y: box.y }] });
    await this.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await sleep(150);
  }
  async click(selector) {
    const box = await this.eval(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
    for (const type of ["mousePressed", "mouseReleased"])
      await this.send("Input.dispatchMouseEvent", { type, x: box.x, y: box.y, button: "left", clickCount: 1 });
    await sleep(150);
  }
}

export async function session(fn) {
  const chrome = await launch();
  const page = new Page(chrome.url);
  await page.open();
  for (const d of ["Page", "Runtime", "Network"]) await page.send(`${d}.enable`);
  try {
    return await fn(page);
  } finally {
    page.ws.close();
    chrome.proc.kill();
    if (chrome.proc.exitCode === null)
      await Promise.race([new Promise(r=>chrome.proc.once('exit',r)), sleep(5000)]);
    // Chrome releases profile handles asynchronously on Windows; retry native cleanup.
    const profile=path.resolve(chrome.profile);
    if (path.dirname(profile)!==path.resolve(os.tmpdir()) || !path.basename(profile).startsWith('hfl-cdp-'))
      throw new Error('unexpected_chrome_profile_path');
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 8, retryDelay: 250 });
  }
}

export function unsafeRequests(page) {
  return page.requests.filter((r) => r.method !== "GET" || /generativelanguage|googleapis|gemini/i.test(r.url));
}

