"""Rename atômico tolerante a bloqueio transitório do sistema (Windows)."""

from pathlib import Path

import pytest

import src.artifacts as artifacts
from src.artifacts import rename_with_retry


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts.time, "sleep", lambda seconds: None)


def flaky_rename(monkeypatch: pytest.MonkeyPatch, failures: int, error: type) -> dict:
    calls = {"n": 0}
    real = Path.rename

    def rename(self: Path, target: Path) -> Path:
        calls["n"] += 1
        if calls["n"] <= failures:
            raise error("[WinError 5] Acesso negado")
        return real(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    return calls


def test_bloqueio_transitorio_e_superado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / ".tmp-x"
    source.mkdir()
    calls = flaky_rename(monkeypatch, failures=3, error=PermissionError)
    rename_with_retry(source, tmp_path / "run")
    assert (tmp_path / "run").is_dir() and calls["n"] == 4


def test_bloqueio_persistente_falha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / ".tmp-x"
    source.mkdir()
    calls = flaky_rename(monkeypatch, failures=100, error=PermissionError)
    with pytest.raises(PermissionError):
        rename_with_retry(source, tmp_path / "run")
    assert calls["n"] == artifacts.RENAME_ATTEMPTS


def test_outro_erro_nao_e_repetido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / ".tmp-x"
    source.mkdir()
    calls = flaky_rename(monkeypatch, failures=100, error=FileNotFoundError)
    with pytest.raises(FileNotFoundError):
        rename_with_retry(source, tmp_path / "run")
    assert calls["n"] == 1
