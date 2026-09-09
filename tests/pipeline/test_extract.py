"""Testes para o módulo de extração (src/pipeline/extract.py)."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.pipeline.extract import DataExtractor, RetryPolicy
from src.pipeline.transform import DataQualityError


def _ohlcv(dates: list[str], *, normalized: bool = False) -> pd.DataFrame:
    base = np.arange(len(dates), dtype=float) + 100
    columns = {
        "abertura" if normalized else "Open": base,
        "maxima" if normalized else "High": base + 1,
        "minima" if normalized else "Low": base - 1,
        "fechamento" if normalized else "Close": base + 0.5,
        "volume" if normalized else "Volume": np.full(len(dates), 1_000_000),
    }
    return pd.DataFrame(columns, index=pd.to_datetime(dates))


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
        mock_df = _ohlcv(["2024-01-02"])

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

        cached_df = _ohlcv(["2024-01-01", "2024-01-02"], normalized=True)
        cached_df.to_csv(cache_path)

        with patch("yfinance.download", side_effect=Exception("não deve chamar")):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download(ticker, "2024-01-01", "2024-01-02")

        assert not df.empty
        assert df.index.tolist() == pd.to_datetime(["2024-01-01", "2024-01-02"]).tolist()
        assert df.iloc[0]["fechamento"] == 100.5

    def test_cache_corrupted_falls_through(self, tmp_path: Path):
        """Cache corrompido → ignora e faz download."""
        ticker = "PETR4.SA"
        cache_path = tmp_path / f"{ticker}.csv"
        cache_path.write_text("conteúdo inválido")

        mock_df = _ohlcv(["2024-01-02"])
        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download(ticker, "2024-01-01", "2024-01-31")

        assert not df.empty

    def test_retry_then_success(self, tmp_path: Path):
        """Falha nas primeiras N-1 tentativas, sucesso na última."""
        mock_df = _ohlcv(["2024-01-02"])
        # Falha 2x, sucesso na 3ª
        side_effects = [Exception("timeout"), Exception("timeout"), mock_df]

        with patch("yfinance.download", side_effect=side_effects):
            extractor = DataExtractor(
                retry_policy=RetryPolicy(max_retries=3, delay_seconds=0.01),
                cache_dir=str(tmp_path),
            )
            df = extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        assert not df.empty
        assert df.iloc[0]["fechamento"] == 100.5

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
        arrays = [
            ["Open", "High", "Low", "Close", "Volume"],
            ["PETR4.SA"] * 5,
        ]
        tuples = list(zip(*arrays))
        mock_df = pd.DataFrame(
            np.array([[100.0, 101.0, 99.0, 100.5, 1_000_000]]),
            index=pd.to_datetime(["2024-01-02"]),
            columns=pd.MultiIndex.from_tuples(tuples),
        )

        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            df = extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        assert "fechamento" in df.columns
        assert "volume" in df.columns
        assert len(df.columns) == 5  # só as colunas mapeadas

    def test_cache_saves_file(self, tmp_path: Path):
        """Após download, arquivo de cache é salvo."""
        mock_df = _ohlcv(["2024-01-02"])

        with patch("yfinance.download", return_value=mock_df):
            extractor = DataExtractor(cache_dir=str(tmp_path))
            extractor.download("PETR4.SA", "2024-01-01", "2024-01-31")

        cache_file = tmp_path / "PETR4.SA.csv"
        assert cache_file.exists()
        assert cache_file.stat().st_size > 0

    def test_complete_cache_is_sliced_without_network(self, tmp_path: Path):
        ticker = "PETR4.SA"
        cached = _ohlcv(
            ["2019-12-31", "2020-01-01", "2021-12-31", "2022-01-03"],
            normalized=True,
        )
        cached.to_csv(tmp_path / f"{ticker}.csv")

        with patch("yfinance.download", side_effect=AssertionError("rede chamada")):
            result = DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2020-01-01", "2021-12-31"
            )

        assert result.index.tolist() == pd.to_datetime(
            ["2020-01-01", "2021-12-31"]
        ).tolist()

    @pytest.mark.parametrize(
        ("cache_dates", "start", "end"),
        [
            (["2024-01-01", "2026-01-02"], "2016-01-01", "2025-12-31"),
            (["2016-01-01", "2023-12-29"], "2016-01-01", "2025-12-31"),
        ],
        ids=["cache-starts-too-late", "cache-ends-too-early"],
    )
    def test_partial_cache_triggers_full_requested_download(
        self,
        tmp_path: Path,
        cache_dates: list[str],
        start: str,
        end: str,
    ):
        ticker = "PETR4.SA"
        _ohlcv(cache_dates, normalized=True).to_csv(tmp_path / f"{ticker}.csv")
        fresh = _ohlcv([start, end])

        with patch("yfinance.download", return_value=fresh) as mock_download:
            result = DataExtractor(cache_dir=str(tmp_path)).download(ticker, start, end)

        mock_download.assert_called_once_with(
            ticker,
            start=start,
            end=(pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            progress=False,
        )
        assert result.index.min() == pd.Timestamp(start)
        assert result.index.max() == pd.Timestamp(end)

    def test_exact_cache_boundaries_are_a_hit(self, tmp_path: Path):
        ticker = "PETR4.SA"
        cached = _ohlcv(["2020-01-01", "2021-12-31"], normalized=True)
        cached.to_csv(tmp_path / f"{ticker}.csv")

        with patch("yfinance.download", side_effect=AssertionError("rede chamada")):
            result = DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2020-01-01", "2021-12-31"
            )

        pd.testing.assert_frame_equal(result, cached, check_freq=False)

    def test_partial_cache_combines_overlap_and_preserves_extra_dates(
        self, tmp_path: Path
    ):
        ticker = "PETR4.SA"
        cached = _ohlcv(["2024-01-02", "2024-01-03"], normalized=True)
        cached.to_csv(tmp_path / f"{ticker}.csv")
        fresh = _ohlcv(["2024-01-01", "2024-01-02"])
        fresh.loc[pd.Timestamp("2024-01-02"), ["Open", "High", "Low", "Close"]] = [
            200.0,
            201.0,
            199.0,
            200.5,
        ]

        with patch("yfinance.download", return_value=fresh):
            result = DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2024-01-01", "2024-01-02"
            )

        persisted = pd.read_csv(
            tmp_path / f"{ticker}.csv", index_col=0, parse_dates=True
        )
        assert result.index.max() == pd.Timestamp("2024-01-02")
        assert persisted.index.tolist() == pd.to_datetime(
            ["2024-01-01", "2024-01-02", "2024-01-03"]
        ).tolist()
        assert persisted.loc[pd.Timestamp("2024-01-02"), "fechamento"] == 200.5

    def test_duplicate_dates_in_cache_fail_fast(self, tmp_path: Path):
        ticker = "PETR4.SA"
        cached = _ohlcv(["2024-01-02", "2024-01-02"], normalized=True)
        cached.to_csv(tmp_path / f"{ticker}.csv")

        with pytest.raises(DataQualityError, match="datas duplicadas"):
            DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2024-01-02", "2024-01-02"
            )

    def test_yfinance_receives_exclusive_end(self, tmp_path: Path):
        ticker = "PETR4.SA"
        fresh = _ohlcv(["2024-01-31"])

        with patch("yfinance.download", return_value=fresh) as mock_download:
            DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2024-01-01", "2024-01-31"
            )

        mock_download.assert_called_once_with(
            ticker,
            start="2024-01-01",
            end="2024-02-01",
            progress=False,
        )

    def test_invalid_downloaded_bar_fails_before_cache(self, tmp_path: Path):
        ticker = "PETR4.SA"
        fresh = _ohlcv(["2024-01-02"])
        fresh.iloc[0, fresh.columns.get_loc("Close")] = 0

        with (
            patch("yfinance.download", return_value=fresh),
            pytest.raises(DataQualityError, match="estritamente positivo"),
        ):
            DataExtractor(cache_dir=str(tmp_path)).download(
                ticker, "2024-01-01", "2024-01-31"
            )

        assert not (tmp_path / f"{ticker}.csv").exists()
