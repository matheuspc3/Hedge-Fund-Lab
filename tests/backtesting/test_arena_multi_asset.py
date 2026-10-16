"""Execução multi-ativo da arena: Equal Weight, Mínima Variância e alocação.

A política de alocação da arena difere do motor legado por construção: quando o
caixa não cobre todos os déficits, o legado atende os tickers em ordem
alfabética até acabar o dinheiro, enquanto a arena escalona todos os alvos pelo
mesmo fator. Os testes de paridade usam cenários sem disputa por caixa; a
divergência intencional tem teste próprio.
"""

import math
from typing import cast

import pandas as pd
import pytest

from src.backtesting.arena import (
    ExecutionEngine,
    MarketObservation,
    OrderIntent,
    weights_to_intents,
)
from src.backtesting.costs import CostModel
from src.backtesting.engine import Trade
from src.backtesting.portfolio import (
    EqualWeightParticipant,
    EqualWeightPortfolio,
    MinVarianceParticipant,
    MinVariancePortfolio,
    PortfolioBacktestEngine,
    PortfolioParticipant,
    PortfolioStrategy,
    PortfolioTrade,
)

SESSIONS = 12


def frame(closes: list[float]) -> pd.DataFrame:
    """``open(t+1)`` nunca coincide com ``close(t)``: o desconto de 2% garante isso."""
    return pd.DataFrame(
        {"abertura": [value * 0.98 for value in closes], "fechamento": closes},
        index=pd.bdate_range("2023-01-02", periods=len(closes)),
    )


def market() -> dict[str, pd.DataFrame]:
    return {
        "PETR4": frame([10.0, 10.6, 10.2, 11.1, 10.7, 11.4, 11.0, 12.2, 11.6, 12.5, 12.0, 13.1]),
        "VALE3": frame([50.0, 49.2, 50.4, 49.5, 51.0, 50.1, 51.8, 50.7, 52.4, 51.3, 53.0, 52.1]),
        "WEGE3": frame([30.0, 30.9, 31.5, 30.7, 32.1, 31.4, 33.0, 32.2, 33.8, 33.1, 34.7, 34.0]),
    }


def signature(trades: list[Trade] | list[PortfolioTrade]) -> list[tuple]:
    """Assinatura canônica, ordenada, comparável entre os dois motores."""
    return sorted(
        (str(trade.date), trade.ticker, trade.type, trade.price, trade.quantity, trade.cost)
        for trade in trades
    )


class StaticWeights(PortfolioStrategy):
    """Pesos fixos: isola a política de alocação da estimativa de pesos."""

    def __init__(self, weights: dict[str, float]):
        self.weights = weights

    def get_weights(self, data, current_date) -> dict[str, float]:
        return dict(self.weights)

    def get_name(self) -> str:
        return "Static Weights"


def cash_at(result, data: dict[str, pd.DataFrame], session: pd.Timestamp) -> float:
    """Caixa implícito: equity menos o valor das posições marcadas no fechamento."""
    positions: dict[str, int] = dict.fromkeys(data, 0)
    for trade in result.trades:
        if trade.date > session:
            continue
        ticker = cast(str, trade.ticker)
        positions[ticker] += trade.quantity if trade.type == "BUY" else -trade.quantity
    invested = sum(
        positions[ticker] * float(data[ticker].loc[session, "fechamento"])
        for ticker in data
    )
    return float(result.equity_curve.loc[session]) - invested


# ── Cadência e causalidade ───────────────────────────────────────


def test_equal_weight_rebalanceia_na_cadencia_do_motor_legado() -> None:
    data = market()
    participant = EqualWeightParticipant(rebalance_freq=4)
    sessions: list[pd.Timestamp] = []

    class Spy:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            intents = participant.decide(observation)
            if intents:
                sessions.append(observation.session)
            return intents

    ExecutionEngine(Spy(), data, 100_000.0).run()

    index = data["PETR4"].index
    assert sessions == [index[0], index[4], index[8]]


def test_equal_weight_distribui_um_enesimo_entre_os_ativos_observados() -> None:
    data = market()
    result = ExecutionEngine(EqualWeightParticipant(rebalance_freq=99), data, 90_000.0).run()

    first = data["PETR4"].index[1]
    invested = {
        cast(str, trade.ticker): trade.quantity * trade.price
        for trade in result.trades
        if trade.date == first
    }
    assert set(invested) == set(data)
    for notional in invested.values():
        assert notional == pytest.approx(30_000.0, rel=0.01)


def test_min_variance_nao_observa_retorno_posterior_a_decisao() -> None:
    """Reescrever o futuro não muda nenhum trade já executado."""
    data = market()
    tampered = {ticker: frame_.copy() for ticker, frame_ in data.items()}
    for ticker in tampered:
        tampered[ticker].iloc[7:] *= 40.0

    baseline = ExecutionEngine(
        MinVarianceParticipant(window=3, rebalance_freq=4), data, 100_000.0
    ).run()
    altered = ExecutionEngine(
        MinVarianceParticipant(window=3, rebalance_freq=4), tampered, 100_000.0
    ).run()

    cutoff = data["PETR4"].index[7]
    assert signature([t for t in baseline.trades if t.date < cutoff]) == signature(
        [t for t in altered.trades if t.date < cutoff]
    )
    assert baseline.equity_curve.iloc[:7].tolist() == altered.equity_curve.iloc[:7].tolist()


def test_participante_multi_ativo_nao_recebe_sessao_futura() -> None:
    data = market()
    seen: list[tuple[pd.Timestamp, tuple[int, ...]]] = []

    class Spy:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            seen.append(
                (
                    observation.session,
                    tuple(len(observation.history[t]) for t in sorted(data)),
                )
            )
            return []

    ExecutionEngine(Spy(), data, 100_000.0).run()

    # Cada histórico termina exatamente na sessão observada, em todos os tickers.
    for offset, (session, lengths) in enumerate(seen):
        assert session == data["PETR4"].index[offset]
        assert lengths == (offset + 1,) * len(data)


# ── Paridade com o motor multi-ativo legado ──────────────────────


@pytest.mark.parametrize(
    ("strategy", "participant"),
    [
        (
            lambda: EqualWeightPortfolio(4),
            lambda: EqualWeightParticipant(rebalance_freq=4),
        ),
        (
            lambda: MinVariancePortfolio(window=3),
            lambda: MinVarianceParticipant(window=3, rebalance_freq=4),
        ),
    ],
    ids=["equal-weight", "min-variance"],
)
def test_paridade_multi_ativo_sem_disputa_por_caixa(strategy, participant) -> None:
    """Sem custos, os alvos sempre cabem no caixa e os dois motores coincidem."""
    data = market()
    legacy = PortfolioBacktestEngine(strategy(), data, 100_000.0, rebalance_freq=4).run()
    arena = ExecutionEngine(participant(), data, 100_000.0).run()

    assert signature(arena.trades) == signature(legacy.trades)
    assert arena.final_equity == pytest.approx(legacy.final_equity, abs=1e-9)
    assert arena.equity_curve.tolist() == pytest.approx(legacy.equity_curve.tolist())


def test_paridade_multi_ativo_com_custos_e_folga_de_caixa() -> None:
    """Com alvo de 90% do patrimônio, os custos cabem na folga e não há disputa."""
    data = market()
    weights = {"PETR4": 0.3, "VALE3": 0.3, "WEGE3": 0.3}
    costs = CostModel(brokerage_fixed=2.0, spread_bps=15.0, tax_rate=0.0005)

    legacy = PortfolioBacktestEngine(
        StaticWeights(weights), data, 100_000.0, rebalance_freq=4, cost_model=costs
    ).run()
    arena = ExecutionEngine(
        PortfolioParticipant(StaticWeights(weights), rebalance_freq=4),
        data,
        100_000.0,
        costs,
    ).run()

    assert signature(arena.trades) == signature(legacy.trades)
    assert arena.final_equity == pytest.approx(legacy.final_equity, abs=1e-9)


def test_legado_privilegia_o_primeiro_ticker_quando_o_caixa_disputa() -> None:
    """Divergência intencional: o legado zera o caixa em ordem alfabética.

    Com pesos somando 1.0 e custos positivos, o dinheiro não cobre todos os
    alvos. O legado compra o máximo de ``PETR4``, depois ``VALE3``, e o último
    ticker fica sem o que sobrou. A arena escalona os três pelo mesmo fator.
    """
    data = market()
    weights = {"PETR4": 1 / 3, "VALE3": 1 / 3, "WEGE3": 1 / 3}
    costs = CostModel(spread_bps=50.0, tax_rate=0.01)

    legacy = PortfolioBacktestEngine(
        StaticWeights(weights), data, 100_000.0, rebalance_freq=99, cost_model=costs
    ).run()
    arena = ExecutionEngine(
        PortfolioParticipant(StaticWeights(weights), rebalance_freq=99),
        data,
        100_000.0,
        costs,
    ).run()

    first = data["PETR4"].index[1]
    legacy_notional = {
        t.ticker: t.quantity * t.price for t in legacy.trades if t.date == first
    }
    arena_notional = {
        cast(str, t.ticker): t.quantity * t.price
        for t in arena.trades
        if t.date == first
    }

    # O legado sacrifica o último ticker da ordem alfabética.
    assert legacy_notional["WEGE3"] < legacy_notional["PETR4"] * 0.99
    # A arena mantém os três alvos proporcionais entre si.
    assert max(arena_notional.values()) / min(arena_notional.values()) < 1.01


# ── Invariância de ordem dos tickers ─────────────────────────────


@pytest.mark.parametrize(
    "build",
    [
        lambda: EqualWeightParticipant(rebalance_freq=4),
        lambda: MinVarianceParticipant(window=3, rebalance_freq=4),
        lambda: PortfolioParticipant(
            StaticWeights({"PETR4": 0.5, "VALE3": 0.3, "WEGE3": 0.2}), rebalance_freq=4
        ),
    ],
    ids=["equal-weight", "min-variance", "static"],
)
def test_ordem_dos_tickers_nao_altera_o_resultado(build) -> None:
    """Mesmo dado, capital e custos: permutar o mapping não muda nada."""
    data = market()
    reversed_data = {ticker: data[ticker] for ticker in reversed(list(data))}
    costs = CostModel(brokerage_fixed=5.0, spread_bps=40.0, tax_rate=0.01)

    direct = ExecutionEngine(build(), data, 100_000.0, costs).run()
    permuted = ExecutionEngine(build(), reversed_data, 100_000.0, costs).run()

    assert list(reversed_data) != list(data)
    pd.testing.assert_series_equal(direct.equity_curve, permuted.equity_curve)
    assert signature(direct.trades) == signature(permuted.trades)
    assert direct.final_equity == permuted.final_equity
    assert sum(trade.cost for trade in direct.trades) == sum(
        trade.cost for trade in permuted.trades
    )


def test_execucao_multi_ativo_e_deterministica() -> None:
    data = market()
    costs = CostModel(brokerage_fixed=1.0, tax_rate=0.005)
    build = lambda: MinVarianceParticipant(window=3, rebalance_freq=3)  # noqa: E731

    first = ExecutionEngine(build(), data, 100_000.0, costs).run()
    second = ExecutionEngine(build(), data, 100_000.0, costs).run()

    pd.testing.assert_series_equal(first.equity_curve, second.equity_curve)
    assert signature(first.trades) == signature(second.trades)


# ── Política de alocação, caixa e custos ─────────────────────────


def test_compras_insuficientes_sao_escalonadas_proporcionalmente() -> None:
    """Com caixa para ~metade dos alvos, os dois ativos encolhem juntos.

    Abertura 9,80 e 19,60; alvo cheio de 51 e 25 ações. Um imposto de 100%
    dobra o desembolso, então nem metade dos alvos cabe em R$ 1.000. O motor
    legado gasta tudo no primeiro ticker da ordem alfabética e deixa o segundo
    zerado; a arena reduz os dois pelo mesmo fator.
    """
    data = {"PETR4": frame([10.0, 10.0, 10.0]), "VALE3": frame([20.0, 20.0, 20.0])}
    weights = {"PETR4": 0.5, "VALE3": 0.5}
    costs = CostModel(tax_rate=1.0)

    arena = ExecutionEngine(
        PortfolioParticipant(StaticWeights(weights), rebalance_freq=99),
        data,
        1_000.0,
        costs,
    ).run()
    legacy = PortfolioBacktestEngine(
        StaticWeights(weights), data, 1_000.0, rebalance_freq=99, cost_model=costs
    ).run()

    assert {cast(str, t.ticker): t.quantity for t in arena.trades} == {
        "PETR4": 26,
        "VALE3": 12,
    }
    assert {t.ticker: t.quantity for t in legacy.trades} == {"PETR4": 51}


def test_vendas_financiam_as_compras_do_mesmo_rebalance() -> None:
    """Trocar toda a carteira exige que a venda preceda a compra."""
    data = {"PETR4": frame([10.0, 10.0, 10.0]), "VALE3": frame([20.0, 20.0, 20.0])}
    plan = [{"PETR4": 1.0, "VALE3": 0.0}, {"PETR4": 0.0, "VALE3": 1.0}]

    class Rotating:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            index = list(data["PETR4"].index).index(observation.session)
            if index >= len(plan):
                return []
            return weights_to_intents(observation, plan[index])

    result = ExecutionEngine(Rotating(), data, 1_000.0).run()

    last = data["PETR4"].index[2]
    rebalance = [trade for trade in result.trades if trade.date == last]
    assert [trade.type for trade in rebalance] == ["SELL", "BUY"]
    assert rebalance[0].ticker == "PETR4"
    assert rebalance[1].ticker == "VALE3"
    assert rebalance[1].quantity == 51  # 1.000 reais / 19,60 na abertura


@pytest.mark.parametrize(
    "costs",
    [
        CostModel(),
        CostModel(brokerage_fixed=12.0, spread_bps=80.0, tax_rate=0.02),
    ],
)
def test_caixa_nunca_fica_negativo_em_nenhuma_sessao(costs: CostModel) -> None:
    data = market()
    result = ExecutionEngine(
        MinVarianceParticipant(window=3, rebalance_freq=3), data, 8_000.0, costs
    ).run()

    for session in result.equity_curve.index:
        assert cash_at(result, data, cast(pd.Timestamp, session)) >= -1e-9


def test_custos_de_rebalance_vem_do_cost_model_por_ticker() -> None:
    data = market()
    costs = CostModel(brokerage_fixed=3.0, spread_bps=20.0, tax_rate=0.001)
    result = ExecutionEngine(
        EqualWeightParticipant(rebalance_freq=4), data, 100_000.0, costs
    ).run()

    assert any(trade.type == "SELL" for trade in result.trades)
    for trade in result.trades:
        notional = trade.quantity * trade.price
        expected = (
            costs.apply_buy(notional)
            if trade.type == "BUY"
            else costs.apply_sell(notional)
        )
        assert trade.cost == expected
        assert trade.ticker in data


# ── Validação de pesos alvo e do calendário ──────────────────────


@pytest.mark.parametrize("weight", [-0.2, 1.5, math.nan, math.inf])
def test_peso_alvo_invalido_e_rejeitado_no_intent(weight: float) -> None:
    with pytest.raises(ValueError, match="target_weight must be finite"):
        OrderIntent(
            ticker="PETR4",
            target_weight=weight,
            decision_time=cast(pd.Timestamp, pd.Timestamp("2023-01-02")),
        )


@pytest.mark.parametrize("weight", [-1e-6, math.nan, math.inf])
def test_participante_de_portfolio_rejeita_peso_invalido(weight: float) -> None:
    data = market()
    participant = PortfolioParticipant(
        StaticWeights({"PETR4": weight, "VALE3": 0.5, "WEGE3": 0.5}), rebalance_freq=99
    )

    with pytest.raises(ValueError, match="must be finite|shorting is not supported"):
        ExecutionEngine(participant, data, 100_000.0).run()


def test_soma_de_pesos_acima_de_um_e_rejeitada() -> None:
    data = market()
    participant = PortfolioParticipant(
        StaticWeights({"PETR4": 0.5, "VALE3": 0.5, "WEGE3": 0.5}), rebalance_freq=99
    )

    with pytest.raises(ValueError, match="sum to at most 1"):
        ExecutionEngine(participant, data, 100_000.0).run()


def test_residuo_numerico_negativo_e_zerado_sem_normalizacao_silenciosa() -> None:
    weights = PortfolioParticipant._sanitize({"PETR4": -1e-15, "VALE3": 0.5})

    assert weights == {"PETR4": 0.0, "VALE3": 0.5}


def test_calendario_comum_usa_a_intersecao_sem_fabricar_barras() -> None:
    data = market()
    trimmed = {
        "PETR4": data["PETR4"],
        "VALE3": data["VALE3"].drop(index=data["VALE3"].index[3]),
        "WEGE3": data["WEGE3"].iloc[:-2],
    }
    engine = ExecutionEngine(EqualWeightParticipant(rebalance_freq=4), trimmed, 100_000.0)

    expected = data["PETR4"].index.drop(data["PETR4"].index[3])[: SESSIONS - 3]
    assert list(engine.sessions) == list(expected)
    assert len(engine.run().equity_curve) == len(expected)


def test_tickers_sem_sessao_comum_sao_rejeitados() -> None:
    data = market()
    shifted = data["VALE3"].copy()
    shifted.index = shifted.index + pd.Timedelta(days=365)

    with pytest.raises(ValueError, match="no session shared by every ticker"):
        ExecutionEngine(
            EqualWeightParticipant(), {"PETR4": data["PETR4"], "VALE3": shifted}, 100_000.0
        )
