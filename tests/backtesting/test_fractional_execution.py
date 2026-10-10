"""Provas da semântica de execução científica em unidades fracionárias.

O que está sob teste não é conveniência numérica: ``floor()`` sobre uma série
de retorno total faz a quantidade depender do **nível** da série, e o nível
depende de proventos pagos depois da decisão. Removê-lo tira a última
dependência do futuro que restava dentro da execução — e, de quebra, elimina o
resíduo de caixa e o falso vínculo com ação física.

O modo inteiro continua existindo e continua sendo o default: os caminhos
legados dependem dele, e um deles é comparado byte a byte com a arena em
``test_arena*.py``.
"""

import math
import random
from typing import cast

import numpy as np
import pandas as pd
import pytest

from src.backtesting.arena import (
    CASH_TOLERANCE,
    QUANTITY_MODE_FRACTIONAL_NOTIONAL,
    QUANTITY_MODE_INTEGER_SHARES,
    ExecutionEngine,
    MarketObservation,
    OrderIntent,
)
from src.backtesting.costs import CostModel

TICKER = "PETR4"
CAPITAL = 100_000.0
SCALE = 3.8718
#: Tarifa do leilão de abertura da B3 na faixa de varejo (0,0320% por perna).
TAX = 0.00032


class FullyInvested:
    """Compra tudo na primeira decisão e mantém — o pior caso de caixa."""

    def __init__(self, weight: float = 1.0) -> None:
        self.weight = weight
        self._entered = False

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        if self._entered:
            return []
        self._entered = True
        return [
            OrderIntent(
                ticker=TICKER,
                target_weight=self.weight,
                decision_time=observation.session,
            )
        ]


class Rebalancer:
    """Persegue um peso alvo a cada sessão, forçando compras e vendas."""

    def __init__(self, weights: list[float]) -> None:
        self.weights = weights
        self._index = 0

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        weight = self.weights[self._index % len(self.weights)]
        self._index += 1
        return [
            OrderIntent(
                ticker=TICKER,
                target_weight=weight,
                decision_time=observation.session,
            )
        ]


def frame(scale: float = 1.0, periods: int = 40, seed: int = 7) -> pd.DataFrame:
    sessions = pd.bdate_range("2024-01-02", periods=periods)
    rng = np.random.default_rng(seed)
    close = 41.93 * np.cumprod(1.0 + rng.normal(0.0005, 0.018, periods))
    return pd.DataFrame(
        {"abertura": close * 0.997, "fechamento": close},
        index=sessions,
    ) * scale


def engine(
    participant: object,
    data: pd.DataFrame,
    *,
    capital: float = CAPITAL,
    costs: CostModel | None = None,
    mode: str = QUANTITY_MODE_FRACTIONAL_NOTIONAL,
) -> ExecutionEngine:
    return ExecutionEngine(
        cast(object, participant),  # type: ignore[arg-type]
        {TICKER: data},
        capital,
        costs if costs is not None else CostModel(tax_rate=TAX),
        quantity_mode=mode,
    )


# ── Peso exato e resíduo zero ────────────────────────────────────


def test_peso_alvo_integral_esgota_o_caixa_e_nao_deixa_residuo() -> None:
    """``w = 1`` com custo proporcional: caixa exatamente zero, peso exato 1.

    Este é o caso que a especificação ingênua — ``quantity = notional / open``
    sem escalonamento — não consegue executar: o alvo custa ``equity·(1+r)`` e
    estouraria o caixa. O escalonamento converge para ``1/(1+r)``.
    """
    data = frame()
    result = engine(FullyInvested(), data).run()

    compra = result.trades[0]
    assert not float(compra.quantity).is_integer(), "unidade fracionária esperada"

    preço = compra.price
    gasto = compra.quantity * preço + compra.cost
    assert gasto == pytest.approx(CAPITAL, abs=1e-6)

    # Caixa zerado: o patrimônio pós-execução é inteiramente posição.
    patrimônio = compra.quantity * preço
    assert patrimônio == pytest.approx(CAPITAL / (1.0 + TAX), rel=1e-12)
    assert compra.cost == pytest.approx(CAPITAL - patrimônio, rel=1e-9)


def test_modo_inteiro_continua_truncando_e_deixando_residuo() -> None:
    """O default legado não muda: quantidade inteira e caixa residual."""
    data = frame()
    result = engine(FullyInvested(), data, mode=QUANTITY_MODE_INTEGER_SHARES).run()

    compra = result.trades[0]
    assert float(compra.quantity).is_integer()
    assert compra.quantity == math.floor(CAPITAL / compra.price)


def test_modo_de_quantidade_desconhecido_e_recusado() -> None:
    with pytest.raises(ValueError, match="unsupported quantity_mode"):
        engine(FullyInvested(), frame(), mode="lote_padrao")


# ── Invariância de escala de preço ───────────────────────────────


def normalized(result) -> np.ndarray:
    return (result.equity_curve / result.equity_curve.iloc[0]).to_numpy()


def test_curva_normalizada_e_identica_sob_escala_de_preco() -> None:
    """FRACTIONAL EXECUTION: ``P`` e ``kP`` produzem a mesma curva relativa."""
    base = engine(FullyInvested(), frame()).run()
    scaled = engine(FullyInvested(), frame(SCALE)).run()

    assert np.allclose(normalized(base), normalized(scaled), rtol=1e-12, atol=0.0)
    assert scaled.final_equity == pytest.approx(base.final_equity, rel=1e-12)


def test_custos_relativos_sao_identicos_sob_escala_de_preco() -> None:
    base = engine(Rebalancer([1.0, 0.4, 0.9, 0.0]), frame()).run()
    scaled = engine(Rebalancer([1.0, 0.4, 0.9, 0.0]), frame(SCALE)).run()

    custo_base = sum(trade.cost for trade in base.trades)
    custo_scaled = sum(trade.cost for trade in scaled.trades)
    assert len(base.trades) == len(scaled.trades) > 3
    assert custo_scaled / CAPITAL == pytest.approx(custo_base / CAPITAL, rel=1e-12)

    for um, outro in zip(base.trades, scaled.trades):
        assert um.type == outro.type
        assert um.quantity * um.price == pytest.approx(
            outro.quantity * outro.price, rel=1e-12
        )


def test_modo_inteiro_nao_e_invariante_a_escala() -> None:
    """O contraponto que justifica o modo fracionário existir.

    Sob quantidade inteira a curva normalizada **muda** com o nível da série —
    e o nível de uma série ajustada é função de proventos posteriores à
    decisão. É este o vazamento que o modo científico fecha.
    """
    base = engine(
        FullyInvested(), frame(), mode=QUANTITY_MODE_INTEGER_SHARES
    ).run()
    scaled = engine(
        FullyInvested(), frame(SCALE), mode=QUANTITY_MODE_INTEGER_SHARES
    ).run()

    assert not np.allclose(normalized(base), normalized(scaled), rtol=1e-12, atol=0.0)


# ── Invariância de escala de capital ─────────────────────────────


def test_capital_e_apenas_escala_nominal_sem_corretagem_fixa() -> None:
    """CAPITAL SCALE INVARIANCE: com ``brokerage_fixed = 0`` o capital só escala.

    É esta homogeneidade que justifica R$100.000 como escala de apresentação —
    e não lote, mercado fracionário ou preço máximo, que deixaram de existir no
    modelo científico.
    """
    data = frame()
    pequeno = engine(Rebalancer([1.0, 0.3, 0.8]), data, capital=1_000.0).run()
    grande = engine(Rebalancer([1.0, 0.3, 0.8]), data, capital=1_000_000.0).run()

    assert np.allclose(normalized(pequeno), normalized(grande), rtol=1e-12, atol=0.0)


def test_corretagem_fixa_quebra_a_invariancia_de_capital() -> None:
    """O mesmo teste, ao contrário: a premissa é condicional e o teste a guarda."""
    data = frame()
    custos = CostModel(brokerage_fixed=12.5, tax_rate=TAX)
    pequeno = engine(
        Rebalancer([1.0, 0.3, 0.8]), data, capital=1_000.0, costs=custos
    ).run()
    grande = engine(
        Rebalancer([1.0, 0.3, 0.8]), data, capital=1_000_000.0, costs=custos
    ).run()

    assert not np.allclose(
        normalized(pequeno), normalized(grande), rtol=1e-12, atol=0.0
    )


# ── Pós-condições numéricas ──────────────────────────────────────


def test_caixa_nunca_fica_negativo_sob_pesos_e_custos_aleatorios() -> None:
    """NO NEGATIVE CASH: property-based sobre preço, peso e custo."""
    rng = random.Random(20260914)
    for caso in range(60):
        pesos = [rng.uniform(0.0, 1.0) for _ in range(5)]
        custos = CostModel(
            brokerage_fixed=rng.choice([0.0, 0.0, 5.0]),
            spread_bps=rng.uniform(0.0, 25.0),
            tax_rate=rng.uniform(0.0, 0.002),
        )
        data = frame(scale=rng.uniform(0.05, 50.0), periods=30, seed=caso)
        result = engine(Rebalancer(pesos), data, costs=custos).run()

        assert float(result.equity_curve.min()) > 0.0
        for trade in result.trades:
            assert math.isfinite(trade.quantity) and trade.quantity > 0
            assert math.isfinite(trade.cost) and trade.cost >= 0


def test_posicao_negativa_e_corrupcao_e_falha_fechado() -> None:
    """A pós-condição existe para falhar, não para decorar o código."""
    data = frame()
    motor = engine(FullyInvested(), data)
    with pytest.raises(RuntimeError, match="long-only"):
        motor._check_numbers(10.0, {TICKER: -1e-6}, cast(pd.Timestamp, data.index[0]))


def test_caixa_negativo_acima_da_tolerancia_e_corrupcao() -> None:
    data = frame()
    motor = engine(FullyInvested(), data)
    with pytest.raises(RuntimeError, match="cash turned negative"):
        motor._check_numbers(
            -CASH_TOLERANCE * 10, {TICKER: 1.0}, cast(pd.Timestamp, data.index[0])
        )


def test_residuo_de_ponto_flutuante_vira_zero_exato_no_modo_cientifico() -> None:
    data = frame()
    motor = engine(FullyInvested(), data)
    sessão = cast(pd.Timestamp, data.index[0])

    assert motor._check_numbers(-CASH_TOLERANCE / 10, {TICKER: 1.0}, sessão) == 0.0
    assert motor._check_numbers(CASH_TOLERANCE / 10, {TICKER: 1.0}, sessão) == 0.0
