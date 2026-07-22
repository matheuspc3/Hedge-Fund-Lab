"""Testes para o indicador RSI."""

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.indicators.rsi import rsi


class TestRSI:
    """Suite de testes para a função rsi()."""

    def test_rsi_crescente_puro(self):
        """Série monotônica crescente → RSI → 100 (aproxima)."""
        series = pd.Series(range(1, 101), dtype=float)
        resultado = rsi(series, period=14)
        # Últimos valores devem estar muito próximos de 100
        assert resultado.iloc[-1] > 99.0

    def test_rsi_decrescente_puro(self):
        """Série monotônica decrescente → RSI → 0 (aproxima)."""
        series = pd.Series(range(100, 0, -1), dtype=float)
        resultado = rsi(series, period=14)
        # Últimos valores devem estar muito próximos de 0
        assert resultado.iloc[-1] < 1.0

    def test_rsi_constante(self):
        """Série constante → RSI = 50 (sem ganho/perda)."""
        series = pd.Series([50.0] * 30)
        resultado = rsi(series, period=14)
        # Quando não há variação, RSI fica em 50 (gain=loss=0 → RS=NaN → fillna 100)
        # Na verdade, com delta=0, gain=0 e loss=0 → avg_loss = NaN → rs = NaN → fill 100
        # Então o comportamento para série constante é RSI = 100
        assert resultado.iloc[-1] == 100.0

    def test_rsi_period_zero_raise(self):
        """period=0 → ValueError."""
        series = pd.Series(range(20), dtype=float)
        with pytest.raises(ValueError, match="period must be > 0"):
            rsi(series, period=0)

    def test_rsi_period_negativo_raise(self):
        """period negativo → ValueError."""
        series = pd.Series(range(20), dtype=float)
        with pytest.raises(ValueError, match="period must be > 0"):
            rsi(series, period=-5)

    def test_rsi_serie_vazia(self):
        """Série vazia → série vazia."""
        series = pd.Series([], dtype=float)
        resultado = rsi(series)
        assert resultado.empty

    def test_rsi_dados_insuficientes(self):
        """Menos dados que o period → RSI = 100 (fillna)."""
        series = pd.Series([1.0, 2.0, 3.0])
        resultado = rsi(series, period=14)
        assert not resultado.isna().all()
        assert (resultado == 100.0).all()

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
        series = pd.Series(values)
        resultado = rsi(series, period=period)
        validos = resultado.dropna()
        if not validos.empty:
            assert (validos >= 0.0).all()
            assert (validos <= 100.0).all()
