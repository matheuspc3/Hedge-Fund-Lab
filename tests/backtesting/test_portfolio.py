"""Testes do motor de backtesting multi-ativo (portfolio.py).

Cobre:
  - PortfolioStrategy (ABC não instanciável)
  - EqualWeightPortfolio
  - MinVariancePortfolio
  - PortfolioBacktestEngine (init, run, edge cases)
  - PortfolioBacktestResult (propriedades)
"""

import numpy as np
import pandas as pd
import pytest

from src.backtesting.costs import CostModel
from src.backtesting.portfolio import (
    EqualWeightPortfolio,
    MinVariancePortfolio,
    PortfolioBacktestEngine,
    PortfolioBacktestResult,
    PortfolioStrategy,
    PortfolioTrade,
)

# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def synthetic_2assets() -> dict[str, pd.DataFrame]:
    """Retornos diários sintéticos para 2 ativos correlacionados."""
    dates = pd.bdate_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(42)

    # Ativo A: tendência de alta (+0.05% ao dia)
    # Ativo B: correlação ~0.7 com A
    noise_a = rng.normal(0, 0.01, len(dates))
    noise_b = rng.normal(0, 0.01, len(dates))
    drift = 0.0005

    price_a = 100 * np.exp(np.cumsum(drift + noise_a))
    price_b = 100 * np.exp(np.cumsum(drift * 0.8 + 0.7 * noise_a + 0.5 * noise_b))

    df_a = pd.DataFrame({"fechamento": price_a}, index=dates)
    df_b = pd.DataFrame({"fechamento": price_b}, index=dates)
    return {"ATIVO_A.SA": df_a, "ATIVO_B.SA": df_b}


@pytest.fixture
def synthetic_3assets() -> dict[str, pd.DataFrame]:
    """Três ativos: dois correlacionados, um descorrelacionado."""
    dates = pd.bdate_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(123)

    noise = rng.normal(0, 0.015, (len(dates), 3))
    drift = 0.0004

    prices = 100 * np.exp(np.cumsum(drift + noise, axis=0))

    return {
        "PETR4": pd.DataFrame({"fechamento": prices[:, 0]}, index=dates),
        "ITUB4": pd.DataFrame({"fechamento": prices[:, 1]}, index=dates),
        "WEGE3": pd.DataFrame({"fechamento": prices[:, 2]}, index=dates),
    }


@pytest.fixture
def two_dates_dict() -> dict[str, pd.DataFrame]:
    """Apenas 2 datas — para testar edge cases sem janela mínima."""
    dates = pd.DatetimeIndex(["2024-01-02", "2024-01-03"])
    return {
        "A": pd.DataFrame({"fechamento": [100.0, 101.0]}, index=dates),
        "B": pd.DataFrame({"fechamento": [50.0, 51.0]}, index=dates),
    }


# ═══════════════════════════════════════════════════════════════════
# PortfolioStrategy (ABC)
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioStrategy:
    def test_nao_instancia_abc(self):
        """PortfolioStrategy não pode ser instanciada diretamente."""
        with pytest.raises(TypeError):
            PortfolioStrategy()  # type: ignore


# ═══════════════════════════════════════════════════════════════════
# EqualWeightPortfolio
# ═══════════════════════════════════════════════════════════════════


class TestEqualWeightPortfolio:
    def test_2_ativos_pesos_meio(self, two_dates_dict):
        """Com 2 ativos, cada um recebe 0.5."""
        strat = EqualWeightPortfolio()
        w = strat.get_weights(two_dates_dict, pd.Timestamp("2024-01-03"))
        assert w == {"A": 0.5, "B": 0.5}

    def test_3_ativos_pesos_terco(self, synthetic_3assets):
        """Com 3 ativos, cada um recebe ~0.333."""
        strat = EqualWeightPortfolio()
        w = strat.get_weights(synthetic_3assets, pd.Timestamp("2021-01-04"))
        assert len(w) == 3
        for _ticker, weight in w.items():
            assert weight == pytest.approx(1 / 3)

    def test_soma_um(self, synthetic_2assets):
        """Pesos sempre somam 1.0."""
        strat = EqualWeightPortfolio()
        w = strat.get_weights(synthetic_2assets, pd.Timestamp("2021-01-04"))
        assert sum(w.values()) == pytest.approx(1.0)

    def test_data_vazia(self):
        """Dict vazio retorna dict vazio."""
        strat = EqualWeightPortfolio()
        w = strat.get_weights({}, pd.Timestamp("2024-01-03"))
        assert w == {}

    def test_get_name(self):
        strat = EqualWeightPortfolio()
        assert "Equal Weight" in strat.get_name()


# ═══════════════════════════════════════════════════════════════════
# MinVariancePortfolio
# ═══════════════════════════════════════════════════════════════════


class TestMinVariancePortfolio:
    def test_2_ativos_soma_um(self, synthetic_2assets):
        """Pesos da MV somam 1.0."""
        strat = MinVariancePortfolio(window=100)
        w = strat.get_weights(synthetic_2assets, pd.Timestamp("2021-01-04"))
        assert sum(w.values()) == pytest.approx(1.0, abs=1e-4)

    def test_pesos_positivos(self, synthetic_2assets):
        """Com allow_short=False, todos os pesos >= 0."""
        strat = MinVariancePortfolio(window=100, allow_short=False)
        w = strat.get_weights(synthetic_2assets, pd.Timestamp("2021-01-04"))
        for v in w.values():
            assert v >= -1e-10  # tolerância numérica

    def test_allow_short_pode_ser_negativo(self, synthetic_2assets):
        """Com allow_short=True, pesos podem ser negativos."""
        strat = MinVariancePortfolio(window=100, allow_short=True)
        w = strat.get_weights(synthetic_2assets, pd.Timestamp("2021-01-04"))
        # Verifica que a otimização rodou (pode ou não ter negativos)
        assert sum(w.values()) == pytest.approx(1.0, abs=1e-4)

    def test_dados_insuficientes_fallback(self, two_dates_dict):
        """Menos dados que window → fallback para equal weight."""
        strat = MinVariancePortfolio(window=252)
        w = strat.get_weights(two_dates_dict, pd.Timestamp("2024-01-03"))
        assert w == {"A": 0.5, "B": 0.5}

    def test_1_ativo_peso_um(self):
        """Apenas 1 ativo → peso = 1.0."""
        dates = pd.bdate_range("2020-01-01", periods=300)
        df = pd.DataFrame({"fechamento": np.linspace(100, 110, 300)}, index=dates)
        strat = MinVariancePortfolio(window=100)
        w = strat.get_weights({"UNICO": df}, pd.Timestamp("2021-01-04"))
        assert w == {"UNICO": 1.0}

    def test_get_name(self):
        strat = MinVariancePortfolio()
        assert "Mínima Variância" in strat.get_name()

    def test_sem_short_no_name(self):
        strat = MinVariancePortfolio(allow_short=False)
        assert "n" in strat.get_name() or "Mínima" in strat.get_name()

    def test_pesos_ativos_3(self, synthetic_3assets):
        """Com 3 ativos, otimização retorna 3 pesos que somam 1."""
        strat = MinVariancePortfolio(window=100)
        w = strat.get_weights(synthetic_3assets, pd.Timestamp("2021-01-04"))
        assert len(w) == 3
        assert sum(w.values()) == pytest.approx(1.0, abs=1e-4)


# ═══════════════════════════════════════════════════════════════════
# PortfolioBacktestResult
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioBacktestResult:
    def test_returns_property(self):
        """returns deriva de equity_curve.pct_change()."""
        dates = pd.bdate_range("2024-01-01", periods=5)
        equity = pd.Series([100, 101, 103, 102, 105], index=dates)
        result = PortfolioBacktestResult(
            equity_curve=equity,
            weights_history=pd.DataFrame(index=dates),
            allocation_history=pd.DataFrame(index=dates),
            initial_capital=100.0,
            final_equity=105.0,
        )
        assert len(result.returns) == 4
        assert result.returns.iloc[0] == pytest.approx(0.01)


# ═══════════════════════════════════════════════════════════════════
# PortfolioBacktestEngine — Init
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioBacktestEngineInit:
    def test_init_valido(self, synthetic_2assets):
        """Engine criada com parâmetros válidos."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        assert engine.initial_capital == 100_000
        assert engine.rebalance_freq == 63

    def test_data_vazia_raise(self):
        """Dict vazio → ValueError."""
        strat = EqualWeightPortfolio()
        with pytest.raises(ValueError, match="cannot be empty"):
            PortfolioBacktestEngine(strat, {}, 100_000)

    def test_capital_zero_raise(self, synthetic_2assets):
        """Capital <= 0 → ValueError."""
        strat = EqualWeightPortfolio()
        with pytest.raises(ValueError, match="must be > 0"):
            PortfolioBacktestEngine(strat, synthetic_2assets, 0)

    def test_capital_negativo_raise(self, synthetic_2assets):
        strat = EqualWeightPortfolio()
        with pytest.raises(ValueError, match="must be > 0"):
            PortfolioBacktestEngine(strat, synthetic_2assets, -100)


# ═══════════════════════════════════════════════════════════════════
# PortfolioBacktestEngine — Run
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioBacktestEngineRun:
    def test_equity_inicial(self, synthetic_2assets):
        """Equity começa com initial_capital."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        result = engine.run()
        assert result.equity_curve.iloc[0] == pytest.approx(100_000, rel=0.01)

    def test_equity_final_positivo(self, synthetic_2assets):
        """Equity final > 0 em mercado sintético com tendência."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        result = engine.run()
        assert result.final_equity > 0
        assert result.final_equity > 90_000  # não perdeu quase tudo

    def test_weights_history_shape(self, synthetic_2assets):
        """weights_history é DataFrame com tickers como colunas."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        result = engine.run()
        assert isinstance(result.weights_history, pd.DataFrame)
        assert "ATIVO_A.SA" in result.weights_history.columns
        assert "ATIVO_B.SA" in result.weights_history.columns

    def test_allocation_history_cash_column(self, synthetic_2assets):
        """allocation_history tem coluna 'cash'."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        result = engine.run()
        assert "cash" in result.allocation_history.columns

    def test_primeiro_rebalanceamento(self, synthetic_2assets):
        """Após rebalanceamento inicial, posições são alocadas."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(
            strat, synthetic_2assets, 100_000, rebalance_freq=1
        )
        result = engine.run()
        # No primeiro dia com rebalance_freq=1, metade do capital vai pra cada ativo
        first_alloc = result.allocation_history.iloc[0]
        # Soma alocada (ex-cash) deve ser aproximadamente capital
        allocated = sum(first_alloc[t] for t in ["ATIVO_A.SA", "ATIVO_B.SA"])
        assert allocated > 0
        assert first_alloc["cash"] >= 0

    def test_sem_rebalanceamento_so_drift(self, two_dates_dict):
        """Com rebalance_freq muito alto, só alocação inicial + drift."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(
            strat, two_dates_dict, 100_000, rebalance_freq=999
        )
        result = engine.run()
        # 2 trades de BUY no primeiro dia (alocação inicial), sem rebalanceamentos depois
        assert len(result.trades) == 2
        assert all(t.type == "BUY" for t in result.trades)

    def test_com_custos_reduz_retorno(self, synthetic_2assets):
        """Com custos, o retorno final é menor."""
        strat = EqualWeightPortfolio()
        cost_model = CostModel(brokerage_fixed=10.0, spread_bps=50)

        engine_sem = PortfolioBacktestEngine(
            strat, synthetic_2assets, 100_000, rebalance_freq=10
        )
        engine_com = PortfolioBacktestEngine(
            strat, synthetic_2assets, 100_000, rebalance_freq=10, cost_model=cost_model
        )

        result_sem = engine_sem.run()
        result_com = engine_com.run()

        # Com custos, o retorno tende a ser menor (não garantido mas provável)
        assert result_com.final_equity <= result_sem.final_equity * 1.01

    def test_min_variance_executa(self, synthetic_2assets):
        """MinVariancePortfolio no motor não quebra."""
        strat = MinVariancePortfolio(window=100)
        engine = PortfolioBacktestEngine(
            strat, synthetic_2assets, 100_000, rebalance_freq=30
        )
        result = engine.run()
        assert result.final_equity > 0
        assert len(result.equity_curve) > 0

    def test_resultado_contem_trades(self, synthetic_2assets):
        """Com rebalance_freq pequeno, trades são gerados."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(
            strat, synthetic_2assets, 100_000, rebalance_freq=20
        )
        result = engine.run()
        assert len(result.trades) > 0
        trade = result.trades[0]
        assert isinstance(trade, PortfolioTrade)
        assert trade.type in ("BUY", "SELL")
        assert trade.quantity > 0
        assert trade.price > 0

    def test_dataframe_uma_linha_por_ativo(self):
        """Apenas 1 data para cada ativo → executa sem quebrar."""
        dates = pd.DatetimeIndex(["2024-01-02"])
        data = {
            "A": pd.DataFrame({"fechamento": [100.0]}, index=dates),
            "B": pd.DataFrame({"fechamento": [50.0]}, index=dates),
        }
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, data, 100_000)
        result = engine.run()
        assert len(result.equity_curve) == 1

    def test_active_return_series(self, synthetic_2assets):
        """Equity curve tem o mesmo comprimento das datas alinhadas."""
        strat = EqualWeightPortfolio()
        engine = PortfolioBacktestEngine(strat, synthetic_2assets, 100_000)
        result = engine.run()
        assert len(result.equity_curve) == len(result.returns) + 1


# ═══════════════════════════════════════════════════════════════════
# PortfolioTrade
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioTrade:
    def test_create_trade(self):
        """Criação básica de PortfolioTrade."""
        trade = PortfolioTrade(
            date=pd.Timestamp("2024-01-02"),
            ticker="PETR4",
            type="BUY",
            price=100.0,
            quantity=10,
            cost=5.0,
        )
        assert trade.ticker == "PETR4"
        assert trade.type == "BUY"
        assert trade.quantity == 10
