"""Testes para o indicador SMA."""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.indicators.sma import sma


class TestSMA:
    """Suite de testes para a função sma()."""

    def test_sma_valores_conhecidos(self):
        """SMA de [1,2,3,4,5] com window=3 → [NaN, NaN, 2, 3, 4]."""
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        resultado = sma(series, window=3)
        esperado = pd.Series([np.nan, np.nan, 2.0, 3.0, 4.0])
        pd.testing.assert_series_equal(resultado, esperado)

    def test_sma_serie_constante(self):
        """SMA de série constante = a própria série."""
        series = pd.Series([5.0] * 10)
        resultado = sma(series, window=3)
        esperado = pd.Series([np.nan, np.nan] + [5.0] * 8)
        pd.testing.assert_series_equal(resultado, esperado)

    def test_sma_window_1(self):
        """SMA com window=1 = a própria série."""
        series = pd.Series([1.0, 2.0, 3.0])
        resultado = sma(series, window=1)
        pd.testing.assert_series_equal(resultado, series)

    def test_sma_window_maior_que_serie(self):
        """SMA com window > len(series) → tudo NaN."""
        series = pd.Series([1.0, 2.0, 3.0])
        resultado = sma(series, window=10)
        assert resultado.isna().all()

    def test_sma_window_zero_raise(self):
        """SMA com window=0 → ValueError."""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="window must be > 0"):
            sma(series, window=0)

    def test_sma_window_negativo_raise(self):
        """SMA com window negativo → ValueError."""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="window must be > 0"):
            sma(series, window=-1)

    def test_sma_serie_vazia(self):
        """SMA de série vazia → série vazia."""
        series = pd.Series([], dtype=float)
        resultado = sma(series, window=3)
        assert resultado.empty

    def test_sma_valor_exato(self):
        """Verifica cálculo manual: [10, 20, 30] window=2 → [NaN, 15, 25]."""
        series = pd.Series([10.0, 20.0, 30.0])
        resultado = sma(series, window=2)
        esperado = pd.Series([np.nan, 15.0, 25.0])
        pd.testing.assert_series_equal(resultado, esperado)

    # ── Property-based tests ───────────────────────────────────

    @given(
        values=st.lists(
            st.floats(min_value=1, max_value=1000, allow_nan=False),
            min_size=1,
            max_size=50,
        ),
        window=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50)
    def test_sma_property_mediana(self, values, window):
        """Property: SMA(window=n) de série constante C = C."""
        series = pd.Series([values[0]] * len(values))
        resultado = sma(series, window=min(window, len(values)))
        # Após o warm-up, todos os valores devem ser iguais a C
        validos = resultado.dropna()
        if not validos.empty:
            assert (validos == values[0]).all()
