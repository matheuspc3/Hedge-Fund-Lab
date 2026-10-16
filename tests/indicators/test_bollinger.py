"""Testes para o indicador Bollinger Bands."""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from src.indicators.bollinger import bollinger_bands


class TestBollingerBands:
    """Suite de testes para a função bollinger_bands()."""

    def test_bandas_dados_constantes(self):
        """Preço constante → middle = preço, upper = lower = middle (std=0)."""
        series = pd.Series([100.0] * 50)
        upper, middle, lower = bollinger_bands(series, window=20, k=2.0)
        # Após warm-up, middle = 100 e upper = lower = 100 (std=0)
        validos_middle = middle.dropna()
        assert (validos_middle == 100.0).all()
        validos_upper = upper.dropna()
        assert (validos_upper == 100.0).all()
        validos_lower = lower.dropna()
        assert (validos_lower == 100.0).all()

    def test_bandas_k_zero(self):
        """k=0 → upper = middle = lower."""
        series = pd.Series([100.0, 102.0, 101.0, 103.0, 99.0] * 10)
        upper, middle, lower = bollinger_bands(series, window=20, k=0.0)
        validos = middle.dropna()
        if not validos.empty:
            pd.testing.assert_series_equal(upper.dropna(), middle.dropna())
            pd.testing.assert_series_equal(lower.dropna(), middle.dropna())

    def test_k_negativo_raise(self):
        """k negativo → ValueError."""
        series = pd.Series([100.0] * 10)
        with pytest.raises(ValueError, match="k must be >= 0"):
            bollinger_bands(series, k=-1.0)

    def test_upper_acima_middle(self):
        """Para k>0, upper > middle > lower (após warm-up)."""
        series = pd.Series(np.random.default_rng(42).uniform(90, 110, 100))
        upper, middle, lower = bollinger_bands(series, window=20, k=2.0)
        validos = slice(20, None)
        assert (upper.iloc[validos] >= middle.iloc[validos]).all()
        assert (middle.iloc[validos] >= lower.iloc[validos]).all()

    def test_preco_acima_upper_sinal_venda(self):
        """Se preço > BB_upper, é sinal de venda (price saiu da banda)."""
        series = pd.Series([100.0] * 30 + [150.0] + [100.0] * 19)
        upper, middle, lower = bollinger_bands(series, window=20, k=2.0)
        # No índice 30, o preço (150) deve estar acima de upper
        assert not pd.isna(upper.iloc[30])
        if not pd.isna(upper.iloc[30]):
            assert 150.0 > upper.iloc[30]

    def test_preco_abaixo_lower_sinal_compra(self):
        """Se preço < BB_lower, é sinal de compra."""
        series = pd.Series([100.0] * 30 + [50.0] + [100.0] * 19)
        upper, middle, lower = bollinger_bands(series, window=20, k=2.0)
        if not pd.isna(lower.iloc[30]):
            assert 50.0 < lower.iloc[30]

    def test_serie_vazia(self):
        """Série vazia → todas as bandas vazias."""
        series = pd.Series([], dtype=float)
        upper, middle, lower = bollinger_bands(series)
        assert upper.empty and middle.empty and lower.empty

    # ── Property-based ─────────────────────────────────────────

    @given(
        values=st.lists(
            st.floats(min_value=1, max_value=1000, allow_nan=False),
            min_size=25,
            max_size=100,
        ),
        k=st.floats(min_value=0.5, max_value=5.0),
    )
    @settings(max_examples=50)
    def test_upper_ge_middle_ge_lower(self, values, k):
        """Property: para k>0, upper >= middle >= lower sempre."""
        series = pd.Series(values)
        upper, middle, lower = bollinger_bands(series, window=20, k=k)
        validos = slice(20, None)
        if upper.iloc[validos].notna().any():
            assert (upper.iloc[validos] >= middle.iloc[validos]).all()
            assert (middle.iloc[validos] >= lower.iloc[validos]).all()
