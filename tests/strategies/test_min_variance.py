"""Testes para a estratégia Mínima Variância."""

import numpy as np
import pandas as pd
import pytest

from src.strategies.min_variance import MinVariance


class TestMinVariance:
    """Suite de testes para MinVariance."""

    def setup_method(self):
        self.strategy = MinVariance(window=252, rebalance_freq=63)

    def test_sinal_compra_no_primeiro_dia(self, synthetic_clean_data):
        """Sinal = 1 no T0."""
        signals = self.strategy.generate_signals(synthetic_clean_data)
        assert signals.iloc[0] == 1

    def test_rebalanceamento_periodico(self):
        """Rebalanceamento a cada rebalance_freq dias (após warm-up)."""
        dates = pd.bdate_range("2022-01-01", periods=300)
        df = pd.DataFrame({"fechamento": range(300)}, index=dates)
        strategy = MinVariance(window=200, rebalance_freq=63)
        signals = strategy.generate_signals(df)
        # Dias de rebalanceamento: 0, 63, 126, 189, 252
        # Apenas 0 e 252 têm sinal (63, 126, 189 < window=200)
        assert signals.iloc[0] == 1
        assert signals.iloc[252] == 1
        # Antes do warm-up, rebalanceamentos são pulados
        for i in [63, 126, 189]:
            assert signals.iloc[i] == 0, f"Falhou no índice {i} (antes do warm-up)"

    def test_sem_rebalanceamento_antes_warmup(self):
        """Antes do warm-up, só o T0 tem sinal."""
        dates = pd.bdate_range("2022-01-01", periods=60)
        df = pd.DataFrame({"fechamento": range(60)}, index=dates)
        strategy = MinVariance(window=252, rebalance_freq=30)
        signals = strategy.generate_signals(df)
        # window=252 > 60 dados → só T0
        for i in range(1, len(signals)):
            assert signals.iloc[i] == 0, f"Falhou no índice {i}"

    def test_dataframe_vazio(self, empty_data):
        """DataFrame vazio → série vazia."""
        signals = self.strategy.generate_signals(empty_data)
        assert signals.empty

    def test_get_name(self):
        """get_name retorna string."""
        assert isinstance(self.strategy.get_name(), str)
        assert "Mínima" in self.strategy.get_name()

    def test_sinais_validos(self, synthetic_price_data):
        """Sinais ∈ {0, 1}."""
        strategy = MinVariance(window=100, rebalance_freq=50)
        signals = strategy.generate_signals(synthetic_price_data)
        assert set(signals.unique()).issubset({0, 1})

    def test_optimize_weights_2_ativos(self):
        """_optimize_weights com 2 ativos: pesos somam 1."""
        rng = np.random.default_rng(42)
        retornos = pd.DataFrame({
            "A": rng.normal(0.001, 0.02, 252),
            "B": rng.normal(0.001, 0.03, 252),
        })
        pesos = MinVariance._optimize_weights(retornos)
        assert len(pesos) == 2
        assert abs(pesos.sum() - 1.0) < 1e-6
