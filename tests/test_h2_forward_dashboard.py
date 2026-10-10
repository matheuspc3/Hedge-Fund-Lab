"""Forward dashboard checks: real records are read-only; all execution tests fake."""

import http.client
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import forward_api as api  # noqa: E402
import forward_jobs as jobs  # noqa: E402
import run_h2_v6_forward_benchmarks as benchmarks  # noqa: E402
import server  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from test_h2_v6_forward import Bars, clock  # noqa: E402


def test_real_october_decision_and_cash_are_distinct():
    if not (api.OUTPUT / "state.json").exists():
        pytest.skip("local forward records absent")
    d = api.decision("2026-10-09")
    assert d["status"] == "DECIDED" and d["target_session"] == "2026-10-13"
    assert [a["signal"] for a in d["analysts"]] == ["COMPRA"] * 5
    assert sum(e["count"] for e in d["evidence_summary"]) == sum(
        len(a["evidence"]) for a in d["analysts"]
    )
    w = api.portfolios()["wallets"]
    if w[0]["mark"]["session"] == "2026-10-09":
        assert d["pending"]["target_weight"] == 1 and d["execution"] is None
        assert w[0]["equity"] == w[1]["equity"] == 100000
        assert w[0]["composition"][0]["weight"] == 0
        assert w[0]["costs"] == 0 and not w[0]["trades"]
    text = json.dumps(d)
    for forbidden in (
        "system_prompt",
        "user_prompt",
        "raw_response",
        "provider_journal",
        "provider_response",
        "api_key",
    ):
        assert forbidden not in text


@pytest.mark.parametrize(
    "session", ["../state", "2026-99-09", "2026-10-09/..", "2026-10-09%00", ""]
)
def test_session_boundary(session):
    with pytest.raises(ValueError):
        api.session_name(session)


def test_missing_failed_and_executed_records(tmp_path):
    assert api.decision(root=tmp_path) is None
    assert not api.portfolios(tmp_path)["wallets"]
    folder = tmp_path / "sessions/2026-10-09"
    folder.mkdir(parents=True)
    data = {"ticker": "PETR4.SA", "target_session": "2026-10-13", "close_used": 56}
    (folder / "input.json").write_text(json.dumps(data))
    assert api.decision(root=tmp_path)["status"] == "AGUARDANDO"
    (folder / "decision.json").write_text(
        json.dumps(
            {
                "status": "FAILED",
                "failure": "secret raw envelope",
                "system_prompt": "DO NOT SERVE",
            }
        )
    )
    d = api.decision(root=tmp_path)
    assert d["status"] == "FAILED" and d["analysts"] == []
    assert "secret raw envelope" not in json.dumps(
        d
    ) and "DO NOT SERVE" not in json.dumps(d)
    (tmp_path / "state.json").write_text(
        json.dumps(
            {
                "sessions": [
                    {
                        "session": "2026-10-13",
                        "executed_decision": "2026-10-09",
                        "trades": [
                            {
                                "type": "BUY",
                                "price": 55,
                                "quantity": 10,
                                "cost": 1,
                                "raw": "DO NOT SERVE",
                            }
                        ],
                    }
                ]
            }
        )
    )
    d = api.decision(root=tmp_path)
    d = api.decision("2026-10-09", tmp_path)
    assert d["execution"]["session"] == "2026-10-13"
    assert "raw" not in d["execution"]["trades"][0]


def test_missed_session_is_in_history(tmp_path):
    (tmp_path / "state.json").write_text(
        json.dumps({"sessions": [{"session": "2026-10-13", "decision": "MISSED"}]})
    )
    assert api.history(tmp_path)[0]["session"] == "2026-10-13"
    assert api.decision("2026-10-13", tmp_path)["status"] == "MISSED"


def wait_job(controller, job):
    end = time.monotonic() + 8
    while time.monotonic() < end:
        result = controller.status(job["id"])["job"]
        if result["state"] != "RUNNING" and not controller.status()["busy"]:
            return result
        time.sleep(0.01)
    raise AssertionError("job did not finish")


@pytest.fixture
def controller(tmp_path, monkeypatch):
    monkeypatch.setattr(api.fwd, "now", clock("2026-10-10 16:00"))
    root = tmp_path / "forward"
    folder = root / "sessions/2026-10-09"
    folder.mkdir(parents=True)
    (folder / "input.json").write_text('{"causal":"fixture"}')
    (root / "state.json").write_text("{}")
    c = jobs.Jobs(tmp_path / "operations", root)
    raw = {
        "ready": True,
        "checks": {"input_frozen": True, "before_target_open": True},
        "calendar": {
            "decision_session": "2026-10-09",
            "target_session": "2026-10-13",
            "target_open_deadline": "2026-10-13T10:00:00-03:00",
        },
        "input": {"sha256": api.fwd.sha_file(folder / "input.json")},
        "identity": {"params": {"model": "FAKE-OFFLINE", "api_key": "NEVER_HTTP"}},
        "estimate_per_session": {"usd_expected": 0.01},
        "secret": "NEVER_HTTP",
    }
    calls = []

    def invoke(command, confirm=None):
        calls.append((command, confirm))
        return subprocess.CompletedProcess(
            [], 0, json.dumps(raw) if command == "preflight" else "{}", ""
        )

    monkeypatch.setattr(c, "_invoke", invoke)
    return c, raw, calls


def test_ready_bound_confirmation_and_duplicate_after_restart(controller):
    c, raw, calls = controller
    job = wait_job(c, c.start("preflight"))
    report = job["report"]
    assert report["ready"] and "NEVER_HTTP" not in json.dumps(report)
    wait_job(c, c.start("run", report["confirmation_token"]))
    assert [x for x in calls if x[0] == "run"] == [("run", raw["input"]["sha256"][:12])]
    with pytest.raises(jobs.Conflict, match="claimed"):
        c.start("run", report["confirmation_token"])
    restarted = jobs.Jobs(c.root, c.forward_root)
    # A second server can mint its own valid token, but cannot bypass the claim.
    with pytest.raises(jobs.Conflict, match="claimed"):
        restarted.start("run", restarted._token(report))
    assert not c.status()["busy"]
    assert c._preflight()["state"] == "RECOVERY_REQUIRED"


@pytest.mark.parametrize("mutation", ["input", "ledger", "deadline", "token", "expired"])
def test_confirmation_invalidated_before_provider(controller, monkeypatch, mutation):
    c, raw, calls = controller
    report = c._preflight()
    token = c._token(report)
    if mutation == "input":
        (c.forward_root / "sessions/2026-10-09/input.json").write_text("changed")
    elif mutation == "ledger":
        (c.forward_root / "state.json").write_text("changed")
    elif mutation == "deadline":
        monkeypatch.setattr(api.fwd, "now", clock("2026-10-13 10:00"))
    elif mutation == "expired":
        monkeypatch.setattr(jobs.time, "time", lambda: 99999999999)
    else:
        token += "bad"
    with pytest.raises(jobs.Conflict):
        c.start("run", token)
    assert not any(x[0] == "run" for x in calls)


def test_existing_decision_and_failed_gate_are_read_only(controller):
    c, raw, calls = controller
    token = c._token(c._preflight())
    decision = c.forward_root / "sessions/2026-10-09/decision.json"
    decision.write_text('{"status":"DECIDED"}')
    assert c._preflight()["state"] == "DECISION_EXISTS"
    with pytest.raises(jobs.Conflict, match="decision_exists"):
        c.start("run", token)
    decision.unlink()
    raw["ready"] = False
    raw["checks"]["before_target_open"] = False
    job = wait_job(c, c.start("preflight"))
    assert (
        job["report"]["state"] == "NOT_READY"
        and "confirmation_token" not in job["report"]
    )
    assert not any(x[0] == "run" for x in calls)


def test_double_click_and_two_servers_while_job_is_long(controller, monkeypatch):
    c, raw, calls = controller
    entered, release = threading.Event(), threading.Event()
    original = c._invoke

    def slow(command, confirm=None):
        if command == "run":
            entered.set()
            assert release.wait(5)
        return original(command, confirm)

    monkeypatch.setattr(c, "_invoke", slow)
    report = c._preflight()
    token = c._token(report)
    job = c.start("run", token)
    assert entered.wait(5)
    try:
        with pytest.raises(jobs.Conflict):
            c.start("run", token)
        other = jobs.Jobs(c.root, c.forward_root)
        with pytest.raises(jobs.Conflict):
            other.start("prepare")
        assert other.status()["job"]["state"] == "RUNNING"
        assert c.status(job["id"])["job"]["progress"]["reserved"] == 0
    finally:
        release.set()
    assert wait_job(c, job)["state"] == "COMPLETE"
    assert len([x for x in calls if x[0] == "run"]) == 1


def test_worker_failure_preserves_claim(controller, monkeypatch):
    c, raw, calls = controller
    report = c._preflight()
    original = c._invoke

    def failing(command, confirm=None):
        return (
            subprocess.CompletedProcess([], 1, "provider secret envelope", "secret")
            if command == "run"
            else original(command, confirm)
        )

    monkeypatch.setattr(c, "_invoke", failing)
    job = wait_job(c, c.start("run", c._token(report)))
    assert job["state"] == "FAILED" and "secret" not in json.dumps(job)
    assert (c.root / "run-2026-10-09.json").exists()
    assert not c.status()["busy"]


@pytest.fixture
def http_server(controller, monkeypatch):
    c, _, _ = controller
    monkeypatch.setattr(jobs, "JOBS", c)
    instance = server.ReusableTCPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield instance, c
    instance.shutdown()
    instance.server_close()
    thread.join()


def request(instance, path, method="GET", body=None, headers=None):
    port = instance.server_address[1]
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    client.request(method, path, body=body, headers=headers or {})
    response = client.getresponse()
    code, data = response.status, response.read()
    client.close()
    return code, data


def test_http_origin_csrf_payload_and_static_isolation(http_server):
    instance, c = http_server
    origin = f"http://127.0.0.1:{instance.server_address[1]}"
    valid = {"Origin": origin, "X-CSRF-Token": c.csrf, "Content-Type": "application/json"}
    assert request(instance, "/api/forward/status")[0] == 200
    for path in (
        "/server.py",
        "/forward_jobs.py",
        "/../.env",
        "/vendor/",
        "/api/forward/decision?session=../../.env",
        "/api/forward/status?job=../../.env",
        "/api/forward/decision?session=2026-10-09&session=2026-10-13",
        "/api/forward/portfolios?source=demo",
    ):
        assert request(instance, path)[0] in (400, 404)
    assert request(instance, "/paper")[0] == 200
    navigation = {
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }
    assert request(instance, "/paper", headers=navigation)[0] == 200
    assert request(instance, "/api/forward/status", headers=navigation)[0] == 403
    assert (
        request(instance, "/api/forward/status", headers={"Host": "evil.example"})[0]
        == 403
    )
    assert (
        request(
            instance, "/api/forward/status", headers={"Origin": "https://evil.example"}
        )[0]
        == 403
    )
    for bad in (
        {},
        {**valid, "Origin": "null"},
        {**valid, "Origin": "http://localhost:1"},
        {**valid, "X-CSRF-Token": "bad"},
        {**valid, "Sec-Fetch-Site": "cross-site"},
    ):
        assert request(instance, "/api/forward/preflight", "POST", "{}", bad)[0] == 403
    for body in (
        "[]",
        '{"extra":1}',
        '{"confirm":true,"confirm":true}',
        '{"x":NaN}',
        "x" * 4097,
    ):
        assert request(instance, "/api/forward/preflight", "POST", body, valid)[0] == 400
    assert (
        request(
            instance,
            "/api/forward/run",
            "POST",
            '{"confirm":false,"confirmation_token":"bad"}',
            valid,
        )[0]
        == 400
    )
    assert (
        request(
            instance,
            "/api/forward/run",
            "POST",
            '{"confirm":true,"confirmation_token":"bad"}',
            valid,
        )[0]
        == 409
    )
    code, data = request(instance, "/api/forward/preflight", "POST", "{}", valid)
    assert code == 202
    job = wait_job(c, json.loads(data))
    assert job["report"]["ready"]


def test_benchmarks_causal_common_inception_settlement_and_no_backfill(
    tmp_path, monkeypatch
):
    f = api.fwd
    identity = f.identity
    monkeypatch.setattr(f, "identity", lambda: identity(clean=False))
    saturday, tuesday = clock("2026-10-10 16:00"), clock("2026-10-13 19:00")
    forward_root, book_root = tmp_path / "ai", tmp_path / "benchmarks"
    bars = Bars()
    with f.no_network():
        f.prepare(forward_root, saturday, bars)
        sha, _ = f.identity()
        state = f.new_state(sha)
        f.reconcile(
            state,
            f.load_bars(forward_root / "sessions/2026-10-09"),
            f._timestamp("2026-10-09"),
        )
        f.save_state(forward_root, state)
        for strategy in benchmarks.STRATEGIES:
            first = benchmarks.sync(strategy, book_root, forward_root, saturday)
            assert (
                first["inception"] == "2026-10-09"
                and first["portfolio"]["cash"] == 100000
            )
            assert first["decisions"][0]["generated_at"].startswith("2026-10-10")
            if first["pending"]:
                assert first["pending"]["target_session"] == "2026-10-13"
            path = book_root / strategy / "state.json"
            before = path.read_bytes()
            benchmarks.sync(strategy, book_root, forward_root, saturday)
            assert path.read_bytes() == before
        assert all(
            w.get("comparable", True)
            for w in api.portfolios(forward_root, book_root)["wallets"]
        )
        path = book_root / benchmarks.STRATEGIES[0] / "state.json"
        original = path.read_bytes()
        altered = json.loads(original)
        altered["sessions"][0]["close"] += 1
        path.write_text(json.dumps(altered))
        assert (
            api.portfolios(forward_root, book_root)["wallets"][2]["comparable"] is False
        )
        path.write_bytes(original)
        f.prepare(forward_root, tuesday, bars)
        f.reconcile(
            state,
            f.load_bars(forward_root / "sessions/2026-10-13"),
            f._timestamp("2026-10-13"),
        )
        f.save_state(forward_root, state)
        for strategy in benchmarks.STRATEGIES:
            updated = benchmarks.sync(strategy, book_root, forward_root, tuesday)
            for row in updated["sessions"]:
                for trade in row["trades"]:
                    assert row["session"] >= "2026-10-13"
                    assert trade["cost"] == pytest.approx(
                        trade["price"] * trade["quantity"] * 0.00082
                    )
            assert len(updated["decisions"]) == 2
        assert all(
            w.get("comparable", True)
            for w in api.portfolios(forward_root, book_root)["wallets"]
        )
        with pytest.raises(ValueError, match="NOT_COMPARABLE"):
            benchmarks.sync(
                benchmarks.STRATEGIES[0], tmp_path / "late", forward_root, tuesday
            )
        with pytest.raises(ValueError, match="deadline"):
            benchmarks.sync(
                benchmarks.STRATEGIES[0],
                tmp_path / "deadline",
                forward_root,
                clock("2026-10-14 10:00"),
            )


def test_projection_never_opens_journal_or_reserved_data(monkeypatch):
    opened = []
    original = Path.open

    def spy(path, *args, **kwargs):
        opened.append(path.resolve())
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy)
    api.history()
    api.decision("2026-10-09")
    api.portfolios()
    assert all("FINAL_TEST" not in str(p) and "snapshots" not in p.parts for p in opened)
    assert all(
        p.name not in ("provider.sqlite", "provider_journal.jsonl", ".env")
        for p in opened
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_browser_never_posts_on_load_and_requires_explicit_checked_confirmation(tmp_path):
    harness = tmp_path / "paper.cjs"
    harness.write_text(
        r"""
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const elements={};
const element=()=>({innerHTML:'',textContent:'',value:'',hidden:false,disabled:false,checked:false,open:false,
  listeners:{},addEventListener(k,f){this.listeners[k]=f},dispatch(k){return this.listeners[k]?.()},
  showModal(){this.open=true},close(){this.open=false},classList:{toggle(){}}});
const document={getElementById:id=>(elements[id]??=element()),querySelectorAll:()=>[]};
document.getElementById('confirm-dialog');
let current={csrf_token:'OFFLINE_CSRF',busy:false,job:null}; const requests=[];
async function fetch(url,options={}) {
  requests.push({url,...options}); let value;
  if(options.method==='POST') { current={...current,busy:true,job:{id:'run1',command:'run',session:'2026-10-09',state:'RUNNING'}}; value=current.job; }
  else if(url.includes('/status')) value=current;
  else if(url.includes('/history')) value=[];
  else if(url.includes('/portfolios')) value={wallets:[]};
  else value=null;
  return {ok:true,json:async()=>value};
}
const ctx=vm.createContext({document,fetch,console,setTimeout(){},Chart:class {destroy(){}},encodeURIComponent});
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
const tick=()=>new Promise(r=>setImmediate(r));
const posts=()=>requests.filter(r=>r.method==='POST');
(async()=>{
  await tick(); await tick();
  assert.equal(posts().length,0); assert.equal(elements.execute.disabled,true);
  elements.execute.dispatch('click'); assert.equal(elements['confirm-dialog'].open,false);
  current.job={id:'pre1',command:'preflight',state:'COMPLETE',report:{ready:true,state:'READY',confirmation_token:'SIGNED_OFFLINE_TOKEN',calendar:{target_session:'2026-10-13'},input:{sha256:'a'.repeat(64)},model:{model:'FAKE'},estimate:{usd_expected:.01,usd_prudent_budget:.02}}};
  await vm.runInContext('pollStatus(false)',ctx);
  assert.equal(elements.execute.disabled,false);
  elements.execute.dispatch('click'); assert.equal(elements['confirm-dialog'].open,true);
  assert.equal(elements['submit-confirm'].disabled,true); assert.equal(posts().length,0);
  elements['submit-confirm'].dispatch('click'); assert.equal(posts().length,0);
  elements['accept-charges'].checked=true; elements['accept-charges'].dispatch('change');
  assert.equal(elements['submit-confirm'].disabled,false);
  elements['submit-confirm'].dispatch('click'); elements['submit-confirm'].dispatch('click');
  await tick(); await tick();
  assert.equal(posts().length,1);
  assert.deepEqual(JSON.parse(posts()[0].body),{confirm:true,confirmation_token:'SIGNED_OFFLINE_TOKEN'});
  assert.equal(posts()[0].headers['X-CSRF-Token'],'OFFLINE_CSRF');
  assert.equal(elements.execute.disabled,true);
  console.log('OFFLINE HUMAN CONFIRMATION OK');
})().catch(e=>{console.error(e);process.exit(1)});
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(harness), str(ROOT / "dashboard/paper.js")],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
