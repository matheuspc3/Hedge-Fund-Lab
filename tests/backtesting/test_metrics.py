"""Testes para métricas de desempenho."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.backtesting.metrics import (
    annualized_return,
    annualized_volatility,
    calmar_ratio,
    cumulative_return,
    max_drawdown,
    max_drawdown_duration,
    performance_metrics,
    periodic_returns,
    sharpe_ratio,
    sortino_ratio,
    total_return,
    total_transaction_cost,
    turnover,
    validate_equity_curve,
)


def equity_curve(values) -> pd.Series:
    return pd.Series(
        list(values), index=pd.bdate_range("2024-01-02", periods=len(values))
    )


class TestSharpeRatio:
    """Testes para sharpe_ratio()."""

    def test_retornos_zero(self):
        """Retornos todos zero → Sharpe = 0."""
        returns = pd.Series([0.0] * 10)
        assert sharpe_ratio(returns, rf=0.0, freq=252) == 0.0

    def test_retornos_positivos_constantes(self):
        """Retornos positivos constantes → Sharpe infinito (vol=0) → 0."""
        returns = pd.Series([0.01] * 100)
        sr = sharpe_ratio(returns, rf=0.0, freq=252)
        # Volatilidade zero → Sharpe = 0 (tratamento de divisão por zero)
        assert sr == pytest.approx(0.0)

    def test_retornos_com_rf_maior_que_media(self):
        """rf > retorno médio → Sharpe negativo."""
        returns = pd.Series([0.001] * 100 + [-0.001] * 100)
        sr = sharpe_ratio(returns, rf=0.05, freq=252)
        assert sr < 0

    def test_sharpe_manual(self):
        """Cálculo manual para 5 retornos conhecidos."""
        returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01])
        # média = 0.004, std = 0.019493...
        # Sharpe anualizado = (0.004 - 0) / 0.019493 * sqrt(252)
        sr = sharpe_ratio(returns, rf=0.0, freq=252)
        mean_r = returns.mean()
        std_r = returns.std(ddof=1)
        esperado = (mean_r - 0.0) / std_r * np.sqrt(252)
        assert abs(sr - esperado) < 1e-10

    def test_serie_vazia_raise(self):
        """Série vazia → ValueError."""
        with pytest.raises(ValueError):
            sharpe_ratio(pd.Series([], dtype=float))


class TestSortinoRatio:
    """Testes para sortino_ratio()."""

    def test_retornos_todos_positivos(self):
        """Retornos todos positivos → downside deviation = 0 → Sortino = 0."""
        returns = pd.Series([0.01] * 50)
        sr = sortino_ratio(returns, rf=0.0, mar=0.0, freq=252)
        assert sr == 0.0

    def test_ganhos_e_perdas_conhecidos(self):
        returns = pd.Series([0.02, -0.01, 0.01, -0.02])

        result = sortino_ratio(returns, rf=0.0, mar=0.0, freq=4)

        downside = np.minimum(returns, 0.0)
        expected = returns.mean() / np.sqrt(np.mean(downside**2)) * np.sqrt(4)
        assert result == pytest.approx(expected)

    def test_serie_vazia_raise(self):
        """Série vazia → ValueError."""
        with pytest.raises(ValueError):
            sortino_ratio(pd.Series([], dtype=float))


class TestMaxDrawdown:
    """Testes para max_drawdown()."""

    def test_monotonico_crescente(self):
        """Série crescente → drawdown = 0."""
        equity = equity_curve([100, 110, 120, 130, 140])
        assert max_drawdown(equity) == 0.0

    def test_max_drawdown_20pct(self):
        """Série [100, 90, 80, 110] → max_drawdown = -20%."""
        equity = equity_curve([100.0, 90.0, 80.0, 110.0])
        # Pico = 100, vale = 80 → drawdown = (80-100)/100 = -0.20
        assert abs(max_drawdown(equity) - (-0.20)) < 1e-10

    def test_drawdown_apos_Novo_pico(self):
        """Série [100, 120, 110, 130] → max_drawdown = -8.33% do pico 120."""
        equity = equity_curve([100.0, 120.0, 110.0, 130.0])
        # Pico = 120, vale = 110 → (110-120)/120 = -0.0833
        dd = max_drawdown(equity)
        assert abs(dd - (-0.0833333333)) < 1e-6

    def test_constante(self):
        """Série constante → drawdown = 0."""
        equity = equity_curve([100.0] * 10)
        assert max_drawdown(equity) == 0.0

    def test_serie_vazia_raise(self):
        """Série vazia → ValueError."""
        with pytest.raises(ValueError):
            max_drawdown(pd.Series([], dtype=float))

    def test_serie_um_elemento(self):
        """1 elemento → drawdown = 0."""
        equity = equity_curve([100.0])
        assert max_drawdown(equity) == 0.0

    def test_queda_continua(self):
        """Queda contínua [100, 90, 80, 70] → max_drawdown = -30%."""
        equity = equity_curve([100.0, 90.0, 80.0, 70.0])
        assert abs(max_drawdown(equity) - (-0.30)) < 1e-10

    def test_queda_de_120_para_90(self):
        equity = equity_curve([100.0, 120.0, 90.0, 110.0])
        assert max_drawdown(equity) == pytest.approx(-0.25)


class TestMaxDrawdownDuration:
    """Testes para max_drawdown_duration()."""

    def test_monotonico_crescente(self):
        """Série crescente → duração = 0."""
        equity = equity_curve([100, 110, 120])
        assert max_drawdown_duration(equity) == 0

    def test_queda_e_recuperacao(self):
        """Série com queda e recuperação → duração em dias."""
        equity = equity_curve([100.0, 95.0, 90.0, 95.0, 100.0])
        duracao = max_drawdown_duration(equity)
        # Drawdown do pico (índice 0) até recuperar (índice 4) = 3 períodos em drawdown
        assert duracao == 3

    def test_serie_vazia_raise(self):
        """Série vazia → ValueError."""
        with pytest.raises(ValueError):
            max_drawdown_duration(pd.Series([], dtype=float))

    def test_pico_periodo_abaixo_e_recuperacao(self):
        equity = equity_curve([100.0, 120.0, 90.0, 110.0, 120.0])
        assert max_drawdown_duration(equity) == 2


class TestTurnover:
    """Testes para turnover()."""

    def test_pesos_constantes(self):
        """Pesos constantes → turnover = 0."""
        weights = pd.DataFrame({"A": [0.5, 0.5, 0.5], "B": [0.5, 0.5, 0.5]})
        assert turnover(weights) == 0.0

    def test_de_1_0_para_0_1(self):
        """De [1,0] para [0,1] → turnover = 2."""
        weights = pd.DataFrame({"A": [1.0, 0.0], "B": [0.0, 1.0]})
        assert abs(turnover(weights) - 2.0) < 1e-10

    def test_sem_mudanca(self):
        """Pesos iguais sem mudança → turnover = 0."""
        weights = pd.DataFrame({"A": [0.5, 0.5], "B": [0.5, 0.5]})
        assert turnover(weights) == 0.0

    def test_serie_unica_linha(self):
        """Apenas 1 linha → turnover = 0."""
        weights = pd.DataFrame({"A": [1.0]})
        assert turnover(weights) == 0.0


class TestCumulativeReturn:
    """Testes para cumulative_return()."""

    def test_constante(self):
        """Equity constante → retorno = 0."""
        equity = equity_curve([100.0] * 5)
        assert cumulative_return(equity) == 0.0

    def test_valor_conhecido(self):
        """100 → 150 → retorno = 50%."""
        equity = equity_curve([100.0, 150.0])
        assert abs(cumulative_return(equity) - 0.50) < 1e-10

    def test_100_para_80(self):
        """100 → 80 → retorno = -20%."""
        equity = equity_curve([100.0, 80.0])
        assert abs(cumulative_return(equity) - (-0.20)) < 1e-10

    def test_100_para_110(self):
        assert total_return(equity_curve([100.0, 110.0])) == pytest.approx(0.10)


class TestPeriodicReturns:
    def test_retornos_manuais(self):
        equity = equity_curve([100.0, 110.0, 99.0])
        expected = pd.Series([0.10, -0.10], index=equity.index[1:])
        pd.testing.assert_series_equal(periodic_returns(equity), expected)


class TestAnnualizedVolatility:
    """Testes para annualized_volatility()."""

    def test_retornos_constantes(self):
        """Retornos constantes → vol = 0."""
        returns = pd.Series([0.01] * 100)
        vol = annualized_volatility(returns, freq=252)
        assert vol == pytest.approx(0.0)

    def test_vol_anualizada(self):
        """Vol diária de 1% → vol anualizada ≈ 15.87%."""
        rng = np.random.default_rng(42)
        returns = pd.Series(rng.normal(0.0, 0.01, 252))
        vol = annualized_volatility(returns, freq=252)
        esperado = 0.01 * np.sqrt(252)
        assert abs(vol - esperado) < esperado * 0.3  # 30% de tolerância (amostra)

    def test_serie_vazia_raise(self):
        """Série vazia → ValueError."""
        with pytest.raises(ValueError):
            annualized_volatility(pd.Series([], dtype=float))


class TestCalmarRatio:
    """Testes para calmar_ratio()."""

    def test_calmar_positivo(self):
        """Retorno positivo, drawdown pequeno → Calmar > 0."""
        # Cria série com drawdown, mas retorno líquido positivo
        returns = pd.Series([0.005] * 200 + [-0.02] + [0.01] * 51)
        equity = equity_curve(100.0 * np.exp(returns.cumsum()))
        dd = max_drawdown(equity)
        cr = calmar_ratio(returns, dd, freq=252)
        assert cr > 0

    def test_max_dd_zero(self):
        """Drawdown = 0 → Calmar = 0 (divisão por zero evitada)."""
        returns = pd.Series([0.001] * 10)
        cr = calmar_ratio(returns, 0.0, freq=252)
        assert cr == 0.0


class TestCanonicalMetrics:
    def test_contract_rejects_non_temporal_duplicate_unsorted_or_non_finite(self):
        with pytest.raises(ValueError, match="DatetimeIndex"):
            validate_equity_curve(pd.Series([100.0, 101.0]))
        with pytest.raises(ValueError, match="duplicates"):
            validate_equity_curve(
                pd.Series([100.0, 101.0], index=pd.to_datetime(["2024-01-02"] * 2))
            )
        with pytest.raises(ValueError, match="sorted"):
            validate_equity_curve(
                pd.Series(
                    [100.0, 101.0],
                    index=pd.to_datetime(["2024-01-03", "2024-01-02"]),
                )
            )
        with pytest.raises(ValueError, match="finite"):
            validate_equity_curve(equity_curve([100.0, np.inf]))

    def test_performance_metrics_derive_from_one_curve(self):
        equity = equity_curve([100.0, 110.0, 99.0])
        returns = periodic_returns(equity)

        result = performance_metrics(equity, freq=2)

        assert result["total_return"] == pytest.approx(-0.01)
        assert result["annualized_return"] == pytest.approx(-0.01)
        assert result["annualized_volatility"] == pytest.approx(
            returns.std(ddof=1) * np.sqrt(2)
        )

    def test_annualized_return_uses_observation_count(self):
        assert annualized_return(equity_curve([100.0, 110.0]), freq=1) == pytest.approx(
            0.10
        )

    def test_total_transaction_cost_sums_executed_trades(self):
        trades = [SimpleNamespace(cost=1.25), SimpleNamespace(cost=2.75)]
        assert total_transaction_cost(trades) == pytest.approx(4.0)
