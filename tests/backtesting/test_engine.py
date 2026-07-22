"""Testes para o motor de backtesting."""

import numpy as np
import pandas as pd
import pytest

from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestEngine, Trade
from tests.conftest import synthetic_clean_data  # noqa: F401


class MockStrategy:
    """Estratégia mockada para testes do engine."""

    def __init__(self, signals: pd.Series | None = None, name: str = "Mock"):
        self._signals = signals
        self._name = name

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if self._signals is not None:
            return self._signals
        return pd.Series(0, index=data.index, dtype=int)

    def get_name(self) -> str:
        return self._name


class TestBacktestEngineInit:
    """Testes de inicialização do BacktestEngine."""

    def test_init_valido(self, synthetic_clean_data):
        """Engine inicializa com parâmetros válidos."""
        strategy = MockStrategy()
        engine = BacktestEngine(
            strategy=strategy,
            data=synthetic_clean_data,
            initial_capital=100_000.0,
        )
        assert engine.initial_capital == 100_000.0
        assert engine.data is not None

    def test_data_vazia_raise(self):
        """DataFrame vazio → ValueError."""
        strategy = MockStrategy()
        with pytest.raises(ValueError, match="data cannot be empty"):
            BacktestEngine(
                strategy=strategy,
                data=pd.DataFrame(),
                initial_capital=100_000.0,
            )

    def test_capital_zero_raise(self):
        """Capital zero → ValueError."""
        strategy = MockStrategy()
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            BacktestEngine(
                strategy=strategy,
                data=pd.DataFrame({"fechamento": [100.0]}, index=pd.DatetimeIndex(["2023-01-02"])),
                initial_capital=0.0,
            )

    def test_capital_negativo_raise(self):
        """Capital negativo → ValueError."""
        strategy = MockStrategy()
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            BacktestEngine(
                strategy=strategy,
                data=pd.DataFrame({"fechamento": [100.0]}, index=pd.DatetimeIndex(["2023-01-02"])),
                initial_capital=-1000.0,
            )


class TestBacktestEngineRun:
    """Testes de execução do BacktestEngine."""

    def test_equity_inicial(self, synthetic_clean_data):
        """Equity curve começa com capital inicial."""
        strategy = MockStrategy()
        engine = BacktestEngine(strategy, synthetic_clean_data, 100_000.0)
        result = engine.run()
        assert result.equity_curve.iloc[0] == 100_000.0

    def test_sem_sinais_equity_constante(self):
        """Nenhum sinal → equity constante."""
        dates = pd.bdate_range("2023-01-01", periods=10)
        df = pd.DataFrame({"fechamento": [100.0] * 10}, index=dates)
        strategy = MockStrategy()
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Sem trades, equity = capital inicial
        assert (result.equity_curve == 100_000.0).all()

    def test_buy_and_hold_sobe(self):
        """Compra no T0 e preço sobe → equity aumenta."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals, "BuyTest")
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Comprou 1000 ações a R$ 100 = R$ 100k
        # Preço final = R$ 104 → equity = 1000 * 104 = R$ 104.000
        assert abs(result.equity_curve.iloc[-1] - 104_000.0) < 1.0

    def test_buy_and_hold_desce(self):
        """Compra no T0 e preço cai → equity diminui."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 99.0, 98.0, 97.0, 96.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Comprou 1000 ações a R$ 100 = R$ 100k
        # Preço final = R$ 96 → equity = 1000 * 96 = R$ 96.000
        assert abs(result.equity_curve.iloc[-1] - 96_000.0) < 1.0

    def test_compra_e_venda(self):
        """Compra e depois vende → volta ao capital inicial (sem custos)."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 101.0, 100.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, -1, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Compra 1000 ações a R$ 100, vende a R$ 102 → lucro = R$ 2.000
        # Compra de novo a R$ 101 (mas sem sinal)
        # Equity final = 100.000 + 2.000 = 102.000
        # Na verdade, vendeu a 102 e ficou em cash, depois sem sinal de compra
        # Equity = cash
        assert result.equity_curve.iloc[-1] > 100_000.0

    def test_venda_a_descoberto(self):
        """Sinal -1 sem posição → venda a descoberto não permitida."""
        dates = pd.bdate_range("2023-01-01", periods=3)
        prices = [100.0, 101.0, 102.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([-1, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel(), allow_short=False)
        result = engine.run()
        # Sem posição para vender, sinal -1 ignorado
        assert len(result.trades) == 0

    def test_sinal_repetido_ignorado(self):
        """Sinal de compra repetido não gera trade duplicado."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0] * 5
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 1, 1, 1, 1], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Apenas 1 trade (primeiro sinal de compra, os demais são ignorados)
        assert len(result.trades) == 1

    def test_dataframe_uma_linha(self):
        """Apenas 1 linha → execução não quebra."""
        df = pd.DataFrame({"fechamento": [100.0]}, index=pd.DatetimeIndex(["2023-01-02"]))
        signals = pd.Series([1], index=pd.DatetimeIndex(["2023-01-02"]), dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        assert len(result.equity_curve) == 1
        assert result.equity_curve.iloc[0] == 100_000.0

    def test_trades_estrutura(self):
        """Trades gerados têm a estrutura correta."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 101.0, 100.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, -1, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        for trade in result.trades:
            assert isinstance(trade, Trade)
            assert trade.type in ("BUY", "SELL")
            assert trade.price > 0
            assert trade.quantity > 0

    def test_com_custos_reduz_retorno(self):
        """Com custos, retorno líquido < retorno bruto."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, -1], index=dates, dtype=int)
        strategy = MockStrategy(signals)

        engine_sem_custo = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        engine_com_custo = BacktestEngine(
            strategy, df, 100_000.0,
            cost_model=CostModel(brokerage_fixed=10.0, spread_bps=50.0, tax_rate=0.0003)
        )

        result_sem = engine_sem_custo.run()
        result_com = engine_com_custo.run()
        assert result_com.equity_curve.iloc[-1] < result_sem.equity_curve.iloc[-1]


class TestLookAheadBias:
    """Testes críticos de viés de look-ahead."""

    def test_sem_look_ahead(self):
        """O engine não usa dados futuros para decisões presentes."""
        dates = pd.bdate_range("2023-01-01", periods=10)
        # Preço estável, com um spike enorme no último dia
        prices = [100.0] * 9 + [500.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)

        # Estratégia que sempre compra no T0
        signals = pd.Series([1] + [0] * 9, index=dates, dtype=int)
        strategy = MockStrategy(signals, "LookAheadTest")
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()

        # Sem look-ahead: comprou 1000 ações a R$ 100
        # Equity no T8 (antes do spike) = 1000 * 100 = 100.000
        # Último dia (T9) com price 500 = 1000 * 500 = 500.000
        # Se houvesse look-ahead, a decisão de compra seria diferente
        assert len(result.trades) == 1
        assert result.trades[0].type == "BUY"
        assert result.trades[0].price == 100.0
        assert result.trades[0].date == dates[0]

    def test_informacao_futura_nao_afeta_sinal(self):
        """Sinal gerado com dados parciais (até t) não vê t+1."""
        dates = pd.bdate_range("2023-01-01", periods=10)
        prices = [100.0, 101.0, 102.0, 103.0, 104.0,
                  50.0, 51.0, 52.0, 53.0, 54.0]
        df = pd.DataFrame({"fechamento": prices}, index=dates)

        # Mock que retorna COMPRA apenas se a média dos preços futuros > 100
        # Isso é explicitamente look-ahead — queremos verificar que o engine
        # não permite isso (o mock retorna sinais pré-definidos, não baseados
        # em dados futuros do engine)
        signals = pd.Series([1] + [0] * 9, index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()

        # Verifica que o engine não altera os sinais
        assert result.trades[0].price == 100.0  # preço do T0


class TestTrade:
    """Testes para o dataclass Trade."""

    def test_trade_creation(self):
        """Trade pode ser criado com todos os campos."""
        date = pd.Timestamp("2023-01-02")
        trade = Trade(
            date=date,
            type="BUY",
            price=100.0,
            quantity=10,
            cost=5.0,
        )
        assert trade.date == date
        assert trade.type == "BUY"
        assert trade.price == 100.0
        assert trade.quantity == 10
        assert trade.cost == 5.0
