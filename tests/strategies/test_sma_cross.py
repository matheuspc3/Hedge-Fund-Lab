"""Testes para a estratégia SMA Cross."""

import numpy as np
import pandas as pd
import pytest

from src.strategies.sma_cross import SMACross


class TestSMACross:
    """Suite de testes para SMACross."""

    def setup_method(self):
        self.strategy = SMACross(fast_window=3, slow_window=10)

    def test_sem_cruzamento_sem_sinal(self):
        """Sem cruzamento → todos os sinais = 0 (após warm-up)."""
        dates = pd.bdate_range("2022-01-01", periods=50)
        # Série constante
        df = pd.DataFrame({"fechamento": [100.0] * 50}, index=dates)
        signals = self.strategy.generate_signals(df)
        assert (signals == 0).all()

    def test_golden_cross_compra(self):
        """SMA rápida cruza acima da lenta → sinal COMPRA (1)."""
        rng = np.random.default_rng(42)
        dates = pd.bdate_range("2022-01-01", periods=30)
        # Preços estáveis, depois sobem
        prices = list(np.full(15, 100.0)) + list(
            100.0 + np.cumsum(rng.uniform(0.5, 1.5, 15))
        )
        df = pd.DataFrame({"fechamento": prices}, index=dates)

        strategy = SMACross(fast_window=3, slow_window=10)
        signals = strategy.generate_signals(df)

        # Deve ter pelo menos 1 golden cross (compra)
        assert 1 in signals.values

    def test_death_cross_venda(self):
        """SMA rápida cruza abaixo da lenta → sinal VENDA (-1)."""
        dates = pd.bdate_range("2022-01-01", periods=30)
        prices = list(np.linspace(100, 150, 15)) + list(np.linspace(150, 100, 15))
        df = pd.DataFrame({"fechamento": prices}, index=dates)

        strategy = SMACross(fast_window=3, slow_window=10)
        signals = strategy.generate_signals(df)

        # Deve ter pelo menos 1 death cross (venda)
        assert -1 in signals.values

    def test_warmup_sma_lenta(self):
        """Antes do warm-up da SMA lenta, sinais = 0."""
        dates = pd.bdate_range("2022-01-01", periods=5)
        df = pd.DataFrame({"fechamento": range(100, 105)}, index=dates)
        strategy = SMACross(fast_window=3, slow_window=10)
        signals = strategy.generate_signals(df)
        # Apenas 5 dias, slow_window=10 → sem sinal
        assert (signals == 0).all()

    def test_dataframe_vazio(self, empty_data):
        """DataFrame vazio → série vazia."""
        signals = self.strategy.generate_signals(empty_data)
        assert signals.empty

    def test_fast_ge_slow_raise(self):
        """fast_window >= slow_window → ValueError."""
        with pytest.raises(ValueError, match="fast_window.*slow_window"):
            SMACross(fast_window=10, slow_window=5)

    def test_get_name(self):
        """get_name retorna o nome com parâmetros."""
        name = self.strategy.get_name()
        assert "SMA Cross" in name
        assert "3" in name
        assert "10" in name

    def test_sinais_validos(self, synthetic_price_data):
        """Sinais ∈ {-1, 0, 1}."""
        strategy = SMACross(fast_window=20, slow_window=50)
        signals = strategy.generate_signals(synthetic_price_data)
        assert set(signals.unique()).issubset({-1, 0, 1})
