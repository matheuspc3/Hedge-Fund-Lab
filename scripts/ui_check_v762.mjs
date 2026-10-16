// V7.6.2 UI evidence entry point. Only navigates and reads pages; every request is
// recorded and any non-GET or provider request fails the run.
//
//   node scripts/ui_check_v762.mjs shots  http://127.0.0.1:8097 <outDir>
//   node scripts/ui_check_v762.mjs checks http://127.0.0.1:8097 <out.json> [<shotsDir>]
import fs from "node:fs";
import path from "node:path";
import { PAGES, VIEWPORTS, session, unsafeRequests } from "./ui_cdp_v762.mjs";
import { run } from "./ui_checks_v762.mjs";

const [mode, base, out, shotsDir] = process.argv.slice(2);

async function shots() {
  fs.mkdirSync(out, { recursive: true });
  const report = await session(async (page) => {
    for (const [vname, v] of Object.entries({ desktop: VIEWPORTS.desktop, phone: VIEWPORTS.phone })) {
      await page.viewport(v);
      for (const [name, route] of PAGES) {
        await page.go(base + route);
        await page.shot(path.join(out, `${name}-${vname}.png`), true);
      }
    }
    return { requests: page.requests.length, unsafe: unsafeRequests(page), console: page.console };
  });
  fs.writeFileSync(path.join(out, "shots.json"), JSON.stringify(report, null, 1) + "\n");
  if (report.unsafe.length) throw new Error("unsafe_request:" + JSON.stringify(report.unsafe));
  console.log(JSON.stringify(report));
}

// PNG evidence -> JPEG (quality 82) through the same headless Chrome, no image library.
async function convert(dir) {
  await session(async (page) => {
    for (const name of fs.readdirSync(dir).filter((f) => f.endsWith(".png"))) {
      const file = path.join(dir, name), buf = fs.readFileSync(file);
      const width = buf.readUInt32BE(16), height = buf.readUInt32BE(20);
      await page.send("Emulation.setDeviceMetricsOverride", { width, height: Math.min(height, 8000), deviceScaleFactor: 1, mobile: false });
      await page.go("file:///" + path.resolve(file).replaceAll("\\", "/"), 300);
      const { data } = await page.send("Page.captureScreenshot", { format: "jpeg", quality: 82, captureBeyondViewport: true, clip: { x: 0, y: 0, width, height, scale: 1 } });
      fs.writeFileSync(file.replace(/\.png$/, ".jpg"), Buffer.from(data, "base64"));
      fs.rmSync(file);
    }
  });
}

if (mode === "shots") await shots();
else if (mode === "convert") await convert(base);
else if (mode === "checks") await run(base, out, shotsDir);
else throw new Error("usage: shots|checks <base> <out>");
