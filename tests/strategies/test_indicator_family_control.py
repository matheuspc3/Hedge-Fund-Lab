"""Indicator-family-matched classical control: quatro sinais e a agregação."""

import math
from types import MappingProxyType

import numpy as np
import pandas as pd
import pytest

from src.backtesting.arena import MarketObservation
from src.experiments.participants import build_participant
from src.experiments.spec import ParticipantSpec
from src.indicators.macd import macd
from src.indicators.rsi import rsi
from src.strategies.bollinger_bands import BollingerParticipant
from src.strategies.indicator_family_control import (
    IndicatorFamilyControlParticipant,
    aggregate,
    crossing_signal,
    rsi_entry_signal,
)
from src.strategies.sma_cross import SMACrossParticipant


def oscillating_close(sessions: int = 420) -> pd.Series:
    """Ciclo lento (cruza SMA 50/200) com ciclo curto (rompe bandas)."""
    steps = np.arange(sessions, dtype=float)
    close = (
        100
        + 15 * np.sin(2 * math.pi * steps / 260)
        + 3 * np.sin(2 * math.pi * steps / 23)
    )
    return pd.Series(close, index=pd.bdate_range("2020-01-01", periods=sessions))


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (35.0, 25.0, 1),
        (30.0, 29.9, 1),
        (25.0, 20.0, 0),
        (65.0, 75.0, -1),
        (70.0, 70.1, -1),
        (75.0, 80.0, 0),
        (50.0, 55.0, 0),
        (float("nan"), 20.0, 0),
    ],
)
def test_rsi_reage_a_entrada_na_zona_extrema(
    previous: float, current: float, expected: int
) -> None:
    assert rsi_entry_signal(previous, current) == expected


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((-1.0, 0.0, 1.0, 0.0), 1),
        ((0.0, 0.0, 1.0, 0.0), 1),
        ((1.0, 0.0, -1.0, 0.0), -1),
        ((1.0, 0.0, 2.0, 0.0), 0),
        ((float("nan"), 0.0, 1.0, 0.0), 0),
    ],
)
def test_macd_usa_a_regra_de_cruzamento_da_sma(args: tuple, expected: int) -> None:
    assert crossing_signal(*args) == expected


@pytest.mark.parametrize(
    ("signals", "expected"),
    [
        ({"sma": 1, "bollinger": 1, "rsi": -1, "macd": 0}, 1),
        ({"sma": 1, "bollinger": -1, "rsi": 0, "macd": 0}, 0),
        ({"sma": -1, "bollinger": -1, "rsi": 1, "macd": 0}, -1),
        ({"sma": 0, "bollinger": 0, "rsi": 0, "macd": 1}, 1),
        ({"sma": 0, "bollinger": 0, "rsi": 0, "macd": 0}, 0),
    ],
)
def test_agregacao_soma_com_pesos_iguais(signals: dict[str, int], expected: int) -> None:
    assert aggregate(signals) == expected


def test_sma_e_bollinger_reutilizam_literalmente_os_benchmarks() -> None:
    close = oscillating_close()
    control = IndicatorFamilyControlParticipant("PETR4")
    sma = SMACrossParticipant("PETR4", 50, 200)
    bollinger = BollingerParticipant("PETR4", 20, 2.0)
    fired = {"sma": 0, "bollinger": 0}
    for end in range(201, len(close) + 1):
        prefix = close.iloc[:end]
        signals = control.family_signals(prefix)
        assert signals["sma"] == sma._signal(prefix)
        assert signals["bollinger"] == bollinger._signal(prefix)
        fired["sma"] += signals["sma"] != 0
        fired["bollinger"] += signals["bollinger"] != 0
    assert fired["sma"] and fired["bollinger"], "a série precisa exercitar as duas regras"


def test_rsi_e_macd_usam_os_indicadores_do_pipeline() -> None:
    close = oscillating_close()
    control = IndicatorFamilyControlParticipant("PETR4")
    rsi_values = rsi(close, 14)
    macd_line, signal_line, _ = macd(close, 12, 26, 9)
    fired = {"rsi": 0, "macd": 0}
    for end in range(30, len(close) + 1):
        signals = control.family_signals(close.iloc[:end])
        i = end - 1
        assert signals["rsi"] == rsi_entry_signal(
            rsi_values.iloc[i - 1], rsi_values.iloc[i]
        )
        assert signals["macd"] == crossing_signal(
            macd_line.iloc[i - 1],
            signal_line.iloc[i - 1],
            macd_line.iloc[i],
            signal_line.iloc[i],
        )
        fired["rsi"] += signals["rsi"] != 0
        fired["macd"] += signals["macd"] != 0
    assert fired["rsi"] and fired["macd"]


def test_sizing_e_o_do_signal_participant() -> None:
    """+1 -> alvo 1.0; -1 -> alvo 0.0; 0 -> mantém o alvo, sem intent repetido."""
    close = oscillating_close(10)
    frame = pd.DataFrame({"fechamento": close})
    control = IndicatorFamilyControlParticipant("PETR4")
    scripted = iter((1, 0, 1, -1, 0))
    control._signal = lambda _close: next(scripted)  # type: ignore[method-assign]

    targets = []
    for end in range(1, 6):
        observation = MarketObservation(
            session=frame.index[end - 1],
            history=MappingProxyType({"PETR4": frame.iloc[:end]}),
            positions=MappingProxyType({"PETR4": 0.0}),
            cash=1_000.0,
            equity=1_000.0,
        )
        targets.append([intent.target_weight for intent in control.decide(observation)])
    assert targets == [[1.0], [], [], [0.0], []]


def test_controle_nao_tem_parametro_calibravel() -> None:
    spec = ParticipantSpec("indicator_family_control", {"ticker": "PETR4"})
    assert isinstance(build_participant(spec), IndicatorFamilyControlParticipant)
    with pytest.raises(ValueError, match="invalid params"):
        build_participant(
            ParticipantSpec(
                "indicator_family_control", {"ticker": "PETR4", "rsi_oversold": 25}
            )
        )
