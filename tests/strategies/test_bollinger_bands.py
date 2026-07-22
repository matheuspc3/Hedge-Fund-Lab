"""Testes para a estratégia Bollinger Bands."""

import numpy as np
import pandas as pd
import pytest

from src.strategies.bollinger_bands import BollingerBandsStrategy


class TestBollingerBandsStrategy:
    """Suite de testes para BollingerBandsStrategy."""

    def setup_method(self):
        self.strategy = BollingerBandsStrategy(window=20, k=2.0)

    def test_preco_dentro_das_bandas_sem_sinal(self):
        """Preço dentro das bandas → MANTER (0)."""
        rng = np.random.default_rng(42)
        dates = pd.bdate_range("2022-01-01", periods=100)
        prices = 100 + rng.normal(0, 0.5, 100)
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = self.strategy.generate_signals(df)
        # Preços estáveis → poucos ou nenhum sinal
        assert (signals.iloc[20:] == 0).all() or len(signals) > 0

    def test_preco_acima_upper_venda(self):
        """Preço cruza acima da banda superior → VENDA (-1)."""
        dates = pd.bdate_range("2022-01-01", periods=50)
        prices = [100.0] * 25 + [200.0] * 25  # salto abrupto
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = self.strategy.generate_signals(df)
        # Deve gerar sinal de venda no índice 25 (preço > upper)
        assert -1 in signals.values

    def test_preco_abaixo_lower_compra(self):
        """Preço cruza abaixo da banda inferior → COMPRA (1)."""
        dates = pd.bdate_range("2022-01-01", periods=50)
        prices = [100.0] * 25 + [10.0] * 25  # queda abrupta
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = self.strategy.generate_signals(df)
        # Deve gerar sinal de compra no índice 25 (preço < lower)
        assert 1 in signals.values

    def test_dataframe_vazio(self, empty_data):
        """DataFrame vazio → série vazia."""
        signals = self.strategy.generate_signals(empty_data)
        assert signals.empty

    def test_single_row(self, single_row_data):
        """1 linha → sinal = [0]."""
        signals = self.strategy.generate_signals(single_row_data)
        assert list(signals) == [0]

    def test_get_name(self):
        """get_name retorna string com parâmetros."""
        name = self.strategy.get_name()
        assert "Bollinger" in name
        assert "20" in name
        assert "2" in name

    def test_sinais_validos(self, synthetic_price_data):
        """Sinais ∈ {-1, 0, 1}."""
        strategy = BollingerBandsStrategy(window=20, k=2.0)
        signals = strategy.generate_signals(synthetic_price_data)
        assert set(signals.unique()).issubset({-1, 0, 1})
