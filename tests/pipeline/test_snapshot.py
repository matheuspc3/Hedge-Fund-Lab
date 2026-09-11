"""Contratos de cobertura, proveniência e imutabilidade do dataset."""

import hashlib
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.backtesting.b3_calendar import B3Calendar
from src.pipeline.snapshot import create_dataset_snapshot
from src.pipeline.transform import DataQualityError


def _ohlcv(dates: list[str]) -> pd.DataFrame:
    base = np.arange(len(dates), dtype=float) + 100
    return pd.DataFrame(
        {
            "abertura": base,
            "maxima": base + 1,
            "minima": base - 1,
            "fechamento": base + 0.5,
            "volume": np.full(len(dates), 1_000_000.0),
        },
        index=pd.to_datetime(dates),
    )


class StubExtractor:
    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.frames = frames
        self.calls: list[tuple[str, str, str]] = []

    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        self.calls.append((ticker, start, end))
        return self.frames[ticker].copy()


def _build(
    tmp_path: Path,
    dates: list[str],
    *,
    start: str = "2020-01-02",
    end: str = "2020-01-10",
    calendar: B3Calendar | None = None,
):
    extractor = StubExtractor({"PETR4.SA": _ohlcv(dates)})
    snapshot = create_dataset_snapshot(
        ["PETR4.SA"],
        start,
        end,
        extractor=extractor,  # type: ignore[arg-type]
        calendar=calendar,
        snapshot_dir=tmp_path / "snapshots",
        repository_dir=tmp_path,
    )
    return snapshot, extractor


def test_snapshot_materializes_csv_manifest_hash_and_provenance(tmp_path: Path):
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
    ]
    snapshot, extractor = _build(tmp_path, dates)

    assert snapshot.path.is_dir()
    assert snapshot.manifest_path.is_file()
    data_path = snapshot.path / "data/PETR4.SA.csv"
    assert data_path.is_file()
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    file_record = manifest["files"][0]
    assert file_record["sha256"] == hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert file_record["size"] == data_path.stat().st_size
    assert manifest["source"]["name"] == "yfinance"
    assert manifest["tickers"] == ["PETR4.SA"]
    assert manifest["requested_start"] == "2020-01-02"
    assert manifest["requested_end"] == "2020-01-10"
    assert manifest["effective_start"] == "2020-01-02"
    assert manifest["effective_end"] == "2020-01-10"
    assert manifest["coverage"][0]["rows"] == 7
    assert manifest["quality"]["scientific_ready"] is True
    assert extractor.calls == [("PETR4.SA", "2020-01-02", "2020-01-10")]


def test_snapshot_is_detached_from_mutable_source_and_hash_detects_change(
    tmp_path: Path,
):
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
    ]
    snapshot, extractor = _build(tmp_path, dates)
    path = snapshot.path / "data/PETR4.SA.csv"
    original = path.read_bytes()
    expected_hash = snapshot.files[0]["sha256"]

    extractor.frames["PETR4.SA"].iloc[0, 0] = 999.0
    assert path.read_bytes() == original
    path.write_bytes(original + b"\n")
    assert hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash


def test_snapshot_does_not_overwrite_existing_id(tmp_path: Path):
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
    ]
    with patch("src.pipeline.snapshot._make_snapshot_id", return_value="fixed-id"):
        first, _ = _build(tmp_path, dates)
        original_manifest = first.manifest_path.read_bytes()
        with pytest.raises(FileExistsError, match="snapshot already exists"):
            _build(tmp_path, dates)

    assert first.manifest_path.read_bytes() == original_manifest


@pytest.mark.parametrize(
    ("dates", "missing"),
    [
        (["2020-01-08", "2020-01-09", "2020-01-10"], "2020-01-02"),
        (["2020-01-02", "2020-01-03", "2020-01-06"], "2020-01-07"),
        (
            [
                "2020-01-02",
                "2020-01-03",
                "2020-01-06",
                "2020-01-08",
                "2020-01-09",
                "2020-01-10",
            ],
            "2020-01-07",
        ),
    ],
    ids=["partial-start", "partial-end", "internal-gap"],
)
def test_incomplete_coverage_is_never_scientific_ready(
    tmp_path: Path, dates: list[str], missing: str
):
    snapshot, _ = _build(tmp_path, dates)
    report = snapshot.coverage[0]

    assert snapshot.quality["status"] == "attention_required"
    assert snapshot.scientific_ready is False
    assert report["complete"] is False
    assert missing in report["missing_sessions"]


def test_partial_source_regression_does_not_report_complete(tmp_path: Path):
    snapshot, _ = _build(
        tmp_path,
        ["2020-01-08", "2020-01-09", "2020-01-10"],
        start="2020-01-01",
        end="2020-01-10",
    )
    report = snapshot.coverage[0]

    assert report["expected_sessions"] == 7
    assert report["missing_sessions"] == [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
    ]
    assert report["complete"] is False
    assert snapshot.scientific_ready is False


def test_weekends_do_not_create_false_missing_sessions(tmp_path: Path):
    snapshot, _ = _build(
        tmp_path,
        ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"],
        start="2020-01-04",
        end="2020-01-12",
    )
    report = snapshot.coverage[0]

    assert report["first_expected_session"] == "2020-01-06"
    assert report["last_expected_session"] == "2020-01-10"
    assert report["missing_sessions_count"] == 0
    assert snapshot.scientific_ready is True


def test_known_holiday_does_not_create_false_missing_session(tmp_path: Path):
    snapshot, _ = _build(
        tmp_path,
        ["2023-04-20", "2023-04-24"],
        start="2023-04-20",
        end="2023-04-24",
    )

    assert snapshot.coverage[0]["expected_sessions"] == 2
    assert snapshot.coverage[0]["missing_sessions"] == []


def test_interval_without_expected_session_is_explicit_attention(tmp_path: Path):
    empty = _ohlcv([])
    snapshot = create_dataset_snapshot(
        ["PETR4.SA"],
        "2026-12-24",
        "2026-12-25",
        extractor=StubExtractor({"PETR4.SA": empty}),  # type: ignore[arg-type]
        snapshot_dir=tmp_path / "snapshots",
        repository_dir=tmp_path,
    )

    assert snapshot.coverage[0]["status"] == "no_expected_sessions"
    assert snapshot.coverage[0]["expected_sessions"] == 0
    assert snapshot.scientific_ready is False


def test_calendar_exceptions_change_expected_sessions_and_manifest(tmp_path: Path):
    calendar = B3Calendar(
        extra_closures=frozenset({date(2024, 1, 3)}),
        extra_openings=frozenset({date(2024, 1, 6)}),
    )
    snapshot, _ = _build(
        tmp_path,
        ["2024-01-02", "2024-01-04", "2024-01-05", "2024-01-06"],
        start="2024-01-02",
        end="2024-01-06",
        calendar=calendar,
    )
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))

    assert snapshot.coverage[0]["complete"] is True
    assert manifest["calendar"]["extra_closures"] == ["2024-01-03"]
    assert manifest["calendar"]["extra_openings"] == ["2024-01-06"]
    assert manifest["calendar"]["official_historical_source"] is False


def test_invalid_ohlcv_does_not_create_snapshot(tmp_path: Path):
    frame = _ohlcv(["2020-01-02"])
    frame.iloc[0, frame.columns.get_loc("fechamento")] = 0.0

    with pytest.raises(DataQualityError, match="estritamente positivo"):
        create_dataset_snapshot(
            ["PETR4.SA"],
            "2020-01-02",
            "2020-01-02",
            extractor=StubExtractor({"PETR4.SA": frame}),  # type: ignore[arg-type]
            snapshot_dir=tmp_path / "snapshots",
            repository_dir=tmp_path,
        )

    assert not (tmp_path / "snapshots").exists()


def test_failed_required_ticker_does_not_publish_partial_snapshot(tmp_path: Path):
    class FailingExtractor(StubExtractor):
        def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
            if ticker == "VALE3.SA":
                raise RuntimeError("fonte indisponível")
            return super().download(ticker, start, end)

    extractor = FailingExtractor(
        {
            "PETR4.SA": _ohlcv(["2020-01-02"]),
            "VALE3.SA": _ohlcv(["2020-01-02"]),
        }
    )

    with pytest.raises(RuntimeError, match="fonte indisponível"):
        create_dataset_snapshot(
            ["PETR4.SA", "VALE3.SA"],
            "2020-01-02",
            "2020-01-02",
            extractor=extractor,  # type: ignore[arg-type]
            snapshot_dir=tmp_path / "snapshots",
            repository_dir=tmp_path,
        )

    assert not (tmp_path / "snapshots").exists()


def test_git_metadata_is_recorded_without_using_real_repository(tmp_path: Path):
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
    ]
    metadata = {"git_commit": "a" * 40, "git_dirty": True}
    with patch("src.pipeline.snapshot._git_metadata", return_value=metadata):
        snapshot, _ = _build(tmp_path, dates)

    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    assert manifest["code"] == metadata


def test_manifest_serialization_is_stable_and_sorted(tmp_path: Path):
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
        "2020-01-10",
    ]
    snapshot, _ = _build(tmp_path, dates)
    text = snapshot.manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(text)

    assert (
        text == json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
