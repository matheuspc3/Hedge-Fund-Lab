"""Provas do contrato incremental da arena e da migração do Buy & Hold."""

from collections.abc import Mapping
from dataclasses import fields
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


def extended_market_data() -> pd.DataFrame:
    """``market_data`` com uma terceira sessão, para variar o horizonte."""
    dates = pd.DatetimeIndex(["2023-01-02", "2023-01-03", "2023-01-04"])
    return pd.DataFrame(
        {"abertura": [90.0, 130.0, 150.0], "fechamento": [100.0, 140.0, 160.0]},
        index=dates,
    )


def standalone_observation(data: pd.DataFrame) -> MarketObservation:
    return MarketObservation(
        session=cast(pd.Timestamp, data.index[-1]),
        history=MappingProxyType({"PETR4": data.copy()}),
        positions=MappingProxyType({"PETR4": 0}),
        cash=1_000.0,
        equity=1_000.0,
    )


def normalize(value: object) -> object:
    if isinstance(value, pd.DataFrame):
        return (value.index.tolist(), value.to_dict("list"))
    if isinstance(value, Mapping):
        return {key: normalize(item) for key, item in value.items()}
    return value


def observation_snapshot(observation: MarketObservation) -> dict[str, object]:
    """Captura todo o contrato entregue ao participante, campo a campo."""
    return {
        field.name: normalize(getattr(observation, field.name))
        for field in fields(MarketObservation)
    }


class SpyParticipant:
    """Registra tudo o que o contrato entrega e ainda opera como Buy & Hold."""

    def __init__(self) -> None:
        self.delegate = BuyAndHoldParticipant("PETR4")
        self.snapshots: list[dict[str, object]] = []
        self.intents: list[list[OrderIntent]] = []

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        self.snapshots.append(observation_snapshot(observation))
        intents = self.delegate.decide(observation)
        self.intents.append(intents)
        return intents


def test_buy_and_hold_emite_intent_apenas_na_primeira_observacao() -> None:
    data = market_data()
    participant = BuyAndHoldParticipant("PETR4")

    first = participant.decide(standalone_observation(data.iloc[:1]))
    second = participant.decide(standalone_observation(data))

    assert first == [
        OrderIntent(
            ticker="PETR4",
            target_weight=1.0,
            decision_time=cast(pd.Timestamp, data.index[0]),
        )
    ]
    assert second == []


def test_observacao_expoe_somente_campos_de_t() -> None:
    assert {field.name for field in fields(MarketObservation)} == {
        "session",
        "history",
        "positions",
        "cash",
        "equity",
    }


def test_intent_nao_declara_sessao_futura() -> None:
    assert {field.name for field in fields(OrderIntent)} == {
        "ticker",
        "target_weight",
        "decision_time",
    }


def test_observacao_nao_revela_o_fim_do_recorte() -> None:
    """A última barra de um recorte é indistinguível da mesma barra no meio."""
    data = extended_market_data()

    short_horizon = SpyParticipant()
    ExecutionEngine(short_horizon, {"PETR4": data.iloc[:2]}, 1_000.0).run()
    long_horizon = SpyParticipant()
    ExecutionEngine(long_horizon, {"PETR4": data}, 1_000.0).run()

    assert len(short_horizon.snapshots) == 2
    assert len(long_horizon.snapshots) == 3
    # A sessão 2023-01-03 encerra o recorte curto e é intermediária no longo;
    # se algum campo denunciasse o horizonte, os contratos divergiriam aqui.
    assert short_horizon.snapshots == long_horizon.snapshots[:2]


def test_participant_recebe_somente_historico_observavel() -> None:
    data = market_data()
    data.loc[data.index[1], "fechamento"] = 999_999.0

    class ClosesSpy:
        def __init__(self) -> None:
            self.observed_closes: list[list[float]] = []

        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            self.observed_closes.append(
                observation.history["PETR4"]["fechamento"].tolist()
            )
            return []

    participant = ClosesSpy()
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

    participant = SpyParticipant()
    result = ExecutionEngine(participant, {"PETR4": data}, 1_000.0).run()

    # O participante decide normalmente; quem descobre que não existe abertura
    # seguinte é o executor.
    assert len(participant.intents) == 1
    assert len(participant.intents[0]) == 1
    assert participant.intents[0][0].decision_time == data.index[0]
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
            target_weight=target_weight,
            decision_time=cast(pd.Timestamp, pd.Timestamp("2023-01-02")),
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


# ── A direção pertence à execução, não ao participante ───────────


class ScriptedTargets:
    """Participante que só sabe declarar onde quer estar em cada sessão."""

    def __init__(self, targets: list[float]) -> None:
        self.targets = targets
        self.observed_weights: list[float] = []

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        index = len(self.observed_weights)
        close = float(observation.history["PETR4"]["fechamento"].iloc[-1])
        self.observed_weights.append(
            observation.positions["PETR4"] * close / observation.equity
        )
        if index >= len(self.targets):
            return []
        return [
            OrderIntent(
                ticker="PETR4",
                target_weight=self.targets[index],
                decision_time=observation.session,
            )
        ]


def gap_data(third_open: float) -> pd.DataFrame:
    """Duas sessões estáveis e uma terceira que abre com gap configurável."""
    return pd.DataFrame(
        {
            "abertura": [10.0, 10.0, third_open],
            "fechamento": [10.0, 10.0, third_open],
        },
        index=pd.DatetimeIndex(["2023-01-02", "2023-01-03", "2023-01-04"]),
    )


@pytest.mark.parametrize(
    ("third_open", "expected_type", "expected_quantity"),
    [(10.0, "BUY", 10), (30.0, "SELL", 10)],
    ids=["sem-gap", "gap-de-alta"],
)
def test_gap_overnight_inverte_a_operacao_sem_mudar_a_intencao(
    third_open: float, expected_type: str, expected_quantity: int
) -> None:
    """A mesma intenção vira compra ou venda conforme a abertura de ``t+1``.

    Em ambos os cenários o participante emite exatamente os mesmos alvos: 0,5
    na primeira sessão e 0,6 na segunda. Em ``close(t)`` o alvo de 0,6 está
    acima do peso observado de 0,5, ou seja, implicaria aumentar a posição. Com
    a abertura estável, é isso que acontece. Com o gap de alta, as 50 ações
    passam a valer 75% do patrimônio na abertura e chegar a 0,6 exige vender.
    O participante não decidiu nada diferente — a direção é derivada do delta
    entre posição e quantidade alvo, no momento da execução.
    """
    data = gap_data(third_open)
    participant = ScriptedTargets([0.5, 0.6])

    result = ExecutionEngine(participant, {"PETR4": data}, 1_000.0).run()

    # Premissa: em close(t) o alvo apontava para aumento de posição.
    assert participant.observed_weights[1] == 0.5

    assert len(result.trades) == 2
    entry, adjustment = result.trades
    assert (entry.type, entry.quantity, entry.price) == ("BUY", 50, 10.0)
    assert adjustment.date == data.index[2]
    assert adjustment.price == third_open
    assert adjustment.type == expected_type
    assert adjustment.quantity == expected_quantity


def test_intencao_ja_no_alvo_na_abertura_nao_gera_trade() -> None:
    """Alvo repetido sem variação de preço não produz operação nenhuma."""
    data = gap_data(10.0)
    result = ExecutionEngine(
        ScriptedTargets([0.5, 0.5]), {"PETR4": data}, 1_000.0
    ).run()

    assert [(trade.type, trade.quantity) for trade in result.trades] == [("BUY", 50)]
