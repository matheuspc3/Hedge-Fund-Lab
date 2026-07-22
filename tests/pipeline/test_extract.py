"""Testes para o módulo de extração (src/pipeline/extract.py)."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.pipeline.extract import DataExtractor, RetryPolicy


class TestRetryPolicy:
    def test_default_values(self):
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.delay_seconds == 1.0
        assert p.backoff_factor == 2.0

    def test_custom_values(self):
        p = RetryPolicy(max_retries=5, delay_seconds=0.5, backoff_factor=3.0)
        assert p.max_retries == 5
        assert p.delay_seconds == 0.5
        assert p.backoff_factor == 3.0


class TestDataExtractor:
    def test_download_success(self, tmp_path: Path):
        """Download bem-sucedido retorna DataFrame com colunas normalizadas."""
        mock_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )

        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        assert not df.empty
        assert "abertura" in df.columns
        assert "fechamento" in df.columns
        assert "maxima" in df.columns
        assert "minima" in df.columns
        assert "volume" in df.columns
        assert df.iloc[0]["abertura"] == 100.0
        assert df.iloc[0]["fechamento"] == 100.5

    def test_cache_hit(self, tmp_path: Path):
        """Se cache existe, não chama yfinance."""
        ticker = "PETR4.SA"
        cache_path = tmp_path / f"{ticker}.csv"

        # Cria cache manualmente
        cached_df = pd.DataFrame(
            {
                "abertura": [100.0],
                "maxima": [101.0],
                "minima": [99.0],
                "fechamento": [100.5],
                "volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )
        cached_df.to_csv(cache_path)

        with patch("yfinance.download", side_effect=Exception("não deve chamar")):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download(ticker, "2024-01-01", "2024-01-02")

        assert not df.empty
        assert df.iloc[0]["fechamento"] == 100.5

    def test_cache_corrupted_falls_through(self, tmp_path: Path):
        """Cache corrompido → ignora e faz download."""
        ticker = "PETR4.SA"
        cache_path = tmp_path / f"{ticker}.csv"
        cache_path.write_text("conteúdo inválido")

        mock_df = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2024-01-02"]),
        )
        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download(ticker, "2024-01-01", "2024-01-31")

        assert not df.empty

    def test_retry_then_success(self, tmp_path: Path):
        """Falha nas primeiras N-1 tentativas, sucesso na última."""
        mock_df = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2024-01-02"]),
        )
        # Falha 2x, sucesso na 3ª
        side_effects = [Exception("timeout"), Exception("timeout"), mock_df]

        with patch("yfinance.download", side_effect=side_effects):
            extractor = DataExtractor(
                retry_policy=RetryPolicy(max_retries=3, delay_seconds=0.01),
                cache_dir=str(tmp_path),
            )
            df = extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        assert not df.empty
        assert df.iloc[0]["fechamento"] == 100.0

    def test_permanent_failure(self, tmp_path: Path):
        """Todas as tentativas falham → levanta RuntimeError."""
        with patch("yfinance.download", side_effect=Exception("sempre falha")):
            extractor = DataExtractor(
                retry_policy=RetryPolicy(max_retries=2, delay_seconds=0.01),
                cache_dir=str(tmp_path),
            )
            with pytest.raises(RuntimeError, match="falhou após 2 tentativas"):
                extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

    def test_empty_dataframe_raises(self, tmp_path: Path):
        """yfinance retorna DataFrame vazio → ValueError."""
        empty_df = pd.DataFrame()

        with patch("yfinance.download", return_value=empty_df):
            extractor = DataExtractor(
                retry_policy=RetryPolicy(max_retries=1, delay_seconds=0.01),
                cache_dir=str(tmp_path),
            )
            with pytest.raises(RuntimeError, match="dados vazios"):
                extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

    def test_column_normalization_multiindex(self, tmp_path: Path):
        """yfinance com MultiIndex nas colunas é normalizado corretamente."""
        import numpy as np

        arrays = [["Close", "Volume"], ["PETR4.SA", "PETR4.SA"]]
        tuples = list(zip(*arrays))
        mock_df = pd.DataFrame(
            np.array([[100.5, 1_000_000]]),
            index=pd.to_datetime(["2024-01-02"]),
            columns=pd.MultiIndex.from_tuples(tuples),
        )

        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        assert "fechamento" in df.columns
        assert "volume" in df.columns
        assert len(df.columns) == 2  # só as colunas mapeadas

    def test_cache_saves_file(self, tmp_path: Path):
        """Após download, arquivo de cache é salvo."""
        mock_df = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2024-01-02"]),
        )

        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        cache_file = tmp_path / "PETR4.SA.csv"
        assert cache_file.exists()
        assert cache_file.stat().st_size > 0
