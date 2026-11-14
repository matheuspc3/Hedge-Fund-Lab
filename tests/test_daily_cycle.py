"""DP-34 daily cycle: slots, retries, daily cap, auto-approval and records. No network."""

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "dashboard"), str(PROJECT / "scripts"), str(PROJECT)]
import daily_cycle as dc  # noqa: E402
from test_radar_analysis import lab as analysis_lab  # noqa: E402,F401
from test_wallet_manager import (  # noqa: E402
    both,
    fake_quotes,
    lab as manager_lab,  # noqa: F401
)

DAY = "2026-10-15"  # Thursday, B3 session
REAL_SEND = dc.send


def at(text):
    return pd.Timestamp(text + "-03:00")


@pytest.fixture(autouse=True)
def cycle(tmp_path, monkeypatch):
    monkeypatch.setattr(dc, "FOLDER", tmp_path / "daily-cycle")
    monkeypatch.setattr(dc, "SLEEP", lambda s: time.sleep(0.01))
    for key in ("HFL_RESEND_API_KEY", "HFL_NOTIFY_TO", "HFL_NOTIFY_FROM"):
        monkeypatch.delenv(key, raising=False)
    sent = []
    monkeypatch.setattr(dc, "send", lambda subject, text: sent.append(subject) or "fake")
    return sent


def clock(monkeypatch, text):
    monkeypatch.setattr(dc.radar, "now", lambda: at(text))


def fake_steps(monkeypatch, *results):
    """cycle() replaced by successive outcomes: None = success, Stop = raised."""
    queue = list(results)

    def fake(rec, day):
        rec["links"]["run"] = "radar-ui-" + "a" * 32
        if outcome := queue.pop(0):
            raise outcome
        rec["outcome"] = "ok"

    monkeypatch.setattr(dc, "cycle", fake)
    monkeypatch.setattr(dc, "day_spent", lambda day, rec: Decimal(0))


def test_slots_windows_and_non_session_days(monkeypatch, cycle):
    calls = []
    monkeypatch.setattr(dc, "attempt", lambda slot="manual": calls.append(slot))
    assert dc.tick(at("2026-10-17T09:30:00")) is None  # Saturday
    assert dc.tick(at("2026-10-12T09:30:00")) is None  # holiday (12/10)
    assert dc.tick(at(DAY + "T08:59:00")) is None
    for when in ("09:00:00", "11:59:00", "12:00:00", "15:59:00", "16:00:00", "16:49:00"):
        dc.tick(at(f"{DAY}T{when}"))
    assert calls == ["09:00", "09:00", "12:00", "12:00", "16:00", "16:00"]
    # The last window ends at the DP-33 closing cutoff (17:50 in the November regime).
    assert dc.windows(pd.Timestamp("2026-11-03").date())[-1][2].hour == 17
    assert not (dc.FOLDER / DAY).exists()
    clock(monkeypatch, DAY + "T17:00:00")
    dc.tick(at(DAY + "T17:00:00"))  # every window passed: the day is closed, not invented
    assert dc.final(DAY)["status"] == "SEM_ANALISE" and cycle == [
        "[HFL] Ciclo 15/10/2026: dia sem análise"
    ]


def test_retry_then_sem_analise_and_closed_day_never_runs_again(monkeypatch, cycle):
    retry = dc.Stop("dados_nao_consolidados: PETR4 no adjustment factor", retry=True)
    fake_steps(monkeypatch, retry, retry, retry)
    for slot, when in (
        ("09:00", "09:00:05"),
        ("12:00", "12:00:05"),
        ("16:00", "16:00:05"),
    ):
        clock(monkeypatch, f"{DAY}T{when}")
        rec = dc.attempt(slot)
    first, second, third = dc.earlier(DAY)
    assert (first["status"], first["next_slot"], first["day_status"]) == (
        "RETRY",
        "12:00",
        None,
    )
    assert second["next_slot"] == "16:00" and third["day_status"] == "SEM_ANALISE"
    assert rec["email"] == "fake" and len(cycle) == 3
    assert dc.final(DAY)["status"] == "SEM_ANALISE"
    monkeypatch.setattr(dc, "cycle", lambda *a: pytest.fail("closed day ran again"))
    assert dc.attempt("manual")["status"] == "SEM_ANALISE"
    assert dc.tick(at(DAY + "T16:10:00")) is None
    assert len(dc.earlier(DAY)) == 3


def test_retry_reuses_the_same_days_analysis_then_succeeds(analysis_lab, monkeypatch):  # noqa: F811
    a = dc.analysis
    monkeypatch.setattr(dc.market, "published", lambda: "2026-10-14")
    monkeypatch.setattr(dc, "update_market", lambda rec: None)
    monkeypatch.setattr(dc, "day_spent", lambda day, rec: Decimal(0))
    prepared, ready = [], iter([False, False, False, True])

    def readiness(day, tickers, root, mode, run):
        state = "FROZEN" if next(ready) else "BLOCKED_DATA"
        error = "ValueError: no adjustment factor around 2026-10-14"
        return {
            "items": [
                {"ticker": t, "input_state": state, "error": error} for t in tickers
            ]
        }

    monkeypatch.setattr(dc.platform, "radar_readiness", readiness)
    monkeypatch.setattr(dc.radar_api, "post", lambda c, p: prepared.append((c, p)))
    monkeypatch.setattr(dc, "analysts", lambda *a: None)
    monkeypatch.setattr(dc, "manager", lambda rec, entry, day: rec.update(outcome="ok"))
    clock(monkeypatch, DAY + "T09:00:00")
    morning = dc.attempt("09:00")
    assert morning["status"] == "RETRY" and "no adjustment factor" in morning["reason"]
    run = morning["links"]["run"]
    assert a.get({"run": run})["context"]["classification"] == "SAME_DAY_ANALYSIS"
    assert a.get({"run": run})["context"]["target_date"] == DAY
    clock(monkeypatch, DAY + "T12:00:00")
    noon = dc.attempt("12:00")
    assert noon["status"] == "CONCLUIDO", noon["reason"]
    assert noon["links"]["run"] == run  # reused
    assert [s["step"] for s in noon["steps"]] == ["analise", "dados_prontos"]
    assert noon["steps"][0]["reused"] is True
    payload = {"tickers": list(a.radar.EXAMPLES), "session": "2026-10-14", "mode": "live"}
    assert prepared == [("prepare", payload), ("prepare", payload)]  # re-prepared, free
    assert dc.final(DAY)["status"] == "CONCLUIDO"
    assert len([e for e in a.runs.load()["runs"] if e.startswith("radar-ui-")]) == 1


def test_unpublished_reference_session_blocks_before_creating(analysis_lab, monkeypatch):  # noqa: F811
    monkeypatch.setattr(dc.market, "published", lambda: "2026-10-13")
    clock(monkeypatch, DAY + "T09:00:00")
    with pytest.raises(dc.Stop) as e:
        dc.open_analysis({"links": {}, "steps": []}, DAY)
    assert e.value.retry and e.value.reason == "reference_session_not_yet_published_by_b3"
    assert not [r for r in dc.runs.load()["runs"] if r.startswith("radar-ui-")]


def test_daily_analysis_keeps_sold_out_asset_in_universe(analysis_lab, monkeypatch):  # noqa: F811
    wallet = dc.manual.get({"wallet": analysis_lab["wallet"]})["selected"]
    wallet = {
        **wallet,
        "strategy": "MULTIAGENT",
        "positions": [{"ticker": "PETR4", "quantity": "1"}],
    }
    monkeypatch.setattr(dc.manual, "get", lambda query: {"wallets": [wallet]})
    monkeypatch.setattr(dc.market, "published", lambda: "2026-10-14")
    clock(monkeypatch, DAY + "T09:00:00")
    run = dc.open_analysis({"links": {}, "steps": []}, DAY)
    entry = dc.runs.run(run)
    assert set(entry["universe"]) == set(dc.radar.EXAMPLES)
    assert "VALE3" in entry["universe"]
    context = dc.analysis.context(entry)
    assert context["wallet"]["positions"] == wallet["positions"]
    assert context["provider_calls"] == 0


def test_pending_auction_retries_before_creating_analysis_or_spending(
    tmp_path, monkeypatch
):
    seen = []
    monkeypatch.setattr(dc, "update_market", lambda rec: seen.append("market"))
    monkeypatch.setattr(dc, "multiagent_wallet", lambda: {"id": "wallet"})
    monkeypatch.setattr(dc.orders, "folders", lambda: [tmp_path])
    monkeypatch.setattr(
        dc.orders,
        "read",
        lambda path: {"wallet": {"id": "wallet"}, "session": DAY, "leg": "OPEN"},
    )
    monkeypatch.setattr(
        dc, "open_analysis", lambda *a: pytest.fail("analysis before settlement")
    )
    with pytest.raises(dc.Stop, match="ordem_aguardando_leilao_oficial") as e:
        dc.cycle({}, DAY)
    assert e.value.retry and seen == ["market"]


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    """Fake run roots with reserved USD per run; reservations never shrink."""
    spent = {}
    monkeypatch.setattr(dc.runs, "run", lambda n, registry=None: {"id": n})
    monkeypatch.setattr(dc.runs, "root_of", lambda e: tmp_path / e["id"])
    monkeypatch.setattr(dc, "spent_in", lambda root: spent.get(root.name, Decimal(0)))
    return spent


def earlier_attempt(run):
    rec = {
        "slot": "09:00",
        "status": "RETRY",
        "started_at": DAY + "T09:00:00-03:00",
        "links": {"run": run},
    }
    dc.radar.write(dc.FOLDER / DAY / "attempt-090000-0900-x.json", dc.b.sealed(rec))


def test_daily_cap_counts_every_attempt_and_the_manager(ledger, tmp_path, monkeypatch):
    clock(monkeypatch, DAY + "T12:00:00")
    root = tmp_path / "radar-today"
    entry = {"id": "radar-today", "session": "2026-10-14", "universe": ["PETR4", "VALE3"]}
    monkeypatch.setattr(dc.radar_api, "ROOT", root)
    monkeypatch.setattr(dc.runs, "committee_outcome", lambda *a: None)
    posts = []

    def post(command, payload):
        posts.append(command)
        assert payload["max_usd"] <= 4 - 0.70 - float(dc.MANAGER_RESERVE)
        return {
            "usd_reserved": 2 * 0.663552,
            "ready": True,
            "confirmation_token": "t",
            "items": [],
        }

    monkeypatch.setattr(dc.radar_api, "post", post)
    earlier_attempt("radar-morning")  # a discarded analysis of an earlier attempt
    ledger["radar-morning"] = Decimal("2.70")
    rec = {"links": {"run": "radar-today"}, "steps": [], "reservations": {}}
    with pytest.raises(dc.Stop) as e:  # 2.70 + 1.33 + manager 0.16 > 4.00
        dc.analysts(rec, entry, root, DAY)
    assert not e.value.retry and e.value.reason.startswith("teto_diario_excedido")
    assert posts == ["preflight"]  # never reached the paid run
    ledger["radar-morning"] = Decimal("0.70")
    budget = {
        "authorization": {"required": True, "state": "ABSENT"},
        "budget_token": "b" * 64,
        "aggregate_exposure_usd": 7.5,
    }
    monkeypatch.setattr(dc.runs, "load", lambda: {})
    monkeypatch.setattr(dc.runs, "budget", lambda run, registry: budget)
    authorized = []
    monkeypatch.setattr(
        dc.platform, "authorize_radar_budget", lambda p, h: authorized.append((p, h))
    )
    monkeypatch.setattr(dc.platform, "radar_post_gate", lambda *a: None)
    outcomes = iter(
        [None, None, {"state": "COMMITTEE_COMPLETED"}, {"state": "COMMITTEE_COMPLETED"}]
    )
    monkeypatch.setattr(dc.runs, "committee_outcome", lambda *a: next(outcomes))
    dc.analysts(rec, entry, root, DAY)
    assert posts == ["preflight", "preflight", "run"]
    assert authorized == [
        (
            {
                "run": "radar-today",
                "budget_token": "b" * 64,
                "max_aggregate_usd": 7.5,
                "confirm": True,
            },
            ["radar-today"],
        )
    ]
    steps = {s["step"]: s for s in rec["steps"]}
    assert (
        steps["orcamento_agregado_autorizado"]["by"] == dc.ACTOR == "DP-34 rotina diária"
    )
    assert steps["analistas_autorizados"]["by"] == dc.ACTOR
    assert "analistas_concluidos" in steps


def fake_provider(monkeypatch, raw):
    m = dc.wm
    generate = m.generate
    calls = []

    def transport(*args):
        calls.append(1)
        return m.global_cli.v1cli.fake_response(raw)

    monkeypatch.setattr(
        m, "generate", lambda root, **kw: generate(root, transport=transport, **kw)
    )
    return calls


def test_manager_auto_approves(manager_lab, monkeypatch):  # noqa: F811
    c, raw = manager_lab
    calls = fake_provider(monkeypatch, raw)
    entry = dc.runs.run(c["run"])
    rec = {"links": {"run": c["run"]}, "steps": [], "reservations": {}}
    dc.manager(rec, entry, DAY)
    proposal = rec["links"]["proposal"]
    assert proposal != c["proposal"] and calls == [1]
    root = dc.wm.folder(c["run"], proposal)
    assert dc.wm.checked(root)["cost_rate_pct"] == "0.10"  # Lucas's last rate reused
    order = dc.b.check_seal(json.loads((root / "order.json").read_text(encoding="utf-8")))
    assert (order["session"], order["leg"]) == (DAY, "CLOSE")  # 10:00: closing auction
    assert rec["links"]["order"]["basket"] == order["basket"]
    assert rec["outcome"].startswith("Ordem aprovada: SELL 4 VALE3, BUY 10 PETR4")
    by = {s["step"]: s.get("by") for s in rec["steps"]}
    assert by["gestor_autorizado"] == by["aprovada"] == dc.ACTOR
    assert dc.b.dec(rec["reservations"]["manager"]) == dc.MANAGER_RESERVE
    rec = {
        "slot": "09:00",
        "status": "RETRY",
        "started_at": DAY + "T09:00:00-03:00",
        "links": {"run": c["run"], "proposal": proposal},
    }
    dc.radar.write(dc.FOLDER / DAY / "attempt-090000-0900-x.json", dc.b.sealed(rec))
    again = {"links": {"run": c["run"]}, "steps": [], "reservations": {}}
    dc.manager(again, entry, DAY)  # a later attempt reuses the proposal: no new call
    assert calls == [1] and again["steps"][-1]["step"] == "ja_aprovada"


def test_stale_thesis_alert_leaves_the_proposal_for_lucas(manager_lab, monkeypatch):  # noqa: F811
    c, raw = manager_lab
    fake_provider(monkeypatch, raw)
    both(monkeypatch)
    fake_quotes(monkeypatch, {"VALE3": 61.00, "PETR4": 40.00})  # VALE3 +1.67% > 3 sigma
    clock(monkeypatch, DAY + "T11:00:00")
    rec = {"links": {"run": c["run"]}, "steps": [], "reservations": {}}
    with pytest.raises(dc.Stop) as e:
        dc.manager(rec, dc.runs.run(c["run"]), DAY)
    assert not e.value.retry and e.value.reason.startswith("alerta_tese_velha: Tese")
    root = dc.wm.folder(c["run"], rec["links"]["proposal"])
    assert not (root / "order.json").exists()
    assert dc.wm.status(c["run"], rec["links"]["proposal"])["status"] == "VALID_PROPOSAL"


def test_manager_cap(manager_lab, monkeypatch):  # noqa: F811
    c, raw = manager_lab
    calls = fake_provider(monkeypatch, raw)
    monkeypatch.setattr(dc, "spent_in", lambda root: Decimal("3.90"))
    rec = {"links": {"run": c["run"]}, "steps": [], "reservations": {}}
    with pytest.raises(dc.Stop) as e:
        dc.manager(rec, dc.runs.run(c["run"]), DAY)
    assert e.value.reason.startswith("teto_diario_excedido") and calls == []
    assert not (
        dc.wm.folder(c["run"], rec["links"]["proposal"]) / "authorization.json"
    ).exists()


def test_email_not_configured_does_not_fail_and_resend_payload(monkeypatch):
    monkeypatch.setattr(dc, "send", REAL_SEND)
    monkeypatch.setattr(
        dc.urllib.request, "urlopen", lambda *a, **k: pytest.fail("network")
    )
    assert dc.send("s", "t") == "e-mail não configurado"
    monkeypatch.setenv("HFL_RESEND_API_KEY", "re_test_no_secret")
    monkeypatch.setenv("HFL_NOTIFY_TO", "lucas@example.com")
    seen = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"{}"

    def urlopen(req, timeout):
        seen.append((req, timeout))
        return Response()

    monkeypatch.setattr(dc.urllib.request, "urlopen", urlopen)
    assert dc.send("Assunto", "Texto") == "enviado"
    req, timeout = seen[0]
    assert req.full_url == "https://api.resend.com/emails" and timeout == 10
    assert req.get_header("Authorization") == "Bearer re_test_no_secret"
    assert json.loads(req.data) == {
        "from": "Hedge Fund Lab <onboarding@resend.dev>",
        "to": ["lucas@example.com"],
        "subject": "Assunto",
        "text": "Texto",
    }

    def down(*a, **k):
        raise OSError("unreachable")

    monkeypatch.setattr(dc.urllib.request, "urlopen", down)
    assert dc.send("s", "t") == "falha no e-mail: OSError"


def test_unconfigured_email_is_recorded_and_the_cycle_continues(monkeypatch):
    monkeypatch.setattr(dc, "send", REAL_SEND)
    fake_steps(monkeypatch, None)
    clock(monkeypatch, DAY + "T09:00:00")
    rec = dc.attempt("09:00")
    assert rec["status"] == "CONCLUIDO" and rec["email"] == "e-mail não configurado"
    assert dc.final(DAY)["status"] == "CONCLUIDO"
