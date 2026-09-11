"""Testes para o motor de backtesting."""

import pandas as pd
import pytest

from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestEngine, Trade


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
                data=pd.DataFrame(
                    {"abertura": [100.0], "fechamento": [100.0]},
                    index=pd.DatetimeIndex(["2023-01-02"]),
                ),
                initial_capital=0.0,
            )

    def test_capital_negativo_raise(self):
        """Capital negativo → ValueError."""
        strategy = MockStrategy()
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            BacktestEngine(
                strategy=strategy,
                data=pd.DataFrame(
                    {"abertura": [100.0], "fechamento": [100.0]},
                    index=pd.DatetimeIndex(["2023-01-02"]),
                ),
                initial_capital=-1000.0,
            )

    def test_exige_preco_de_abertura(self):
        data = pd.DataFrame(
            {"fechamento": [100.0]}, index=pd.DatetimeIndex(["2023-01-02"])
        )
        with pytest.raises(ValueError, match="abertura"):
            BacktestEngine(MockStrategy(), data, 1_000.0)

    def test_short_incompleto_e_rejeitado_explicitamente(self, synthetic_clean_data):
        with pytest.raises(ValueError, match="short policy"):
            BacktestEngine(
                MockStrategy(), synthetic_clean_data, 1_000.0, allow_short=True
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
        df = pd.DataFrame(
            {"abertura": [100.0] * 10, "fechamento": [100.0] * 10}, index=dates
        )
        strategy = MockStrategy()
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Sem trades, equity = capital inicial
        assert (result.equity_curve == 100_000.0).all()

    def test_buy_and_hold_sobe(self):
        """Compra no T0 e preço sobe → equity aumenta."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals, "BuyTest")
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Sinal em T0, compra 990 ações na abertura de T1 a R$ 101.
        assert result.equity_curve.iloc[-1] == pytest.approx(102_970.0)

    def test_buy_and_hold_desce(self):
        """Compra no T0 e preço cai → equity diminui."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 99.0, 98.0, 97.0, 96.0]
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Sinal em T0, compra 1010 ações na abertura de T1 a R$ 99.
        assert result.equity_curve.iloc[-1] == pytest.approx(96_970.0)

    def test_compra_e_venda(self):
        """Compra e depois vende → volta ao capital inicial (sem custos)."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0, 101.0, 102.0, 101.0, 100.0]
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, -1, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Compra e venda ocorrem nas aberturas seguintes aos sinais.
        assert result.trades[0].price == 101.0
        assert result.trades[1].price == 101.0
        assert result.equity_curve.iloc[-1] == 100_000.0

    def test_venda_a_descoberto(self):
        """Sinal -1 sem posição → venda a descoberto não permitida."""
        dates = pd.bdate_range("2023-01-01", periods=3)
        prices = [100.0, 101.0, 102.0]
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([-1, 0, 0], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(
            strategy, df, 100_000.0, cost_model=CostModel(), allow_short=False
        )
        result = engine.run()
        # Sem posição para vender, sinal -1 ignorado
        assert len(result.trades) == 0

    def test_sinal_repetido_ignorado(self):
        """Sinal de compra repetido não gera trade duplicado."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        prices = [100.0] * 5
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([1, 1, 1, 1, 1], index=dates, dtype=int)
        strategy = MockStrategy(signals)
        engine = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        result = engine.run()
        # Apenas 1 trade (primeiro sinal de compra, os demais são ignorados)
        assert len(result.trades) == 1

    def test_dataframe_uma_linha(self):
        """Apenas 1 linha → execução não quebra."""
        df = pd.DataFrame(
            {"abertura": [100.0], "fechamento": [100.0]},
            index=pd.DatetimeIndex(["2023-01-02"]),
        )
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
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
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
        df = pd.DataFrame({"abertura": prices, "fechamento": prices}, index=dates)
        signals = pd.Series([1, 0, 0, 0, -1], index=dates, dtype=int)
        strategy = MockStrategy(signals)

        engine_sem_custo = BacktestEngine(strategy, df, 100_000.0, cost_model=CostModel())
        engine_com_custo = BacktestEngine(
            strategy,
            df,
            100_000.0,
            cost_model=CostModel(brokerage_fixed=10.0, spread_bps=50.0, tax_rate=0.0003),
        )

        result_sem = engine_sem_custo.run()
        result_com = engine_com_custo.run()
        assert result_com.equity_curve.iloc[-1] < result_sem.equity_curve.iloc[-1]


class TestLookAheadBias:
    """Testes críticos de viés de look-ahead."""

    def test_sinal_no_fechamento_executa_na_proxima_abertura(self):
        dates = pd.bdate_range("2023-01-01", periods=2)
        data = pd.DataFrame(
            {"abertura": [90.0, 130.0], "fechamento": [100.0, 140.0]},
            index=dates,
        )
        signals = pd.Series([1, 0], index=dates, dtype=int)

        result = BacktestEngine(MockStrategy(signals), data, 1_000.0).run()

        assert len(result.trades) == 1
        assert result.trades[0].price == 130.0
        assert result.trades[0].date == dates[1]
        assert result.equity_curve.tolist() == [1_000.0, 1_070.0]

    def test_ultimo_sinal_sem_proxima_abertura_nao_executa(self):
        dates = pd.bdate_range("2023-01-01", periods=2)
        data = pd.DataFrame(
            {"abertura": [90.0, 130.0], "fechamento": [100.0, 140.0]},
            index=dates,
        )
        signals = pd.Series([0, 1], index=dates, dtype=int)

        result = BacktestEngine(MockStrategy(signals), data, 1_000.0).run()

        assert result.trades == []
        assert result.final_equity == 1_000.0

    def test_custo_da_compra_usa_notional_total(self):
        dates = pd.bdate_range("2023-01-01", periods=2)
        data = pd.DataFrame(
            {"abertura": [90.0, 100.0], "fechamento": [100.0, 100.0]},
            index=dates,
        )
        signals = pd.Series([1, 0], index=dates, dtype=int)

        result = BacktestEngine(
            MockStrategy(signals), data, 1_010.0, CostModel(tax_rate=0.01)
        ).run()

        assert result.trades[0].quantity == 10
        assert result.trades[0].cost == 10.0
        assert result.final_equity == 1_000.0

    def test_compra_reserva_custos_e_preserva_caixa_nao_negativo(self):
        dates = pd.bdate_range("2023-01-01", periods=2)
        data = pd.DataFrame(
            {"abertura": [90.0, 100.0], "fechamento": [100.0, 100.0]},
            index=dates,
        )
        signals = pd.Series([1, 0], index=dates, dtype=int)

        result = BacktestEngine(
            MockStrategy(signals), data, 1_000.0, CostModel(tax_rate=0.01)
        ).run()

        trade = result.trades[0]
        cash = result.final_equity - trade.quantity * data["fechamento"].iloc[-1]
        assert trade.quantity == 9
        assert cash == pytest.approx(91.0)
        assert cash >= 0

    def test_venda_que_excederia_caixa_e_rejeitada(self):
        dates = pd.bdate_range("2023-01-01", periods=3)
        data = pd.DataFrame(
            {"abertura": [90.0, 100.0, 10.0], "fechamento": [100.0, 100.0, 10.0]},
            index=dates,
        )
        signals = pd.Series([1, -1, 0], index=dates, dtype=int)

        result = BacktestEngine(
            MockStrategy(signals),
            data,
            151.0,
            CostModel(brokerage_fixed=50.0),
        ).run()

        assert [trade.type for trade in result.trades] == ["BUY"]
        assert result.final_equity == 11.0


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
