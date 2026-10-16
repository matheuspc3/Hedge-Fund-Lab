"""H2_SCIENTIFIC_SHARPE_DEFINITION_V1 (Amendment 5): fórmula, convenções e golden."""

import math

import numpy as np
import pandas as pd
import pytest

from src.backtesting import metrics
from src.backtesting.metrics import (
    SCIENTIFIC_SHARPE_DEFINITION,
    scientific_sharpe,
    sharpe_components,
    sharpe_ratio,
)

DAYS = pd.bdate_range("2024-03-01", periods=8)


def curve(values: list[float]) -> pd.Series:
    return pd.Series(values, index=DAYS[: len(values)], dtype=float)


def test_constantes_congeladas() -> None:
    assert SCIENTIFIC_SHARPE_DEFINITION == "H2_SCIENTIFIC_SHARPE_DEFINITION_V1"
    assert metrics.TRADING_PERIODS_PER_YEAR == 252
    assert metrics.SCIENTIFIC_RISK_FREE_RATE == 0.0
    assert metrics.SHARPE_MIN_STD == 1e-15


def test_menos_de_dois_retornos_e_zero_por_convencao() -> None:
    assert sharpe_ratio(pd.Series([0.01])) == 0.0
    parts = scientific_sharpe(curve([100.0, 101.0]))
    assert parts["sharpe"] == 0.0 and parts["convention_zero"] and parts["observations"] == 1


def test_trajetoria_toda_em_caixa_e_zero_e_continua_completa() -> None:
    parts = scientific_sharpe(curve([100_000.0] * 8))
    assert parts["sharpe"] == 0.0 and parts["convention_zero"]
    assert parts["observations"] == 7  # nenhum dia removido


def test_serie_constante_diferente_de_zero_e_zero_por_convencao() -> None:
    """Propriedade geral congelada: volatilidade < 1e-15 -> 0.0, sem exceção."""
    parts = sharpe_components(pd.Series([0.001] * 10))
    assert parts["sample_std"] < 1e-15
    assert parts["sharpe"] == 0.0 and parts["convention_zero"]


def test_serie_normal_segue_a_formula_exata() -> None:
    r = pd.Series([0.01, -0.005, 0.0, 0.02, -0.01])
    expected = r.mean() / r.std(ddof=1) * math.sqrt(252)
    assert sharpe_ratio(r) == pytest.approx(expected, rel=0, abs=1e-15)
    parts = sharpe_components(r)
    assert parts["annualization_factor"] == math.sqrt(252)
    assert not parts["convention_zero"]


def test_dias_em_caixa_permanecem_e_remove_los_muda_o_valor() -> None:
    values = [100.0, 100.0, 101.0, 101.0, 101.0, 100.5, 102.0, 102.0]
    parts = scientific_sharpe(curve(values))
    returns = curve(values).pct_change().dropna()
    assert parts["observations"] == len(returns) == 7
    assert parts["sharpe"] == pytest.approx(sharpe_ratio(returns))
    without_zeros = sharpe_ratio(returns[returns != 0])
    assert without_zeros != pytest.approx(parts["sharpe"])  # NÃO é o científico


def test_rf_zero_e_252() -> None:
    r = pd.Series([0.01, -0.005, 0.0, 0.02, -0.01])
    parts = scientific_sharpe(curve([100.0, *(100.0 * np.cumprod(1 + r)).tolist()]))
    assert parts["mean_excess"] == pytest.approx(r.mean())  # rf = 0: excesso = retorno
    assert parts["annualization_factor"] == math.sqrt(252)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_dado_invalido_continua_falhando_fechado(bad: float) -> None:
    with pytest.raises(ValueError):
        sharpe_ratio(pd.Series([0.01, bad, 0.02]))
    with pytest.raises(ValueError):
        scientific_sharpe(curve([100.0, bad, 101.0]))


def test_golden_impede_mudanca_silenciosa_da_definicao() -> None:
    values = [100_000.0, 100_000.0, 100_950.0, 100_400.0, 100_400.0, 101_900.0, 101_250.0, 101_250.0]
    parts = scientific_sharpe(curve(values))
    assert parts["observations"] == 7
    assert parts["sharpe"] == pytest.approx(3.687107432608234, rel=1e-12)
