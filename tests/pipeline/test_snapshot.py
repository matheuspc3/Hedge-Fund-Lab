"""Contratos de cobertura, proveniência e imutabilidade do dataset."""

import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.backtesting.b3_calendar import B3Calendar
from src.pipeline.snapshot import (
    MANIFEST_SCHEMA_VERSION,
    SNAPSHOT_ID_DIGEST_LENGTH,
    SnapshotIdentityError,
    SnapshotIntegrityError,
    create_dataset_snapshot,
    load_dataset_snapshot,
    snapshot_identity_digest,
    snapshot_identity_payload,
    verify_snapshot_integrity,
)
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


# ── Identidade verificável do manifest ───────────────────────────

COMPLETE_DATES = [
    "2020-01-02",
    "2020-01-03",
    "2020-01-06",
    "2020-01-07",
    "2020-01-08",
    "2020-01-09",
    "2020-01-10",
]
INCOMPLETE_DATES = ["2020-01-02", "2020-01-03", "2020-01-09", "2020-01-10"]


def _rewrite_manifest(snapshot, mutate) -> dict:
    """Edita o manifest publicado sem recalcular a identidade do snapshot.

    Falha se a mutação não mudou nada: um teste de adulteração que não adultera
    passaria por engano.
    """
    original = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    manifest = json.loads(json.dumps(original))
    mutate(manifest)
    assert manifest != original, "a mutação precisa alterar o manifest"
    snapshot.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def test_snapshot_id_ancora_o_digest_da_identidade(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    timestamp, _, digest = snapshot.snapshot_id.rpartition("-")
    assert digest == snapshot_identity_digest(manifest)[:SNAPSHOT_ID_DIGEST_LENGTH]
    assert len(digest) == SNAPSHOT_ID_DIGEST_LENGTH
    # O ID não entra no próprio payload: nada de circularidade.
    assert "snapshot_id" not in snapshot_identity_payload(manifest)
    # O prefixo temporal é coerente com created_at.
    assert timestamp == datetime.fromisoformat(
        manifest["created_at"].replace("Z", "+00:00")
    ).strftime("%Y%m%dT%H%M%S%fZ")
    assert snapshot.path.name == snapshot.snapshot_id


def test_identidade_cobre_todo_o_manifest_menos_o_id(tmp_path: Path):
    """Nenhum campo científico do artefato fica fora da identidade."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    payload = snapshot_identity_payload(manifest)

    assert set(payload) == set(manifest) - {"snapshot_id"}
    assert {
        "schema_version",
        "created_at",
        "source",
        "requested_start",
        "requested_end",
        "effective_start",
        "effective_end",
        "tickers",
        "files",
        "coverage",
        "quality",
        "calendar",
        "pipeline",
        "code",
    } <= set(payload)


def test_snapshot_valido_recarrega_e_reconstroi_o_mesmo_objeto(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)

    reloaded = load_dataset_snapshot(snapshot.path)

    assert reloaded == snapshot
    assert reloaded.identity_digest == snapshot.identity_digest
    verify_snapshot_integrity(reloaded)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m["quality"].update(scientific_ready=False, status="attention"),
        lambda m: m["coverage"][0].update(missing_sessions_count=5),
        lambda m: m["coverage"][0].update(complete=False),
        lambda m: m["coverage"][0].update(coverage_ratio=0.1),
        lambda m: m["files"][0].update(sha256="0" * 64),
        lambda m: m["files"][0].update(size=1),
        lambda m: m.update(tickers=["ITUB4.SA"]),
        lambda m: m["files"][0].update(ticker="ITUB4.SA"),
        lambda m: m.update(requested_start="2019-01-01"),
        lambda m: m.update(effective_end="2030-01-01"),
        lambda m: m["calendar"].update(extra_closures=["2020-01-06"]),
        lambda m: m["source"].update(name="outra-fonte"),
        lambda m: m["pipeline"].update(extractor="outro.extrator"),
        lambda m: m["code"].update(git_dirty=False),
        lambda m: m.update(created_at="2020-01-02T00:00:00.000000Z"),
    ],
    ids=[
        "quality",
        "coverage-missing",
        "coverage-complete",
        "coverage-ratio",
        "files-sha256",
        "files-size",
        "tickers",
        "files-ticker",
        "requested-interval",
        "effective-interval",
        "calendar",
        "source",
        "pipeline",
        "code",
        "created-at",
    ],
)
def test_manifest_adulterado_e_rejeitado(tmp_path: Path, mutate):
    """Adulterar o manifest quebra a identidade, sem tocar em CSV algum."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    csv_before = (snapshot.path / "data/PETR4.SA.csv").read_bytes()

    _rewrite_manifest(snapshot, mutate)

    with pytest.raises(SnapshotIdentityError, match="identity mismatch"):
        load_dataset_snapshot(snapshot.path)
    assert (snapshot.path / "data/PETR4.SA.csv").read_bytes() == csv_before


def test_promover_snapshot_reprovado_pelo_manifest_e_rejeitado(tmp_path: Path):
    """O caso crítico: `scientific_ready` false -> true sem regenerar nada."""
    snapshot, _ = _build(tmp_path, INCOMPLETE_DATES)
    assert snapshot.scientific_ready is False

    _rewrite_manifest(
        snapshot,
        lambda m: m["quality"].update(scientific_ready=True, status="ready"),
    )

    with pytest.raises(SnapshotIdentityError, match="identity mismatch"):
        load_dataset_snapshot(snapshot.path)


def test_snapshot_id_alterado_no_manifest_e_rejeitado(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    last = snapshot.snapshot_id[-1]
    forged = snapshot.snapshot_id[:-1] + ("0" if last != "0" else "1")

    _rewrite_manifest(snapshot, lambda m: m.update(snapshot_id=forged))

    with pytest.raises(SnapshotIdentityError, match="identity mismatch"):
        load_dataset_snapshot(snapshot.path)


def test_snapshot_id_fora_do_formato_e_rejeitado(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)

    _rewrite_manifest(snapshot, lambda m: m.update(snapshot_id="snapshot-bonitinho"))

    with pytest.raises(SnapshotIdentityError, match="not a valid identity token"):
        load_dataset_snapshot(snapshot.path)


def test_prefixo_temporal_incoerente_com_created_at_e_rejeitado(tmp_path: Path):
    """Identidade científica não pode depender só do digest do conteúdo."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))
    del manifest["snapshot_id"]
    digest = snapshot_identity_digest(manifest)[:SNAPSHOT_ID_DIGEST_LENGTH]
    forged_id = f"20191231T235959000000Z-{digest}"
    manifest["snapshot_id"] = forged_id

    forged_dir = snapshot.path.parent / forged_id
    forged_dir.mkdir()
    forged_dir.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(SnapshotIdentityError, match="does not match created_at"):
        load_dataset_snapshot(forged_dir)


def test_manifest_valido_em_diretorio_de_outro_nome_e_rejeitado(tmp_path: Path):
    """Copiar um manifest íntegro para outro diretório não o torna esse snapshot."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    clone = snapshot.path.parent / "outro-diretorio"
    shutil.copytree(snapshot.path, clone)

    with pytest.raises(SnapshotIdentityError, match="does not match manifest"):
        load_dataset_snapshot(clone)
    # O original continua carregável: nada nele foi tocado.
    assert load_dataset_snapshot(snapshot.path).snapshot_id == snapshot.snapshot_id


def test_schema_legado_nao_ganha_confianca_cientifica(tmp_path: Path):
    """Schema 1 é reconhecido, nomeado e recusado — nunca migrado em silêncio."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)

    _rewrite_manifest(snapshot, lambda m: m.update(schema_version=1))

    with pytest.raises(SnapshotIdentityError, match="regenerate the snapshot"):
        load_dataset_snapshot(snapshot.path)


def test_schema_desconhecido_continua_sendo_erro_de_valor(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)

    _rewrite_manifest(snapshot, lambda m: m.update(schema_version=99))

    with pytest.raises(ValueError, match="unsupported snapshot manifest schema_version"):
        load_dataset_snapshot(snapshot.path)


def test_csv_adulterado_com_manifest_intacto_e_pego_pela_integridade(tmp_path: Path):
    """Identidade do manifest e integridade dos arquivos são garantias distintas."""
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    target = snapshot.path / "data/PETR4.SA.csv"
    target.write_bytes(target.read_bytes() + b"2020-01-13,1.0,1.0,1.0,1.0,1.0\n")

    reloaded = load_dataset_snapshot(snapshot.path)  # identidade intacta

    assert reloaded.snapshot_id == snapshot.snapshot_id
    with pytest.raises(SnapshotIntegrityError, match="size mismatch"):
        verify_snapshot_integrity(reloaded)


def test_estruturas_do_snapshot_nao_aceitam_mutacao_direta(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)

    with pytest.raises(TypeError):
        snapshot.quality["scientific_ready"] = False  # type: ignore[index]
    with pytest.raises(TypeError):
        snapshot.files[0]["sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(TypeError):
        snapshot.coverage[0]["complete"] = False  # type: ignore[index]

    assert snapshot.scientific_ready is True


def test_evidencia_do_snapshot_e_canonica_e_independente_do_disco(tmp_path: Path):
    snapshot, _ = _build(tmp_path, COMPLETE_DATES)
    evidence = snapshot.evidence()
    manifest_before = evidence.manifest

    _rewrite_manifest(snapshot, lambda m: m.update(tickers=["ITUB4.SA"]))
    shutil.rmtree(snapshot.path)

    assert evidence.manifest == manifest_before
    assert evidence.snapshot_id == snapshot.snapshot_id
    assert evidence.identity_digest == snapshot_identity_digest(manifest_before)
    assert evidence.schema_version == MANIFEST_SCHEMA_VERSION
    assert json.loads(evidence.manifest_json) == manifest_before
