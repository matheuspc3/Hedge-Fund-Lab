"""Wallet/date analysis creation, immutable history and safe worker switching."""

import http.client
import json
import sys
import threading
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dashboard"), str(ROOT / "scripts"), str(ROOT)]
import radar_analysis_api as a  # noqa: E402
import server  # noqa: E402


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(a.runs, "RADAR_DIR", tmp_path / "radar")
    monkeypatch.setattr(a.runs, "REGISTRY", tmp_path / "radar/registry.json")
    monkeypatch.setattr(a.manual, "ROOT", tmp_path / "personal")
    monkeypatch.setattr(a.radar_api, "ROOT", tmp_path / "radar/old")
    monkeypatch.setattr(a.radar_api, "ACTIVE", False)
    monkeypatch.setattr(a.radar, "now", lambda: pd.Timestamp("2026-10-15T02:00:00-03:00"))
    monkeypatch.setattr(
        a.radar, "prepare", lambda *x, **kw: pytest.fail("unexpected preparation")
    )
    monkeypatch.setattr(
        a.radar, "run", lambda *x, **kw: pytest.fail("unexpected inference")
    )
    a.runs.register(
        "radar-old", "data/radar/old", "2026-10-13", list(a.radar.EXAMPLES), select=True
    )
    a.radar_api.ROOT.mkdir()
    sentinel = a.radar_api.ROOT / "preserved.txt"
    sentinel.write_text("existing history", encoding="utf-8")
    w = a.manual.post(
        "confirm",
        {
            "request": {
                "kind": "CREATE",
                "name": "Multiagentes",
                "nature": "SIMULATION",
                "capital": "100000.00",
                "start_date": "2026-10-14",
            },
            "command_id": "create-wallet",
            "preview_token": None,
            "confirm": True,
        },
    )["wallet"]
    return {
        "command_id": "a" * 32,
        "wallet": w["id"],
        "wallet_revision": w["revision"],
        "target_date": "2026-10-16",
        "reference_session": "2026-10-14",
        "tickers": list(a.radar.EXAMPLES),
        "confirm": True,
    }


def test_defaults_creation_switch_without_restart_and_idempotent_history(lab):
    d = a.get({})
    assert (d["target_date"], d["reference_session"]) == ("2026-10-16", "2026-10-14")
    registry_before = a.runs.REGISTRY.read_bytes()
    result = a.create(lab)
    assert a.platform.runner()["id"] == result["run"]
    view = a.platform.radar_view(result["run"])
    assert view["mutation_available"] and view["universe"] == lab["tickers"]
    a.platform.radar_post_gate(
        "prepare",
        {"tickers": lab["tickers"], "session": lab["reference_session"], "mode": "live"},
        [result["run"]],
    )
    assert result["provider_calls"] == result["financial_operations"] == 0
    c = a.get({"run": result["run"]})["context"]
    assert c["wallet"]["id"] == lab["wallet"] and c["target_date"] == "2026-10-16"
    assert c["classification"] == "FUTURE_ANALYSIS"
    after = a.runs.REGISTRY.read_bytes()
    assert after != registry_before
    assert a.create(lab) == result and a.runs.REGISTRY.read_bytes() == after
    assert (a.runs.RADAR_DIR / "old/preserved.txt").read_text() == "existing history"
    assert len(a.get({})["history"]) == 1
    with pytest.raises(ValueError, match="header_mismatch"):
        a.platform.radar_post_gate(
            "prepare",
            {"tickers": lab["tickers"], "session": "2026-10-14", "mode": "live"},
            ["radar-old"],
        )


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("target_date", "2026-10-17", "target_not_a_planned"),
        ("reference_session", "2026-10-15", "reference_must_be_closed"),
        ("reference_session", "2026-10-16", "reference_must_be_closed"),
        ("reference_session", "2026-08-31", "reference_must_be_closed"),
        ("wallet_revision", "stale", "wallet_changed"),
        ("wallet", "other-wallet", "wallet_not_found"),
        ("confirm", False, "confirmation_required"),
        ("command_id", "../../other", "invalid_analysis_command"),
    ],
)
def test_invalid_creation_preserves_registry(lab, field, value, error):
    before = a.runs.REGISTRY.read_bytes()
    with pytest.raises(ValueError, match=error):
        a.create({**lab, field: value})
    assert a.runs.REGISTRY.read_bytes() == before


def test_busy_worker_cannot_be_rebound(lab, monkeypatch):
    monkeypatch.setattr(a.radar_api, "ACTIVE", True)
    with pytest.raises(ValueError, match="busy"):
        a.create(lab)
    assert a.platform.runner()["id"] == "radar-old"


def test_repeated_command_cannot_change_context(lab):
    a.create(lab)
    with pytest.raises(ValueError, match="command_conflict"):
        a.create({**lab, "target_date": "2026-10-19"})


def test_interrupted_registration_resumes_original_context(lab, monkeypatch):
    register = a.runs.register
    monkeypatch.setattr(
        a.runs, "register", lambda *x, **kw: (_ for _ in ()).throw(OSError("interrupted"))
    )
    with pytest.raises(OSError, match="interrupted"):
        a.create(lab)
    path = a.runs.RADAR_DIR / ("analysis-" + lab["command_id"]) / a.CONTEXT
    before = path.read_bytes()
    monkeypatch.setattr(a.runs, "register", register)
    result = a.create(lab)
    assert path.read_bytes() == before and a.get({"run": result["run"]})["context"]


def test_snapshot_and_prior_analyses_survive_wallet_change(lab):
    first = a.create(lab)
    request = {
        "kind": "TRADE",
        "wallet": lab["wallet"],
        "trade": {
            "ticker": "PETR4",
            "side": "BUY",
            "quantity": "1",
            "price": "50.00",
            "costs": "0.00",
            "economic_date": "2026-10-14",
        },
    }
    preview = a.manual.post("preview", {"request": request})
    changed = a.manual.post(
        "confirm",
        {
            "request": request,
            "command_id": "buy",
            "preview_token": preview["preview_token"],
            "confirm": True,
        },
    )["wallet"]
    assert a.get({"run": first["run"]})["wallet_changed"]
    assert a.create(lab) == first  # lost receipt keeps its original snapshot
    second = a.create(
        {
            **lab,
            "command_id": "b" * 32,
            "wallet_revision": changed["revision"],
            "target_date": "2026-10-15",
        }
    )
    assert second["context"]["classification"] == "SAME_DAY_ANALYSIS"
    assert first["context"]["wallet"]["positions"] == []
    assert len(a.get({})["history"]) == 2


def test_weekend_default_and_historical_classification(lab, monkeypatch):
    monkeypatch.setattr(a.radar, "now", lambda: pd.Timestamp("2026-10-16T20:00:00-03:00"))
    assert a.choices()["target_date"] == "2026-10-19"
    result = a.create({**lab, "target_date": "2026-10-15"})
    assert result["context"]["classification"] == "HISTORICAL_REANALYSIS"


def test_session_closed_but_not_yet_published_by_b3_is_an_explicit_gap(lab, monkeypatch):
    # 20/10 20:56: the calendar says 20/10 closed, the B3 file only reaches 19/10.
    monkeypatch.setattr(a.radar, "now", lambda: pd.Timestamp("2026-10-20T20:56:00-03:00"))
    monkeypatch.setattr(a.base, "published", lambda: "2026-10-19")
    c = a.choices()
    assert (c["reference_session"], c["last_closed_session"]) == ("2026-10-19", "2026-10-20")
    assert "20/10/2026" in c["reference_note"] and "19/10/2026" in c["reference_note"]
    lab = {**lab, "target_date": "2026-10-21"}
    with pytest.raises(ValueError, match="reference_must_be_closed"):
        a.create({**lab, "reference_session": "2026-10-20"})
    # A run whose session is not in the base yet: prepare refused, readiness explains.
    run = a.create(lab)["run"]
    monkeypatch.setattr(a.base, "published", lambda: "2026-10-13")
    body = {"tickers": lab["tickers"], "session": "2026-10-14", "mode": "live"}
    with pytest.raises(ValueError, match="not_yet_published_by_b3"):
        a.platform.radar_post_gate("prepare", body, [run])
    item = a.platform.radar_readiness(
        "2026-10-14", ["PETR4"], a.radar_api.ROOT, run=run
    )["items"][0]
    assert item["error"] == "reference_session_not_yet_published_by_b3"
    assert "13/10/2026" in item["action"] and "KeyError" not in item["action"]
    # 20/10 22:11: B3 published, but Yahoo's row of the session is provisional (volume 0).
    monkeypatch.setattr(a.base, "published", lambda: "2026-10-14")
    error = "ValueError: no adjustment factor around 2026-10-14"
    blocked = {"ticker": "PETR4", "session": "2026-10-14", "status": "BLOCKED", "error": error}
    (a.radar_api.ROOT / "last_prepare.json").write_bytes(json.dumps({"items": [blocked]}).encode())
    item = a.platform.radar_readiness(
        "2026-10-14", ["PETR4"], a.radar_api.ROOT, run=run
    )["items"][0]
    assert "Yahoo ainda não consolidou o pregão de 14/10/2026" in item["action"]
    assert "dados até 13/10/2026" in item["action"]


def test_context_tampering_is_not_silently_ignored(lab):
    result = a.create(lab)
    path = a.radar_api.ROOT / a.CONTEXT
    value = json.loads(path.read_text(encoding="utf-8"))
    value["target_date"] = "2026-10-19"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="hash_mismatch"):
        a.get({"run": result["run"]})


@pytest.mark.parametrize("remaining", [[], ["BBAS3", "ITUB4", "PETR4", "WEGE3"]])
def test_multiagent_universe_survives_zero_positions_and_preserves_history(
    lab, monkeypatch, remaining
):
    # An old four-asset analysis stays exactly as registered, even after this fix.
    subset = {**lab, "tickers": [t for t in lab["tickers"] if t != "VALE3"]}
    old = a.create(subset)
    path = a.radar_api.ROOT / a.CONTEXT
    before = path.read_bytes()
    wallet = a.manual.get({"wallet": lab["wallet"]})["selected"]
    wallet = {
        **wallet,
        "strategy": "MULTIAGENT",
        "positions": [{"ticker": t, "quantity": "1"} for t in remaining],
    }
    monkeypatch.setattr(a.manual, "get", lambda query: {"wallets": [wallet]})
    offered = a.get({})["wallets"][0]["analysis_tickers"]
    assert set(offered) == set(a.radar.EXAMPLES) and "VALE3" in offered
    assert a.create(subset) == old and path.read_bytes() == before
    registry = a.runs.REGISTRY.read_bytes()
    with pytest.raises(ValueError, match="multiagent_requires_full_universe"):
        a.create({**subset, "command_id": "b" * 32})
    assert a.runs.REGISTRY.read_bytes() == registry
    new = a.create({**lab, "command_id": "c" * 32, "tickers": offered})
    assert new["context"]["wallet"]["positions"] == wallet["positions"]
    assert set(a.runs.run(new["run"])["universe"]) == set(a.radar.EXAMPLES)
    assert new["provider_calls"] == new["financial_operations"] == 0
    assert path.read_bytes() == before
    # Personal wallets keep their existing position-based, editable default.
    assert a.default_tickers({**wallet, "strategy": None}) == (
        remaining or list(a.radar.EXAMPLES)
    )


def test_http_creation_requires_origin_csrf_and_preserves_active_dispatch(lab):
    with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as web:
        thread = threading.Thread(target=web.serve_forever, daemon=True)
        thread.start()
        port = web.server_address[1]

        def call(headers):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            c.request("POST", "/api/platform/radar-analysis", json.dumps(lab), headers)
            r = c.getresponse()
            result = r.status, r.read()
            c.close()
            return result

        try:
            assert call({"Content-Type": "application/json"})[0] == 403
            headers = {
                "Content-Type": "application/json",
                "Origin": f"http://127.0.0.1:{port}",
                "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
            }
            status, raw = call(headers)
            assert (
                status == 201
                and json.loads(raw)["run"] == "radar-ui-" + lab["command_id"]
            )
        finally:
            web.shutdown()
            thread.join()
