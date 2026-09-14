"""Testes para os flows Prefect (src/pipeline/flows.py)."""

from unittest.mock import patch

import pandas as pd
import pytest


@pytest.fixture
def mock_dataframe():
    """DataFrame simulado para retorno das tasks."""
    dates = pd.date_range("2024-01-01", periods=10)
    return pd.DataFrame(
        {
            "fechamento": [100.0 + i for i in range(10)],
            "abertura": [100.0 + i for i in range(10)],
            "maxima": [101.0 + i for i in range(10)],
            "minima": [99.0 + i for i in range(10)],
            "volume": [1_000_000] * 10,
            "sma_50": [None] * 10,
            "sma_200": [None] * 10,
            "bb_upper": [102.0] * 10,
            "bb_middle": [100.0] * 10,
            "bb_lower": [98.0] * 10,
            "rsi": [55.0] * 10,
            "macd": [0.5] * 10,
            "macd_sinal": [0.3] * 10,
        },
        index=dates,
    )


class TestPipelineFlow:
    def test_full_flow_success(self, mock_dataframe):
        """Flow completo executa sem erros."""
        from src.pipeline.flows import pipeline_etl

        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            result = pipeline_etl(
                tickers=["TEST4.SA"], start="2024-01-01", end="2024-01-31"
            )

        assert mock_load.called
        assert result.complete
        assert result.success_tickers == ("TEST4.SA",)
        assert result.failed_tickers == ()

    def test_partial_flow_returns_explicit_failure_summary(self, mock_dataframe):
        from src.pipeline.flows import pipeline_etl

        with (
            patch(
                "src.pipeline.flows.extract_task",
                side_effect=[mock_dataframe, RuntimeError("fonte indisponível")],
            ),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task"),
        ):
            result = pipeline_etl(
                tickers=["OK4.SA", "FAIL4.SA"],
                start="2024-01-01",
                end="2024-01-31",
            )

        assert not result.complete
        assert result.success_tickers == ("OK4.SA",)
        assert result.failed_tickers == ("FAIL4.SA",)
        assert result.errors == {"FAIL4.SA": "RuntimeError: fonte indisponível"}

    def test_extract_retry_on_failure(self, mock_dataframe):
        """Extract falha e depois sucede -> flow completa."""
        from src.pipeline.flows import pipeline_etl

        # Extract task mockada para retornar dados com sucesso
        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            pipeline_etl(tickers=["TEST4.SA"], start="2024-01-01", end="2024-01-31")

        assert mock_load.called

    def test_custom_tickers(self, mock_dataframe):
        """Tickers customizados são processados."""
        from src.pipeline.flows import pipeline_etl

        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            pipeline_etl(tickers=["CUSTOM3.SA"], start="2024-01-01", end="2024-01-31")

        assert mock_load.called

    def test_single_ticker(self, mock_dataframe):
        """Apenas um ticker processado."""
        from src.pipeline.flows import pipeline_etl

        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            pipeline_etl(tickers=["UNICO3.SA"], start="2024-01-01", end="2024-01-31")

        assert mock_load.call_count == 1

    def test_empty_tickers(self, mock_dataframe):
        """Lista vazia de tickers -> nenhuma task chamada."""
        from src.pipeline.flows import pipeline_etl

        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            pipeline_etl(tickers=[], start="2024-01-01", end="2024-01-31")

        assert not mock_load.called

    def test_default_tickers_from_settings(self, mock_dataframe):
        """Sem argumento tickers, usa settings.default_tickers."""
        from src.pipeline.flows import pipeline_etl

        with (
            patch("src.pipeline.flows.extract_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.transform_task", return_value=mock_dataframe),
            patch("src.pipeline.flows.load_task") as mock_load,
        ):
            pipeline_etl()

        # Deve ter processado os tickers do settings
        assert mock_load.call_count > 0


class TestExtractTask:
    """Testes para extract_task — executa a função diretamente."""

    def test_extract_task_calls_extractor(self, mock_dataframe):
        """extract_task delega ao DataExtractor."""
        from src.pipeline.flows import extract_task

        with patch("src.pipeline.flows.DataExtractor") as MockExtractor:
            instance = MockExtractor.return_value
            instance.download.return_value = mock_dataframe

            result = extract_task("PETR4.SA", "2024-01-01", "2024-01-31")

            pd.testing.assert_frame_equal(result, mock_dataframe)
            instance.download.assert_called_once_with(
                "PETR4.SA", "2024-01-01", "2024-01-31"
            )


class TestTransformTask:
    """Testes para transform_task — executa a função diretamente."""

    def test_transform_task_calls_transformer(self, mock_dataframe):
        """transform_task usa DataTransformer.clean e calculate_indicators."""
        from src.pipeline.flows import transform_task

        with (
            patch(
                "src.pipeline.flows.DataTransformer.clean", return_value=mock_dataframe
            ),
            patch(
                "src.pipeline.flows.DataTransformer.calculate_indicators",
                return_value=mock_dataframe,
            ),
        ):
            result = transform_task(mock_dataframe)

            pd.testing.assert_frame_equal(result, mock_dataframe)


class TestLoadTask:
    """Testes para load_task — executa a função diretamente."""

    def test_load_task_calls_loader(self, mock_dataframe):
        """load_task usa upsert para cotações e indicadores."""
        from src.pipeline.flows import load_task

        with (
            patch("src.pipeline.flows.DataLoader") as MockLoader,
            patch("src.pipeline.flows.get_session"),
        ):
            instance = MockLoader.return_value
            load_task("PETR4.SA", mock_dataframe, mock_dataframe)

            assert instance.upsert_cotacoes.called
            assert instance.upsert_indicators.called
