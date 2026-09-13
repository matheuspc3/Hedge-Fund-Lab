"""Orquestração de uma execução experimental identificável e auditável.

O runner não contém regra de estratégia nem regra financeira: ele resolve o
snapshot, monta os objetos a partir da spec, delega a execução ao
``ExecutionEngine`` da arena, pede as métricas ao módulo canônico e publica o
artefato. Qualquer decisão sobre preço, quantidade, direção ou custo continua
dentro do motor.
"""

import json
import logging
import platform
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

import pandas as pd

from src.artifacts import RunArtifact, RunArtifactProvider
from src.backtesting.arena import (
    EvaluationWindow,
    ExecutionEngine,
    common_sessions,
    resolve_evaluation_window,
)
from src.backtesting.engine import BacktestResult
from src.backtesting.metrics import performance_metrics, total_transaction_cost
from src.config import settings
from src.experiments.context import RunContext
from src.experiments.participants import build_participant, required_tickers
from src.experiments.spec import ExperimentSpec
from src.pipeline.snapshot import (
    DatasetSnapshot,
    SnapshotEvidence,
    SnapshotNotReadyError,
    _git_metadata,
    _package_version,
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)

logger = logging.getLogger(__name__)

# Schema 2: a proveniência do snapshot passa a ser capturada no ``run()`` e o
# manifest registra a identidade verificável do artefato consumido.
# Schema 3: o manifest publica ``participant_artifacts`` — caminho, versão de
# schema e SHA-256 da evidência que o participante produziu durante o run.
# Schema 4: o manifest separa três coisas que antes se confundiam numa só —
# a janela *pedida* (dentro da spec e do ``spec_hash``), o contexto
# metodológico do run (``phase``/``case_id``, fora do hash) e a janela
# *realizada* (``evaluation_evidence``), derivada do calendário efetivamente
# executado. No mesmo schema, ``sessions`` virou ``equity_points``: ao lado de
# ``evaluated_sessions`` o nome antigo passou a descrever outra coisa do que
# sugeria — a curva publicada inclui a ``settlement_session``.
RUN_MANIFEST_SCHEMA_VERSION = 4
EQUITY_FILE = "equity.csv"
TRADES_FILE = "trades.csv"
MANIFEST_FILE = "manifest.json"
#: Nomes que o runner escreve por conta própria; um artefato de participante
#: não pode reivindicá-los.
RESERVED_FILES = frozenset({EQUITY_FILE, TRADES_FILE, MANIFEST_FILE})


class MissingRunContextError(Exception):
    """Um run científico foi iniciado sem declarar a fase do protocolo.

    A fase precisa existir *antes* da execução: anexá-la depois permitiria
    escolher o rótulo após observar o resultado, que é exatamente o risco que
    declarar a fase existe para conter.
    """


class DirtyRepositoryError(Exception):
    """A proveniência do código não é comprovadamente um commit limpo.

    Cobre os estados que impedem reprodução a partir do commit: working tree
    com alterações não commitadas, commit indeterminado e proveniência Git não
    verificável.
    """


def _is_verified_provenance(commit: object, dirty: object) -> bool:
    """Proveniência reproduzível: commit conhecido *e* tree limpa.

    Fonte única da regra, usada pelo guard e por ``RunResult.clean_source``, de
    modo que os dois não possam divergir. ``_git_metadata`` hoje derruba commit
    e dirty juntos quando o Git falha, mas isso é consequência da sua
    implementação e não um contrato: aqui os dois campos são conferidos.
    """
    return dirty is False and isinstance(commit, str) and bool(commit.strip())


def _provenance_failure(commit: object, dirty: object) -> str:
    if dirty is True:
        return "the repository working tree has uncommitted changes"
    if dirty is False:
        return (
            "the repository reports a clean working tree but no HEAD commit "
            "could be determined"
        )
    return (
        "the repository provenance could not be verified "
        "(no usable git metadata for this directory)"
    )


@dataclass(frozen=True)
class RunResult:
    """Resultado canônico de uma execução, identificado por ``run_id``.

    Compõe o ``BacktestResult`` da arena em vez de reimplementá-lo: curva,
    trades e capital continuam vindo do motor.
    """

    run_id: str
    spec_hash: str
    spec: ExperimentSpec
    created_at: str
    # Proveniência do snapshot capturada no run, em forma canônica congelada:
    # publicar o resultado não pode reler o diretório para redescobrir o que
    # foi executado.
    snapshot: SnapshotEvidence
    universe: tuple[str, ...]
    # Janela efetivamente executada, resolvida contra o calendário comum antes
    # de o participante existir. É evidência do run, não a configuração pedida:
    # esta última continua na ``ExperimentSpec``.
    evaluation: EvaluationWindow
    # Papel metodológico declarado antes da execução. ``None`` só no modo
    # técnico legado, em que nenhuma fase científica foi reivindicada.
    context: RunContext | None
    backtest: BacktestResult
    metrics: Mapping[str, float | int]
    total_transaction_cost: float
    # Evidência congelada que o participante produziu durante *esta* execução,
    # capturada logo após o motor terminar. ``persist()`` escreve estes bytes
    # e mais nada: nunca reconsulta o participante nem o provedor.
    artifacts: tuple[RunArtifact, ...] = ()
    # Proveniência conferida no início do run, não no momento de publicar: o
    # manifest registra exatamente o estado que passou (ou dispensou) o guard.
    git_commit: str | None = None
    git_dirty: bool | None = None

    @property
    def clean_source(self) -> bool:
        """Só é ``True`` quando o código é comprovadamente um commit limpo."""
        return _is_verified_provenance(self.git_commit, self.git_dirty)

    @property
    def snapshot_id(self) -> str:
        return self.snapshot.snapshot_id

    @property
    def equity_curve(self) -> pd.Series:
        return self.backtest.equity_curve

    @property
    def trades(self) -> list:
        return self.backtest.trades

    @property
    def initial_capital(self) -> float:
        return self.backtest.initial_capital

    @property
    def final_equity(self) -> float:
        return self.backtest.final_equity


class ExperimentRunner:
    """Executa uma ``ExperimentSpec`` sobre um snapshot imutável."""

    def __init__(
        self,
        spec: ExperimentSpec,
        *,
        context: RunContext | None = None,
        snapshot_dir: str | Path | None = None,
        runs_dir: str | Path | None = None,
        repository_dir: str | Path | None = None,
        allow_dirty: bool = False,
    ) -> None:
        # O contexto é congelado aqui, antes de qualquer execução: ``run()`` e
        # ``persist()`` apenas o leem. Não existe caminho que declare a fase
        # depois de conhecer o resultado.
        if spec.evaluation is not None and context is None:
            raise MissingRunContextError(
                "a spec that declares an evaluation window is a scientific "
                "run and must declare its protocol phase before executing; "
                "pass context=RunContext(phase=...) to ExperimentRunner"
            )
        self.spec = spec
        self.context = context
        self.snapshot_dir = Path(snapshot_dir or settings.snapshot_dir)
        self.runs_dir = Path(runs_dir or settings.runs_dir)
        self.repository_dir = Path(repository_dir or Path.cwd())
        # Política operacional do runner, não parâmetro experimental: liberar
        # working tree suja não altera dados, custos, métricas nem spec_hash.
        self.allow_dirty = allow_dirty

    # ── Execução ─────────────────────────────────────────────────

    def run(self) -> RunResult:
        """Executa a spec e devolve o resultado, sem persistir nada."""
        # Guard de código antes de qualquer trabalho: um run que não pode ser
        # reproduzido não deve nem carregar dados, nem criar participante.
        provenance = self._code_provenance()
        snapshot = self._load_snapshot()
        # Evidência congelada no mesmo ponto em que o snapshot passou pelos
        # guards e antes de qualquer execução: é esta descrição, e não o estado
        # posterior do diretório, que o manifest do run publicará.
        evidence = snapshot.evidence()
        universe = self._resolve_universe(snapshot)
        frames = load_snapshot_frames(snapshot, universe)

        # Gate da janela **antes** de construir o participante: uma janela sem
        # settlement, fora do calendário ou com warm-up insuficiente não pode
        # custar uma única chamada paga ao provedor. Mesmo motivo pelo qual o
        # guard de proveniência roda antes de carregar dados.
        evaluation = self._resolve_evaluation(frames)

        # Instância nova a cada run: participantes clássicos carregam estado
        # entre sessões e não podem atravessar execuções.
        participant = build_participant(self.spec.participant)
        window = self.spec.evaluation
        engine = ExecutionEngine(
            participant,
            frames,
            self.spec.initial_capital,
            self.spec.costs.build(),
            decision_start=None if window is None else window.decision_start,
            decision_end=None if window is None else window.decision_end,
            minimum_history_sessions=(
                None if window is None else window.minimum_history_sessions
            ),
        )
        backtest = engine.run()
        # Mesmo princípio do ``SnapshotEvidence``: a evidência é congelada no
        # ponto em que o fato aconteceu, não redescoberta na hora de publicar.
        artifacts = _participant_artifacts(participant)

        metrics = performance_metrics(
            backtest.equity_curve,
            rf=self.spec.metrics.risk_free_rate,
            mar=self.spec.metrics.mar,
            freq=self.spec.metrics.periods_per_year,
        )
        created = datetime.now(timezone.utc)
        run_id = f"{created.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:12]}"
        logger.info(
            "Run %s | spec_hash=%s | participante=%s | universo=%s | "
            "fase=%s | janela=%s..%s (%d sessões avaliadas, warm-up %d sessões)",
            run_id,
            self.spec.spec_hash,
            self.spec.participant.kind,
            ",".join(universe),
            None if self.context is None else self.context.phase,
            evaluation.decision_start.date(),
            evaluation.decision_end.date(),
            evaluation.evaluated_sessions,
            evaluation.warmup_sessions,
        )
        return RunResult(
            run_id=run_id,
            spec_hash=self.spec.spec_hash,
            spec=self.spec,
            created_at=_isoformat(created),
            snapshot=evidence,
            universe=universe,
            evaluation=evaluation,
            context=self.context,
            backtest=backtest,
            metrics=metrics,
            total_transaction_cost=total_transaction_cost(backtest.trades),
            artifacts=artifacts,
            git_commit=provenance.get("git_commit"),
            git_dirty=provenance.get("git_dirty"),
        )

    def run_and_persist(self) -> tuple[RunResult, Path]:
        """Executa e publica; uma falha na execução não deixa run publicado."""
        result = self.run()
        return result, self.persist(result)

    # ── Proveniência do código ───────────────────────────────────

    def _code_provenance(self) -> dict[str, Any]:
        """Aceita apenas proveniência comprovadamente reproduzível.

        Fail-closed estrito: exige commit conhecido *e* working tree limpa.
        Tree suja, commit indeterminado e proveniência não verificável são
        rejeitados igualmente — nenhum dos três permite reproduzir o run a
        partir de um commit.
        """
        metadata = _git_metadata(self.repository_dir)
        commit = metadata.get("git_commit")
        dirty = metadata.get("git_dirty")
        if _is_verified_provenance(commit, dirty):
            return metadata

        if not self.allow_dirty:
            raise DirtyRepositoryError(
                f"{_provenance_failure(commit, dirty)}; a run started from it "
                "cannot be reproduced from a commit alone. Commit or stash the "
                "changes — or run from a readable git checkout — or pass "
                "allow_dirty=True to ExperimentRunner, an explicit "
                "development-only escape that records clean_source=false in "
                "the manifest."
            )
        logger.warning(
            "Run liberado sem código comprovadamente limpo: git_commit=%r git_dirty=%r",
            commit,
            dirty,
        )
        return metadata

    # ── Snapshot ─────────────────────────────────────────────────

    def _load_snapshot(self) -> DatasetSnapshot:
        snapshot = load_dataset_snapshot(self.snapshot_dir / self.spec.snapshot_id)
        if not snapshot.scientific_ready:
            raise SnapshotNotReadyError(
                f"snapshot {snapshot.snapshot_id} did not pass the scientific "
                f"coverage gate (quality status: {snapshot.quality.get('status')}); "
                "experiments must not run on an incomplete dataset"
            )
        verify_snapshot_integrity(snapshot)
        return snapshot

    def _resolve_evaluation(self, frames: Mapping[str, pd.DataFrame]) -> EvaluationWindow:
        """Resolve a janela sobre o calendário comum, ou falha antes do run.

        Usa exatamente a mesma função que o ``ExecutionEngine`` usará sobre os
        mesmos quadros, de modo que o gate pré-run e a execução não podem
        discordar sobre qual sessão existe, onde a janela começa ou se há
        settlement.
        """
        window = self.spec.evaluation
        return resolve_evaluation_window(
            common_sessions(frames),
            decision_start=None if window is None else window.decision_start,
            decision_end=None if window is None else window.decision_end,
            minimum_history_sessions=(
                None if window is None else window.minimum_history_sessions
            ),
        )

    def _resolve_universe(self, snapshot: DatasetSnapshot) -> tuple[str, ...]:
        """Universo efetivo, derivado da spec sem seleção dinâmica."""
        requested = required_tickers(self.spec.participant)
        universe = requested or snapshot.tickers
        missing = [ticker for ticker in universe if ticker not in snapshot.tickers]
        if missing:
            raise ValueError(
                f"snapshot {snapshot.snapshot_id} does not contain "
                f"{', '.join(missing)}; available: {', '.join(snapshot.tickers)}"
            )
        return tuple(universe)

    # ── Persistência ─────────────────────────────────────────────

    def persist(self, result: RunResult) -> Path:
        """Publica o run atomicamente: staging completo, depois rename.

        Nada aqui relê o snapshot: o que o manifest descreve é a evidência
        capturada no ``run()``. Alterar o artefato no disco entre executar e
        publicar não reescreve retroativamente a proveniência do resultado.
        """
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        staging = self.runs_dir / f".tmp-{uuid4().hex}"
        staging.mkdir(parents=True)
        try:
            _write_equity(result, staging / EQUITY_FILE)
            _write_trades(result, staging / TRADES_FILE)
            for artifact in result.artifacts:
                (staging / artifact.filename).write_bytes(artifact.content)
            manifest = self._manifest(result)
            (staging / MANIFEST_FILE).write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            target = self.runs_dir / result.run_id
            if target.exists():
                raise FileExistsError(f"run already exists: {target}")
            staging.rename(target)
        except BaseException:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        return target

    def _manifest(self, result: RunResult) -> dict[str, Any]:
        snapshot = result.snapshot.manifest
        return {
            "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
            "run_id": result.run_id,
            "spec_hash": result.spec_hash,
            "created_at": result.created_at,
            "experiment_spec": result.spec.to_dict(),
            "participant": result.spec.participant.to_dict(),
            "snapshot": {
                "snapshot_id": result.snapshot.snapshot_id,
                "schema_version": result.snapshot.schema_version,
                "identity_digest": result.snapshot.identity_digest,
                "path": result.snapshot.path,
                "created_at": snapshot["created_at"],
                "requested_start": snapshot["requested_start"],
                "requested_end": snapshot["requested_end"],
                "effective_start": snapshot["effective_start"],
                "effective_end": snapshot["effective_end"],
                "tickers": snapshot["tickers"],
                "files": snapshot["files"],
                "quality": snapshot["quality"],
            },
            "universe": list(result.universe),
            # Contexto metodológico declarado antes da execução, deliberadamente
            # fora do ``spec_hash``: ele não altera o que foi computado.
            "run_context": (
                {"phase": None, "case_id": None}
                if result.context is None
                else result.context.to_dict()
            ),
            # Evidência realizada da janela, derivada do calendário executado —
            # nunca copiada da configuração pedida, que já está em
            # ``experiment_spec.evaluation``.
            "evaluation_evidence": result.evaluation.to_dict(),
            "cost_model": result.spec.costs.to_dict(),
            "metric_configuration": result.spec.metrics.to_dict(),
            "initial_capital": result.initial_capital,
            "final_equity": result.final_equity,
            "metrics": dict(result.metrics),
            "trade_count": len(result.trades),
            "total_transaction_cost": result.total_transaction_cost,
            # Pontos da curva publicada, não sessões avaliadas nem decisões:
            # com janela declarada a curva inclui a ``settlement_session``, e
            # ``sessions`` — o nome anterior — era lido como as três coisas.
            # A contagem da janela vive em ``evaluation_evidence``.
            "equity_points": len(result.equity_curve),
            "code": {
                "git_commit": result.git_commit,
                "git_dirty": result.git_dirty,
                "python": platform.python_version(),
                "project_version": _package_version("hedge-fund-lab"),
            },
            "reproducibility": {
                "clean_source": result.clean_source,
                "allow_dirty": self.allow_dirty,
            },
            "artifacts": {"equity_curve": EQUITY_FILE, "trades": TRADES_FILE},
            # Vazio para os participantes clássicos, que não produzem
            # evidência própria e não implementam contrato nenhum para isso.
            "participant_artifacts": {
                artifact.name: artifact.describe() for artifact in result.artifacts
            },
        }


def _participant_artifacts(participant: object) -> tuple[RunArtifact, ...]:
    """Evidência declarada pelo participante, se ele declarar alguma.

    O runner não conhece participante nenhum em particular: o teste é o
    ``Protocol`` genérico :class:`~src.artifacts.RunArtifactProvider`, não
    ``isinstance(participant, LLMParticipant)``. Clássicos não implementam
    ``run_artifacts`` e seguem publicando apenas curva, trades e manifest.
    """
    if not isinstance(participant, RunArtifactProvider):
        return ()
    artifacts = tuple(participant.run_artifacts())
    names: set[str] = set()
    filenames: set[str] = set()
    for artifact in artifacts:
        if artifact.name in names:
            raise ValueError(f"duplicate participant artifact name: {artifact.name}")
        if artifact.filename in filenames:
            raise ValueError(f"duplicate participant artifact file: {artifact.filename}")
        if artifact.filename in RESERVED_FILES:
            raise ValueError(
                f"participant artifact cannot overwrite {artifact.filename}, "
                "which the runner publishes itself"
            )
        names.add(artifact.name)
        filenames.add(artifact.filename)
    return artifacts


def _isoformat(moment: datetime) -> str:
    return moment.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _write_equity(result: RunResult, path: Path) -> None:
    curve = result.equity_curve.rename("equity")
    curve.index.name = "date"
    curve.to_csv(path, date_format="%Y-%m-%d", lineterminator="\n")


def _write_trades(result: RunResult, path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(trade.date).date().isoformat(),
                "ticker": trade.ticker,
                "type": trade.type,
                "price": trade.price,
                "quantity": trade.quantity,
                "cost": trade.cost,
            }
            for trade in result.trades
        ],
        columns=["date", "ticker", "type", "price", "quantity", "cost"],
    )
    frame.to_csv(path, index=False, lineterminator="\n")
