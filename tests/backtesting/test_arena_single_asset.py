"""Migração de SMA Cross e Bandas de Bollinger para o contrato comum da arena.

Os preços sintéticos mantêm ``close(t) != open(t+1)`` em toda sessão, de modo
que qualquer execução feita no fechamento da própria decisão apareceria como
divergência de preço, e não apenas de valor final.
"""

from typing import cast

import pandas as pd
import pytest

from src.backtesting.arena import ExecutionEngine, MarketObservation, OrderIntent
from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestEngine, Trade
from src.strategies.bollinger_bands import BollingerBandsStrategy, BollingerParticipant
from src.strategies.sma_cross import SMACross, SMACrossParticipant

TICKER = "PETR4"


def frame(closes: list[float], opens: list[float]) -> pd.DataFrame:
    assert len(closes) == len(opens)
    return pd.DataFrame(
        {"abertura": opens, "fechamento": closes},
        index=pd.bdate_range("2023-01-02", periods=len(closes)),
    )


def sma_data() -> pd.DataFrame:
    """Warm-up, golden cross, death cross e um segundo ciclo completo."""
    return frame(
        closes=[20.0, 18.0, 16.0, 14.0, 30.0, 32.0, 10.0, 8.0, 30.0, 31.0],
        opens=[21.0, 19.0, 17.0, 15.0, 28.0, 33.0, 11.0, 9.0, 28.0, 34.0],
    )


def bollinger_data() -> pd.DataFrame:
    """Rompimento inferior, rompimento superior e novo rompimento inferior."""
    closes = [10.0, 10.2, 9.9, 10.1, 8.0, 9.0, 9.5, 12.5, 10.0, 9.8, 7.0, 9.0]
    return frame(closes=closes, opens=[value + 0.5 for value in closes])


def signature(trades: list[Trade]) -> list[tuple]:
    return [
        (trade.date, trade.type, trade.price, trade.quantity, trade.cost)
        for trade in trades
    ]


def sma_participant() -> SMACrossParticipant:
    return SMACrossParticipant(TICKER, fast_window=2, slow_window=3)


def bollinger_participant() -> BollingerParticipant:
    return BollingerParticipant(TICKER, window=3, k=1.0)


# ── SMA Cross ────────────────────────────────────────────────────


def test_sma_nao_decide_durante_o_warm_up() -> None:
    data = sma_data()
    participant = sma_participant()
    decisions = []

    for size in range(1, len(data) + 1):
        history = data.iloc[:size]
        decisions.append(
            participant.decide(
                MarketObservation(
                    session=cast(pd.Timestamp, history.index[-1]),
                    history={TICKER: history},
                    positions={TICKER: 0},
                    cash=1_000.0,
                    equity=1_000.0,
                )
            )
        )

    # slow_window=3: as três primeiras sessões não têm média lenta anterior.
    assert decisions[:4] == [[], [], [], []]
    assert [intent.target_weight for batch in decisions for intent in batch] == [
        1.0,
        0.0,
        1.0,
    ]


def test_sma_entra_sai_e_reentra_na_abertura_seguinte() -> None:
    data = sma_data()
    result = ExecutionEngine(sma_participant(), {TICKER: data}, 1_000.0).run()

    assert [(trade.date, trade.type, trade.price) for trade in result.trades] == [
        (data.index[5], "BUY", 33.0),
        (data.index[7], "SELL", 9.0),
        (data.index[9], "BUY", 34.0),
    ]


def test_sma_mantem_posicao_sem_repetir_trade() -> None:
    """Um segundo golden cross sem saída no meio não gera nova compra.

    As médias se encostam em ``t=6`` sem cruzar para baixo, então ``t=7`` volta
    a ser golden cross com a posição ainda aberta. O motor legado descarta a
    ordem porque já está comprado; o participante nem chega a emiti-la.
    """
    data = frame(
        closes=[20.0, 18.0, 16.0, 14.0, 30.0, 25.0, 35.0, 40.0, 41.0],
        opens=[21.0, 19.0, 17.0, 15.0, 28.0, 24.0, 33.0, 38.0, 42.0],
    )
    participant = sma_participant()
    result = ExecutionEngine(participant, {TICKER: data}, 1_000.0).run()
    legacy = BacktestEngine(
        SMACross(fast_window=2, slow_window=3), data, 1_000.0
    ).run()

    assert [trade.type for trade in result.trades] == ["BUY"]
    assert signature(result.trades) == signature(legacy.trades)


def test_sma_ultima_decisao_nao_encontra_abertura() -> None:
    """O cruzamento da última sessão vira intenção, nunca trade."""
    data = sma_data().iloc[:5]
    participant = sma_participant()
    intents: list[list[OrderIntent]] = []

    class Spy:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            batch = participant.decide(observation)
            intents.append(batch)
            return batch

    result = ExecutionEngine(Spy(), {TICKER: data}, 1_000.0).run()

    assert intents[-1] and intents[-1][0].target_weight == 1.0
    assert intents[-1][0].decision_time == data.index[-1]
    assert result.trades == []
    assert result.final_equity == 1_000.0


def test_sma_so_observa_historico_ate_t() -> None:
    """Alterar o futuro não muda nenhuma decisão já tomada."""
    data = sma_data()
    tampered = data.copy()
    tampered.iloc[6:] = 1_000_000.0

    baseline = ExecutionEngine(sma_participant(), {TICKER: data}, 1_000.0).run()
    altered = ExecutionEngine(sma_participant(), {TICKER: tampered}, 1_000.0).run()

    assert signature(baseline.trades)[:1] == signature(altered.trades)[:1]
    assert baseline.equity_curve.iloc[:6].tolist() == altered.equity_curve.iloc[:6].tolist()


@pytest.mark.parametrize(
    "costs",
    [CostModel(), CostModel(brokerage_fixed=1.5, spread_bps=10.0, tax_rate=0.005)],
)
def test_sma_tem_paridade_com_motor_legado(costs: CostModel) -> None:
    data = sma_data()
    legacy = BacktestEngine(SMACross(fast_window=2, slow_window=3), data, 1_000.0, costs)
    arena = ExecutionEngine(sma_participant(), {TICKER: data}, 1_000.0, costs)

    legacy_result = legacy.run()
    arena_result = arena.run()

    assert signature(arena_result.trades) == signature(legacy_result.trades)
    assert arena_result.final_equity == legacy_result.final_equity
    pd.testing.assert_series_equal(
        arena_result.equity_curve, legacy_result.equity_curve
    )


# ── Bollinger Bands ──────────────────────────────────────────────


def test_bollinger_nao_decide_antes_de_duas_bandas_validas() -> None:
    data = bollinger_data()
    participant = bollinger_participant()

    for size in range(1, 5):
        history = data.iloc[:size]
        assert (
            participant.decide(
                MarketObservation(
                    session=cast(pd.Timestamp, history.index[-1]),
                    history={TICKER: history},
                    positions={TICKER: 0},
                    cash=1_000.0,
                    equity=1_000.0,
                )
            )
            == []
        )


def test_bollinger_executa_ciclos_na_abertura_seguinte() -> None:
    data = bollinger_data()
    result = ExecutionEngine(bollinger_participant(), {TICKER: data}, 1_000.0).run()

    assert [(trade.date, trade.type, trade.price) for trade in result.trades] == [
        (data.index[5], "BUY", 9.5),
        (data.index[8], "SELL", 10.5),
        (data.index[11], "BUY", 9.5),
    ]


def test_bollinger_mantem_posicao_entre_rompimentos() -> None:
    data = bollinger_data()
    participant = bollinger_participant()
    ExecutionEngine(participant, {TICKER: data}, 1_000.0).run()

    # Três mudanças de alvo em doze sessões: as demais mantêm sem novo trade.
    assert participant._target_weight == 1.0


def test_bollinger_ultima_decisao_nao_encontra_abertura() -> None:
    data = bollinger_data().iloc[:11]
    result = ExecutionEngine(bollinger_participant(), {TICKER: data}, 1_000.0).run()

    # O rompimento inferior acontece na última sessão do recorte.
    assert [trade.type for trade in result.trades] == ["BUY", "SELL"]


def test_bollinger_so_observa_historico_ate_t() -> None:
    data = bollinger_data()
    tampered = data.copy()
    tampered.iloc[6:] = 1_000_000.0

    baseline = ExecutionEngine(bollinger_participant(), {TICKER: data}, 1_000.0).run()
    altered = ExecutionEngine(bollinger_participant(), {TICKER: tampered}, 1_000.0).run()

    assert signature(baseline.trades)[:1] == signature(altered.trades)[:1]
    assert (
        baseline.equity_curve.iloc[:6].tolist() == altered.equity_curve.iloc[:6].tolist()
    )


@pytest.mark.parametrize(
    "costs",
    [CostModel(), CostModel(brokerage_fixed=2.0, spread_bps=25.0, tax_rate=0.003)],
)
def test_bollinger_tem_paridade_com_motor_legado(costs: CostModel) -> None:
    data = bollinger_data()
    legacy = BacktestEngine(
        BollingerBandsStrategy(window=3, k=1.0), data, 1_000.0, costs
    ).run()
    arena = ExecutionEngine(
        bollinger_participant(), {TICKER: data}, 1_000.0, costs
    ).run()

    assert signature(arena.trades) == signature(legacy.trades)
    assert arena.final_equity == legacy.final_equity
    pd.testing.assert_series_equal(arena.equity_curve, legacy.equity_curve)


# ── Invariantes comuns ───────────────────────────────────────────


@pytest.mark.parametrize(
    ("build", "data"),
    [(sma_participant, sma_data()), (bollinger_participant, bollinger_data())],
)
def test_participantes_single_asset_sao_deterministicos(build, data) -> None:
    costs = CostModel(brokerage_fixed=1.0, tax_rate=0.01)
    first = ExecutionEngine(build(), {TICKER: data}, 5_000.0, costs).run()
    second = ExecutionEngine(build(), {TICKER: data}, 5_000.0, costs).run()

    pd.testing.assert_series_equal(first.equity_curve, second.equity_curve)
    assert signature(first.trades) == signature(second.trades)


@pytest.mark.parametrize(
    ("build", "data"),
    [(sma_participant, sma_data()), (bollinger_participant, bollinger_data())],
)
def test_participantes_single_asset_nunca_deixam_caixa_negativo(build, data) -> None:
    costs = CostModel(brokerage_fixed=3.0, spread_bps=50.0, tax_rate=0.01)
    result = ExecutionEngine(build(), {TICKER: data}, 900.0, costs).run()

    position = 0
    for session, equity in result.equity_curve.items():
        for trade in result.trades:
            if trade.date == session:
                position += trade.quantity if trade.type == "BUY" else -trade.quantity
        cash = equity - position * float(data.loc[session, "fechamento"])
        assert cash >= -1e-9
