"""Fixtures compartilhadas para todos os testes do Hedge-fund-lab."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Adiciona src/ ao path
SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC.parent))

# ── Dados sintéticos ─────────────────────────────────────────────


@pytest.fixture
def synthetic_ohlcv() -> pd.DataFrame:
    """Gera ~5 anos de dados OHLCV sintéticos (random walk)."""
    dates = pd.bdate_range("2020-01-01", "2024-12-31")
    rng = np.random.default_rng(42)
    n = len(dates)
    prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
    prices = np.maximum(prices, 1.0)  # preço mínimo 1

    df = pd.DataFrame(
        {
            "abertura": prices,
            "maxima": prices * 1.02,
            "minima": prices * 0.98,
            "fechamento": prices,
            "volume": rng.integers(100_000, 10_000_000, n),
        },
        index=dates,
    )
    df.index.name = "data"
    return df


@pytest.fixture
def synthetic_clean_data() -> pd.DataFrame:
    """Pequeno DataFrame limpo para testes rápidos."""
    dates = pd.bdate_range("2023-01-01", "2023-12-31")
    prices = 100 + np.arange(len(dates)) * 0.1  # tendência estável de alta

    df = pd.DataFrame(
        {
            "fechamento": prices,
            "abertura": prices,
            "maxima": prices + 1,
            "minima": prices - 1,
            "volume": 1_000_000,
        },
        index=dates,
    )
    df.index.name = "data"
    return df


@pytest.fixture
def synthetic_data_with_nan(synthetic_clean_data: pd.DataFrame) -> pd.DataFrame:
    """DataFrame com valores NaN para testar clean()."""
    df = synthetic_clean_data.copy()
    df.iloc[5:7, :] = np.nan  # duas linhas totalmente NaN
    df.iloc[10, 0] = np.nan  # NaN pontual em fechamento
    return df


# ── Mock helpers ─────────────────────────────────────────────────


@pytest.fixture
def mock_db_session():
    """Cria uma sessão SQLAlchemy mockada."""
    from unittest.mock import MagicMock

    session = MagicMock()
    return session


@pytest.fixture
def mock_session_factory(mock_db_session):
    """Cria uma factory que retorna a sessão mockada."""
    return lambda: mock_db_session


@pytest.fixture
def sample_cotacoes_df() -> pd.DataFrame:
    """DataFrame pequeno de cotações para testes de carga."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "data": [d.date() for d in dates],
            "abertura": [100.0] * 10,
            "maxima": [101.0] * 10,
            "minima": [99.0] * 10,
            "fechamento": [100.5] * 10,
            "volume": [1_000_000] * 10,
        }
    )


@pytest.fixture
def sample_indicadores_df() -> pd.DataFrame:
    """DataFrame pequeno de indicadores para testes de carga."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "data": [d.date() for d in dates],
            "sma_50": [100.0] * 10,
            "sma_200": [None] * 10,
            "bb_upper": [102.0] * 10,
            "bb_middle": [100.0] * 10,
            "bb_lower": [98.0] * 10,
            "rsi": [55.0] * 10,
            "macd": [0.5] * 10,
            "macd_sinal": [0.3] * 10,
        }
    )
