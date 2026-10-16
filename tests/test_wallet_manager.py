"""Wallet sizing → durable fake inference → preview → atomic paper approval."""

import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "dashboard"), str(PROJECT / "scripts"), str(PROJECT)]
import wallet_manager_api as m  # noqa: E402


@pytest.fixture
def lab(tmp_path, monkeypatch):
    a = m.analysis
    monkeypatch.setattr(m.manual, "ROOT", tmp_path / "personal")
    monkeypatch.setattr(m.runs, "RADAR_DIR", tmp_path / "radar")
    monkeypatch.setattr(m.runs, "REGISTRY", tmp_path / "radar/registry.json")
    monkeypatch.setattr(a.radar_api, "ROOT", tmp_path / "radar/old")
    monkeypatch.setattr(a.radar_api, "ACTIVE", False)
    monkeypatch.setattr(m.radar, "now", lambda: pd.Timestamp("2026-10-15T10:00:00-03:00"))
    monkeypatch.setattr(m, "used_budget", lambda: m.b.ZERO)
    monkeypatch.setattr(m.network_scope, "qualified", lambda: True)
    monkeypatch.setenv("GEMINI_API_KEY", "OFFLINE_TEST_NO_SECRET")
    m.runs.register(
        "radar-old", "data/radar/old", "2026-10-13", list(m.radar.EXAMPLES), select=True
    )
    a.radar_api.ROOT.mkdir()
    wallet = m.manual.post(
        "confirm",
        {
            "request": {
                "kind": "CREATE",
                "name": "Multiagentes",
                "nature": "SIMULATION",
                "capital": "1000.00",
                "start_date": "2026-10-14",
            },
            "command_id": "wallet",
            "preview_token": None,
            "confirm": True,
        },
    )["wallet"]
    request = {
        "kind": "TRADE",
        "wallet": wallet["id"],
        "trade": {
            "ticker": "VALE3",
            "side": "BUY",
            "quantity": "10",
            "price": "60.00",
            "costs": "0.00",
            "economic_date": "2026-10-14",
        },
    }
    p = m.manual.post("preview", {"request": request})
    wallet = m.manual.post(
        "confirm",
        {
            "request": request,
            "command_id": "initial",
            "preview_token": p["preview_token"],
            "confirm": True,
        },
    )["wallet"]
    request = {
        "command_id": "c" * 32,
        "wallet": wallet["id"],
        "wallet_revision": wallet["revision"],
        "target_date": "2026-10-16",
        "reference_session": "2026-10-14",
        "tickers": ["PETR4", "VALE3"],
        "confirm": True,
    }
    run = a.create(request)["run"]
    prices = {"PETR4": "40.00", "VALE3": "60.00"}
    refs = {
        t: {"input": "frozen-raw", "result": "verified-quorum", "opinion": t}
        for t in prices
    }
    opinions = {
        t: {
            "recommendation": "VENDA" if t == "VALE3" else "COMPRA",
            "risk_verdict": "APROVADO",
            "confidence": 0.7,
        }
        for t in prices
    }
    monkeypatch.setattr(m, "sources", lambda *args: (prices, refs, opinions))
    payload = {"run": run, "proposal": "a" * 32, "cost_rate_pct": "0.10"}
    c = m.prepare(payload)["context"]
    raw = {
        "summary": "Reduzir VALE3 parcialmente e aumentar PETR4, preservando caixa.",
        "actions": [
            {
                "ticker": "VALE3",
                "side": "SELL",
                "quantity": "4",
                "reasoning": "Reduzir posição, sem liquidar.",
            },
            {
                "ticker": "PETR4",
                "side": "BUY",
                "quantity": "10",
                "reasoning": "Compra coordenada com caixa disponível.",
            },
        ],
        "risks": ["Preços são referências históricas, sem risco global qualificado."],
    }
    return c, raw


def result(c, raw):
    root = m.folder(c["run"], c["proposal"])
    value = m.b.sealed(
        {
            "identity": m.IDENTITY,
            "context_sha256": c["sha256"],
            "completed_at": m.radar.now().isoformat(),
            "status": "VALID_PROPOSAL",
            **m.compile_proposal(c, raw),
        }
    )
    m.radar.write(root / "result.json", value, immutable=True)
    return value


def test_partial_sale_quantities_costs_raw_and_weights(lab):
    c, raw = lab
    p = m.compile_proposal(c, raw)
    vale = next(r for r in p["rows"] if r["ticker"] == "VALE3")
    assert (vale["quantity_before"], vale["quantity"], vale["quantity_after"]) == (
        "10",
        "4",
        "6",
    )
    assert p["cash_after"] == "239.36"
    assert p["total_costs"] == "0.64"
    assert sum(m.b.dec(r["value_after"]) for r in p["rows"]) + m.b.dec(
        p["cash_after"]
    ) == m.b.dec(p["equity_after"])
    prompt = json.loads(m.prompt_input(c))
    assert prompt["wallet"]["positions"][0]["quantity"] == "10"
    assert prompt["target_date"] == "2026-10-16" and prompt["prices"]["VALE3"] == "60.00"


@pytest.mark.parametrize(
    "change,error",
    [
        ("short", "insufficient_units"),
        ("cash", "insufficient_cash"),
        ("veto", "incompatible_with_opinion"),
        ("duplicate", "unique_universe"),
        ("fraction", "número válido"),
        ("hold", "hold_quantity"),
    ],
)
def test_invalid_quantities_signals_and_cash(lab, change, error):
    c, raw = lab
    if change == "short":
        raw["actions"][0]["quantity"] = "11"
    elif change == "cash":
        raw["actions"][1]["quantity"] = "100"
    elif change == "veto":
        c["opinions"]["PETR4"]["risk_verdict"] = "VETADO"
    elif change == "duplicate":
        raw["actions"][1]["ticker"] = "VALE3"
    elif change == "fraction":
        raw["actions"][0]["quantity"] = "0.5"
    else:
        raw["actions"][0]["side"] = "HOLD"
    with pytest.raises(ValueError, match=error):
        m.compile_proposal(c, raw)


def test_exit_and_all_hold_are_supported(lab):
    c, raw = lab
    raw["actions"][0]["quantity"] = "10"
    assert (
        next(r for r in m.compile_proposal(c, raw)["rows"] if r["ticker"] == "VALE3")[
            "quantity_after"
        ]
        == "0"
    )
    for a in raw["actions"]:
        a.update(side="HOLD", quantity="0")
    assert m.compile_proposal(c, raw)["trades"] == []


def test_preview_atomic_confirmation_retry_history_and_correction(lab):
    c, raw = lab
    r = result(c, raw)
    before = m.manual.path().read_bytes()
    p = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"}
    preview = m.post("preview", p)
    assert m.manual.path().read_bytes() == before
    assert preview["after"]["cash"] == "239.36"
    payload = {**p, "preview_token": preview["preview_token"], "confirm": True}
    d = m.post("apply", payload)
    assert d["wallet"]["cash"] == "239.36"
    assert len(d["wallet"]["trades"]) == 3
    assert all(
        t["source"]["proposal_sha256"] == r["sha256"] for t in d["wallet"]["trades"][-2:]
    )
    assert m.post("apply", payload)["replayed"]
    assert m.get({"run": c["run"]})["history"][0]["status"] == "APPLIED"
    # Individual operations retain existing correction IDs and append-only originals.
    sale = d["wallet"]["trades"][1]
    correction = {
        "kind": "CORRECTION",
        "wallet": c["wallet"]["id"],
        "target": sale["id"],
        "reason": "Conferência da simulação",
        "trade": {
            k: sale[k]
            for k in ("ticker", "side", "quantity", "price", "costs", "economic_date")
        },
    }
    preview = m.manual.post("preview", {"request": correction})
    corrected = m.manual.post(
        "confirm",
        {
            "request": correction,
            "command_id": "correct",
            "preview_token": preview["preview_token"],
            "confirm": True,
        },
    )
    assert len(corrected["wallet"]["audit"]) == 4
    assert corrected["wallet"]["audit"][1]["source"]["proposal_sha256"] == r["sha256"]


def test_atomic_batch_rollback_on_second_insert(lab, monkeypatch):
    c, raw = lab
    r = result(c, raw)
    original = m.manual.append
    calls = []

    def failing(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise OSError("simulated disk failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(m.manual, "append", failing)
    p = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"}
    preview = m.post("preview", p)
    with pytest.raises(OSError, match="disk failure"):
        m.post("apply", {**p, "confirm": True, "preview_token": preview["preview_token"]})
    current = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    assert current["revision"] == c["wallet"]["revision"]
    assert len(current["trades"]) == 1
    assert r["status"] == "VALID_PROPOSAL"


def test_stale_wallet_blocks_preflight_and_application(lab):
    c, raw = lab
    result(c, raw)
    request = {
        "kind": "TRADE",
        "wallet": c["wallet"]["id"],
        "trade": {
            "ticker": "VALE3",
            "side": "SELL",
            "quantity": "1",
            "price": "60.00",
            "costs": "0",
            "economic_date": "2026-10-15",
        },
    }
    p = m.manual.post("preview", {"request": request})
    m.manual.post(
        "confirm",
        {
            "request": request,
            "command_id": "changed",
            "preview_token": p["preview_token"],
            "confirm": True,
        },
    )
    with pytest.raises(ValueError, match="wallet_changed"):
        m.post(
            "preflight", {"run": c["run"], "proposal": c["proposal"], "max_usd": "0.25"}
        )
    with pytest.raises(ValueError, match="carteira mudou"):
        m.post(
            "preview",
            {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"},
        )


def test_explicit_paid_and_financial_consent(lab):
    c, raw = lab
    root = m.folder(c["run"], c["proposal"])
    p = m.post(
        "preflight", {"run": c["run"], "proposal": c["proposal"], "max_usd": "0.25"}
    )
    assert p["ready"] and p["estimate"]["calls_max"] == 1
    with pytest.raises(ValueError, match="paid_consent"):
        m.post(
            "run",
            {
                "run": c["run"],
                "proposal": c["proposal"],
                "max_usd": "0.25",
                "confirmation_token": p["confirmation_token"],
                "authorize_paid": False,
            },
        )
    assert not (root / "authorization.json").exists()
    result(c, raw)
    with pytest.raises(ValueError, match="financial_consent"):
        m.post(
            "apply",
            {
                "run": c["run"],
                "proposal": c["proposal"],
                "economic_date": "2026-10-15",
                "preview_token": "no",
                "confirm": False,
            },
        )


def test_concurrent_confirmation_registers_one_cesta(lab):
    c, raw = lab
    result(c, raw)
    request = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"}
    preview = m.post("preview", request)
    request.update(preview_token=preview["preview_token"], confirm=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: m.post("apply", request), range(2)))
    assert sorted(d["replayed"] for d in responses) == [False, True]
    assert len(m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["trades"]) == 3


@pytest.mark.parametrize(
    "nature,strategy,error",
    [("EXTERNAL", None, "simulada"), ("SIMULATION", "BUY_HOLD", "rebalanceamento")],
)
def test_external_and_buy_hold_refuse_automatic_simulated_basket(
    lab, nature, strategy, error
):
    c, _ = lab
    request = {
        "kind": "CREATE",
        "name": nature,
        "nature": nature,
        "capital": "1000.00",
        "start_date": "2026-10-14",
    }
    if strategy:
        request.update(
            strategy=strategy,
            comparison_group="test",
            initialization_note="Isolated test",
        )
    w = m.manual.post(
        "confirm",
        {
            "request": request,
            "command_id": nature,
            "preview_token": None,
            "confirm": True,
        },
    )["wallet"]
    trade = {
        "kind": "TRADE",
        "wallet": w["id"],
        "trade": {
            "ticker": "PETR4",
            "side": "BUY",
            "quantity": "1",
            "price": "40.00",
            "costs": "0",
            "economic_date": "2026-10-15",
        },
    }
    with pytest.raises(ValueError, match=error):
        m.manual.batch(w["id"], w["revision"], [trade], {"proposal_sha256": c["sha256"]})


def test_changed_source_and_budget_require_new_review(lab, monkeypatch):
    c, raw = lab
    root = m.folder(c["run"], c["proposal"])
    payload = {"run": c["run"], "proposal": c["proposal"], "max_usd": "0.25"}
    report = m.post("preflight", payload)
    monkeypatch.setattr(m, "used_budget", lambda: m.b.dec("0.01"))
    with pytest.raises(ValueError, match="preflight_required"):
        m.post(
            "run",
            {
                **payload,
                "confirmation_token": report["confirmation_token"],
                "authorize_paid": True,
            },
        )
    assert not (root / "authorization.json").exists()
    result(c, raw)
    prices, refs, opinions = m.sources(None, None)
    monkeypatch.setattr(
        m, "sources", lambda *args: ({**prices, "PETR4": "41.00"}, refs, opinions)
    )
    with pytest.raises(ValueError, match="sources_changed"):
        m.post(
            "preview",
            {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"},
        )


def test_durable_fake_native_call_offline_replay(lab):
    c, raw = lab
    root = m.folder(c["run"], c["proposal"])
    m.radar.write(
        root / "authorization.json",
        m.b.sealed(
            {
                "identity": m.IDENTITY,
                "context_sha256": c["sha256"],
                "usd_reserved": "0.16",
            }
        ),
        immutable=True,
    )
    calls = []

    def transport(*args):
        calls.append(1)
        return m.global_cli.v1cli.fake_response(raw)

    value = m.generate(root, transport=transport)
    assert value["rows"][0]["quantity_after"] == "6"
    assert len(calls) == 1
    # Lost result can be rebuilt entirely from the durable response, no transport.
    (root / "result.json").unlink()
    replayed = m.generate(
        root, replay=True, transport=lambda *args: pytest.fail("replay used network")
    )
    assert replayed == value
    assert len(calls) == 1


def test_history_survives_contract_change_but_cannot_apply(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    monkeypatch.setattr(m, "contracts", lambda: {"version": "new"})
    item = m.get({"run": c["run"]})["history"][0]
    assert item["result"]["response"] == raw and not item["compatible"]
    with pytest.raises(ValueError, match="contract_changed"):
        m.post(
            "preview",
            {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"},
        )


def test_rejected_response_and_each_recovery_failure_are_preserved(lab):
    c, raw = lab
    raw["actions"][0]["quantity"] = "11"
    root = m.folder(c["run"], c["proposal"])
    m.radar.write(
        root / "authorization.json",
        m.b.sealed(
            {
                "identity": m.IDENTITY,
                "context_sha256": c["sha256"],
                "usd_reserved": "0.16",
            }
        ),
        immutable=True,
    )
    calls = []

    def transport(*args):
        calls.append(1)
        return m.global_cli.v1cli.fake_response(raw)

    with pytest.raises(ValueError, match="insufficient_units"):
        m.generate(root, transport=transport)
    with pytest.raises(ValueError, match="insufficient_units"):
        m.generate(
            root,
            replay=True,
            transport=lambda *args: pytest.fail("recovery made another call"),
        )
    item = m.status(c["run"], c["proposal"])
    assert len(item["failures"]) == 2 and item["result"] is None
    assert len(calls) == 1
    assert len(m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["trades"]) == 1


def test_expired_proposal_remains_readable_but_cannot_record(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    monkeypatch.setattr(m.radar, "now", lambda: pd.Timestamp("2026-10-17T10:00:00-03:00"))
    assert m.status(c["run"], c["proposal"])["result"]["status"] == "VALID_PROPOSAL"
    with pytest.raises(ValueError, match="context_expired"):
        m.post(
            "preview",
            {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"},
        )


def test_actual_source_guard_refuses_incomplete_quorum(lab, monkeypatch):
    c, _ = lab
    # Exercise the real source boundary, not the fixture's deterministic source.
    import importlib.util

    spec = importlib.util.spec_from_file_location("manager_source_guard", m.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        m.runs, "committee_outcome", lambda *args: {"state": "FAILED_REPLAY_ONLY"}
    )
    with pytest.raises(ValueError, match="incomplete_quorum"):
        module.sources(m.runs.run(c["run"]), c["wallet"])


def test_browser_end_to_end_when_requested(lab, monkeypatch, tmp_path):
    if not os.environ.get("HFL_MANAGER_BROWSER"):
        pytest.skip("Set HFL_MANAGER_BROWSER=1 for real Chrome + HTTP + isolated SQLite")
    import server

    c, raw = lab
    generate = m.generate
    calls = []

    def fake_provider(*args):
        calls.append(1)
        return m.global_cli.v1cli.fake_response(raw)

    monkeypatch.setattr(
        m,
        "generate",
        lambda root, **kwargs: generate(root, transport=fake_provider, **kwargs),
    )
    with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        try:
            subprocess.run(
                [
                    "node",
                    "tests/wallet_manager_browser_check.mjs",
                    f"http://127.0.0.1:{httpd.server_address[1]}",
                    c["run"],
                    c["wallet"]["id"],
                    str(tmp_path / "screenshots"),
                ],
                cwd=PROJECT,
                check=True,
                timeout=120,
            )
        finally:
            httpd.shutdown()
            worker.join()
    wallet = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    assert wallet["cash"] == "239.36" and len(wallet["trades"]) == 3
    assert len(calls) == 1
