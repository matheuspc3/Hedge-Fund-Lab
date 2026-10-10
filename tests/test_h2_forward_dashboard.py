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
    assert d["session"] == "2026-10-09"  # latest decision, even after a MISSED session
    assert d["execution"]["session"] == "2026-10-13"
    assert "raw" not in d["execution"]["trades"][0]


@pytest.mark.parametrize(
    "weight,effect", [(0, "EFETIVO"), (1, "SEM EFEITO"), (None, None)]
)
def test_veto_effect_requires_recorded_position(tmp_path, weight, effect):
    folder = tmp_path / "sessions/2026-10-09"
    folder.mkdir(parents=True)
    (folder / "input.json").write_text(
        json.dumps({"ticker": "PETR4.SA", "target_session": "2026-10-13"})
    )
    (folder / "decision.json").write_text(
        json.dumps(
            {
                "status": "DECIDED",
                "risk_verdict": {"verdict": "VETADO"},
                "record": {"technical_outcome": "COMPRA", "observed_weight": weight},
            }
        )
    )
    assert api.decision(root=tmp_path)["risk"]["veto_effect"] == effect


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


def test_atomic_job_writes_are_not_blocked_by_readers(controller):
    c, _, _ = controller
    c.root.mkdir(parents=True)
    job = {"id": "a" * 32, "state": "RUNNING", "sequence": 0}
    c._save(job)
    errors = []

    def write():
        try:
            for i in range(100):
                c._save({**job, "sequence": i})
        except OSError:
            import traceback
            errors.append(traceback.format_exc())

    thread = threading.Thread(target=write)
    thread.start()
    for _ in range(500):
        assert api.read(c.root / f"job-{job['id']}.json")["state"] == "RUNNING"
    thread.join(10)
    assert not thread.is_alive() and not errors, "\n".join(errors)


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
        {**valid, "X-CSRF-Token": "é"},
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
    original = api.read

    def spy(path, *args, **kwargs):
        opened.append(path.resolve())
        return original(path, *args, **kwargs)

    monkeypatch.setattr(api, "read", spy)
    api.history()
    api.decision("2026-10-09")
    api.portfolios()
    api.agents()
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
  // Local quorum simulator mirrors src/agents/technical_analyst.py and never fetches.
  const before=requests.length, q=(...a)=>vm.runInContext(`quorum(${a.map(v=>JSON.stringify(v)).join(',')})`,ctx);
  assert.equal(q(5,.6,{COMPRA:3,VENDA:2,MANTER:0},true).winner,'COMPRA');
  assert.equal(q(5,.6,{COMPRA:2,VENDA:2,MANTER:1},true).reached,false);
  assert.equal(q(5,.6,{COMPRA:4,VENDA:0,MANTER:0},true).reached,false);
  assert.equal(q(5,.6,{COMPRA:3,VENDA:0,MANTER:0},false).winner,'COMPRA');
  assert.equal(q(10,.6,{COMPRA:3,VENDA:3,MANTER:3},false).share,1/3);
  assert.equal(q(4,.5,{COMPRA:2,VENDA:0,MANTER:2},false).winner,'MANTER');
  assert.ok(q(5,.6,{COMPRA:6,VENDA:0,MANTER:0},true).error);
  assert.equal(requests.length,before);
  console.log('OFFLINE HUMAN CONFIRMATION OK');
})().catch(e=>{console.error(e);process.exit(1)});
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(harness), str(ROOT / "dashboard/paper.js")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ── Premium UI v1: presentation projections over synthetic ledgers ──────────


def write_session(root, session, decision=None, trace=(), target="2026-10-13"):
    folder = root / "sessions" / session
    folder.mkdir(parents=True)
    (folder / "input.json").write_text(
        json.dumps({"ticker": "PETR4.SA", "target_session": target, "close_used": 56})
    )
    if decision is not None:
        (folder / "decision.json").write_text(json.dumps(decision))
    (folder / "llm_trace.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in trace), encoding="utf-8"
    )


def analyst(i, signal="COMPRA", status="ok", evidence=None, **extra):
    evidence = evidence or [
        {"code": "CLOSE_ABOVE_SMA50", "role": "SUPPORTS_COMPRA"},
        {"code": "RSI_CURRENT", "role": "CAUTION"},
    ]
    return {
        "stage": "technical_analyst",
        "analyst_id": i,
        "sequence": i - 1,
        "status": status,
        "retry_count": 0,
        "attempt_count": 1,
        "token_usage": {"prompt_tokens": 1000, "completion_tokens": 100, "total_tokens": 1100},
        "system_prompt": "DO NOT SERVE",
        "raw_response": "DO NOT SERVE",
        "validated_response": {"signal": signal, "confidence": 0.75, "evidence": evidence}
        if status == "ok"
        else None,
        "technical_evidence": {
            "rendered_explanation": "fechamento acima da SMA50 — classificado pelo analista como suporte à COMPRA; "
            "RSI atual = 74.9 — classificado pelo analista como cautela"
        },
        **extra,
    }


def decided(outcome="COMPRA", reached=True, votes=None, verdict="APROVADO", final=None, status="DECIDED"):
    votes = votes or {"COMPRA": 5, "MANTER": 0, "VENDA": 0}
    return {
        "status": status,
        "record": {
            "vote_counts": votes,
            "valid_votes": sum(votes.values()),
            "consensus_threshold": 0.6,
            "consensus_reached": reached,
            "technical_outcome": outcome,
            "observed_weight": 0.0,
            "target_weight": 1.0 if (final or outcome) == "COMPRA" else 0.0,
            "risk_source": "LLM",
            "final_cause": "ACTION_BUY",
        },
        "risk_verdict": {"verdict": verdict},
        "portfolio_action": {"decision": final or outcome},
        "technical_signal": {"signal": outcome, "confidence": 0.75},
        "intents": [{"ticker": "PETR4.SA", "target_weight": 1.0}],
    }


def test_consensus_flow_evidence_synthesis_and_order_states(tmp_path):
    write_session(tmp_path, "2026-10-09", decided(), [analyst(i) for i in range(1, 6)])
    pending = {"decision_session": "2026-10-09", "target_session": "2026-10-13", "target_weight": 1.0}
    (tmp_path / "state.json").write_text(
        json.dumps({"sessions": [{"session": "2026-10-09", "decision": "DECIDED"}], "pending": pending})
    )
    d = api.decision("2026-10-09", tmp_path)
    assert [s["changed"] for s in d["flow"]][2:4] == [False, False]  # Risk/Portfolio kept the signal
    assert d["order"]["state"] == "PENDENTE" and "13/10/2026" in d["order"]["detail"]
    assert d["committee"] == {
        "analyst_count": 5, "consensus_threshold": 0.6, "require_all_votes": True, "responded": 5
    }
    by_code = {e["code"]: e for e in d["evidence_summary"]}
    assert by_code["CLOSE_ABOVE_SMA50"]["stance"] == "favorable"
    rsi = by_code["RSI_CURRENT"]
    assert (rsi["stance"], rsi["count"], rsi["label"]) == ("caution", 5, "RSI atual = 74.9")
    assert rsi["analysts"] == [1, 2, 3, 4, 5] and d["divergences"] == []
    assert "DO NOT SERVE" not in json.dumps(d)
    assert api.history(tmp_path)[0]["vote_counts"] == {"COMPRA": 5, "MANTER": 0, "VENDA": 0}

    # Executed, late and failed sessions never look like a pending order.
    trade = {"type": "BUY", "price": 55, "quantity": 10, "cost": 1}
    (tmp_path / "state.json").write_text(
        json.dumps({"sessions": [{"session": "2026-10-13", "executed_decision": "2026-10-09", "trades": [trade]}]})
    )
    assert api.decision("2026-10-09", tmp_path)["order"]["state"] == "EXECUTADA"
    write_session(tmp_path, "2026-10-14", decided(status="FAILED"))
    write_session(tmp_path, "2026-10-15", decided(status="LATE_NOT_EXECUTABLE"))
    assert api.decision("2026-10-14", tmp_path)["order"]["state"] == "SEM_ORDEM"
    assert api.decision("2026-10-15", tmp_path)["order"]["state"] == "NAO_EXECUTAVEL"


def test_no_consensus_missing_and_invalid_analysts_are_not_votes(tmp_path):
    trace = [
        analyst(1),
        analyst(2, "VENDA", evidence=[{"code": "CLOSE_ABOVE_SMA50", "role": "SUPPORTS_VENDA"}]),
        analyst(3, "MANTER"),
        analyst(4, status="error", error_type="INVALID_RESPONSE"),
    ]  # analyst 5 never answered
    votes = {"COMPRA": 1, "VENDA": 1, "MANTER": 1}
    write_session(tmp_path, "2026-10-09", decided("MANTER", False, votes, verdict=None), trace)
    d = api.decision("2026-10-09", tmp_path)
    assert d["committee"]["responded"] == 3 and len(d["analysts"]) == 4
    assert d["analysts"][3]["signal"] is None
    assert d["analysts"][3]["error_type"] == "INVALID_RESPONSE"
    assert d["flow"][1]["result"] == "SEM CONSENSO" and d["flow"][2]["changed"] is None
    stances = {(e["code"], e["role"]): e["stance"] for e in d["evidence_summary"]}
    # No directional outcome: evidences keep their literal role instead of "favorable".
    assert stances["CLOSE_ABOVE_SMA50", "SUPPORTS_COMPRA"] == "supports_compra"
    assert any("Votos divididos" in t for t in d["divergences"])
    assert any("classificada de formas diferentes" in t for t in d["divergences"])


def ledger_row(session, equity, trades=(), executed=None):
    return {
        "session": session, "open": 55, "close": 56, "executed_decision": executed,
        "trades": list(trades), "benchmark_trades": [], "equity": equity, "benchmark_equity": 100000.0,
    }


def test_wallet_metrics_pending_composition_and_short_history(tmp_path):
    state = {
        "initial_capital": 100000.0, "costs": {}, "execution": {}, "manifest_sha256": "x",
        "portfolio": {"cash": 100000.0, "units": 0.0},
        "benchmark": {"cash": 100000.0, "units": 0.0, "invested": False},
        "mark": {"session": "2026-10-09", "close": 56.0},
        "pending": {"decision_session": "2026-10-09", "target_session": "2026-10-13", "target_weight": 1.0},
        "sessions": [ledger_row("2026-10-09", 100000.0)],
        "decisions": [],
    }
    (tmp_path / "state.json").write_text(json.dumps(state))
    ai = api.portfolios(tmp_path, tmp_path / "none")["wallets"][0]
    # A 100% buy intention is not a 100% stock position.
    assert ai["pending"]["target_weight"] == 1 and ai["exposure"] == 0
    assert [c["weight"] for c in ai["composition"]] == [0, 1]
    assert ai["observations"] == 1 and ai["max_drawdown"] is None and ai["dividends"] is None

    trade = {"type": "BUY", "price": 55.0, "quantity": 1800.0, "cost": 50.0}
    state.update(
        portfolio={"cash": 950.0, "units": 1800.0},
        pending=None,
        mark={"session": "2026-10-14", "close": 54.0},
        sessions=[
            ledger_row("2026-10-09", 100000.0),
            ledger_row("2026-10-13", 101750.0, [trade], "2026-10-09"),
            ledger_row("2026-10-14", 98150.0),
        ],
    )
    (tmp_path / "state.json").write_text(json.dumps(state))
    ai = api.portfolios(tmp_path, tmp_path / "none")["wallets"][0]
    assert ai["equity"] == 950 + 1800 * 54 and ai["pnl"] == ai["equity"] - 100000
    assert ai["max_drawdown"] == pytest.approx((101750 - 98150) / 101750)
    assert ai["trades"] == [
        {"session": "2026-10-13", "decision_session": "2026-10-09", "asset": "PETR4", **trade, "equity_after": 101750.0}
    ]
    assert sum(c["weight"] for c in ai["composition"]) == pytest.approx(1)
    assert ai["costs"] == 50 and ai["cash"] == 950


def test_agent_catalog_separates_active_slots_from_future_ones(tmp_path):
    rm = {
        "stage": "risk_manager", "status": "ok", "retry_count": 1,
        "validated_response": {"verdict": "APROVADO"}, "token_usage": None,
    }
    write_session(tmp_path, "2026-10-09", decided(), [analyst(i) for i in range(1, 6)] + [rm])
    a = api.agents(tmp_path)
    assert a["configuration"]["frozen"] and a["configuration"]["analyst_count"] == 5
    slots = a["agents"]
    assert len(slots) == 32 and [s["id"] for s in slots[-2:]] == ["RM", "PM"]
    assert sum(s["active"] for s in slots if s["role"] == "Technical Analyst") == 5
    assert all(s["observations"] is None and s["params"] is None for s in slots[5:30])
    ta = slots[0]["observations"]
    assert ta["outputs"] == {"COMPRA": 1} and ta["agreement"] == 1 and ta["tokens"] == 1100
    assert ta["cost_usd"] == pytest.approx((1000 * 0.75 + 100 * 3.75) / 1e6)
    risk = slots[30]["observations"]
    assert risk["agreement"] is None and risk["tokens"] is None and risk["retry_rate"] == 1
    assert slots[31]["observations"] is None and slots[31]["prompt_version"] is None
    assert "DO NOT SERVE" not in json.dumps(a)


def test_read_projections_make_no_network_calls(monkeypatch):
    if not (api.OUTPUT / "state.json").exists():
        pytest.skip("local forward records absent")
    import socket

    def refuse(*_args, **_kwargs):
        raise AssertionError("dashboard read attempted a network call")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    api.history(), api.decision(), api.portfolios()
    text = json.dumps(api.agents())
    for forbidden in ("system_prompt", "user_prompt", "raw_response", "api_key", "provider_journal"):
        assert forbidden not in text


def test_agents_endpoint_is_read_only(http_server):
    instance, c = http_server
    origin = f"http://127.0.0.1:{instance.server_address[1]}"
    assert request(instance, "/api/forward/agents")[0] == 200
    assert request(instance, "/api/forward/agents?session=2026-10-09")[0] == 400
    headers = {"Origin": origin, "X-CSRF-Token": c.csrf, "Content-Type": "application/json"}
    assert request(instance, "/api/forward/agents", "POST", "{}", headers)[0] == 404
