"""Orquestração experimental: guards, isolamento, reprodutibilidade e manifest.

Estes testes exercitam a camada de orquestração. A correção financeira
(execução em ``open(t+1)``, custos, caixa, invariância de ordem) pertence à
suíte da arena e não é duplicada aqui.
"""

import hashlib
import json
from dataclasses import fields
from pathlib import Path

import pandas as pd
import pytest

import src.experiments.runner as runner_module
import src.pipeline.snapshot as snapshot_module
from src.backtesting.engine import BacktestResult
from src.experiments.participants import build_participant
from src.experiments.runner import (
    DirtyRepositoryError,
    ExperimentRunner,
    RunResult,
)
from src.experiments.spec import (
    CostSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
    canonical_json,
)
from src.pipeline.snapshot import (
    DatasetSnapshot,
    SnapshotEvidence,
    SnapshotIdentityError,
    SnapshotIntegrityError,
    SnapshotNotReadyError,
)

SMA = ParticipantSpec(
    "sma_cross", {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15}
)
EQUAL_WEIGHT = ParticipantSpec("equal_weight", {"rebalance_freq": 10})
MIN_VARIANCE = ParticipantSpec(
    "min_variance", {"window": 10, "rebalance_freq": 15}
)


def spec_for(snapshot: DatasetSnapshot, participant: ParticipantSpec) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=participant,
        initial_capital=100_000.0,
        costs=CostSpec(brokerage_fixed=1.0, spread_bps=15.0, tax_rate=0.001),
        metrics=MetricSpec(),
    )


def runner_for(
    snapshot: DatasetSnapshot,
    participant: ParticipantSpec,
    snapshot_dir: Path,
    runs_dir: Path,
    repository_dir: Path,
    *,
    allow_dirty: bool = False,
) -> ExperimentRunner:
    return ExperimentRunner(
        spec_for(snapshot, participant),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=repository_dir,
        allow_dirty=allow_dirty,
    )


def set_provenance(
    monkeypatch: pytest.MonkeyPatch, *, dirty: bool | None, commit: str | None = "abc123"
) -> None:
    """Fixa a proveniência Git: o estado do repo real não pode reger o teste."""
    monkeypatch.setattr(
        runner_module,
        "_git_metadata",
        lambda repository_dir: {"git_commit": commit, "git_dirty": dirty},
    )


def published_runs(runs_dir: Path) -> list[Path]:
    return sorted(runs_dir.iterdir()) if runs_dir.exists() else []


def signature(result: RunResult) -> list[tuple]:
    return [
        (str(trade.date), trade.ticker, trade.type, trade.price, trade.quantity,
         trade.cost)
        for trade in result.trades
    ]


# ── Guards do snapshot ───────────────────────────────────────────


def test_snapshot_nao_scientific_ready_bloqueia_antes_da_arena(
    incomplete_snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    """Lacuna real de pregões, identidade íntegra: o gate científico barra."""
    runner = runner_for(incomplete_snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(SnapshotNotReadyError, match="scientific coverage gate"):
        runner.run_and_persist()

    assert published_runs(runs_dir) == []


def test_manifest_adulterado_bloqueia_antes_do_gate_cientifico(
    incomplete_snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    tamper_manifest,
) -> None:
    """Promover um snapshot reprovado editando o manifest não funciona."""

    def approve(manifest: dict) -> None:
        manifest["quality"]["scientific_ready"] = True
        manifest["quality"]["status"] = "ready"

    tamper_manifest(incomplete_snapshot, approve)
    runner = runner_for(incomplete_snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(SnapshotIdentityError, match="identity mismatch"):
        runner.run_and_persist()

    assert published_runs(runs_dir) == []


def test_snapshot_adulterado_apos_materializacao_e_rejeitado(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    tamper_csv,
) -> None:
    target = tamper_csv(snapshot)
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(SnapshotIntegrityError, match="hash mismatch"):
        runner.run_and_persist()

    assert target.is_file()
    assert published_runs(runs_dir) == []


def test_arquivo_ausente_no_snapshot_e_rejeitado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    (snapshot.path / snapshot.files[0]["path"]).unlink()
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(SnapshotIntegrityError, match="missing"):
        runner.run_and_persist()

    assert published_runs(runs_dir) == []


def test_ticker_ausente_no_snapshot_falha_sem_remocao_silenciosa(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    absent = ParticipantSpec("buy_and_hold", {"ticker": "ITUB4.SA"})
    runner = runner_for(snapshot, absent, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(ValueError, match="does not contain ITUB4.SA"):
        runner.run()

    assert published_runs(runs_dir) == []


def test_runner_nao_toca_em_rede_nem_em_cache_mutavel(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O snapshot é a única fonte de OHLCV; baixar dados aqui é um bug."""

    def explode(*args, **kwargs):
        raise AssertionError("o runner não deve baixar dados")

    monkeypatch.setattr("yfinance.download", explode)
    monkeypatch.setattr(
        "src.pipeline.extract.DataExtractor.download",
        lambda *args, **kwargs: explode(),
    )

    result, _ = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert result.final_equity > 0


# ── Participante novo por run ────────────────────────────────────


def test_factory_devolve_instancia_nova_e_sem_estado_herdado() -> None:
    first = build_participant(EQUAL_WEIGHT)
    second = build_participant(EQUAL_WEIGHT)

    assert first is not second
    first._session_index = 999  # type: ignore[attr-defined]
    assert second._session_index == 0  # type: ignore[attr-defined]


def test_runner_constroi_participante_novo_a_cada_run(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pega reutilização de instância mesmo que o participante se auto-corrija.

    Os participantes clássicos reiniciam o próprio estado ao reconhecer a
    primeira sessão do recorte, o que mascararia o compartilhamento num teste
    apenas comportamental. Aqui a construção é observada diretamente.
    """
    built: list[object] = []
    original = runner_module.build_participant

    def spy(spec):
        instance = original(spec)
        built.append(instance)
        return instance

    monkeypatch.setattr(runner_module, "build_participant", spy)
    runner = runner_for(snapshot, EQUAL_WEIGHT, snapshot_dir, runs_dir, tmp_path)

    runner.run()
    runner.run()

    assert len(built) == 2, "cada run deve construir seu próprio participante"
    assert built[0] is not built[1]
    # Ambos percorreram o recorte inteiro a partir do zero.
    assert [item._session_index for item in built] == [61, 61]  # type: ignore[attr-defined]


def test_mesma_spec_executada_duas_vezes_comeca_do_estado_inicial(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Estado vazado entre runs deslocaria a cadência de rebalance do segundo."""
    runner = runner_for(snapshot, EQUAL_WEIGHT, snapshot_dir, runs_dir, tmp_path)

    first = runner.run()
    second = runner.run()

    rebalance_sessions = sorted({str(trade.date) for trade in first.trades})
    assert len(rebalance_sessions) > 1, "cenário precisa de mais de um rebalance"
    assert rebalance_sessions == sorted({str(t.date) for t in second.trades})
    assert signature(first) == signature(second)
    assert first.spec_hash == second.spec_hash
    assert first.run_id != second.run_id


def test_participante_single_asset_tambem_reinicia_entre_runs(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    first = runner.run()
    second = runner.run()

    assert signature(first) == signature(second)
    assert len(first.trades) > 1, "cenário precisa de entradas e saídas"


# ── Reprodutibilidade ────────────────────────────────────────────


@pytest.mark.parametrize(
    "participant", [SMA, EQUAL_WEIGHT, MIN_VARIANCE], ids=["sma", "equal", "minvar"]
)
def test_execucoes_repetidas_sao_reproduziveis(
    participant: ParticipantSpec,
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    runner = runner_for(snapshot, participant, snapshot_dir, runs_dir, tmp_path)

    first = runner.run()
    second = runner.run()

    pd.testing.assert_series_equal(first.equity_curve, second.equity_curve)
    assert signature(first) == signature(second)
    assert first.metrics == second.metrics
    assert first.total_transaction_cost == second.total_transaction_cost
    assert first.spec_hash == second.spec_hash
    assert first.run_id != second.run_id


def test_snapshot_recriado_com_os_mesmos_dados_reproduz_o_resultado(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    make_snapshot,
) -> None:
    """Reprodutibilidade real: outro artefato, mesmos dados, mesmo resultado."""
    other_dir = tmp_path / "snapshots-bis"
    twin = make_snapshot(other_dir, tmp_path)

    first = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path).run()
    second = runner_for(twin, SMA, other_dir, runs_dir, tmp_path).run()

    assert twin.snapshot_id != snapshot.snapshot_id
    assert first.spec_hash != second.spec_hash  # o snapshot faz parte da spec
    assert signature(first) == signature(second)
    assert first.metrics == second.metrics


# ── Execução ponta a ponta ───────────────────────────────────────


def test_single_asset_end_to_end_usa_apenas_o_ticker_pedido(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    result, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert result.universe == ("PETR4.SA",)
    assert {trade.ticker for trade in result.trades} == {"PETR4.SA"}
    assert len(result.equity_curve) == 62
    assert result.initial_capital == 100_000.0
    assert path.name == result.run_id


def test_multi_asset_end_to_end_recebe_o_universo_do_snapshot(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    result, _ = runner_for(
        snapshot, EQUAL_WEIGHT, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert result.universe == snapshot.tickers
    assert {trade.ticker for trade in result.trades} == set(snapshot.tickers)


def test_metricas_e_custos_vem_da_implementacao_canonica(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    from src.backtesting.metrics import performance_metrics, total_transaction_cost

    result = runner_for(snapshot, MIN_VARIANCE, snapshot_dir, runs_dir, tmp_path).run()

    assert result.metrics == performance_metrics(
        result.equity_curve, rf=0.0, mar=0.0, freq=252
    )
    assert result.total_transaction_cost == total_transaction_cost(result.trades)
    assert result.total_transaction_cost > 0


# ── Persistência e manifest ──────────────────────────────────────


def test_run_publicado_tem_manifest_curva_e_trades(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    result, path = runner_for(
        snapshot, EQUAL_WEIGHT, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert sorted(item.name for item in path.iterdir()) == [
        "equity.csv",
        "manifest.json",
        "trades.csv",
    ]
    equity = pd.read_csv(path / "equity.csv", index_col="date", parse_dates=["date"])
    assert equity["equity"].tolist() == pytest.approx(result.equity_curve.tolist())
    trades = pd.read_csv(path / "trades.csv")
    assert len(trades) == len(result.trades)
    assert list(trades.columns) == [
        "date",
        "ticker",
        "type",
        "price",
        "quantity",
        "cost",
    ]


def test_manifest_registra_identidade_proveniencia_e_configuracao(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    result, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 2
    assert manifest["run_id"] == result.run_id
    assert manifest["spec_hash"] == result.spec_hash
    assert manifest["experiment_spec"] == result.spec.to_dict()
    assert manifest["participant"]["kind"] == "sma_cross"
    assert manifest["snapshot"]["snapshot_id"] == snapshot.snapshot_id
    assert manifest["snapshot"]["schema_version"] == 2
    assert manifest["snapshot"]["identity_digest"] == snapshot.identity_digest
    assert manifest["snapshot"]["files"][0]["sha256"] == snapshot.files[0]["sha256"]
    assert manifest["universe"] == ["PETR4.SA"]
    assert manifest["snapshot"]["tickers"] == list(snapshot.tickers)
    assert manifest["cost_model"] == {
        "brokerage_fixed": 1.0,
        "spread_bps": 15.0,
        "tax_rate": 0.001,
    }
    assert manifest["metric_configuration"] == {
        "risk_free_rate": 0.0,
        "mar": 0.0,
        "periods_per_year": 252,
    }
    assert manifest["metrics"] == result.metrics
    assert manifest["trade_count"] == len(result.trades)
    assert manifest["total_transaction_cost"] == result.total_transaction_cost
    assert manifest["final_equity"] == result.final_equity
    assert "git_commit" in manifest["code"] and "git_dirty" in manifest["code"]


def test_manifest_e_json_estavel_e_ordenado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    _, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()
    raw = (path / "manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(raw)

    assert raw == json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert isinstance(manifest["final_equity"], float)
    assert isinstance(manifest["initial_capital"], float)


def test_falha_ao_publicar_nao_deixa_run_parcial(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    def explode(*args, **kwargs):
        raise OSError("disco cheio no meio da publicação")

    monkeypatch.setattr("src.experiments.runner._write_trades", explode)

    with pytest.raises(OSError, match="disco cheio"):
        runner.run_and_persist()

    assert published_runs(runs_dir) == []


def test_dois_runs_publicam_diretorios_distintos(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    _, first = runner.run_and_persist()
    _, second = runner.run_and_persist()

    assert first != second
    assert len(published_runs(runs_dir)) == 2
    manifests = [
        json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        for path in (first, second)
    ]
    assert manifests[0]["spec_hash"] == manifests[1]["spec_hash"]
    assert manifests[0]["run_id"] != manifests[1]["run_id"]


# ── Guard de working tree limpa ──────────────────────────────────


@pytest.mark.parametrize(
    ("dirty", "commit", "expected"),
    [
        (True, "abc123", "uncommitted changes"),
        (None, None, "provenance could not be verified"),
        (False, None, "no HEAD commit could be determined"),
        (False, "   ", "no HEAD commit could be determined"),
    ],
    ids=[
        "tree-suja",
        "proveniencia-indeterminada",
        "commit-desconhecido",
        "commit-vazio",
    ],
)
def test_proveniencia_nao_limpa_bloqueia_o_run_por_padrao(
    dirty: bool | None,
    commit: str | None,
    expected: str,
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed estrito: só ``git_dirty is False`` passa sem allow_dirty."""
    set_provenance(monkeypatch, dirty=dirty, commit=commit)
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    with pytest.raises(DirtyRepositoryError, match=expected):
        runner.run_and_persist()

    assert published_runs(runs_dir) == []


@pytest.mark.parametrize(
    ("dirty", "commit"),
    [(True, "abc123"), (None, None), (False, None)],
    ids=["tree-suja", "proveniencia-indeterminada", "commit-desconhecido"],
)
def test_run_bloqueado_nao_chega_a_carregar_dados_nem_criar_participante(
    dirty: bool | None,
    commit: str | None,
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O guard é a primeira coisa do run: nada depois dele deve ser tocado."""
    touched: list[str] = []
    set_provenance(monkeypatch, dirty=dirty, commit=commit)
    monkeypatch.setattr(
        runner_module,
        "load_snapshot_frames",
        lambda *args, **kwargs: touched.append("frames"),
    )
    monkeypatch.setattr(
        runner_module,
        "build_participant",
        lambda *args, **kwargs: touched.append("participant"),
    )

    with pytest.raises(DirtyRepositoryError):
        runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path).run()

    assert touched == []
    assert published_runs(runs_dir) == []


def test_allow_dirty_libera_a_execucao_e_marca_o_resultado(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_provenance(monkeypatch, dirty=True)
    runner = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path, allow_dirty=True
    )

    result, path = runner.run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.git_dirty is True
    assert result.clean_source is False
    assert manifest["code"]["git_dirty"] is True
    assert manifest["code"]["git_commit"] == "abc123"
    assert manifest["reproducibility"] == {"clean_source": False, "allow_dirty": True}
    assert sorted(item.name for item in path.iterdir()) == [
        "equity.csv",
        "manifest.json",
        "trades.csv",
    ]


def test_proveniencia_limpa_executa_com_o_guard_fechado(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_provenance(monkeypatch, dirty=False, commit="deadbeef")
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)

    result, path = runner.run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.git_dirty is False
    assert result.clean_source is True
    assert manifest["code"]["git_dirty"] is False
    assert manifest["code"]["git_commit"] == "deadbeef"
    assert manifest["reproducibility"] == {"clean_source": True, "allow_dirty": False}
    assert result.final_equity > 0


def test_allow_dirty_nao_entra_na_spec_nem_muda_o_spec_hash(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Política operacional não é parâmetro experimental."""
    spec = spec_for(snapshot, SMA)
    assert "allow_dirty" not in spec.to_dict()
    assert "allow_dirty" not in {field.name for field in fields(ExperimentSpec)}

    set_provenance(monkeypatch, dirty=False)
    clean = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path).run()
    set_provenance(monkeypatch, dirty=True)
    dirty = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path, allow_dirty=True
    ).run()

    assert clean.spec_hash == dirty.spec_hash == spec.spec_hash
    assert clean.git_dirty is False and dirty.git_dirty is True
    assert signature(clean) == signature(dirty)


def test_allow_dirty_tem_default_fechado() -> None:
    import inspect

    parameter = inspect.signature(ExperimentRunner).parameters["allow_dirty"]

    assert parameter.default is False
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_allow_dirty_libera_proveniencia_indeterminada_sem_inventar_commit(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem Git utilizável, o escape libera mas nada é marcado como limpo."""
    set_provenance(monkeypatch, dirty=None, commit=None)

    result, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path, allow_dirty=True
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.git_dirty is None
    assert result.git_commit is None
    assert result.clean_source is False
    assert manifest["code"]["git_dirty"] is None
    # Commit desconhecido continua nulo: nada é inventado.
    assert manifest["code"]["git_commit"] is None
    assert manifest["reproducibility"] == {"clean_source": False, "allow_dirty": True}
    assert sorted(item.name for item in path.iterdir()) == [
        "equity.csv",
        "manifest.json",
        "trades.csv",
    ]


def test_commit_desconhecido_com_tree_limpa_nao_conta_como_reproduzivel(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tree limpa sem commit conhecido é liberável, mas nunca "clean_source"."""
    set_provenance(monkeypatch, dirty=False, commit=None)

    result, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path, allow_dirty=True
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.git_dirty is False
    assert result.git_commit is None
    assert result.clean_source is False
    assert manifest["reproducibility"] == {"clean_source": False, "allow_dirty": True}


@pytest.mark.parametrize(
    ("commit", "dirty", "verified"),
    [
        ("a" * 40, False, True),
        ("abc123", False, True),
        ("a" * 40, True, False),
        ("a" * 40, None, False),
        (None, False, False),
        ("", False, False),
        ("  ", False, False),
    ],
)
def test_guard_e_clean_source_usam_a_mesma_regra(
    commit: str | None, dirty: bool | None, verified: bool
) -> None:
    """Guard e manifest não podem divergir sobre o que é reproduzível."""
    assert runner_module._is_verified_provenance(commit, dirty) is verified

    result = RunResult(
        run_id="r",
        spec_hash="h",
        spec=ExperimentSpec(
            snapshot_id="s",
            participant=SMA,
            initial_capital=1.0,
        ),
        created_at="2020-01-01T00:00:00.000000Z",
        snapshot=SnapshotEvidence(
            snapshot_id="s",
            schema_version=2,
            identity_digest="0" * 64,
            path="data/snapshots/s",
            manifest_json='{"snapshot_id":"s"}',
        ),
        universe=("PETR4.SA",),
        backtest=BacktestResult(equity_curve=pd.Series(dtype=float)),
        metrics={},
        total_transaction_cost=0.0,
        git_commit=commit,
        git_dirty=dirty,
    )
    assert result.clean_source is verified


def test_git_metadata_real_nunca_reporta_tree_limpa_sem_commit(
    tmp_path: Path,
) -> None:
    """Invariante do helper compartilhado, no caminho de falha.

    O runner não depende disto — ele confere os dois campos —, mas se
    ``_git_metadata`` passar a devolver ``dirty=False`` sem commit, este teste
    avisa antes que o manifest registre proveniência incoerente.
    """
    metadata = snapshot_module._git_metadata(tmp_path / "nao-e-um-repo")

    assert metadata == {"git_commit": None, "git_dirty": None}
    assert not runner_module._is_verified_provenance(
        metadata["git_commit"], metadata["git_dirty"]
    )


# ── Provenance do snapshot capturada no run ──────────────────────


def test_run_captura_a_evidencia_do_snapshot_executado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A evidência descreve o artefato verificado, não uma releitura posterior."""
    result = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path).run()
    evidence = result.snapshot

    assert evidence.snapshot_id == snapshot.snapshot_id
    assert result.snapshot_id == snapshot.snapshot_id
    assert evidence.schema_version == 2
    assert evidence.identity_digest == snapshot.identity_digest
    assert evidence.manifest == json.loads(
        snapshot.manifest_path.read_text(encoding="utf-8")
    )
    # Cada leitura devolve uma cópia nova: mutar o retorno não reescreve nada.
    mutated = evidence.manifest
    mutated["quality"]["scientific_ready"] = "adulterado"
    assert evidence.manifest["quality"]["scientific_ready"] is True


def test_persist_nao_rele_o_snapshot(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publicar não pode depender do diretório do snapshot ainda estar lá."""
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)
    result = runner.run()

    def explode(*args, **kwargs):
        raise AssertionError("persist não deve reler o snapshot")

    monkeypatch.setattr(runner_module, "load_dataset_snapshot", explode)
    path = runner.persist(result)

    assert (path / "manifest.json").is_file()


def test_manifest_descreve_o_snapshot_executado_e_nao_o_adulterado_depois(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    tamper_manifest,
) -> None:
    """Janela run/persist: o passado não é reescrito pelo estado atual do disco.

    Entre executar e publicar, o manifest do snapshot é adulterado. O manifest
    do run deve continuar descrevendo o artefato que passou pelos guards e foi
    entregue ao ``ExecutionEngine``.
    """
    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)
    result = runner.run()
    executed = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))

    def rewrite_history(manifest: dict) -> None:
        manifest["tickers"] = ["ITUB4.SA"]
        manifest["quality"]["scientific_ready"] = False
        manifest["files"][0]["sha256"] = "0" * 64
        manifest["effective_end"] = "1999-12-31"

    tamper_manifest(snapshot, rewrite_history)
    path = runner.persist(result)
    published = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert published["snapshot"]["tickers"] == executed["tickers"]
    assert published["snapshot"]["quality"] == executed["quality"]
    assert published["snapshot"]["files"] == executed["files"]
    assert published["snapshot"]["effective_end"] == executed["effective_end"]
    assert published["snapshot"]["identity_digest"] == snapshot.identity_digest
    assert published["snapshot"]["tickers"] != ["ITUB4.SA"]


def test_snapshot_removido_entre_run_e_persist_nao_muda_o_manifest(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Forma extrema da mesma janela: o artefato some antes de publicar."""
    import shutil

    runner = runner_for(snapshot, SMA, snapshot_dir, runs_dir, tmp_path)
    result = runner.run()
    expected_digest = snapshot.identity_digest
    shutil.rmtree(snapshot.path)

    path = runner.persist(result)
    published = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert published["snapshot"]["snapshot_id"] == snapshot.snapshot_id
    assert published["snapshot"]["identity_digest"] == expected_digest


# ── Coerência interna do manifest publicado ──────────────────────


def test_manifest_publicado_prova_spec_hash_igual_ao_hash_da_spec(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A garantia fica presa no artefato: ninguém precisa confiar no runner."""
    _, path = runner_for(
        snapshot, SMA, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    recomputed = hashlib.sha256(
        canonical_json(manifest["experiment_spec"]).encode("utf-8")
    ).hexdigest()

    assert recomputed == manifest["spec_hash"]


def test_spec_hash_do_manifest_nao_muda_com_mutacao_externa_do_participante(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """run() e persist() usam exatamente a mesma ExperimentSpec."""
    params = {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15}
    runner = runner_for(
        snapshot, ParticipantSpec("sma_cross", params), snapshot_dir, runs_dir, tmp_path
    )
    expected = runner.spec.spec_hash

    result = runner.run()
    params["fast_window"] = 999
    path = runner.persist(result)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert runner.spec.spec_hash == expected
    assert result.spec_hash == expected
    assert manifest["spec_hash"] == expected
    assert manifest["experiment_spec"]["participant"]["params"]["fast_window"] == 5
