"""dashboard/h2.js never applies a stale answer: newer clicks, run and source switches win.

Runs the real h2.js under Node with a minimal DOM stub and a manual fetch whose
responses arrive in an order the test chooses. The fetch ignores aborts on
purpose (the worst case: the old answer still arrives) and records them.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
const vm = require("node:vm"), fs = require("node:fs"), assert = require("node:assert/strict");
const el = () => ({ innerHTML: "", textContent: "", style: {}, classList: { toggle() {} },
  querySelectorAll: () => [], setAttribute() {}, addEventListener() {}, scrollIntoView() {} });
const els = {};
const document = { documentElement: {}, getElementById: (id) => (els[id] ??= el()),
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {} };
const pending = [];
function fetch(url, { signal }) {
  return new Promise((resolve) => {
    const req = { url, signal, reply: (body) => resolve({ ok: body != null, json: async () => body }) };
    pending.push(req);
  });
}
const take = (part) => {
  const i = pending.findIndex((p) => p.url.includes(part));
  assert.ok(i >= 0, `no pending request for ${part}: ${pending.map((p) => p.url)}`);
  return pending.splice(i, 1)[0];
};
const tick = () => new Promise((r) => setImmediate(r));
const ctx = vm.createContext({ document, fetch, AbortController, setTimeout, clearTimeout, console,
  getComputedStyle: () => ({ getPropertyValue: () => "" }), history: { replaceState() {} }, location: { hash: "" } });
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), ctx);
const run = (code) => vm.runInContext(code, ctx);
const state = run("state");

(async () => {
  take("/api/h2/status").reply(null); take("validation?source=provisional").reply(null); await tick();

  // 1. Newer click wins even when the older answer arrives last.
  run(`loadDecision("L01", "2024-09-18"); loadDecision("L02", "2025-02-13")`);
  const older = take("run=L01&session=2024-09-18"), newer = take("run=L02&session=2025-02-13");
  assert.ok(older.signal.aborted && !newer.signal.aborted);
  newer.reply({ slot: "L02", session: "2025-02-13" }); await tick();
  older.reply({ slot: "L01", session: "2024-09-18" }); await tick();
  assert.equal(state.decision.session, "2025-02-13");

  // 2. A source switch drops pending decisions and analysis of the old source.
  state.analysis = undefined;
  run(`loadDecision("L01", "2024-09-04"); loadAnalysis()`);
  const decision = take("session=2024-09-04"), analysis = take("analysis?source=provisional");
  run(`setSource("demo")`);
  assert.ok(decision.signal.aborted && analysis.signal.aborted);
  assert.equal(state.decision, null);
  decision.reply({ slot: "L01", session: "2024-09-04", source: "provisional" });
  analysis.reply({ source: "provisional" }); await tick();
  assert.equal(state.decision, null);
  assert.notEqual(state.analysis?.source, "provisional");

  // 3. Rapid demo -> official: the synthetic payload never lands under "official".
  run(`setSource("official")`);
  const demoData = take("validation?source=demo");
  take("validation?source=official").reply(null); take("/api/h2/status").reply(null);
  demoData.reply({ synthetic: true, source: "demo" }); await tick();
  while (pending.length) pending.pop().reply(null);
  await tick();
  assert.equal(state.source, "official");
  assert.equal(state.data, null);

  // 4. Audit: a run switch discards the previous run's detail and trace.
  run(`state.auditRun = "L01"; loadDetail()`);
  const d1 = take("run?source=official&run=L01");
  run(`state.auditRun = "L02"; loadDetail()`);
  take("run?source=official&run=L02").reply({ slot: "L02" }); d1.reply({ slot: "L01" }); await tick();
  assert.equal(state.detail.slot, "L02");
  run(`loadTrace("2024-09-18")`);
  const tr = take("trace?source=official&run=L02");
  run(`state.auditRun = "L03"; loadDetail()`);
  assert.ok(tr.signal.aborted);
  tr.reply({ slot: "L02", calls: [] }); take("run=L03").reply({ slot: "L03" }); await tick();
  assert.equal(state.trace, null);
  assert.equal(state.detail.slot, "L03");
  console.log("ASYNC GUARDS OK");
})().catch((e) => { console.error(e); process.exit(1); });
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_stale_responses_are_never_applied(tmp_path):
    harness = tmp_path / "harness.cjs"
    harness.write_text(HARNESS, encoding="utf-8")
    result = subprocess.run(
        ["node", str(harness), str(ROOT / "dashboard" / "h2.js")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ASYNC GUARDS OK" in result.stdout
