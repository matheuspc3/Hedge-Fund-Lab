"""H2-V6-FORWARD-PAPER end to end offline: generated bars, fake Gemini, network blocked."""

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_h2_v6_forward as fwd  # noqa: E402
from qualify_h2_v6_production import NativeFactory  # noqa: E402

from src.backtesting.b3_calendar import B3Calendar  # noqa: E402
from src.experiments.h2_evaluation_offline import no_network  # noqa: E402


def clock(text):
    return lambda: pd.Timestamp(text, tz=fwd.TZ)


class Bars:
    """Generated official-calendar bars; nothing is downloaded."""

    def __init__(self, end="2026-10-14"):
        days = pd.DatetimeIndex(
            B3Calendar().sessions_between(date(2016, 1, 4), date.fromisoformat(end))
        )
        steps = np.arange(len(days), dtype=float)
        close = 30 + steps * 0.01 + np.sin(steps / 9)
        opening = np.r_[close[0], close[:-1]] * 1.002
        self.frame = pd.DataFrame(
            {
                "abertura": opening,
                "maxima": np.maximum(opening, close) * 1.01,
                "minima": np.minimum(opening, close) * 0.99,
                "fechamento": close,
                "volume": 1e6,
            },
            index=days,
        )

    def download(self, ticker, start, end):
        return self.frame.loc[:end].copy()

    def official_bar(self, session):
        return self.frame.loc[session].to_dict()

    def source_description(self):
        return {"name": "generated test bars"}


class Leaky(Bars):
    def download(self, ticker, start, end):
        return self.frame.copy()  # bars after the decision close


def test_forward_paper_cycle(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "OFFLINE_TEST_NOT_A_SECRET")
    real_identity = fwd.identity
    monkeypatch.setattr(fwd, "identity", lambda: real_identity(clean=False))
    bars, saturday, tuesday = Bars(), clock("2026-10-10 12:00"), clock("2026-10-13 19:00")

    # Calendar: Saturday decides on Friday's close for Tuesday (12/10 holiday).
    assert fwd.last_closed_session(saturday()) == pd.Timestamp("2026-10-09")
    assert fwd.last_closed_session(clock("2026-10-13 17:59")()) == pd.Timestamp(
        "2026-10-09"
    )
    assert fwd.target_open(pd.Timestamp("2026-10-09")) == pd.Timestamp(
        "2026-10-13 10:00", tz=fwd.TZ
    )

    # Causality: a bar after the decision close is refused before anything is frozen.
    with pytest.raises(ValueError, match="calendar"):
        fwd.prepare(tmp_path / "leak", saturday, Leaky())

    with no_network():
        path = fwd.prepare(tmp_path, saturday, bars)
    frozen = json.loads(path.read_text(encoding="utf-8"))
    assert (frozen["decision_session"], frozen["target_session"]) == (
        "2026-10-09",
        "2026-10-13",
    )
    assert [d["date"] for d in frozen["calendar"]["closed_days_before_target"]] == [
        "2026-10-10", "2026-10-11", "2026-10-12",
    ]  # fmt: skip
    assert fwd.load_bars(path.parent).index[-1] == pd.Timestamp("2026-10-09")

    report = fwd.preflight(tmp_path, saturday)
    assert report["ready"], report["checks"]
    token = report["input"]["sha256"][:12]
    with pytest.raises(SystemExit, match="confirm"):
        fwd.run("0" * 12, tmp_path, saturday)
    assert not (path.parent / "provider.sqlite").exists()  # nothing reserved

    factory = NativeFactory("COMPRA")
    with no_network():
        decision = fwd.run(token, tmp_path, saturday, transport=factory("L01"))
    assert decision["status"] == "DECIDED" and decision["persisted_before_target_open"]
    assert decision["record"]["vote_counts"] == {"COMPRA": 5, "MANTER": 0, "VENDA": 0}
    assert decision["intents"] == [{"ticker": "PETR4.SA", "target_weight": 1.0}]
    assert decision["portfolio_at_close"]["equity"] == fwd.CAPITAL
    calls = factory.calls

    # Same session never infers again, even with a confirmed token.
    with pytest.raises(SystemExit, match="not_yet_decided"):
        fwd.run(token, tmp_path, saturday, transport=factory("L01"))
    assert factory.calls == calls

    # Tuesday after the close: execute at 13/10's open, mark, decide again.
    with no_network():
        path = fwd.prepare(tmp_path, tuesday, bars)
    report = fwd.preflight(tmp_path, tuesday)
    assert report["ready"], report["checks"]
    with no_network():
        fwd.run(report["input"]["sha256"][:12], tmp_path, tuesday, NativeFactory()("L01"))
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    day = state["sessions"][-1]
    (trade,) = day["trades"]
    opening = bars.frame.at[pd.Timestamp("2026-10-13"), "abertura"]
    assert day["executed_decision"] == "2026-10-09" and trade["type"] == "BUY"
    assert trade["price"] == opening
    assert trade["cost"] == pytest.approx(
        trade["price"] * trade["quantity"] * (5e-4 + 0.00032)
    )
    assert state["portfolio"]["cash"] == 0.0
    assert day["equity"] == pytest.approx(trade["quantity"] * day["close"])
    assert day["benchmark_equity"] == pytest.approx(
        day["equity"]
    )  # B&H bought the same open
    assert state["pending"] is None and [d["status"] for d in state["decisions"]] == [
        "DECIDED", "DECIDED",
    ]  # fmt: skip

    # A run that would start at or after the target open is refused.
    late = fwd.preflight(tmp_path, clock("2026-10-14 10:00"))
    assert late["checks"]["before_target_open"] is False and not late["ready"]
