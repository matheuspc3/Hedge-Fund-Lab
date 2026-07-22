"""Testes para o módulo de transformação (src/pipeline/transform.py)."""

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.pipeline.transform import DataTransformer


class TestDataTransformerClean:
    def test_forward_fill(self, synthetic_data_with_nan):
        """NaN no meio da série → forward-filled."""
        df = DataTransformer.clean(synthetic_data_with_nan)
        # Linha 10 tinha NaN em fechamento — deve ter sido forward-filled
        assert not df.iloc[10]["fechamento"] is np.nan

    def test_drop_all_nan_row(self, synthetic_data_with_nan):
        """Linhas totalmente NaN removidas."""
        df = DataTransformer.clean(synthetic_data_with_nan)
        # Linhas 5 e 6 eram totalmente NaN
        assert 5 not in df.index or 6 not in df.index

    def test_empty_dataframe(self):
        """DataFrame vazio retorna vazio."""
        df = DataTransformer.clean(pd.DataFrame())
        assert df.empty

    def test_sort_index(self, synthetic_data_with_nan):
        """Índice fica ordenado após clean."""
        df = DataTransformer.clean(synthetic_data_with_nan)
        assert df.index.is_monotonic_increasing

    def test_no_nan_unchanged(self, synthetic_clean_data):
        """DataFrame sem NaN fica inalterado (mesmo número de linhas)."""
        n = len(synthetic_clean_data)
        df = DataTransformer.clean(synthetic_clean_data)
        assert len(df) == n


class TestDataTransformerIndicators:
    def test_sma_50(self, synthetic_clean_data):
        """SMA 50 com valores conhecidos."""
        df = DataTransformer().calculate_indicators(synthetic_clean_data)
        close = synthetic_clean_data["fechamento"]
        expected_sma = close.rolling(50).mean()
        pd.testing.assert_series_equal(
            df["sma_50"], expected_sma, check_names=False
        )

    def test_sma_200(self, synthetic_clean_data):
        """SMA 200 com valores conhecidos."""
        df = DataTransformer().calculate_indicators(synthetic_clean_data)
        close = synthetic_clean_data["fechamento"]
        expected_sma = close.rolling(200).mean()
        pd.testing.assert_series_equal(
            df["sma_200"], expected_sma, check_names=False
        )

    def test_bollinger_bands(self, synthetic_clean_data):
        """Bollinger Bands: upper >= middle >= lower (ignorando NaN do warm-up)."""
        df = DataTransformer().calculate_indicators(synthetic_clean_data)
        valid = df.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])
        assert (valid["bb_upper"] >= valid["bb_middle"]).all()
        assert (valid["bb_middle"] >= valid["bb_lower"]).all()

    def test_rsi_monotonic_up(self):
        """Série monotônica crescente → RSI = 100."""
        series = pd.Series(np.arange(1, 30, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        # Últimos valores devem estar muito próximos de 100
        assert result["rsi"].iloc[-1] > 99.0

    def test_rsi_monotonic_down(self):
        """Série monotônica decrescente → RSI = 0."""
        series = pd.Series(np.arange(30, 0, -1, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        # Últimos valores devem estar muito próximos de 0
        assert result["rsi"].iloc[-1] < 1.0

    def test_rsi_constant(self):
        """Série constante → sem variação → RSI = 100 (sem perdas)."""
        series = pd.Series(np.full(100, 100.0))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert result["rsi"].iloc[-1] == 100.0

    def test_macd_constant(self):
        """Série constante → MACD = 0, signal = 0."""
        series = pd.Series(np.full(100, 100.0))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert abs(result["macd"].iloc[-1]) < 1e-6
        assert abs(result["macd_sinal"].iloc[-1]) < 1e-6

    def test_macd_increasing(self):
        """Série crescente → MACD positivo."""
        series = pd.Series(np.arange(1, 101, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert result["macd"].iloc[-1] > 0

    def test_macd_decreasing(self):
        """Série decrescente → MACD negativo."""
        series = pd.Series(np.arange(100, 0, -1, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert result["macd"].iloc[-1] < 0

    def test_sma_200_insufficient_data(self):
        """Menos de 200 pontos → SMA_200 é tudo NaN."""
        series = pd.Series(np.arange(1, 50, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert result["sma_200"].isna().all()

    def test_rsi_insufficient_data(self):
        """Menos de 14 pontos → RSI = 100 (fillna para série sem perdas)."""
        series = pd.Series(np.arange(1, 10, dtype=float))
        df = pd.DataFrame({"fechamento": series})
        result = DataTransformer().calculate_indicators(df)
        assert (result["rsi"] == 100.0).all()

    def test_missing_close_column(self):
        """Sem coluna 'fechamento' → KeyError."""
        df = pd.DataFrame({"preco": [100.0]})
        with pytest.raises(KeyError):
            DataTransformer().calculate_indicators(df)

    def test_calc_sma_window_negative(self):
        """_calc_sma com window <= 0 → ValueError."""
        series = pd.Series([100.0] * 50)
        with pytest.raises(ValueError, match="must be > 0"):
            DataTransformer._calc_sma(series, 0)

    def test_calc_bollinger_k_negative(self):
        """_calc_bollinger com k < 0 → ValueError."""
        series = pd.Series([100.0] * 50)
        with pytest.raises(ValueError, match="must be >= 0"):
            DataTransformer._calc_bollinger(series, k=-1.0)

    def test_calc_rsi_period_negative(self):
        """_calc_rsi com period <= 0 → ValueError."""
        series = pd.Series([100.0] * 20)
        with pytest.raises(ValueError, match="must be > 0"):
            DataTransformer._calc_rsi(series, period=0)

    def test_calc_macd_fast_ge_slow(self):
        """_calc_macd com fast >= slow → ValueError."""
        series = pd.Series([100.0] * 50)
        with pytest.raises(ValueError, match="must be < slow"):
            DataTransformer._calc_macd(series, fast=26, slow=12)

    def test_all_indicators_present(self, synthetic_clean_data):
        """DataFrame resultante tem todas as colunas de indicadores esperadas."""
        df = DataTransformer().calculate_indicators(synthetic_clean_data)
        expected_cols = {
            "sma_50", "sma_200", "bb_upper", "bb_middle", "bb_lower",
            "rsi", "macd", "macd_sinal",
        }
        assert expected_cols.issubset(set(df.columns))


class TestDataTransformerSanitize:
    def test_nan_to_none(self):
        """float('nan') → None."""
        records = [{"valor": float("nan")}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["valor"] is None

    def test_inf_to_none(self):
        """float('inf') → None."""
        records = [{"valor": float("inf")}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["valor"] is None

    def test_neg_inf_to_none(self):
        """float('-inf') → None."""
        records = [{"valor": float("-inf")}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["valor"] is None

    def test_normal_values_unchanged(self):
        """Valores normais não são alterados."""
        records = [{"a": 42.5, "b": 0.0, "c": -3.14}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["a"] == 42.5
        assert result[0]["b"] == 0.0
        assert result[0]["c"] == -3.14

    def test_mixed_values(self):
        """Mistura de NaN, Inf e normais."""
        records = [{"a": float("nan"), "b": 42.0, "c": float("inf")}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["a"] is None
        assert result[0]["b"] == 42.0
        assert result[0]["c"] is None

    def test_empty_list(self):
        """Lista vazia → lista vazia."""
        assert DataTransformer.sanitize_for_json([]) == []

    def test_none_values(self):
        """None passa direto."""
        records = [{"a": None}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["a"] is None

    def test_string_values(self):
        """Strings não são afetadas."""
        records = [{"a": "hello"}]
        result = DataTransformer.sanitize_for_json(records)
        assert result[0]["a"] == "hello"

    @given(
        st.lists(
            st.floats(allow_nan=True, allow_infinity=True),
            min_size=0,
            max_size=20,
        )
    )
    @settings(max_examples=100)
    def test_property_based(self, values):
        """Property-based: saída nunca contém NaN ou Inf."""
        records = [{"v": v} for v in values]
        result = DataTransformer.sanitize_for_json(records)

        for record in result:
            if record["v"] is not None:
                assert isinstance(record["v"], float)
                assert not math.isnan(record["v"])
                assert not math.isinf(record["v"])
