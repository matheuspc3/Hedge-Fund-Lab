"""Testes para o indicador MACD."""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.indicators.macd import macd


class TestMACD:
    """Suite de testes para a função macd()."""

    def test_macd_constante(self):
        """Série constante → MACD = 0, Signal = 0, Histograma = 0."""
        series = pd.Series([100.0] * 50)
        macd_line, signal_line, histogram = macd(series)
        # Últimos valores (após convergência) devem ser ~0
        assert abs(macd_line.iloc[-1]) < 1e-10
        assert abs(signal_line.iloc[-1]) < 1e-10
        assert abs(histogram.iloc[-1]) < 1e-10

    def test_macd_crescente(self):
        """Série crescente → MACD positivo."""
        series = pd.Series(np.linspace(100, 200, 100))
        macd_line, _, _ = macd(series)
        assert macd_line.iloc[-1] > 0

    def test_macd_decrescente(self):
        """Série decrescente → MACD negativo."""
        series = pd.Series(np.linspace(200, 100, 100))
        macd_line, _, _ = macd(series)
        assert macd_line.iloc[-1] < 0

    def test_macd_fast_ge_slow_raise(self):
        """fast >= slow → ValueError."""
        series = pd.Series(range(50), dtype=float)
        with pytest.raises(ValueError, match="fast.*must be < slow"):
            macd(series, fast=26, slow=12)

    def test_macd_fast_eq_slow_raise(self):
        """fast == slow → ValueError."""
        series = pd.Series(range(50), dtype=float)
        with pytest.raises(ValueError, match="fast.*must be < slow"):
            macd(series, fast=12, slow=12)

    def test_macd_serie_vazia(self):
        """Série vazia → tuplas vazias."""
        series = pd.Series([], dtype=float)
        macd_line, signal_line, histogram = macd(series)
        assert macd_line.empty and signal_line.empty and histogram.empty

    def test_macd_serie_curta(self):
        """Série muito curta → valores NaN (não quebra)."""
        series = pd.Series([100.0, 101.0])
        macd_line, signal_line, histogram = macd(series)
        assert not macd_line.isna().all()  # EMA funciona com 2 pontos

    # ── Property-based ─────────────────────────────────────────

    @given(
        values=st.lists(st.floats(min_value=1, max_value=1000, allow_nan=False), min_size=30, max_size=200),
    )
    @settings(max_examples=50)
    def test_macd_histograma_consistente(self, values):
        """Property: histograma = macd_line - signal_line."""
        series = pd.Series(values)
        macd_line, signal_line, histogram = macd(series)
        # Para valores válidos, histograma = macd - signal
        mask = macd_line.notna() & signal_line.notna()
        if mask.any():
            diff = (histogram[mask] - (macd_line[mask] - signal_line[mask])).abs()
            assert (diff < 1e-10).all()
