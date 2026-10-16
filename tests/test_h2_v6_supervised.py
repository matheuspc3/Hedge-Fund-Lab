"""H2 v6 supervised ledger: offline, synthetic decisions, no model, no network."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_h2_v6_forward as fwd  # noqa: E402
import run_h2_v6_supervised as sup  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from test_h2_v6_forward import Bars, clock  # noqa: E402

SAT, TUE, WED, THU = (
    clock("2026-10-10 16:00"),
    clock("2026-10-13 19:00"),
    clock("2026-10-14 19:00"),
    clock("2026-10-15 19:00"),
)
BEFORE_OPEN = clock("2026-10-10 17:00")
TARGET = {"ACTION_BUY": 1.0, "ACTION_SELL": 0.0}


class RawBars(Bars):
    """Official raw bars = adjusted / factor; optional inconsistent open factor or gap."""

    def __init__(self, factor=1.0, open_factor=None, gap=None):
        super().__init__(end="2026-10-16")
        if gap is not None:
            close = self.frame.at[fwd.pd.Timestamp("2026-10-09"), "fechamento"]
            self.frame.at[fwd.pd.Timestamp("2026-10-13"), "abertura"] = close * (1 + gap)
        self.factor, self.open_factor = factor, open_factor or factor

    def official_bar(self, session):
        bar = {k: v / self.factor for k, v in self.frame.loc[session].items()}
        bar["abertura"] = self.frame.at[session, "abertura"] / self.open_factor
        return bar


@pytest.fixture(scope="module")
def identity():
    # Hashing the whole manifest per sync is the forward tests' job; verify once here.
    return fwd.identity(clean=False)


@pytest.fixture
def world(tmp_path, monkeypatch, identity):
    monkeypatch.setattr(fwd, "identity", lambda: identity)
    manifest, _ = identity
    return SimpleNamespace(
        forward=tmp_path / "ai",
        root=tmp_path / "h2_v6_supervised",
        bars=RawBars(),
        manifest=manifest,
    )


def close_session(
    w, at, cause="ACTION_BUY", status="DECIDED", volatility=0.3, decide=True
):
    """Freeze S, reconcile the original ledger and record a synthetic decision for S."""
    with fwd.no_network():
        fwd.prepare(w.forward, at, w.bars)
    session = fwd.last_closed_session(at())
    name, folder = str(session.date()), w.forward / "sessions" / str(session.date())
    state = fwd.load_state(w.forward, w.manifest)
    fwd.reconcile(state, fwd.load_bars(folder), session)
    if decide:
        frozen = fwd.read(folder / "input.json")
        target = TARGET.get(cause) if status == "DECIDED" else None
        decision = {
            "decision_session": name,
            "target_session": frozen["target_session"],
            "target_open_deadline": frozen["target_open_deadline"],
            "generated_at": at().isoformat(),
            "status": status,
            "input_sha256": fwd.sha_file(folder / "input.json"),
            "record": {"final_cause": cause},
            "risk_verdict": {"risk_metrics": {"recent_volatility": volatility}},
            "intents": []
            if target is None
            else [{"ticker": fwd.TICKER, "target_weight": target}],
        }
        (folder / "decision.json").write_text(json.dumps(decision), encoding="utf-8")
        state["pending"] = (
            {
                "decision_session": name,
                "target_session": frozen["target_session"],
                "target_weight": target,
            }
            if target is not None
            else None
        )
    fwd.save_state(w.forward, state)
    return name, fwd.sha_file(folder / "decision.json") if decide else None


def act(w, action, session, digest, limits=None, at=BEFORE_OPEN):
    return sup.act(action, session, digest, limits, w.root, w.forward, at)


def sync(w, at):
    return sup.sync(w.root, w.forward, at)


def tree(path):
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def outcome(state, session):
    return state["outcomes"][session]


def test_approval_concentration_execution_idempotency_and_isolation(world):
    w = world
    s, digest = close_session(w, SAT)
    state = sync(w, SAT)
    assert state["inception"] == "2026-10-09" and state["portfolio"]["cash"] == 100000
    assert state["proposals"][s]["state"] == "AGUARDANDO_APROVACAO"
    record = act(
        w, "APPROVE", s, digest, {"max_concentration": 0.8, "max_buy_price": 1000}
    )
    assert record["effect"] == {
        "state": "AJUSTADA_CONCENTRACAO",
        "target_weight": 0.8,
        "reason": "Alvo reduzido de 100% para 80% pelo limite de concentração.",
    }
    with pytest.raises(sup.Conflict):
        act(w, "APPROVE", s, digest)  # one immutable action per session
    t, _ = close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    original = tree(w.forward)
    state = sync(w, TUE)
    done = outcome(state, s)
    assert done["state"] == "EXECUTADA" and done["target_weight"] == 0.8
    [trade] = done["trades"]
    assert trade["type"] == "BUY"
    # Same base costs as the original: spread 5 bps + tax 0.032%, both in the cost.
    assert trade["cost"] == pytest.approx(trade["price"] * trade["quantity"] * 0.00082)
    assert trade["price"] == pytest.approx(
        done["prices"]["adjusted_open"]
    )  # settles adjusted
    assert done["prices"]["raw_open"] == pytest.approx(done["prices"]["adjusted_open"])
    assert done["prices"]["raw_source"] == "sessions/2026-10-13/input.json"
    invested = trade["price"] * trade["quantity"]
    assert invested / (invested + state["portfolio"]["cash"]) == pytest.approx(
        0.8, abs=2e-3
    )
    assert state["proposals"][t]["state"] == "SEM_ORDEM_NECESSARIA"  # MANTER
    before = (tree(w.root), tree(w.forward))
    assert sync(w, TUE)["portfolio"] == state["portfolio"]  # idempotent, no second trade
    assert (tree(w.root), tree(w.forward)) == before
    assert tree(w.forward) == original  # the original Forward Test is never written
    assert sup.verify(w.root, w.forward) == {"ok": True, "events": 4, "errors": []}


def test_reject_expire_cancel_deadline_and_tampered_hash(world):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    with pytest.raises(sup.Conflict, match="decision_hash_mismatch"):
        act(w, "APPROVE", s, "0" * 64)
    with pytest.raises(sup.Conflict, match="deadline_passed"):
        act(w, "APPROVE", s, digest, at=clock("2026-10-13 10:00"))
    with pytest.raises(ValueError, match="reject_has_no_limits"):
        act(w, "REJECT", s, digest, {"max_volatility": 1})
    act(w, "APPROVE", s, digest)
    act(w, "CANCEL", s, digest)
    with pytest.raises(sup.Conflict, match="duplicate_action|invalid_transition"):
        act(w, "CANCEL", s, digest)
    with pytest.raises(sup.Conflict, match="invalid_transition"):
        act(w, "REJECT", s, digest)
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    state = sync(w, TUE)
    assert outcome(state, s)["state"] == "CANCELADA" and state["portfolio"]["units"] == 0
    # Inception is only possible before the first open: a fresh ledger now refuses.
    with pytest.raises(ValueError, match="NOT_COMPARABLE"):
        sync(SimpleNamespace(**{**vars(w), "root": w.root.parent / "late"}), TUE)


def test_concentration_cap_includes_costs_and_existing_position(world):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest, {"max_concentration": 0.4})
    t, digest = close_session(w, TUE, "ACTION_BUY")
    state = sync(w, TUE)
    trade = outcome(state, s)["trades"][0]
    invested = trade["price"] * trade["quantity"]
    assert invested / (invested + state["portfolio"]["cash"]) <= 0.4 + 1e-12
    act(w, "APPROVE", t, digest, {"max_concentration": 0.8}, at=clock("2026-10-13 20:00"))
    close_session(w, WED, "TECH_EXPLICIT_HOLD")
    state = sync(w, WED)
    done = outcome(state, t)
    assert done["state"] == "EXECUTADA" and done["target_weight"] == 0.8
    invested = state["portfolio"]["units"] * done["prices"]["adjusted_open"]
    assert invested / (invested + state["portfolio"]["cash"]) == pytest.approx(
        0.8, abs=1e-12
    )


@pytest.mark.parametrize("action,expected", [("REJECT", "REJEITADA"), (None, "EXPIRADA")])
def test_rejection_and_expiry_keep_cash(world, action, expected):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    if action:
        act(w, action, s, digest)
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    state = sync(w, TUE)
    assert outcome(state, s)["state"] == expected
    assert state["portfolio"] == {"cash": 100000.0, "units": 0.0}
    assert sup.verify(w.root, w.forward)["ok"]


@pytest.mark.parametrize(
    "bars,limits,expected",
    [
        (RawBars(), {"max_buy_price": 1.0}, "NAO_EXECUTADA_LIMITE_PRECO"),
        (RawBars(gap=0.05), {"max_gap_up": 0.03}, "NAO_EXECUTADA_GAP"),
        (RawBars(gap=-0.05), {"max_gap_down": 0.03}, "NAO_EXECUTADA_GAP"),
        (
            RawBars(gap=-0.05),
            {"max_gap_up": 0.03},
            "EXECUTADA",
        ),  # only the down side failed
        (RawBars(), {"max_volatility": 0.2}, "BLOQUEADA_VOLATILIDADE"),
        (RawBars(factor=0.9, open_factor=0.8), {}, "BLOQUEADA_BASE_PRECOS"),
    ],
)
def test_limits_are_checked_on_official_raw_prices(world, bars, limits, expected):
    w = world
    w.bars = bars
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest, limits)
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    state = sync(w, TUE)
    assert outcome(state, s)["state"] == expected, outcome(state, s)["reason"]
    if expected != "EXECUTADA":
        assert state["portfolio"] == {"cash": 100000.0, "units": 0.0}


def test_buy_limit_uses_raw_not_adjusted_price(world):
    w = world
    w.bars = RawBars(factor=0.9)  # raw = adjusted / 0.9, consistent within the day
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    adjusted_open = w.bars.frame.at[fwd.pd.Timestamp("2026-10-13"), "abertura"]
    # Between adjusted and raw open: an adjusted comparison would wrongly execute.
    act(w, "APPROVE", s, digest, {"max_buy_price": adjusted_open / 0.95})
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    done = outcome(sync(w, TUE), s)
    assert done["state"] == "NAO_EXECUTADA_LIMITE_PRECO"
    assert done["prices"]["raw_open"] == pytest.approx(adjusted_open / 0.9)
    assert done["prices"]["adjusted_open"] == pytest.approx(adjusted_open)


def test_divergent_positions_follow_supervised_semantics(world):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest)
    t, sell = close_session(w, TUE, "ACTION_SELL")
    state = sync(w, TUE)
    assert outcome(state, s)["state"] == "EXECUTADA"
    assert state["proposals"][t]["state"] == "AGUARDANDO_APROVACAO"
    raw_open = w.bars.frame.at[fwd.pd.Timestamp("2026-10-14"), "abertura"]
    act(
        w,
        "APPROVE",
        t,
        sell,
        {"min_sell_price": raw_open * 1.1},
        at=clock("2026-10-13 20:00"),
    )
    u, _ = close_session(w, WED, "TECH_EXPLICIT_HOLD")
    state = sync(w, WED)
    assert outcome(state, t)["state"] == "NAO_EXECUTADA_LIMITE_PRECO"
    original = fwd.read(w.forward / "state.json")["portfolio"]
    assert (
        original["units"] == 0 and state["portfolio"]["units"] > 0
    )  # sold vs still long
    assert state["proposals"][u]["state"] == "SEM_ORDEM_NECESSARIA"  # MANTER never trades
    v, _ = close_session(w, THU, "ACTION_BUY")
    state = sync(w, THU)
    # The original buys again from cash; the supervised is already long: no order.
    assert state["proposals"][v]["state"] == "SEM_ORDEM_NECESSARIA"
    assert state["proposals"][v]["reason"].startswith(
        "Carteira supervisionada já está no alvo"
    )


@pytest.mark.parametrize(
    "cause,status,decide,expected",
    [
        ("RISK_VETO_LLM", "DECIDED", True, "SEM_ORDEM_NECESSARIA"),
        ("TECH_NO_MAJORITY", "DECIDED", True, "SEM_ORDEM_NECESSARIA"),
        ("BUY_AT_TARGET_NOOP", "DECIDED", True, "SEM_DECISAO"),
        ("PROVIDER_FAILURE", "FAILED", True, "SEM_DECISAO"),
        ("ACTION_BUY", "LATE_NOT_EXECUTABLE", True, "SEM_DECISAO"),
        (None, None, False, "SEM_DECISAO"),  # MISSED: no decision before the deadline
    ],
)
def test_no_executable_decision_creates_no_order(world, cause, status, decide, expected):
    w = world
    s, _ = close_session(w, SAT, cause, status, decide=decide)
    state = sync(w, SAT)
    assert (s in state["proposals"]) is decide  # a missing decision may still arrive
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    state = sync(w, TUE)
    assert state["proposals"][s]["state"] == expected
    assert outcome(state, s)["state"] == expected
    assert state["portfolio"]["units"] == 0


def test_skipped_sync_is_never_offered_retroactively(world):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest)
    t, _ = close_session(w, TUE, "ACTION_SELL")
    close_session(w, WED, "TECH_EXPLICIT_HOLD")
    state = sync(w, WED)  # no supervised sync on 13/10
    assert outcome(state, s)["state"] == "EXECUTADA"
    assert outcome(state, s)["prices"]["raw_source"] == "sessions/2026-10-13/input.json"
    assert (
        state["proposals"][t]["state"] == "SEM_DECISAO"
        and state["portfolio"]["units"] > 0
    )


def test_crash_windows_recover_without_duplicate_execution(world, monkeypatch):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    real_repair = sup.repair
    calls = []

    def crash_on_second(root, state):
        calls.append(1)
        if len(calls) == 2:
            raise OSError("simulated crash after the write-once record")
        return real_repair(root, state)

    monkeypatch.setattr(sup, "repair", crash_on_second)
    with pytest.raises(OSError):
        act(w, "APPROVE", s, digest)
    monkeypatch.setattr(sup, "repair", real_repair)
    assert not (w.root / "state.json.lock").exists()
    assert not sup.verify(w.root, w.forward)["ok"]  # approval without its event
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    real_save = fwd.save_state
    monkeypatch.setattr(
        fwd, "save_state", lambda *_: (_ for _ in ()).throw(OSError("crash"))
    )
    with pytest.raises(OSError):
        sync(w, TUE)  # settlement only in memory: nothing persisted
    monkeypatch.setattr(fwd, "save_state", real_save)
    assert fwd.read(w.root / "state.json")["mark"]["session"] == "2026-10-09"
    with (w.root / "audit.jsonl").open("ab") as stream:
        stream.write(b'{"torn":')  # interrupted append
    state = sync(w, TUE)
    sync(w, TUE)
    assert len(outcome(state, s)["trades"]) == 1
    assert sum(len(r["trades"]) for r in state["sessions"]) == 1
    report = sup.verify(w.root, w.forward)
    assert report["ok"], report["errors"]
    events = [
        json.loads(line) for line in (w.root / "audit.jsonl").read_text().splitlines()
    ]
    assert [e["event"] for e in events] == [
        "PROPOSED",
        "APPROVED",
        "RESOLVED",
        "PROPOSED",
    ]


def test_audit_chain_detects_tampering(world):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest, {"max_buy_price": 999})
    assert sup.verify(w.root, w.forward)["ok"]
    approval = w.root / "approvals" / f"{s}.json"
    original = approval.read_bytes()
    approval.write_bytes(original.replace(b"999.0", b"998.0"))
    assert any("APPROVED" in e for e in sup.verify(w.root, w.forward)["errors"])
    approval.write_bytes(original)
    audit = w.root / "audit.jsonl"
    lines = audit.read_text().splitlines()
    lines[0] = lines[0].replace('"PROPOSED"', '"PROPOSED "')
    audit.write_text("\n".join(lines) + "\n")
    assert any("chain broken" in e for e in sup.verify(w.root, w.forward)["errors"])


@pytest.mark.parametrize("changed", ["approval", "decision", "input", "journal"])
def test_integrity_failure_blocks_actions_and_settlement(world, changed):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    act(w, "APPROVE", s, digest, {"max_buy_price": 999})
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    path = {
        "approval": w.root / "approvals" / f"{s}.json",
        "decision": w.forward / "sessions" / s / "decision.json",
        "input": w.forward / "sessions" / s / "input.json",
        "journal": w.root / "audit.jsonl",
    }[changed]
    if changed == "journal":
        # Alter a complete event, rather than a recoverable incomplete append.
        path.write_bytes(path.read_bytes().replace(b"PROPOSED", b"CORRUPTED"))
    else:
        path.write_bytes(path.read_bytes() + b" ")
    before = tree(w.root), tree(w.forward)
    assert not sup.verify(w.root, w.forward)["ok"]
    with pytest.raises(sup.Conflict, match="supervision_integrity_failed"):
        act(w, "CANCEL", s, digest)
    with pytest.raises(sup.Conflict, match="supervision_integrity_failed"):
        sync(w, TUE)
    assert (tree(w.root), tree(w.forward)) == before


@pytest.mark.parametrize(
    "limits",
    [
        {"max_buy_price": float("nan")},
        {"max_buy_price": float("inf")},
        {"max_buy_price": -1},
        {"max_buy_price": True},
        {"max_buy_price": "57.3"},
        {"max_concentration": 1.5},
        {"max_gap_up": 0},
        {"unknown": 1},
        {"min_sell_price": 50},  # incoherent with a COMPRA
    ],
)
def test_invalid_limits_are_refused_in_the_backend(world, limits):
    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    with pytest.raises(ValueError):
        act(w, "APPROVE", s, digest, limits)
    assert not (w.root / "approvals" / f"{s}.json").exists()


# ── Phase B: HTTP endpoints over the same synthetic world ───────────────────


def test_supervision_endpoints_are_guarded_and_never_touch_the_original(
    world, monkeypatch, tmp_path
):
    import http.client
    import threading
    import time

    sys.path.insert(0, str(ROOT / "dashboard"))
    import forward_api as api
    import forward_jobs as jobs
    import server

    w = world
    s, digest = close_session(w, SAT)
    sync(w, SAT)
    monkeypatch.setattr(api, "OUTPUT", w.forward)
    monkeypatch.setattr(fwd, "now", BEFORE_OPEN)
    for paid in ("run", "ForwardGeminiClient", "DurableGeminiClient"):
        monkeypatch.setattr(fwd, paid, lambda *a, **k: pytest.fail("model path reached"))
    controller = jobs.Jobs(tmp_path / "operations", w.forward)
    synced = []
    monkeypatch.setattr(controller, "_supervised", lambda: synced.append(1) or "SYNCED")
    monkeypatch.setattr(jobs, "JOBS", controller)
    instance = server.ReusableTCPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=instance.serve_forever, daemon=True).start()
    port = instance.server_address[1]
    valid = {
        "Origin": f"http://127.0.0.1:{port}",
        "X-CSRF-Token": controller.csrf,
        "Content-Type": "application/json",
    }

    def call(path, payload=None, headers=None, raw=None):
        client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = (
            raw if raw is not None else None if payload is None else json.dumps(payload)
        )
        client.request("GET" if body is None else "POST", path, body, headers or valid)
        response = client.getresponse()
        code, data = response.status, response.read()
        client.close()
        return code, json.loads(data) if data else None

    try:
        original = tree(w.forward)
        code, view = call("/api/forward/supervision", headers={})
        assert code == 200 and view["selected"]["order_state"] == "AGUARDANDO_APROVACAO"
        assert view["selected"]["decision_sha256"] == digest and view["audit"]["ok"]
        base = {"confirm": True, "decision_session": s, "decision_sha256": digest}
        approve = "/api/forward/supervision/approve"
        for bad in (
            {},
            base,  # approve requires an explicit limits object, even empty
            {**base, "limits": {}, "extra": 1},
            {**base, "confirm": False, "limits": {}},
            {**base, "confirm": "true", "limits": {}},
        ):
            assert call(approve, bad)[0] == 400
        nonfinite = '{"confirm":true,"decision_session":"%s","decision_sha256":"%s","limits":{"max_buy_price":NaN}}'
        assert call(approve, raw=nonfinite % (s, digest))[0] == 400
        assert call(approve, {**base, "limits": {"max_buy_price": -1}}) == (
            400,
            {"error": "invalid_limit:max_buy_price"},
        )
        assert (
            call(approve, {**base, "limits": {}}, {**valid, "X-CSRF-Token": "x"})[0]
            == 403
        )
        foreign = {**valid, "Origin": "http://evil.example"}
        assert call(approve, {**base, "limits": {}}, foreign)[0] == 403
        assert (
            call(approve, {**base, "decision_sha256": "f" * 64, "limits": {}})[0] == 409
        )
        code, record = call(approve, {**base, "limits": {"max_buy_price": 1000}})
        assert code == 201 and record["effect"]["state"] == "APROVADA"
        assert call(approve, {**base, "limits": {}})[0] == 409  # never edited
        assert call("/api/forward/supervision/cancel", base)[0] == 201
        reject = call("/api/forward/supervision/reject", base)
        assert reject[0] == 409 and reject[1]["error"].startswith("invalid_transition")
        code, job = call("/api/forward/supervision/sync", {})
        assert code == 202 and job["command"] == "supervised"
        for _ in range(500):
            if not controller.status()["busy"]:
                break
            time.sleep(0.01)
        assert (
            synced == [1]
            and controller.status(job["id"])["job"]["supervised"] == "SYNCED"
        )
        assert call("/api/forward/supervision?session=../x", headers={})[0] == 400
        assert call("/api/forward/supervision?other=1", headers={})[0] == 400
        assert call(approve, headers={})[0] == 404  # GET on an action path
        assert call("/api/forward/supervision", {}, valid)[0] == 404  # no bare POST
        code, view = call(f"/api/forward/supervision?session={s}", headers={})
        assert view["selected"]["order_state"] == "CANCELADA" and view["audit"]["ok"]
        wallets = {
            x["key"]: x for x in call("/api/forward/portfolios", headers={})[1]["wallets"]
        }
        assert wallets[sup.STRATEGY]["available"] and wallets[sup.STRATEGY]["comparable"]
        assert tree(w.forward) == original  # the original Forward Test is untouched
        assert "approvals" not in json.dumps(view)  # no private paths served
    finally:
        instance.shutdown()
        instance.server_close()
