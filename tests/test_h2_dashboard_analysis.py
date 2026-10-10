"""Post-Validation analysis endpoints, checked against the sealed OA-1 Validation.

Read-only: no provider, no snapshot. Skipped when the sealed directory is absent.
The expected numbers are the ones asserted by scripts/h2_v6_oa1_validation_diagnostic.py.
"""

import builtins
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import h2_api  # noqa: E402

VALIDATION = h2_api.SOURCES["provisional"]
pytestmark = pytest.mark.skipif(
    not (VALIDATION / "validation_release.json").is_file(),
    reason="sealed OA-1 Validation absent",
)


@pytest.fixture(scope="module")
def analysis():
    return h2_api.analysis("provisional")


def test_reads_only_the_sealed_validation_directory(monkeypatch):
    opened = []
    real = builtins.open

    def spy(file, *args, **kwargs):
        opened.append(Path(file).resolve())
        return real(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy)
    h2_api._cached.cache_clear()
    h2_api.analysis("provisional")
    h2_api.decision("provisional", "L01", "2025-08-08")
    assert opened and all(p.is_relative_to(VALIDATION.resolve()) for p in opened)
    assert all("FINAL" not in str(p).upper() for p in h2_api.SOURCES.values())
    assert h2_api.analysis("demo") is None and h2_api.analysis("final_test") is None


def test_markers_match_trades_and_execution_dates(analysis):
    dates = analysis["market"]["dates"]
    for slot in h2_api.LLM:
        decisions = h2_api._runs(VALIDATION)[slot]["decisions"]
        for t in analysis["participants"][slot]["trades"]:
            assert dates[dates.index(t["date"]) - 1] == t["decision_session"]
            d = decisions[t["decision_session"]]
            assert (
                d["final_cause"]
                == {"BUY": "ACTION_BUY", "SELL": "ACTION_SELL"}[t["type"]]
            )
            assert h2_api._implied(d, 1.0) == t["type"]
            detail = h2_api.decision("provisional", slot, t["decision_session"])
            assert detail["execution_session"] == t["date"]
            assert detail["execution"]["trade"]["price"] == t["price"]


def test_runs_are_filtered_independently(analysis):
    p = analysis["participants"]
    assert [len(p[s]["trades"]) for s in h2_api.LLM] == [12, 14, 14]
    assert p["L02"]["trades"] == p["L03"]["trades"] != p["L01"]["trades"]
    pairs = {x["pair"]: x for x in analysis["cross_runs"]["pairs"]}
    assert pairs["L02 vs L03"]["identical_equity_and_trades"]
    assert (
        pairs["L02 vs L03"]["outcome_divergent"],
        pairs["L02 vs L03"]["order_divergent"],
    ) == (10, 0)


def test_cycles_exposure_and_prices(analysis):
    m = analysis["market"]
    for slot, final in (("L01", 75983.55), ("L02", 73440.57)):
        p = analysis["participants"][slot]
        assert round(sum(c["pnl"] for c in p["cycles"]) + h2_api.CAPITAL, 2) == final
        e = p["exposure"]
        assert e["closes"]["long"] + e["closes"]["cash"] == e["closes"]["total"] == 247
        assert sum(x["days"] for x in e["daily"].values()) == e["daily_total"] == 247
    assert analysis["participants"]["L01"]["exposure"]["closes"]["long"] == 141
    assert (
        round(
            analysis["participants"]["L01"]["exposure"]["daily"]["cash"]["asset_return"],
            3,
        )
        == 0.287
    )
    assert m["close"][0] is None and round(m["close"][1], 4) == 30.1357
    features = h2_api._runs(VALIDATION)["L01"]["calls"]["2025-03-05"][0]["prompt"][
        "features"
    ]
    i = m["dates"].index("2025-03-05")
    assert abs(m["close"][i] / m["sma50"][i] - 1 - features["sma50_gap"]) < 1e-5


def test_layers_called_decided_changed(analysis):
    for slot in h2_api.LLM:
        a = analysis["agents"][slot]
        assert a["risk"]["vetoes_effective"] == 0 and a["portfolio"]["changed"] == 0
        assert a["orders"]["differs_from_consensus"] == 0
        assert a["technical"]["implied_orders"] == a["orders"]["executed"]
    assert analysis["agents"]["L01"]["portfolio"]["called"] == 80
    assert analysis["agents"]["L01"]["risk"]["vetoes"] == 76


def test_decision_detail_and_missing_data():
    noop = h2_api.decision("provisional", "L01", "2024-09-04")
    assert (
        noop["risk"]["veto_effect"] == "SEM EFEITO" and noop["execution"]["trade"] is None
    )
    assert [r["status"] for r in noop["risk"]["rules"]] == [
        "PASSOU",
        "PASSOU",
        "DISPAROU",
        "NÃO CHAMADO",
    ]
    assert noop["portfolio"]["reasoning"] is None  # rendered as "Não registrado"
    crash = h2_api.decision("provisional", "L01", "2025-08-08")
    assert (
        crash["risk"]["drawdown"] == 0.253629 and crash["portfolio"]["followed_consensus"]
    )
    assert len(crash["technical"]["analysts"]) == 5
    payload = json.dumps(crash, ensure_ascii=False)
    assert "raw_response" not in payload and "system_prompt" not in payload
    for args in (
        ("provisional", "L01", "2025-08-29"),
        ("provisional", "buy_and_hold", "2024-09-04"),
        ("demo", "L01", "2024-09-04"),
        ("official", "L01", "2024-09-04"),
    ):
        assert h2_api.decision(*args) is None
