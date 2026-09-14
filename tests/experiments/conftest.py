"""Snapshot sintético materializado de verdade, sem rede nem cache mutável."""

import json
from datetime import date
from pathlib import Path
from typing import Any, Callable, cast

import numpy as np
import pandas as pd
import pytest

import src.experiments.runner as runner_module
from src.backtesting.b3_calendar import B3Calendar
from src.pipeline.snapshot import DatasetSnapshot, create_dataset_snapshot

TICKERS = ("PETR4.SA", "VALE3.SA")
START = "2020-01-02"
END = "2020-03-31"


class StubExtractor:
    """Devolve séries pré-construídas; o snapshot é o único caminho de dados."""

    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self.frames[ticker].copy()

    def download_actions(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Universo sintético sem eventos corporativos: evidência vazia, não ausente."""
        return pd.DataFrame(
            {"dividends": [], "splits": []},
            index=pd.DatetimeIndex([], name="date"),
            dtype=float,
        )


def price_series(sessions: pd.DatetimeIndex, base: float, wave: float) -> pd.DataFrame:
    """Preços determinísticos com oscilação suficiente para cruzar médias."""
    steps = np.arange(len(sessions), dtype=float)
    close = base + steps * 0.35 + wave * np.sin(steps / 3.0) * 4.0
    open_ = close * 0.985
    return pd.DataFrame(
        {
            "abertura": open_,
            "maxima": close + 1.0,
            "minima": open_ - 1.0,
            "fechamento": close,
            "volume": np.full(len(sessions), 1_000_000.0),
        },
        index=sessions,
    )


def build_snapshot(
    snapshot_dir: Path,
    repository_dir: Path,
    *,
    tickers: tuple[str, ...] = TICKERS,
    drop_sessions: int = 0,
) -> DatasetSnapshot:
    """Materializa um snapshot real.

    ``drop_sessions`` remove pregões do meio do recorte e produz um artefato
    legitimamente incompleto: ``scientific_ready=false`` obtido pelo próprio
    pipeline, com identidade válida. É a única forma honesta de exercitar o
    gate científico agora que editar o manifest quebra a identidade.
    """
    calendar = B3Calendar()
    sessions = pd.DatetimeIndex(
        calendar.sessions_between(
            cast(date, pd.Timestamp(START).date()),
            cast(date, pd.Timestamp(END).date()),
        )
    )
    frames = {
        ticker: price_series(sessions, 20.0 + index * 30.0, 1.0 - index * 0.4)
        for index, ticker in enumerate(tickers)
    }
    if drop_sessions:
        frames = {
            ticker: frame.drop(frame.index[10 : 10 + drop_sessions])
            for ticker, frame in frames.items()
        }
    return create_dataset_snapshot(
        list(tickers),
        START,
        END,
        extractor=StubExtractor(frames),  # type: ignore[arg-type]
        calendar=calendar,
        snapshot_dir=snapshot_dir,
        repository_dir=repository_dir,
    )


CLEAN_COMMIT = "0" * 40


@pytest.fixture(autouse=True)
def clean_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os testes rodam como se o repositório estivesse limpo, por padrão.

    O guard do runner é fail-closed estrito e os testes não vivem dentro de um
    checkout Git. Quem testa proveniência sobrescreve este default.
    """
    monkeypatch.setattr(
        runner_module,
        "_git_metadata",
        lambda repository_dir: {"git_commit": CLEAN_COMMIT, "git_dirty": False},
    )


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


@pytest.fixture
def runs_dir(tmp_path: Path) -> Path:
    return tmp_path / "runs"


@pytest.fixture
def snapshot(snapshot_dir: Path, tmp_path: Path) -> DatasetSnapshot:
    built = build_snapshot(snapshot_dir, tmp_path)
    assert built.scientific_ready, "fixture must start from a valid snapshot"
    return built


@pytest.fixture
def incomplete_snapshot(snapshot_dir: Path, tmp_path: Path) -> DatasetSnapshot:
    """Snapshot com lacuna real de pregões: reprovado no gate, identidade válida."""
    built = build_snapshot(snapshot_dir, tmp_path, drop_sessions=3)
    assert not built.scientific_ready, "fixture precisa reprovar no gate científico"
    return built


@pytest.fixture
def make_snapshot():
    """Materializa outro snapshot com exatamente os mesmos dados."""
    return build_snapshot


@pytest.fixture
def tamper_manifest():
    return _tamper_manifest


@pytest.fixture
def tamper_csv():
    return _tamper_csv


def _tamper_manifest(
    snapshot: DatasetSnapshot, mutate: Callable[[dict[str, Any]], None]
) -> None:
    """Edita o manifest publicado sem recalcular a identidade do snapshot."""
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    snapshot.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _tamper_csv(snapshot: DatasetSnapshot) -> Path:
    """Altera um preço depois da materialização, sem tocar no manifest."""
    target = snapshot.path / snapshot.files[0]["path"]
    lines = target.read_text(encoding="utf-8").splitlines()
    fields = lines[1].split(",")
    fields[1] = str(float(fields[1]) * 2.0)
    lines[1] = ",".join(fields)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return target
