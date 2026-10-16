"""Read-only monitoring: real sealed evidence and isolated persisted ledger fixtures."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dashboard"), str(ROOT / "scripts")]
import monitoring_api as api  # noqa: E402

V1 = "v7-5a78ea5d15214e37bcae18f167ffcee3"
V2 = "v74-76d07c0d32444cecaf07e875deacb519"


def test_primary_decisions_and_no_implied_execution():
    if not (api.platform.pm2.OUTPUT / V2 / "result.json").exists():
        pytest.skip("local sealed evidence absent")
    with api.forward.fwd.no_network():
        v1 = api.platform.public_global(V1)
        d = api.get({"wallet": "global:" + V2})
    assert v1["validation_status"] == "REJECTED_BY_VALIDATOR"
    assert d["decision"]["validation_status"] == "VALID_PROPOSAL"
    assert d["decision"]["result"]["response"]["target_cash_weight"] == "1.00"
    assert d["summary"]["cash"] == "100000.00"
    assert d["positions"] == d["trades"] == d["curve"] == []
    assert not d["persistent_execution"] and d["read_only"]
    assert d["mark"]["source"] == "SYNTHETIC_OFFLINE_NOT_MARKET_DATA"
    assert {
        w["ticker"] for w in d["decision"]["result"]["response"]["watchlist_candidates"]
    } == {"PETR4", "ITUB4"}
    assert [t["kind"] for t in d["timeline"]] == [
        "Contexto preparado",
        "Inferência concluída",
        "Validação",
    ]
    with pytest.raises(ValueError):
        api.global_snapshot(V1)
    assert all(r["mode"] != "SYNTHETIC_DEMO" for r in api.catalog()["records"])


@pytest.mark.parametrize(
    "query",
    [
        {"wallet": "../state.json"},
        {"wallet": "h2:unknown"},
        {"wallet": "global:../../x"},
        {"wallet": "global:" + V1},
        {"wallet": "h2:ai", "execute": "true"},
        {"wallet": []},
        {"wallet": "x" * 101},
    ],
)
def test_trust_boundary(query):
    with pytest.raises(ValueError):
        api.get(query)


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    folder = tmp_path / "h2_v6_paper"
    folder.mkdir()
    state = {
        "portfolio": {"cash": 100000, "units": 0},
        "benchmark": {"cash": 100000, "units": 0, "invested": False},
        "initial_capital": 100000,
        "mark": {"session": "2026-10-09", "close": 56},
        "sessions": [
            {"session": "2026-10-09", "equity": 100000, "benchmark_equity": 100000}
        ],
        "decisions": [],
        "pending": {
            "decision_session": "2026-10-09",
            "target_session": "2026-10-13",
            "target_weight": 1,
        },
    }
    path = folder / "state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(api.forward, "OUTPUT", folder)
    reader = api.forward.portfolios
    monkeypatch.setattr(
        api.forward, "portfolios", lambda: reader(folder, tmp_path / "missing_benchmarks")
    )
    # Only the existing source verifier is stubbed: fixtures exercise persisted view contracts.
    monkeypatch.setattr(api.platform, "forward_integrity", lambda root: {"ok": True})
    return state, path


def test_persisted_refresh_pending_execution_gaps_and_absence(ledger):
    state, path = ledger
    before = path.read_bytes()
    d = api.get({"wallet": "h2:ai"})
    assert path.read_bytes() == before
    assert d["positions"] == d["trades"] == [] and d["operation_status"] == "PENDENTE"
    assert d["summary"]["cash"] == 100000 and d["summary"]["receivable"] is None
    assert d["summary"]["drawdown"] is None and len(d["curve"]) == 1
    assert d["future"][0]["target_session"] == "2026-10-13"
    state["portfolio"] = {"cash": 99439, "units": 10}
    state["pending"] = None
    state["mark"] = {"session": "2026-10-14", "close": 57}
    state["sessions"].append(
        {
            "session": "2026-10-14",
            "equity": 100009,
            "benchmark_equity": 100000,
            "executed_decision": "2026-10-09",
            "trades": [{"type": "BUY", "quantity": 10, "price": 56, "cost": 1}],
        }
    )
    path.write_text(json.dumps(state), encoding="utf-8")
    before = path.read_bytes()
    d = api.get({"wallet": "h2:ai"})
    assert path.read_bytes() == before
    assert (
        d["positions"][0]["quantity"] == 10 and d["positions"][0]["market_value"] == 570
    )
    assert (
        d["positions"][0]["available"] is None
        and d["positions"][0]["average_cost"] is None
    )
    assert d["summary"]["costs"] == 1 and d["summary"]["equity"] == 100009
    assert [p["session"] for p in d["curve"]] == ["2026-10-09", "2026-10-14"]
    assert d["trades"][0]["settlement"] is None  # H2 does not publish D+2.
    assert d["trades"][0]["decision_session"] == "2026-10-09"
    assert any(e["kind"] == "Execução paper" for e in d["timeline"])
    assert not d["future"]
    assert api.get({"wallet": "h2:sma_regime_h2_proposed"})["available"] is False
    path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError):
        api.get({"wallet": "h2:ai"})


def test_missing_ledger_and_integrity_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(api.forward, "OUTPUT", tmp_path)
    assert not api.get({"wallet": "h2:ai"})["available"]


def test_expiration_is_read_only_backend_state(ledger, monkeypatch):
    _, path = ledger
    proposal = {
        "decision_session": "2026-10-09",
        "target_session": "2026-10-13",
        "deadline": "2026-10-13T10:00:00-03:00",
        "order_state": "EXPIRADA",
        "approval": None,
        "cancel": None,
        "outcome": None,
    }
    w = api.forward.portfolios()["wallets"][0]
    w.update(key=api.forward.sup.STRATEGY, pending=None, last_decision=None)
    monkeypatch.setattr(api.forward, "portfolios", lambda: {"wallets": [w]})
    monkeypatch.setattr(
        api.forward, "supervision", lambda: {"selected": proposal, "audit": {"ok": True}}
    )
    before = path.read_bytes()
    d = api.get({"wallet": "h2:" + api.forward.sup.STRATEGY})
    assert d["operation_status"] == "EXPIRADA" and d["positions"] == d["trades"] == []
    assert any(e["status"] == "EXPIRADA" for e in d["timeline"])
    assert not d["future"] and path.read_bytes() == before
    monkeypatch.setattr(api.platform, "forward_integrity", lambda _: {"ok": False})
    with pytest.raises(ValueError):
        api.get({"wallet": "h2:" + api.forward.sup.STRATEGY})
