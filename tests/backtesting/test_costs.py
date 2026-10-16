"""Testes para o modelo de custos de transação."""

import pytest

from src.backtesting.costs import CostModel


class TestCostModel:
    """Suite de testes para CostModel."""

    def test_custo_zero(self):
        """CostModel tudo zero → custo = 0."""
        model = CostModel(brokerage_fixed=0.0, spread_bps=0.0, tax_rate=0.0)
        assert model.apply_buy(1000.0) == 0.0
        assert model.apply_sell(1000.0) == 0.0

    def test_brokerage_fixa_compra(self):
        """brokerage_fixed = 10 → compra de R$ 1000 custa R$ 10."""
        model = CostModel(brokerage_fixed=10.0, spread_bps=0.0, tax_rate=0.0)
        assert model.apply_buy(1000.0) == 10.0

    def test_brokerage_fixa_venda(self):
        """brokerage_fixed = 10 → venda de R$ 1000 custa R$ 10."""
        model = CostModel(brokerage_fixed=10.0, spread_bps=0.0, tax_rate=0.0)
        assert model.apply_sell(1000.0) == 10.0

    def test_spread_50bps(self):
        """spread_bps = 50 → compra de R$ 1000 custa R$ 5 (0.5%)."""
        model = CostModel(brokerage_fixed=0.0, spread_bps=50.0, tax_rate=0.0)
        assert model.apply_buy(1000.0) == 5.0
        assert model.apply_sell(1000.0) == 5.0

    def test_tax_rate_003pct(self):
        """tax_rate = 0.03% → compra de R$ 1000 custa R$ 0.30."""
        model = CostModel(brokerage_fixed=0.0, spread_bps=0.0, tax_rate=0.0003)
        assert model.apply_buy(1000.0) == 0.30
        assert abs(model.apply_sell(1000.0) - 0.30) < 1e-10

    def test_custos_combinados(self):
        """Todos os custos juntos: brokerage + spread + tax."""
        model = CostModel(brokerage_fixed=5.0, spread_bps=30.0, tax_rate=0.0003)
        # spread: 1000 * 0.003 = 3.0
        # tax: 1000 * 0.0003 = 0.30
        # brokerage: 5.0
        # total: 8.30
        custo = model.apply_buy(1000.0)
        assert abs(custo - 8.30) < 1e-10

    def test_trade_value_zero(self):
        """trade_value = 0 → custo = brokerage_fixed apenas."""
        model = CostModel(brokerage_fixed=5.0, spread_bps=30.0, tax_rate=0.0003)
        assert model.apply_buy(0.0) == 5.0
        assert model.apply_sell(0.0) == 5.0

    def test_trade_value_negativo_raise(self):
        """trade_value negativo → ValueError."""
        model = CostModel()
        with pytest.raises(ValueError, match="trade_value must be >= 0"):
            model.apply_buy(-100.0)
        with pytest.raises(ValueError, match="trade_value must be >= 0"):
            model.apply_sell(-100.0)

    def test_brokerage_negativo_raise(self):
        """brokerage_fixed negativo → ValueError."""
        with pytest.raises(ValueError, match="brokerage_fixed must be >= 0"):
            CostModel(brokerage_fixed=-1.0)

    def test_spread_negativo_raise(self):
        """spread_bps negativo → ValueError."""
        with pytest.raises(ValueError, match="spread_bps must be >= 0"):
            CostModel(spread_bps=-1.0)

    def test_tax_rate_negativo_raise(self):
        """tax_rate negativo → ValueError."""
        with pytest.raises(ValueError, match="tax_rate must be >= 0"):
            CostModel(tax_rate=-0.01)

    def test_total_cost_property(self):
        """Property: custo total >= brokerage_fixed."""
        model = CostModel(brokerage_fixed=5.0, spread_bps=10.0, tax_rate=0.001)
        custo = model.apply_buy(500.0)
        assert custo >= 5.0

    def test_compra_venda_mesmo_valor(self):
        """Compra e venda com mesmo valor devem ter mesmo custo (simétrico)."""
        model = CostModel(brokerage_fixed=5.0, spread_bps=20.0, tax_rate=0.0003)
        assert model.apply_buy(2000.0) == model.apply_sell(2000.0)

    def test_quantidade_maxima_reserva_custos(self):
        model = CostModel(brokerage_fixed=1.0, tax_rate=0.01)

        quantity = model.max_affordable_quantity(cash=1_000.0, price=100.0)

        notional = quantity * 100.0
        assert quantity == 9
        assert notional + model.apply_buy(notional) <= 1_000.0
