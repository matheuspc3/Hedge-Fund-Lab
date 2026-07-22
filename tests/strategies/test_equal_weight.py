"""Testes para a estratégia Equal Weight."""

import pandas as pd
import pytest

from src.strategies.equal_weight import EqualWeight


class TestEqualWeight:
    """Suite de testes para EqualWeight."""

    def setup_method(self):
        self.strategy = EqualWeight(rebalance_freq=63)

    def test_sinal_compra_no_primeiro_dia(self, synthetic_clean_data):
        """Sinal = 1 no T0."""
        signals = self.strategy.generate_signals(synthetic_clean_data)
        assert signals.iloc[0] == 1

    def test_rebalanceamento_trimestral(self):
        """Rebalanceamento a cada rebalance_freq dias."""
        dates = pd.bdate_range("2023-01-01", periods=200)
        df = pd.DataFrame({"fechamento": range(200)}, index=dates)
        signals = self.strategy.generate_signals(df)
        # Dias de rebalanceamento: 0, 63, 126, 189
        for i in [0, 63, 126, 189]:
            if i < len(signals):
                assert signals.iloc[i] == 1, f"Falhou no índice {i}"

    def test_sem_rebalanceamento_entre_datas(self):
        """Entre rebalanceamentos, sinal = 0."""
        dates = pd.bdate_range("2023-01-01", periods=70)
        df = pd.DataFrame({"fechamento": range(70)}, index=dates)
        signals = self.strategy.generate_signals(df)
        # Entre T0 e T63, só T0 tem sinal
        for i in range(1, 63):
            if i < len(signals):
                assert signals.iloc[i] == 0, f"Falhou no índice {i}"

    def test_dataframe_vazio(self, empty_data):
        """DataFrame vazio → série vazia."""
        signals = self.strategy.generate_signals(empty_data)
        assert signals.empty

    def test_single_row(self, single_row_data):
        """1 linha → sinal = [1]."""
        signals = self.strategy.generate_signals(single_row_data)
        assert list(signals) == [1]

    def test_sem_coluna_fechamento(self):
        """Sem coluna fechamento → ValueError."""
        df = pd.DataFrame({"preco": [100.0]})
        with pytest.raises(ValueError, match="fechamento"):
            self.strategy.generate_signals(df)

    def test_get_name(self):
        """get_name retorna string."""
        assert isinstance(self.strategy.get_name(), str)
        assert "Equal" in self.strategy.get_name()

    def test_sinais_validos(self, synthetic_clean_data):
        """Sinais ∈ {0, 1}."""
        signals = self.strategy.generate_signals(synthetic_clean_data)
        assert set(signals.unique()).issubset({0, 1})
