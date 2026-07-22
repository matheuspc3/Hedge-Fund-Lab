"""Fixtures compartilhadas para testes de estratégias."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_price_data() -> pd.DataFrame:
    """Fixture: 500 dias de preços sintéticos (senoide + ruído)."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2022-01-01", periods=500)
    t = np.linspace(0, 4 * np.pi, 500)
    prices = 100 + 10 * np.sin(t) + rng.normal(0, 0.5, 500)
    prices = np.maximum(prices, 1.0)
    df = pd.DataFrame({"fechamento": prices}, index=dates)
    df.index.name = "data"
    return df


@pytest.fixture
def empty_data() -> pd.DataFrame:
    """Fixture: DataFrame vazio."""
    return pd.DataFrame()


@pytest.fixture
def single_row_data() -> pd.DataFrame:
    """Fixture: DataFrame com 1 linha."""
    df = pd.DataFrame({"fechamento": [100.0]}, index=pd.DatetimeIndex(["2023-01-02"]))
    df.index.name = "data"
    return df


@pytest.fixture
def trend_up_data() -> pd.DataFrame:
    """Fixture: tendência de alta clara (usada pelo SMA Cross)."""
    dates = pd.bdate_range("2022-01-01", periods=500)
    prices = 100 + np.linspace(0, 50, 500) + np.random.default_rng(42).normal(0, 1, 500)
    df = pd.DataFrame({"fechamento": prices}, index=dates)
    df.index.name = "data"
    return df
