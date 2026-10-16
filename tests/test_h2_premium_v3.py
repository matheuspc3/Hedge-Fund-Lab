"""Offline V3 checks, using the supervised runner's existing synthetic world."""

# ruff: noqa: F811 -- pytest injects the imported reusable world fixture.

import itertools
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))
import market_api as market
from test_h2_v6_supervised import (  # noqa: F401
    SAT,
    TUE,
    RawBars,
    act,
    clock,
    close_session,
    fwd,
    identity,
    sup,
    sync,
    tree,
    world,
)


def request(w, price, limits=None):
    proposal = fwd.read(w.root / "state.json")["proposals"]["2026-10-09"]
    return market.scenario(
        {
            "decision_session": "2026-10-09",
            "decision_sha256": proposal["decision_sha256"],
            "limits": limits or {},
            "hypothetical_open": price,
        },
        w.forward,
    )


def test_mandatory_examples_and_no_writes(world):
    w = world
    w.bars.frame.at[fwd._timestamp("2026-10-09"), "fechamento"] = 56
    close_session(w, SAT)
    state = sync(w, SAT)
    root = w.forward
    before = tree(w.root), tree(root)
    p = state["proposals"]["2026-10-09"]
    assert p["decision_session"] == "2026-10-09" and p["raw_close"] == 56
    limits = {
        "max_buy_price": 56,
        "max_gap_up": 0.02,
        "max_gap_down": 0.02,
        "max_concentration": 0.05,
    }
    for price, allowed in [
        (54, False),
        (54.88, True),
        (55, True),
        (56, True),
        (56.5, False),
        (57.5, False),
    ]:
        r = market.scenario(
            {
                "decision_session": p["decision_session"],
                "decision_sha256": p["decision_sha256"],
                "limits": limits,
                "hypothetical_open": price,
            },
            root,
        )
        assert r["allowed"] is allowed
        assert r["band"]["lower"] == pytest.approx(54.88) and r["band"]["upper"] == 56
        assert r["band"]["inclusive"] and r["band"]["redundant_gap_up"]
        assert r["concentration_amount_at_mark"] == 5000
        assert r["estimate"]["concentration_after_costs"] == pytest.approx(
            0.05 if allowed else 0
        )
        assert r["persisted"] is False and r["kind"] == "hypothetical"
    market.market(root, SAT)
    assert before == (tree(w.root), tree(root))


@pytest.mark.parametrize("direction", ["COMPRA", "VENDA"])
def test_all_limit_subsets_existing_positions_and_raw_adjusted(
    world, monkeypatch, direction
):
    w = world
    w.bars = RawBars(factor=0.5)
    close_session(w, SAT, "ACTION_BUY" if direction == "COMPRA" else "ACTION_SELL")
    original = sup.propose

    def positioned(state, *args):
        state["portfolio"] = {"cash": 90000, "units": 10000 / state["mark"]["close"]}
        return original(state, *args)

    monkeypatch.setattr(sup, "propose", positioned)
    state = sync(w, SAT)
    reference = state["proposals"]["2026-10-09"]["raw_close"]
    fields = {"max_gap_up": 0.02, "max_gap_down": 0.02, "max_volatility": 0.4}
    fields.update(
        {"max_buy_price": reference, "max_concentration": 0.2}
        if direction == "COMPRA"
        else {"min_sell_price": reference}
    )
    before = tree(w.root), tree(w.forward)
    for count in range(len(fields) + 1):
        for keys in itertools.combinations(fields, count):
            limits = {k: fields[k] for k in keys}
            r = request(w, reference, limits)
            assert r["allowed"], r["reason"]
            e = r["estimate"]
            assert e["adjusted_open"] == reference * 0.5
            assert e["adjustment_factor"] == 0.5
            assert e["cost"] == pytest.approx(e["order_value"] * 0.00082)
            assert e["equity_after"] == pytest.approx(100000 - e["cost"])
            if direction == "COMPRA" and "max_concentration" in keys:
                assert e["concentration_after_costs"] == pytest.approx(0.2)
                assert e["order_value"] < 10000  # incremental, not 20k from cash
            if direction == "VENDA":
                assert e["units_after"] == pytest.approx(0)
    assert before == (tree(w.root), tree(w.forward))


def test_gate_failures_missing_data_and_direction(world):
    w = world
    close_session(w, SAT)
    state = sync(w, SAT)
    ref = state["proposals"]["2026-10-09"]["raw_close"]
    r = request(w, ref, {"max_buy_price": ref * 0.9, "max_gap_down": 0.02})
    assert not r["allowed"] and r["band"]["empty"]
    assert not request(w, ref, {"max_volatility": 0.1})["allowed"]
    for limits in [
        {"min_sell_price": 50},
        {"max_concentration": 1.1},
        {"x": 1},
        {"max_gap_up": True},
    ]:
        with pytest.raises(ValueError):
            request(w, ref, limits)
    for price in [0, -1, 1e-320, True, float("nan"), float("inf"), "56", 1e7]:
        with pytest.raises(ValueError):
            request(w, price)
    assert request(w, None, {"max_concentration": 0.05})["estimate"] is None
    state["portfolio"] = {"cash": 90000, "units": 10000 / state["mark"]["close"]}
    fwd.save_state(w.root, state)
    assert not request(w, ref, {"max_concentration": 0.05})["allowed"]
    (w.forward / "sessions/2026-10-09/bars.csv").unlink()
    assert request(w, ref)["estimate"] is None
    assert market.market(w.forward, SAT)["official_close"] is None


@pytest.mark.parametrize(
    "cause", ["TECH_EXPLICIT_HOLD", "RISK_VETO_VOLATILITY", "ACTION_SELL"]
)
def test_never_promotes_hold_veto_or_empty_sale(world, cause):
    w = world
    close_session(w, SAT, cause)
    sync(w, SAT)
    result = request(w, 56)
    assert not result["allowed"] and result["estimate"] is None


def test_actual_position_direction_vintage_and_missing_volatility(world):
    w = world
    close_session(w, SAT, volatility=None)
    state = sync(w, SAT)
    ref = state["proposals"]["2026-10-09"]["raw_close"]
    assert not request(w, ref, {"max_volatility": 0.5})["allowed"]
    state["portfolio"] = {"cash": 30000, "units": 70000 / state["mark"]["close"]}
    fwd.save_state(w.root, state)
    # Cap passes at the reference close; a price jump would require selling.
    r = request(w, ref * 2, {"max_concentration": 0.8})
    assert not r["allowed"] and r["estimate"]["quantity"] == 0
    state["mark"]["session"] = "2026-10-13"
    fwd.save_state(w.root, state)
    assert request(w, ref)["estimate"] is None


def test_scenario_runner_parity_inclusive_boundary(world):
    w = world
    w.bars = RawBars(gap=-0.02)
    session, digest = close_session(w, SAT)
    sync(w, SAT)
    ref = fwd.read(w.root / "state.json")["proposals"][session]["raw_close"]
    limits = {"max_gap_down": 0.02, "max_concentration": 0.05}
    predicted = request(w, ref * 0.98, limits)
    act(w, "APPROVE", session, digest, limits)
    close_session(w, TUE, "TECH_EXPLICIT_HOLD")
    actual = sync(w, TUE)["outcomes"][session]
    assert predicted["allowed"] and actual["state"] == "EXECUTADA"
    [trade] = actual["trades"]
    for key in ("quantity", "cost"):
        assert trade[key] == pytest.approx(predicted["estimate"][key])


class Feed:
    def __init__(
        self, price=1, timestamp="2026-10-13T10:02:00-03:00", classification="delayed"
    ):
        self.data = {
            "price": price,
            "timestamp": timestamp,
            "source": "Synthetic test provider",
            "classification": classification,
        }

    def quote(self, ticker, at):
        return self.data


def test_market_calendar_quotes_and_informational_monitoring(world):
    w = world
    s, digest = close_session(w, SAT)
    state = sync(w, SAT)
    ref = state["proposals"][s]["raw_close"]
    act(w, "APPROVE", s, digest, {"max_buy_price": ref, "max_gap_down": 0.02})
    before = tree(w.root), tree(w.forward)
    monday = market.market(w.forward, clock("2026-10-12 11:00"))
    assert monday["session"]["state"] == "fechada"
    assert monday["session"]["next_session"] == "2026-10-13"
    assert monday["approved_conditions"][0]["state"] == "Aguardando abertura"
    assert monday["intraday"]["price"] is None
    frozen_input = fwd.read(w.forward / "sessions" / s / "input.json")
    assert monday["official_close"]["timestamp"] == frozen_input["fetched_at"]
    at = clock("2026-10-13 10:10")
    for feed, expected in [
        (Feed(ref), "Dentro do limite"),
        (Feed(ref * 1.01), "Fora do limite"),
        (Feed(ref * 0.97), "Fora do limite"),
        (market.OfflineProvider(), "Dados insuficientes"),
        (Feed(ref, "2026-10-09T16:00:00-03:00"), "Informação desatualizada"),
        (Feed(ref, classification="official_close"), "Dados insuficientes"),
        (Feed(ref, "2026-10-13T11:00:00-03:00"), "Dados insuficientes"),
        (Feed(ref, classification="realtime_verified"), "Dados insuficientes"),
    ]:
        r = market.market(w.forward, at, feed)
        assert r["approved_conditions"][0]["state"] == expected
        assert "execution" not in r and "trades" not in r
    assert market.session_clock(clock("2026-10-13 09:50")())["state"] == "pré-abertura"
    assert market.session_clock(at())["state"] == "negociação"
    assert market.session_clock(TUE())["state"] == "encerrada"
    assert market.session_clock(clock("2026-11-03 11:00")())["state"] == "desconhecido"
    assert market.session_clock(clock("2026-11-03 11:00")())["expected_open"] is None
    broken = Feed()
    broken.data = None
    assert market.observation(broken, at())["price"] is None
    assert before == (tree(w.root), tree(w.forward))


def test_http_scenario_security_and_no_jobs(world, monkeypatch):
    import http.client
    import threading

    import server

    w = world
    session, digest = close_session(w, SAT)
    sync(w, SAT)
    monkeypatch.setattr(market.api, "OUTPUT", w.forward)
    monkeypatch.setattr(
        server.forward_jobs.JOBS,
        "start",
        lambda *a: pytest.fail("No jobs from scenarios"),
    )
    instance = server.ReusableTCPServer(("127.0.0.1", 0), server.Handler)
    worker = threading.Thread(target=instance.serve_forever, daemon=True)
    worker.start()
    port = instance.server_address[1]
    headers = {
        "Origin": f"http://127.0.0.1:{port}",
        "Content-Type": "application/json",
        "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
    }
    body = json.dumps(
        {
            "decision_session": session,
            "decision_sha256": digest,
            "limits": {},
            "hypothetical_open": 56,
        }
    )

    def call(path, value=None, changes=None):
        client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        client.request(
            "POST" if value is not None else "GET",
            path,
            value,
            {**headers, **(changes or {})},
        )
        response = client.getresponse()
        result = response.status, json.loads(response.read())
        client.close()
        return result

    before = tree(w.root), tree(w.forward)
    try:
        assert call("/api/forward/scenario", body)[0] == 403
        assert call("/api/forward/market")[0] == 200
        for changes in [
            {"Origin": "http://evil.example"},
            {"Host": "evil.example"},
            {"X-CSRF-Token": "wrong"},
        ]:
            assert call("/api/forward/scenario", body, changes)[0] == 403
        for invalid in [
            body[:-1] + ',"confirm":true}',
            body.replace('"limits": {}', '"limits": {"max_gap_up":NaN}'),
            body.replace(
                '"hypothetical_open": 56', '"hypothetical_open":56,"hypothetical_open":55'
            ),
            "[]",
        ]:
            assert call("/api/forward/scenario", invalid)[0] == 403
        assert call("/api/forward/scenario?x=1", body)[0] == 403
        assert call("/api/forward/market?session=2026-10-09")[0] == 400
        assert call("/api/forward/scenario", body.replace(digest, "0" * 64))[0] == 403
        assert before == (tree(w.root), tree(w.forward))
    finally:
        instance.shutdown()
        instance.server_close()
        worker.join(5)
