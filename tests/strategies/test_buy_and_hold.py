"""Testes para a estratégia Buy and Hold."""

import pandas as pd
import pytest

from src.strategies.buy_and_hold import BuyAndHold


class TestBuyAndHold:
    """Suite de testes para BuyAndHold."""

    def setup_method(self):
        self.strategy = BuyAndHold()

    def test_sinal_compra_no_primeiro_dia(self, synthetic_clean_data):
        """Sinal = 1 no T0, 0 no resto."""
        signals = self.strategy.generate_signals(synthetic_clean_data)
        assert signals.iloc[0] == 1
        assert (signals.iloc[1:] == 0).all()

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
        assert "Buy" in self.strategy.get_name()

    def test_determinismo(self, synthetic_clean_data):
        """Mesma entrada → mesma saída."""
        s1 = self.strategy.generate_signals(synthetic_clean_data)
        s2 = self.strategy.generate_signals(synthetic_clean_data)
        pd.testing.assert_series_equal(s1, s2)

    def test_sinais_validos(self, synthetic_clean_data):
        """Sinais ∈ {0, 1}."""
        signals = self.strategy.generate_signals(synthetic_clean_data)
        assert set(signals.unique()).issubset({0, 1})
