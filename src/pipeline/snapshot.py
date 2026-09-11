"""Materialização imutável e auditável de datasets OHLCV."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pandas as pd

from src.backtesting.b3_calendar import B3Calendar
from src.config import settings
from src.pipeline.extract import DataExtractor
from src.pipeline.transform import validate_ohlcv

MANIFEST_SCHEMA_VERSION = 1
MISSING_SESSION_SAMPLE_LIMIT = 50


@dataclass(frozen=True)
class DatasetSnapshot:
    """Descrição do artefato materializado em ``data/snapshots``."""

    snapshot_id: str
    path: Path
    created_at: str
    requested_start: str
    requested_end: str
    effective_start: str | None
    effective_end: str | None
    tickers: tuple[str, ...]
    files: tuple[dict[str, Any], ...]
    coverage: tuple[dict[str, Any], ...]
    quality: dict[str, Any]

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @property
    def scientific_ready(self) -> bool:
        return bool(self.quality["scientific_ready"])


def analyze_session_coverage(
    ticker: str,
    df: pd.DataFrame,
    requested_start: str,
    requested_end: str,
    calendar: B3Calendar,
) -> dict[str, Any]:
    """Compara barras observadas com sessões esperadas pelo calendário local."""
    start = cast(pd.Timestamp, pd.Timestamp(requested_start)).normalize()
    end = cast(pd.Timestamp, pd.Timestamp(requested_end)).normalize()
    expected = calendar.sessions_between(start.date(), end.date())
    observed = {
        cast(pd.Timestamp, value).date() for value in cast(pd.DatetimeIndex, df.index)
    }
    missing = sorted(set(expected) - observed)
    unexpected = sorted(observed - set(expected))
    first_expected = calendar.first_session_on_or_after(start.date(), end.date())
    last_expected = calendar.last_session_on_or_before(start.date(), end.date())
    expected_count = len(expected)
    observed_expected_count = expected_count - len(missing)
    complete = bool(expected) and not missing and not unexpected

    return {
        "ticker": ticker,
        "requested_start": start.date().isoformat(),
        "requested_end": end.date().isoformat(),
        "first_expected_session": (
            first_expected.isoformat() if first_expected else None
        ),
        "last_expected_session": last_expected.isoformat() if last_expected else None,
        "effective_start": (
            cast(pd.Timestamp, df.index[0]).date().isoformat() if len(df) else None
        ),
        "effective_end": (
            cast(pd.Timestamp, df.index[-1]).date().isoformat() if len(df) else None
        ),
        "rows": len(df),
        "expected_sessions": expected_count,
        "observed_expected_sessions": observed_expected_count,
        "missing_sessions_count": len(missing),
        "missing_sessions": [
            value.isoformat() for value in missing[:MISSING_SESSION_SAMPLE_LIMIT]
        ],
        "missing_sessions_truncated": len(missing) > MISSING_SESSION_SAMPLE_LIMIT,
        "unexpected_sessions_count": len(unexpected),
        "unexpected_sessions": [
            value.isoformat() for value in unexpected[:MISSING_SESSION_SAMPLE_LIMIT]
        ],
        "coverage_ratio": (
            observed_expected_count / expected_count if expected_count else None
        ),
        "ohlcv_valid": True,
        "complete": complete,
        "status": (
            "complete"
            if complete
            else "no_expected_sessions"
            if not expected
            else "attention_required"
        ),
    }


def create_dataset_snapshot(
    tickers: list[str],
    start: str,
    end: str,
    *,
    extractor: DataExtractor | None = None,
    calendar: B3Calendar | None = None,
    snapshot_dir: str | Path | None = None,
    repository_dir: str | Path | None = None,
) -> DatasetSnapshot:
    """Cria uma cópia imutável dos dados usados e seu manifest determinístico.

    Lacunas não são preenchidas nem interpretadas como corrupção. O artefato é
    criado com ``scientific_ready=false`` e ``attention_required`` para permitir
    auditoria, mas consumidores científicos devem rejeitá-lo.
    """
    requested_start, requested_end = DataExtractor._parse_interval(start, end)
    ordered_tickers = tuple(sorted(set(tickers)))
    if not ordered_tickers:
        raise ValueError("at least one ticker is required")

    extractor = extractor or DataExtractor()
    calendar = calendar or B3Calendar()
    root = Path(snapshot_dir or settings.snapshot_dir)
    repo = Path(repository_dir or Path.cwd())

    frames: dict[str, pd.DataFrame] = {}
    coverage: list[dict[str, Any]] = []
    for ticker in ordered_tickers:
        _validate_ticker(ticker)
        frame = extractor.download(ticker, start, end)
        validate_ohlcv(frame)
        frames[ticker] = frame.copy()
        coverage.append(analyze_session_coverage(ticker, frame, start, end, calendar))

    created = datetime.now(timezone.utc)
    created_at = created.isoformat(timespec="microseconds").replace("+00:00", "Z")
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f".tmp-{uuid4().hex}"
    staging_data = staging / "data"
    staging_data.mkdir(parents=True)

    try:
        files = _materialize_files(frames, staging_data)
        snapshot_id = _make_snapshot_id(
            created,
            ordered_tickers,
            requested_start.date().isoformat(),
            requested_end.date().isoformat(),
            files,
            calendar,
        )
        target = root / snapshot_id
        if target.exists():
            raise FileExistsError(f"snapshot already exists: {target}")

        complete = all(item["complete"] for item in coverage)
        effective_starts = [
            item["effective_start"] for item in coverage if item["effective_start"]
        ]
        effective_ends = [
            item["effective_end"] for item in coverage if item["effective_end"]
        ]
        quality = {
            "status": "ready" if complete else "attention_required",
            "scientific_ready": complete,
            "ohlcv_valid": True,
            "all_tickers_complete": complete,
            "tickers_attention_required": [
                item["ticker"] for item in coverage if not item["complete"]
            ],
        }
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "created_at": created_at,
            "source": {
                "name": "yfinance",
                "version": _package_version("yfinance"),
                "price_adjustment": (
                    "provider default; auto_adjust is not explicitly configured"
                ),
            },
            "requested_start": requested_start.date().isoformat(),
            "requested_end": requested_end.date().isoformat(),
            "effective_start": min(effective_starts) if effective_starts else None,
            "effective_end": max(effective_ends) if effective_ends else None,
            "tickers": list(ordered_tickers),
            "files": files,
            "coverage": coverage,
            "quality": quality,
            "calendar": _calendar_metadata(calendar),
            "pipeline": {
                "project": "Hedge-Fund-Lab",
                "project_version": _package_version("hedge-fund-lab"),
                "extractor": "src.pipeline.extract.DataExtractor",
                "quality_gate": "src.pipeline.transform.validate_ohlcv",
                "python": platform.python_version(),
            },
            "code": _git_metadata(repo),
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        staging.rename(target)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return DatasetSnapshot(
        snapshot_id=snapshot_id,
        path=target,
        created_at=created_at,
        requested_start=manifest["requested_start"],
        requested_end=manifest["requested_end"],
        effective_start=manifest["effective_start"],
        effective_end=manifest["effective_end"],
        tickers=ordered_tickers,
        files=tuple(files),
        coverage=tuple(coverage),
        quality=quality,
    )


def _materialize_files(
    frames: dict[str, pd.DataFrame], data_dir: Path
) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for ticker, frame in frames.items():
        path = data_dir / f"{ticker}.csv"
        materialized = frame.copy()
        materialized.index.name = "date"
        materialized.to_csv(path, date_format="%Y-%m-%d", lineterminator="\n")
        files.append(
            {
                "ticker": ticker,
                "path": path.relative_to(data_dir.parent).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return files


def _make_snapshot_id(
    created: datetime,
    tickers: tuple[str, ...],
    start: str,
    end: str,
    files: list[dict[str, Any]],
    calendar: B3Calendar,
) -> str:
    identity = {
        "tickers": tickers,
        "start": start,
        "end": end,
        "files": files,
        "calendar": _calendar_metadata(calendar),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    return f"{created.strftime('%Y%m%dT%H%M%S%fZ')}-{digest}"


def _calendar_metadata(calendar: B3Calendar) -> dict[str, Any]:
    return {
        "name": "B3Calendar",
        "rule_version": "local-rules-v1",
        "official_historical_source": False,
        "limitation": (
            "Local recurring rules plus explicit exceptions; pending validation "
            "against an official versioned B3 calendar."
        ),
        "extra_closures": sorted(value.isoformat() for value in calendar.extra_closures),
        "extra_openings": sorted(value.isoformat() for value in calendar.extra_openings),
    }


def _git_metadata(repository_dir: Path) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"git_commit": commit, "git_dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"git_commit": None, "git_dirty": None}


def _package_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _validate_ticker(ticker: str) -> None:
    if (
        not ticker
        or Path(ticker).name != ticker
        or ticker in {".", ".."}
        or re.fullmatch(r"[A-Za-z0-9.^_=+\-]+", ticker) is None
    ):
        raise ValueError(f"invalid ticker for snapshot path: {ticker!r}")
