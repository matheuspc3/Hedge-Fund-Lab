"""Provas do contrato incremental da arena e da migração do Buy & Hold."""

from types import MappingProxyType
from typing import cast

import pandas as pd
import pytest

from src.backtesting.arena import (
    ExecutionEngine,
    MarketObservation,
    OrderIntent,
)
from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestEngine
from src.strategies.buy_and_hold import BuyAndHold, BuyAndHoldParticipant


def market_data() -> pd.DataFrame:
    dates = pd.DatetimeIndex(["2023-01-02", "2023-01-03"])
    return pd.DataFrame(
        {"abertura": [90.0, 130.0], "fechamento": [100.0, 140.0]},
        index=dates,
    )


def observation(
    data: pd.DataFrame, *, next_session: pd.Timestamp | None
) -> MarketObservation:
    return MarketObservation(
        session=cast(pd.Timestamp, data.index[-1]),
        history=MappingProxyType({"PETR4": data.copy()}),
        positions=MappingProxyType({"PETR4": 0}),
        cash=1_000.0,
        equity=1_000.0,
        next_session=next_session,
    )


def test_buy_and_hold_emite_intent_apenas_na_primeira_observacao() -> None:
    data = market_data()
    participant = BuyAndHoldParticipant("PETR4")

    first = participant.decide(
        observation(data.iloc[:1], next_session=cast(pd.Timestamp, data.index[1]))
    )
    second = participant.decide(observation(data, next_session=None))

    assert first == [
        OrderIntent(
            ticker="PETR4",
            side="BUY",
            target_weight=1.0,
            decision_time=cast(pd.Timestamp, data.index[0]),
            eligible_execution_time=cast(pd.Timestamp, data.index[1]),
        )
    ]
    assert second == []


def test_participant_recebe_somente_historico_observavel() -> None:
    data = market_data()
    data.loc[data.index[1], "fechamento"] = 999_999.0

    class SpyParticipant:
        def __init__(self) -> None:
            self.observed_closes: list[list[float]] = []

        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            self.observed_closes.append(
                observation.history["PETR4"]["fechamento"].tolist()
            )
            return []

    participant = SpyParticipant()
    ExecutionEngine(participant, {"PETR4": data}, 1_000.0).run()

    assert participant.observed_closes == [[100.0], [100.0, 999_999.0]]


def test_intent_executa_na_proxima_abertura_e_trade_guarda_ticker() -> None:
    data = market_data()
    result = ExecutionEngine(
        BuyAndHoldParticipant("PETR4"), {"PETR4": data}, 1_000.0
    ).run()

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.ticker == "PETR4"
    assert trade.type == "BUY"
    assert trade.date == data.index[1]
    assert trade.price == 130.0
    assert trade.quantity == 7
    assert trade.cost == 0.0
    assert result.equity_curve.tolist() == [1_000.0, 1_070.0]


def test_intent_na_ultima_sessao_existe_mas_nao_gera_trade() -> None:
    data = market_data().iloc[:1]

    class RecordingParticipant:
        def __init__(self) -> None:
            self.delegate = BuyAndHoldParticipant("PETR4")
            self.intents: list[OrderIntent] = []

        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            self.intents = self.delegate.decide(observation)
            return self.intents

    participant = RecordingParticipant()
    result = ExecutionEngine(participant, {"PETR4": data}, 1_000.0).run()

    assert len(participant.intents) == 1
    assert participant.intents[0].eligible_execution_time is None
    assert result.trades == []
    assert result.final_equity == 1_000.0


def test_compra_aplica_custo_sobre_notional_e_preserva_caixa() -> None:
    data = market_data()
    data.loc[data.index[1], ["abertura", "fechamento"]] = 100.0
    result = ExecutionEngine(
        BuyAndHoldParticipant("PETR4"),
        {"PETR4": data},
        1_010.0,
        CostModel(tax_rate=0.01),
    ).run()

    trade = result.trades[0]
    cash = result.final_equity - trade.quantity * data["fechamento"].iloc[-1]
    assert trade.quantity == 10
    assert trade.cost == 10.0
    assert cash == 0.0
    assert result.final_equity == 1_000.0


@pytest.mark.parametrize("target_weight", [-0.1, 1.1])
def test_short_e_alavancagem_sao_rejeitados_explicitamente(
    target_weight: float,
) -> None:
    with pytest.raises(ValueError, match="shorting and leverage are not supported"):
        OrderIntent(
            ticker="PETR4",
            side="SELL",
            target_weight=target_weight,
            decision_time=cast(pd.Timestamp, pd.Timestamp("2023-01-02")),
            eligible_execution_time=cast(pd.Timestamp, pd.Timestamp("2023-01-03")),
        )


def test_execucao_e_deterministica() -> None:
    data = market_data()
    first = ExecutionEngine(
        BuyAndHoldParticipant("PETR4"), {"PETR4": data}, 1_000.0
    ).run()
    second = ExecutionEngine(
        BuyAndHoldParticipant("PETR4"), {"PETR4": data}, 1_000.0
    ).run()

    pd.testing.assert_series_equal(first.equity_curve, second.equity_curve)
    assert first.trades == second.trades
    assert first.final_equity == second.final_equity


def test_buy_and_hold_novo_tem_paridade_com_motor_legado() -> None:
    data = market_data()
    costs = CostModel(brokerage_fixed=1.0, tax_rate=0.01)

    legacy = BacktestEngine(BuyAndHold(), data, 1_000.0, costs).run()
    arena = ExecutionEngine(
        BuyAndHoldParticipant("PETR4"), {"PETR4": data}, 1_000.0, costs
    ).run()

    assert len(legacy.trades) == len(arena.trades) == 1
    legacy_trade = legacy.trades[0]
    arena_trade = arena.trades[0]
    assert arena_trade.date == legacy_trade.date
    assert arena_trade.price == legacy_trade.price == 130.0
    assert arena_trade.quantity == legacy_trade.quantity
    assert arena_trade.cost == legacy_trade.cost
    assert arena.final_equity == legacy.final_equity
