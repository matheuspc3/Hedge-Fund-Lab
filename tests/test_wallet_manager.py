"""Wallet sizing → durable fake inference → preview → atomic paper approval."""

import json
import math
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
    # DP-33 B: no real market base and no Yahoo; the snapshot falls back to "no value".
    monkeypatch.setattr(m.orders.base, "ROOT", tmp_path / "base")
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *a: {})
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


def seed(monkeypatch, rows):
    """Fake DP-27 base: {(ticker, session): (open, close)}; unlisted = not in the base."""

    def merged(ticker, as_of=None):
        return [
            {"date": d, "open": o, "close": cl, "conflict": False}
            for (t, d), (o, cl) in sorted(rows.items())
            if t == ticker and d <= as_of
        ]

    monkeypatch.setattr(m.orders.base, "merged", merged)


def approve(c, date="2026-10-15"):
    p = {"run": c["run"], "proposal": c["proposal"], "economic_date": date}
    preview = m.post("preview", p)
    return m.post(
        "apply", {**p, "preview_token": preview["preview_token"], "confirm": True}
    )


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


def test_preview_atomic_confirmation_retry_history_and_correction(lab, monkeypatch):
    c, raw = lab
    r = result(c, raw)
    before = m.manual.path().read_bytes()
    p = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"}
    preview = m.post("preview", p)
    assert m.manual.path().read_bytes() == before
    assert preview["after"]["cash"] == "239.36"
    assert preview["schedule"]["leg"] == "CLOSE" and preview["schedule"]["valid"]
    payload = {**p, "preview_token": preview["preview_token"], "confirm": True}
    order = m.post("apply", payload)["order"]
    assert (order["session"], order["leg"]) == ("2026-10-15", "CLOSE")
    # DP-33: approving only stores the order; cash and positions do not move yet.
    assert m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["cash"] == "400.00"
    assert m.post("apply", payload)["replayed"]
    assert m.get({"run": c["run"]})["history"][0]["status"] == "PENDING_AUCTION"
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (59, 60.0), ("PETR4", "2026-10-15"): (41, 40.0)},
    )
    assert m.orders.settle_pending()["settled"] == [c["proposal"]]
    d = {"wallet": m.manual.get({"wallet": c["wallet"]["id"]})["selected"]}
    assert d["wallet"]["cash"] == "239.36"
    assert len(d["wallet"]["trades"]) == 3
    assert all(
        t["source"]["proposal_sha256"] == r["sha256"] for t in d["wallet"]["trades"][-2:]
    )
    assert m.get({"run": c["run"]})["history"][0]["status"] == "EXECUTED"
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
    result(c, raw)
    approve(c)
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (59, 60.0), ("PETR4", "2026-10-15"): (41, 40.0)},
    )
    original = m.manual.append
    calls = []

    def failing(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise OSError("simulated disk failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(m.manual, "append", failing)
    out = m.orders.settle_pending()  # never raises: the order just stays pending
    assert out["settled"] == [] and "disk failure" in out["errors"][0]["error"]
    current = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    assert current["revision"] == c["wallet"]["revision"]
    assert len(current["trades"]) == 1
    assert m.status(c["run"], c["proposal"])["status"] == "PENDING_AUCTION"
    monkeypatch.setattr(m.manual, "append", original)
    assert m.orders.settle_pending()["settled"] == [c["proposal"]]
    assert m.orders.settle_pending()["settled"] == []  # idempotent


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
    assert len(m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["trades"]) == 1


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


def test_daily_budget_uses_sp_date_and_preserves_uncertain_reservations(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(m.runs, "load", lambda: {"runs": {"run": {}}})
    monkeypatch.setattr(m.runs, "root_of", lambda entry: tmp_path)
    monkeypatch.setattr(m.radar, "now", lambda: pd.Timestamp("2026-10-21T10:00:00-03:00"))
    for name, at, usd in (
        ("yesterday", "2026-10-21T02:59:59+00:00", "5.00"),
        ("today", "2026-10-21T03:00:00+00:00", "3.90"),
    ):
        m.radar.write(
            tmp_path / "wallet-manager" / name / "authorization.json",
            m.b.sealed({"authorized_at": at, "usd_reserved": usd}),
        )
    assert m.used_budget() == m.b.dec("3.90")
    monkeypatch.setattr(m.radar, "now", lambda: pd.Timestamp("2026-10-22T00:00:00-03:00"))
    assert m.used_budget() == m.b.ZERO


def test_daily_manager_cap_is_enforced(lab, monkeypatch):
    c, _ = lab
    root = m.folder(c["run"], c["proposal"])
    with pytest.raises(ValueError, match="invalid_budget"):
        m.preflight(c, root, "4.01")
    monkeypatch.setattr(m, "used_budget", lambda: m.b.dec("3.90"))
    report = m.preflight(c, root, "4.00")
    assert not report["ready"] and "manager_budget_exceeded" in report["errors"]
    assert report["budget_date"] == "2026-10-15"
    assert not (root / "authorization.json").exists()


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
    # Friday 16:50 = past the last cutoff of the target session (2026-10-16).
    monkeypatch.setattr(m.radar, "now", lambda: pd.Timestamp("2026-10-16T16:50:00-03:00"))
    s = m.status(c["run"], c["proposal"])
    assert s["result"]["status"] == "VALID_PROPOSAL" and s["status"] == "EXPIRED"
    root = m.folder(c["run"], c["proposal"])
    with pytest.raises(ValueError, match="proposal_expired"):
        m.post(
            "apply",
            {
                "run": c["run"],
                "proposal": c["proposal"],
                "economic_date": "2026-10-16",
                "preview_token": "x",
                "confirm": True,
            },
        )
    assert not (root / "order.json").exists()
    record = m.orders.read(root / "expired.json")
    assert record["decision_prices"] == {"VALE3": "60.00", "PETR4": "40.00"}
    # settle computes the opportunity-cost inputs once the target close is official
    seed(
        monkeypatch,
        {("VALE3", "2026-10-16"): (59, 62.0), ("PETR4", "2026-10-16"): (41, 39.0)},
    )
    m.orders.settle_pending()
    items = {i["ticker"]: i for i in m.orders.read(root / "opportunity.json")["items"]}
    assert items["VALE3"]["official_close"] == "62.00"
    assert items["VALE3"]["move_vs_decision"] == "-8.00"  # sold 4 below the later close
    assert items["PETR4"]["move_vs_decision"] == "-10.00"
    assert m.latest({"wallet": c["wallet"]["id"]})["latest"]["status"] == "EXPIRED"
    assert m.wallet_current(c)["cash"] == "400.00"


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
    assert wallet["cash"] == "400.00" and len(wallet["trades"]) == 1  # order pending
    assert len(calls) == 1


def test_latest_proposal_for_wallet(lab):
    c, raw = lab
    wallet = c["wallet"]["id"]
    assert m.latest({"wallet": "f" * 32})["latest"] is None
    assert m.latest({"wallet": wallet})["latest"]["status"] == "PREPARED"
    result(c, raw)
    got = m.latest({"wallet": wallet})["latest"]
    assert got["status"] == "VALID_PROPOSAL" and got["applied_at"] is None
    assert got["proposal"] == c["proposal"] and got["trades"][0]["ticker"] == "VALE3"
    assert got["results_url"].startswith(f"/radar?run={c['run']}&")


def test_booked_dividend_feeds_manager_cash_and_invalidates_open_proposal(lab):
    c, raw = lab
    result(c, raw)
    r = m.manual.request(
        {
            "kind": "DIVIDEND",
            "wallet": c["wallet"]["id"],
            "dividend": {
                "ticker": "VALE3",
                "kind": "DIVIDENDO",
                "data_com": "2026-10-14",
                "payment_date": "2026-10-15",
                "quantity": "10",
                "gross": "100.00",
                "net": "100.00",
            },
        }
    )
    out = m.manual.book_dividends([(r, {"snapshot_sha256": "a" * 64, "url": "u"})])
    assert out["booked"] == 1
    # the old proposal is stale (wallet revision changed) with the clear refusal
    with pytest.raises(ValueError, match="wallet_changed"):
        m.wallet_current(c)
    with pytest.raises(ValueError, match="carteira mudou"):
        m.post(
            "preview",
            {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"},
        )
    # a new analysis sees the ledger cash that already includes the dividend
    fresh = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    assert m.b.dec(fresh["cash"]) == m.b.dec(c["wallet"]["cash"]) + 100
    big = {**raw, "actions": [raw["actions"][0], {**raw["actions"][1], "quantity": "17"}]}
    with pytest.raises(ValueError, match="insufficient_cash"):
        m.compile_proposal(c, big)  # 680 > 400 + 240 of the sale
    assert m.compile_proposal({**c, "wallet": fresh}, big)["cash_after"]


def at(text):
    return pd.Timestamp(text + "-03:00")


def test_manager_ui_labels_keep_portuguese_utf8():
    source = (PROJECT / "dashboard/wallet-manager.js").read_text(encoding="utf-8")
    for label in (
        "leilão de ",
        "Executa ao preço oficial B3.",
        "Preço de referência",
        "Caixa e posições só mudam",
        "Movimentação",
        "Peso antes → depois",
        "teto diário US$ 4",
    ):
        assert label in source
    assert not any(bad in source for bad in ("Ã£", "Ã§", "Ãµ", "Â·", "â†", "�"))


@pytest.mark.parametrize(
    "when,expected",
    [
        ("2026-10-19T09:44:59", ("2026-10-19", "OPEN")),  # before the pre-auction
        ("2026-10-19T09:45:00", ("2026-10-19", "CLOSE")),
        ("2026-10-19T14:00:00", ("2026-10-19", "CLOSE")),
        ("2026-10-22T10:35:22", ("2026-10-22", "CLOSE")),  # approved after opening
        ("2026-10-19T16:49:59", ("2026-10-19", "CLOSE")),
        ("2026-10-19T16:50:00", ("2026-10-20", "OPEN")),  # inside the closing margin
        ("2026-10-16T18:30:00", ("2026-10-19", "OPEN")),  # Friday evening -> Monday
        ("2026-10-17T12:00:00", ("2026-10-19", "OPEN")),  # weekend
        ("2026-11-03T10:44:00", ("2026-11-03", "OPEN")),  # winter regime: +1h
        ("2026-11-03T10:45:00", ("2026-11-03", "CLOSE")),
        ("2026-11-03T17:49:00", ("2026-11-03", "CLOSE")),
        ("2026-11-03T17:50:00", ("2026-11-04", "OPEN")),
    ],
)
def test_auction_schedule_cutoffs(when, expected):
    assert m.orders.first_auction(at(when)) == expected


def test_validity_ends_with_the_target_sessions_last_cutoff():
    assert not m.orders.expired("2026-10-16", at("2026-10-16T16:49:59"))
    assert m.orders.expired("2026-10-16", at("2026-10-16T16:50:00"))
    assert m.orders.expired("2026-10-16", at("2026-10-17T10:00:00"))
    assert m.orders.schedule(at("2026-10-15T08:00:00"), "2026-10-16")["valid_until"] == (
        "2026-10-16T16:50-03:00"
    )


def test_open_leg_books_at_official_open_with_session_economic_date(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-15T09:00:00"))
    order = approve(c)["order"]
    assert (order["session"], order["leg"]) == ("2026-10-15", "OPEN")
    assert order["decision_prices"] == {"VALE3": "60.00", "PETR4": "40.00"}
    # before the pre-open and with an empty base: flagged snapshots without a value
    flags = {t: (q["flag"], q["value"]) for t, q in order["quotes"]["approval"].items()}
    assert flags == {t: ("INTRADAY_UNAVAILABLE", None) for t in ("PETR4", "VALE3")}
    wallet = c["wallet"]["id"]
    seed(monkeypatch, {})  # auction price not in the base yet: waits, nothing changes
    assert m.orders.settle_pending()["waiting"] == [c["proposal"]]
    assert m.latest({"wallet": wallet})["latest"]["status"] == "PENDING_AUCTION"
    assert m.manual.get({"wallet": wallet})["selected"]["cash"] == "400.00"
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (62.5, 61.0), ("PETR4", "2026-10-15"): (41.0, 40.0)},
    )
    m.orders.settle_pending()
    m.orders.settle_pending()  # repeating is harmless
    trades = m.manual.get({"wallet": wallet})["selected"]["trades"][1:]
    assert [(t["ticker"], t["side"], t["price"], t["economic_date"]) for t in trades] == [
        ("VALE3", "SELL", "62.50", "2026-10-15"),
        ("PETR4", "BUY", "41.00", "2026-10-15"),
    ]
    prices = trades[0]["source"]["prices"]["VALE3"]  # the four prices of the TCC
    assert prices == {
        "decision": "60.00",
        "preview_quote": order["quotes"]["preview"]["VALE3"],
        "approval_quote": order["quotes"]["approval"]["VALE3"],
        "auction": "62.50",
    }
    import portfolio_history_api

    assert (
        trades[0]["source"]["kind"] in portfolio_history_api.MANAGER_KINDS
    )  # origin: gestor
    got = m.latest({"wallet": wallet})["latest"]
    assert got["status"] == "EXECUTED" and got["auction"]["leg"] == "OPEN"
    assert got["trades"][0]["price"] == "62.50"


def test_one_pending_order_per_wallet(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    approve(c)
    c2 = m.prepare({"run": c["run"], "proposal": "b" * 32, "cost_rate_pct": "0.10"})[
        "context"
    ]
    result(c2, raw)
    with pytest.raises(ValueError, match="pending_order_exists"):
        approve(c2)
    assert not (m.folder(c2["run"], c2["proposal"]) / "order.json").exists()


def test_insufficient_cash_at_official_price_reduces_buys_deterministically(
    lab, monkeypatch
):
    c, raw = lab
    result(c, raw)
    approve(c)
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (59, 60.0), ("PETR4", "2026-10-15"): (41, 80.0)},
    )
    m.orders.settle_pending()
    wallet = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    buy = wallet["trades"][-1]
    # cash 400 + 239.76 (sale) = 639.76; 10 x 80 would not fit: floor(10 * 639.76/800.80) = 7
    assert (buy["ticker"], buy["quantity"], buy["costs"]) == ("PETR4", "7", "0.56")
    assert wallet["cash"] == "79.20"
    done = m.orders.read(m.folder(c["run"], c["proposal"]) / "execution.json")
    assert done["adjustments"] == [
        {
            "ticker": "PETR4",
            "ordered": "10",
            "executed": "7",
            "reason": "INSUFFICIENT_CASH",
        }
    ]
    assert [t["quantity_ordered"] for t in done["trades"]] == ["4", "10"]


def test_leg_without_official_price_is_not_executed_nor_invented(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    approve(c)
    seed(
        monkeypatch, {("VALE3", "2026-10-15"): (59, 60.0)}
    )  # session published, PETR4 absent
    m.orders.settle_pending()
    wallet = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    assert [t["ticker"] for t in wallet["trades"]] == ["VALE3", "VALE3"]
    done = m.orders.read(m.folder(c["run"], c["proposal"]) / "execution.json")
    assert done["not_executed"] == [{"ticker": "PETR4", "reason": "NO_OFFICIAL_PRICE"}]
    assert done["prices"]["PETR4"]["auction"] is None
    assert wallet["cash"] == "639.76"


def test_dividend_while_pending_does_not_block_execution(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    approve(c)
    r = m.manual.request(
        {
            "kind": "DIVIDEND",
            "wallet": c["wallet"]["id"],
            "dividend": {
                "ticker": "VALE3",
                "kind": "DIVIDENDO",
                "data_com": "2026-10-14",
                "payment_date": "2026-10-15",
                "quantity": "10",
                "gross": "5.00",
                "net": "5.00",
            },
        }
    )
    m.manual.book_dividends([(r, {"snapshot_sha256": "a" * 64, "url": "u"})])
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (59, 60.0), ("PETR4", "2026-10-15"): (41, 40.0)},
    )
    assert m.orders.settle_pending()["settled"] == [c["proposal"]]
    assert m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["cash"] == "244.36"


def test_sweep_leaves_a_proposal_booked_under_the_old_rule_alone(lab, monkeypatch):
    c, raw = lab
    r = result(c, raw)
    wid, source = c["wallet"]["id"], {"proposal_sha256": r["sha256"]}
    requests = [
        {"kind": "TRADE", "wallet": wid, "trade": {**t, "economic_date": "2026-10-15"}}
        for t in r["trades"]
    ]
    token = m.manual.batch(wid, c["wallet"]["revision"], requests, source)[
        "preview_token"
    ]
    m.manual.batch(
        wid, c["wallet"]["revision"], requests, source, confirm=True, token=token
    )
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-19T10:00:00"))
    out = m.orders.settle_pending()
    assert out["expired"] == [] and out["errors"] == []
    assert m.status(c["run"], c["proposal"])["status"] == "APPLIED"


# ---- DP-33 stage B: delayed-quote snapshot, tolerance band, stale thesis ----


def synthetic(close, a=0.01, gap=0.0, n=70):
    """Fake base rows: alternating +-a intraday (and +-gap overnight) returns ending at `close`."""
    days = [d.date().isoformat() for d in pd.bdate_range(end="2026-10-14", periods=n)]
    rows, prev = [], 100.0
    for i, day in enumerate(days):
        sign = 1 if i % 2 == 0 else -1
        opened = prev * math.exp(sign * gap)
        rows.append((day, opened, opened * math.exp(sign * a)))
        prev = rows[-1][2]
    scale = close / prev
    return [
        {"date": d, "open": o * scale, "close": cl * scale, "conflict": False}
        for d, o, cl in rows
    ]


def fake_base(monkeypatch, per_ticker):
    def merged(ticker, as_of=None):
        return [r for r in per_ticker.get(ticker, []) if not as_of or r["date"] <= as_of]

    monkeypatch.setattr(m.orders.base, "merged", merged)


def both(monkeypatch):
    fake_base(monkeypatch, {"VALE3": synthetic(60.0), "PETR4": synthetic(40.0)})


def fake_quotes(monkeypatch, px):
    """Fake DP-26 provider: one coherent 1-min bar at `px[ticker]` + an empty trailing bar."""

    def delayed(tickers, now, day):
        return {
            t: {
                "day": day,
                "interval": "1m",
                "fetched_at": now.isoformat(),
                "bars": [
                    ["10:58", px[t], px[t], px[t], px[t], 10.0],
                    ["10:59", None, None, None, None, None],
                ],
            }
            for t in tickers
        }

    monkeypatch.setattr(m.orders, "delayed_bars", delayed)


def clock(monkeypatch, text):
    monkeypatch.setattr(m.radar, "now", lambda: at(text))


def preview_at(monkeypatch, c, when="2026-10-15T11:00:00"):
    p = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-15"}
    clock(monkeypatch, when)
    return p, m.post("preview", p)


def apply_at(monkeypatch, p, preview, when, **extra):
    clock(monkeypatch, when)
    token = {"preview_token": preview["preview_token"], "confirm": True}
    return m.post("apply", {**p, **token, **extra})


def test_volatility_and_tolerance_band(monkeypatch):
    fake_base(monkeypatch, {"X": synthetic(50.0, a=0.01, gap=0.005)})
    v = m.orders.volatility("X", "2026-10-14")
    assert v["sessions"] == 60 and v["as_of"] == "2026-10-14"
    assert v["sigma60"] == pytest.approx(0.01 * math.sqrt(60 / 59))
    assert v["sigma_d"] == pytest.approx(0.015 * math.sqrt(60 / 59))
    assert v["overnight_share"] == pytest.approx(1 / 9)
    sigma, tol = v["sigma60"], m.orders.tolerance
    assert tol(sigma, 15) == pytest.approx(3 * sigma * math.sqrt(15 / 415))
    assert tol(sigma, 2) == 0.005  # floor: a few minutes is noise
    assert tol(sigma, 400) == 0.02  # ceiling
    assert tol(sigma, 15, early=True) == pytest.approx(2 * tol(sigma, 15))  # first 30 min
    assert tol(None, 15) == 0.02  # unknown sigma: ceiling, nothing invented
    fake_base(monkeypatch, {"X": synthetic(50.0, n=15)})  # short base
    assert m.orders.volatility("X", "2026-10-14") is None
    rows = synthetic(50.0)  # conflicts are skipped, leaving too few sessions
    fake_base(
        monkeypatch, {"X": [{**r, "conflict": True} for r in rows[:-3]] + rows[-3:]}
    )
    assert m.orders.volatility("X", "2026-10-14") is None


def test_snapshot_shape_open_session(lab, monkeypatch):
    fake_base(monkeypatch, {"VALE3": synthetic(60.0)})
    fake_quotes(monkeypatch, {"VALE3": 60.55})
    clock(monkeypatch, "2026-10-15T11:00:00")
    snap = m.orders.snapshot(["VALE3"], m.radar.now())["VALE3"]
    assert (snap["value"], snap["basis"], snap["flag"]) == (
        "60.55",
        "DELAYED_QUOTE",
        None,
    )
    assert (snap["source"], snap["declared_delay_min"]) == ("Yahoo (atraso ~15 min)", 15)
    assert snap["quote_time"] == "2026-10-15T10:58:00-03:00"  # last coherent bar
    assert snap["fetched_at"] == "2026-10-15T11:00:00-03:00"
    assert (snap["session_state"], snap["session_fraction"]) == (
        "OPEN",
        round(60 / 415, 6),
    )
    assert snap["policy"] == m.orders.POLICY and len(snap["payload_sha256"]) == 64


def test_closed_session_snapshot_carries_the_flagged_official_close(lab, monkeypatch):
    fake_base(monkeypatch, {"VALE3": synthetic(60.0)})  # official closes through 14/10
    asked = []
    monkeypatch.setattr(
        m.orders, "delayed_bars", lambda t, now, day: asked.append((t, day)) or {}
    )
    for when, state, flag, session in (
        ("2026-10-15T08:00:00", "PRE", "SESSION_PRE", "2026-10-14"),
        ("2026-10-14T17:30:00", "CLOSED", "SESSION_CLOSED", "2026-10-14"),
        ("2026-10-10T12:00:00", "CLOSED", "SESSION_CLOSED", "2026-10-09"),  # Saturday
    ):
        clock(monkeypatch, when)
        snap = m.orders.snapshot(["VALE3", "PETR4"], m.radar.now())
        vale = snap["VALE3"]
        assert (vale["session_state"], vale["flag"]) == (state, flag)
        assert vale["basis"] == "LAST_OFFICIAL_CLOSE"
        assert vale["quote_session"] == session and vale["declared_delay_min"] is None
        assert snap["PETR4"]["value"] is None  # nothing in the base: no value invented
        # Yahoo only for what the base lacks: never VALE3, whose close is published
        assert asked.pop() == (["PETR4"], session)
    # open session but Yahoo gave nothing: flagged fallback, never a made-up quote
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *a: {})
    clock(monkeypatch, "2026-10-15T11:00:00")
    snap = m.orders.snapshot(["VALE3"], m.radar.now())["VALE3"]
    assert (snap["session_state"], snap["flag"], snap["value"]) == (
        "OPEN",
        "INTRADAY_UNAVAILABLE",
        "60.00",
    )


def test_ended_session_without_official_close_uses_its_last_delayed_bar(lab, monkeypatch):
    """20/10 bug: a 17:10 preview showed 19/10's close while the 20/10 session had moved."""
    c, _ = lab
    fake_base(monkeypatch, {"VALE3": synthetic(60.0)})  # COTAHIST of 15/10 not in yet
    fake_quotes(monkeypatch, {"VALE3": 62.00})
    vol = m.orders.volatility("VALE3", "2026-10-14")
    for when, state, session in (
        ("2026-10-15T17:10:00", "CLOSED", "2026-10-15"),  # after the session, same day
        ("2026-10-16T08:00:00", "PRE", "2026-10-15"),  # next morning, before COTAHIST
    ):
        clock(monkeypatch, when)
        snap = m.orders.snapshot(["VALE3"], m.radar.now())["VALE3"]
        assert (snap["basis"], snap["value"], snap["flag"]) == (
            "DELAYED_QUOTE",
            "62.00",
            "SESSION_" + state,
        )
        assert snap["quote_session"] == session and snap["session_fraction"] == 1.0
        stale = m.orders.stale_check(
            c, "VALE3", snap, vol
        )  # one whole session: 3 sigma_d
        assert stale["band"] == pytest.approx(3 * vol["sigma_d"], abs=1e-6)
        assert stale["alert"] and stale["move"] == pytest.approx(62 / 60 - 1, abs=1e-6)
    # Yahoo down: flagged as unavailable, not as if the old close were the session's
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *a: {})
    clock(monkeypatch, "2026-10-15T17:10:00")
    snap = m.orders.snapshot(["VALE3"], m.radar.now())["VALE3"]
    assert (snap["flag"], snap["quote_session"]) == ("INTRADAY_UNAVAILABLE", "2026-10-14")


def test_delayed_bars_reuses_the_dp26_path_and_its_lock(monkeypatch):
    stock = m.orders.stock
    now = at("2026-10-15T11:00:00")
    monkeypatch.setattr(stock, "session_today", lambda n: "2026-10-15")
    monkeypatch.setattr(stock, "LIVE", {})

    def collect(ticker, n):
        if ticker == "BAD":
            raise OSError("yahoo down")
        if ticker == "OLD":  # fetch "succeeds" without refreshing the cached record
            return
        stock.LIVE[ticker] = {
            "day": "2026-10-15",
            "fetched_at": n.isoformat(),
            "bars": [],
        }

    monkeypatch.setattr(stock, "collect", collect)
    old = "2026-10-15T09:00:00-03:00"
    stock.LIVE["OLD"] = {"day": "2026-10-15", "fetched_at": old, "bars": []}
    got = m.orders.delayed_bars(["GOOD", "BAD", "OLD"], now, "2026-10-15")
    assert list(got) == ["GOOD"]  # failed and stale-cached tickers are left out
    assert not stock.INTRADAY_LOCK.locked()
    monkeypatch.setattr(stock, "session_today", lambda n: None)
    assert m.orders.delayed_bars(["GOOD"], now, "2026-10-15") == {}  # not closed yet
    # from 18:00 the day is closed: collect archives it and the sealed archive is read
    archive = {"day": "2026-10-15", "fetched_at": old, "bars": []}
    monkeypatch.setattr(stock, "load_day", lambda t, d: archive if t == "GOOD" else None)
    night = at("2026-10-15T19:00:00")
    got = m.orders.delayed_bars(["GOOD", "BAD", "NONE"], night, "2026-10-15")
    assert got == {"GOOD": archive}  # an archive's older fetch time is not "stale"


def test_preview_seals_quotes_and_shows_the_band_without_a_stale_alert(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    fake_quotes(monkeypatch, {"VALE3": 60.20, "PETR4": 40.00})
    p, preview = preview_at(monkeypatch, c)
    row = preview["quotes"]["VALE3"]
    assert row["decision"] == "60.00" and row["quote"]["value"] == "60.20"
    assert row["tolerance_by_minutes"]["15"] == pytest.approx(
        3 * row["volatility"]["sigma60"] * math.sqrt(15 / 415), rel=1e-4
    )
    assert preview["stale_alert"] == []
    root = m.folder(c["run"], c["proposal"])
    assert m.orders.read(root / "quotes-preview.json")["quotes"]["VALE3"] == row["quote"]
    assert not (root / "order.json").exists()


def test_approval_refused_when_the_quote_moves_beyond_the_band(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    px = {"VALE3": 60.00, "PETR4": 40.00}
    fake_quotes(monkeypatch, px)
    p, preview = preview_at(monkeypatch, c)
    px["VALE3"] = 60.60  # +1.00% in 15 minutes; limit 0.58%
    with pytest.raises(m.manual.Invalid) as e:
        apply_at(monkeypatch, p, preview, "2026-10-15T11:15:00")
    assert e.value.field == "manager_quote_moved"
    assert str(e.value) == (
        "O preço de VALE3 mudou 1,00% desde a prévia (limite 0,58%). Gere uma nova prévia."
    )
    assert not (m.folder(c["run"], c["proposal"]) / "order.json").exists()
    px["VALE3"] = 60.20  # +0.33%: inside the band
    order = apply_at(monkeypatch, p, preview, "2026-10-15T11:15:00")["order"]
    assert order["quotes"]["preview"]["VALE3"]["value"] == "60.00"
    assert order["quotes"]["approval"]["VALE3"]["value"] == "60.20"
    assert order["checks"]["bands"]["VALE3"]["minutes"] == 15.0
    assert (
        order["checks"]["stale_alert"] == [] and not order["checks"]["stale_acknowledged"]
    )


def test_band_doubles_in_the_first_half_hour_of_trading(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    px = {"VALE3": 60.00, "PETR4": 40.00}
    fake_quotes(monkeypatch, px)
    p, preview = preview_at(monkeypatch, c, "2026-10-15T10:05:00")
    assert preview["quotes"]["VALE3"]["tolerance_by_minutes"]["15"] == pytest.approx(
        0.011503, abs=1e-5
    )
    px["VALE3"] = 60.60  # +1.00%: over 0.58%, inside the doubled 1.15%
    done = apply_at(
        monkeypatch, p, preview, "2026-10-15T10:20:00", acknowledge_stale=True
    )  # +1.00% also breaches the 0.66% stale band: acknowledged
    order = done["order"]
    assert order["checks"]["bands"]["VALE3"]["tolerance"] == pytest.approx(
        0.011503, abs=1e-5
    )


def test_two_closed_session_snapshots_pass_trivially(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    p, preview = preview_at(monkeypatch, c, "2026-10-15T17:30:00")
    # 15/10 ended without its official close and Yahoo is offline: same fallback twice
    assert preview["quotes"]["VALE3"]["quote"]["flag"] == "INTRADAY_UNAVAILABLE"
    order = apply_at(monkeypatch, p, preview, "2026-10-15T17:40:00")["order"]
    assert order["checks"]["bands"]["VALE3"]["move"] == 0
    assert order["quotes"]["approval"]["VALE3"]["basis"] == "LAST_OFFICIAL_CLOSE"


def test_stale_thesis_alert_requires_and_records_the_acknowledgement(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    px = {
        "VALE3": 61.00,
        "PETR4": 40.00,
    }  # +1.67% at 11:00; band 3 sigma sqrt(60/415) = 1.15%
    fake_quotes(monkeypatch, px)
    p, preview = preview_at(monkeypatch, c)
    assert preview["stale_alert"] == [
        "Tese possivelmente desatualizada: VALE3 moveu +1,67% desde o fechamento usado pelo"
        " gestor (faixa de 3 desvios: 1,15%)."
    ]
    assert not preview["quotes"]["PETR4"]["stale"]["alert"]
    with pytest.raises(m.manual.Invalid) as e:  # never silently approved or rejected
        apply_at(monkeypatch, p, preview, "2026-10-15T11:05:00")
    assert e.value.field == "manager_stale_thesis_acknowledgement_required"
    assert "Tese possivelmente desatualizada: VALE3" in str(e.value)
    with pytest.raises(m.manual.Invalid):  # only a real True counts
        apply_at(monkeypatch, p, preview, "2026-10-15T11:05:00", acknowledge_stale="yes")
    assert not (m.folder(c["run"], c["proposal"]) / "order.json").exists()
    done = apply_at(
        monkeypatch, p, preview, "2026-10-15T11:05:00", acknowledge_stale=True
    )
    checks = done["order"]["checks"]
    assert checks["stale_alert"] == ["VALE3"] and checks["stale_acknowledged"]
    assert checks["stale"]["VALE3"]["move"] == pytest.approx(61 / 60 - 1, abs=1e-6)


def test_dividend_adjusts_the_stale_reference(lab, monkeypatch):
    c, _ = lab
    fake_base(monkeypatch, {"VALE3": synthetic(60.0)})
    vol = m.orders.volatility("VALE3", "2026-10-14")
    snap = {
        "value": "59.00",
        "basis": "DELAYED_QUOTE",
        "quote_session": "2026-10-15",
        "session_fraction": 0.1,
    }
    plain = m.orders.stale_check(c, "VALE3", snap, vol)
    assert plain["alert"] and plain["move"] == pytest.approx(59 / 60 - 1, abs=1e-6)
    event = {"kind": "DIVIDENDO", "data_com": "2026-10-14", "value_per_share": "1.00"}
    monkeypatch.setattr(m.orders.dividends, "events", lambda t: [event])  # ex-date 15/10
    adjusted = m.orders.stale_check(c, "VALE3", snap, vol)
    assert adjusted["adjusted_reference"] == 59.0 and adjusted["move"] == 0
    assert not adjusted["alert"] and adjusted["dividends"][0]["value_per_share"] == "1.00"
    old = {
        **event,
        "data_com": "2026-10-13",
    }  # ex-date 14/10: already in the manager's close
    monkeypatch.setattr(m.orders.dividends, "events", lambda t: [old])
    assert m.orders.stale_check(c, "VALE3", snap, vol)["dividends"] == []


def test_quotes_reach_the_ledger_trade_source_prices(lab, monkeypatch):
    c, raw = lab
    result(c, raw)
    both(monkeypatch)
    px = {"VALE3": 60.10, "PETR4": 40.00}
    fake_quotes(monkeypatch, px)
    p, preview = preview_at(monkeypatch, c)
    px["VALE3"] = 60.25
    order = apply_at(monkeypatch, p, preview, "2026-10-15T11:05:00")["order"]
    seed(
        monkeypatch,
        {("VALE3", "2026-10-15"): (59, 60.5), ("PETR4", "2026-10-15"): (41, 40.0)},
    )
    m.orders.settle_pending()
    trade = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["trades"][1]
    prices = trade["source"]["prices"]["VALE3"]
    assert prices["decision"] == "60.00" and prices["auction"] == "60.50"
    assert prices["preview_quote"] == order["quotes"]["preview"]["VALE3"]
    assert prices["approval_quote"] == order["quotes"]["approval"]["VALE3"]
    assert (prices["preview_quote"]["value"], prices["approval_quote"]["value"]) == (
        "60.10",
        "60.25",
    )
