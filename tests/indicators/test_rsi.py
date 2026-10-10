"""Testes para o indicador RSI (suavização canônica de Wilder)."""

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.indicators.rsi import RSI_NO_MOVEMENT, rsi

# Fonte primária VERIFICADA em 2026-10-04: planilha ``cs-rsi.xls`` anexada à
# página "Relative Strength Index (RSI)" da StockCharts ChartSchool
# (chartschool.stockcharts.com/.../relative-strength-index-rsi), autor
# Art Hill, salva em 2010-06-22, SHA-256
# 20c0d922322f4c0c900b9c378d82219cb323c2f11897c2399e9c0605bcec61a5.
# Aba "RSI": coluna "QQQQ Close" (33 fechamentos, linhas 1-33) e coluna
# "14-day RSI" (linhas 15-33), lidas célula a célula com ``xlrd``. Os
# fechamentos abaixo são idênticos aos da planilha; o RSI é o valor da célula
# em precisão completa. Tolerância 1e-9 (diferença medida: 1.4e-14).
REFERENCE_CLOSES = [
    44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245,
    45.8433, 46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028,
    46.0328, 46.4116, 46.2222, 45.6439, 46.2122, 46.2521, 45.7137, 46.4515,
    45.7835, 45.3548, 44.0288, 44.1783, 44.2181, 44.5672, 43.4205, 42.6628,
    43.1314,
]  # fmt: skip
REFERENCE_RSI_14 = [
    70.53278948369497, 66.31856180517232, 66.54982993552764, 69.40630533884433,
    66.3551690562718, 57.97485571430819, 62.929606754597, 63.25714756254528,
    56.05929871526324, 62.37707144318042, 54.70757308126129, 50.4227744114564,
    39.989823145376604, 41.46048197570564, 41.86891609254328, 45.46321244528675,
    37.30404208985967, 33.07952299438848, 37.77295211443486,
]  # fmt: skip


def wilder_loop(closes: list[float], period: int) -> list[float]:
    """Wilder escrito como laço explícito: a definição, sem truque vetorial."""
    deltas = [b - a for a, b in zip(closes, closes[1:])]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out = [math.nan] * period

    def value() -> float:
        total = avg_gain + avg_loss
        return RSI_NO_MOVEMENT if total == 0 else 100.0 * avg_gain / total

    out.append(value())
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((period - 1) * avg_gain + gain) / period
        avg_loss = ((period - 1) * avg_loss + loss) / period
        out.append(value())
    return out


class TestRSI:
    """Suite de testes para a função rsi()."""

    def test_reproduz_a_planilha_da_stockcharts(self):
        resultado = rsi(pd.Series(REFERENCE_CLOSES), period=14)
        assert resultado.iloc[:14].isna().all()
        assert np.allclose(resultado.iloc[14:], REFERENCE_RSI_14, rtol=0, atol=1e-9)

    @pytest.mark.parametrize("position", [0, 5, 25, 32], ids=["inicio", "semente", "meio", "fim"])
    def test_nan_no_preco_e_recusado(self, position):
        """NaN não encolhe a semente nem repete o RSI anterior: falha."""
        closes = pd.Series(REFERENCE_CLOSES)
        closes.iloc[position] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            rsi(closes, period=14)

    def test_equivale_ao_laco_explicito_de_wilder(self):
        """A semente simples é o que separa Wilder de um ``ewm`` cru."""
        steps = np.arange(300, dtype=float)
        closes = 100 * np.exp(
            np.cumsum(0.01 * np.sin(steps / 2.3) + 0.002 * np.cos(steps / 7.1))
        )
        for period in (2, 14, 30):
            esperado = wilder_loop(closes.tolist(), period)
            obtido = rsi(pd.Series(closes), period=period).tolist()
            assert np.allclose(obtido, esperado, rtol=0, atol=1e-10, equal_nan=True)

    def test_ewm_cru_nao_e_wilder(self):
        """Prova de que a inicialização importa: o ``ewm`` cru diverge."""
        closes = pd.Series(REFERENCE_CLOSES)
        delta = closes.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        loss = (-delta).clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        cru = 100 * gain / (gain + loss)
        assert abs(cru.iloc[14] - rsi(closes).iloc[14]) > 1.0

    def test_warmup_fica_nan(self):
        resultado = rsi(pd.Series(range(1, 31), dtype=float), period=14)
        assert resultado.iloc[:14].isna().all()
        assert resultado.iloc[14:].notna().all()

    def test_sem_perdas_e_100(self):
        resultado = rsi(pd.Series(range(1, 101), dtype=float), period=14)
        assert (resultado.dropna() == 100.0).all()

    def test_sem_ganhos_e_0(self):
        resultado = rsi(pd.Series(range(100, 0, -1), dtype=float), period=14)
        assert (resultado.dropna() == 0.0).all()

    def test_nunca_passa_de_100_por_arredondamento(self):
        """Contraexemplo achado pelo Hypothesis: ``(100·G)/G`` > 100 em float."""
        resultado = rsi(pd.Series([1.0] * 19 + [329.19935413158794]), period=1)
        assert resultado.max() == 100.0

    def test_sem_ganhos_nem_perdas_e_neutro(self):
        resultado = rsi(pd.Series([50.0] * 30), period=14)
        assert (resultado.dropna() == RSI_NO_MOVEMENT).all()

    def test_rsi_period_zero_raise(self):
        series = pd.Series(range(20), dtype=float)
        with pytest.raises(ValueError, match="period must be > 0"):
            rsi(series, period=0)

    def test_rsi_period_negativo_raise(self):
        series = pd.Series(range(20), dtype=float)
        with pytest.raises(ValueError, match="period must be > 0"):
            rsi(series, period=-5)

    def test_rsi_serie_vazia(self):
        assert rsi(pd.Series([], dtype=float)).empty

    def test_rsi_dados_insuficientes(self):
        """Menos variações que o period: nenhum valor é inventado."""
        resultado = rsi(pd.Series([1.0, 2.0, 3.0]), period=14)
        assert resultado.isna().all()

    # ── Property-based ─────────────────────────────────────────

    @given(
        values=st.lists(
            st.floats(min_value=0.01, max_value=1000, allow_nan=False),
            min_size=20,
            max_size=200,
        ),
        period=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50)
    def test_rsi_range(self, values, period):
        """Property: RSI sempre ∈ [0, 100] para qualquer entrada."""
        resultado = rsi(pd.Series(values), period=period).dropna()
        assert (resultado >= 0.0).all()
        assert (resultado <= 100.0).all()
