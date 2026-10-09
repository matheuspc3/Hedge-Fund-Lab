"""Synthetic-only qualification harness around the existing ExperimentRunner.

No CLI/live mode. Real reserved snapshot is refused before reading its prices.
SQLite reserves each logical call before invoking a fresh mock; interrupted
runs become replay-only. The two declared post-CAL-B4 infrastructure patches
are verified separately; historical scientific artifacts remain unchanged.
"""

import hashlib
import ipaddress
import json
import os
import socket
import sqlite3
import tempfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.agents.llm_client import LLMCallMetadata, LLMClient, MockLLMClient
from src.agents.llm_trace import (
    LLMCallRequest,
    RecordingLLMClient,
    ReplayLLMClient,
    ReplayMismatchError,
    _jsonable_options,
    load_trace,
    schema_digest,
    schema_name,
)
from src.agents.participant import LLMParticipant
from src.artifacts import canonical_json
from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.engine import BacktestResult, Trade
from src.backtesting.metrics import periodic_returns
from src.experiments.context import RunContext
from src.experiments.h2_evaluation import (
    AMENDMENT_STATUS,
    BASE_COSTS,
    BENCHMARK_SPECS,
    CAPITAL,
    COLUMNS,
    EVALUATION_WINDOWS,
    EXECUTION,
    INVALID_COST_REPLAY,
    METRICS,
    PARTICIPANT_SHA256,
    PHASE_WINDOWS,
    RESERVED_SNAPSHOT,
    TICKER,
    digest,
    phase_statistics,
    secondary_metrics,
)
from src.experiments.phases import require_execution_within_phase
from src.experiments.runner import ExperimentRunner, _write_equity, _write_trades
from src.experiments.spec import CostSpec, ExperimentSpec, ParticipantSpec
from src.pipeline.snapshot import create_dataset_snapshot, verify_snapshot_integrity

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATHS = (
    "scripts/qualify_h2_v6_evaluation.py",
    "src/experiments/h2_evaluation.py",
    "src/experiments/h2_evaluation_offline.py",
    "src/experiments/runner.py",
    "src/experiments/spec.py",
    "src/backtesting/arena.py",
    "src/backtesting/costs.py",
    "src/backtesting/metrics.py",
    "src/agents/participant.py",
    "src/agents/llm_trace.py",
    "src/strategies/base.py",
    "src/strategies/buy_and_hold.py",
    "src/indicators/sma.py",
    "src/indicators/bollinger.py",
    "docs/H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md",
    "docs/H2_V6_EVALUATION_AMENDMENT_DELIBERATION.md",
)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    from src.experiments.h2_evaluation_manifest import verify_preservation

    verify_preservation()
    return {p: sha_file(ROOT / p) for p in _SOURCE_PATHS}


def _safe_fixture_root(root):
    root = Path(root).resolve()
    for forbidden in (ROOT / "data", ROOT / "docs/evidence/cal_b4"):
        if root.is_relative_to(forbidden.resolve()):
            raise ValueError("offline artifacts may not use reserved data/evidence roots")
    return root


@contextmanager
def no_network():
    connect, connect_ex = socket.socket.connect, socket.socket.connect_ex

    def guarded(original):
        def call(sock, address):
            # asyncio needs its local self-pipe, including Windows socketpair.
            local = sock.family == getattr(socket, "AF_UNIX", object())
            if isinstance(address, tuple):
                try:
                    local = ipaddress.ip_address(address[0]).is_loopback
                except ValueError:
                    local = False
            if not local:
                raise RuntimeError("offline qualification forbids network")
            return original(sock, address)

        return call

    with patch.object(socket.socket, "connect", guarded(connect)), patch.object(
        socket.socket, "connect_ex", guarded(connect_ex)
    ), patch.object(
        socket,
        "create_connection",
        side_effect=RuntimeError("offline qualification forbids network"),
    ):
        yield


def synthetic_fixture(root):
    """Only fixture materializer: generated OHLCV, canonical snapshot pipeline."""
    root = _safe_fixture_root(root)
    calendar = B3Calendar()
    start, end = "2022-07-01", "2026-08-31"
    sessions = pd.DatetimeIndex(
        calendar.sessions_between(pd.Timestamp(start).date(), pd.Timestamp(end).date())
    )
    steps = np.arange(len(sessions), dtype=float)
    close = 100 + steps * 0.01 + 2 * np.sin(steps / 9) + 0.5 * np.cos(steps / 3)
    # A known generated loss exposes cost-dependent Risk/Portfolio payloads.
    for phase in PHASE_WINDOWS.values():
        first = sessions.get_loc(pd.Timestamp(phase.start))
        close[first + 1] = close[first] * 0.97
    opening = np.r_[close[0], close[:-1]]
    frame = pd.DataFrame(
        {
            "abertura": opening,
            "fechamento": close,
            "maxima": np.maximum(opening, close) * 1.01,
            "minima": np.minimum(opening, close) * 0.99,
            "volume": np.full(len(sessions), 1e6),
        },
        index=sessions,
    )

    class SyntheticExtractor:
        def download(self, ticker, start, end):
            return frame.copy()

        def download_actions(self, ticker, start, end):
            return pd.DataFrame(
                {"dividends": [], "splits": []}, index=pd.DatetimeIndex([], name="date")
            )

    with no_network():
        snapshot = create_dataset_snapshot(
            [TICKER],
            start,
            end,
            extractor=SyntheticExtractor(),
            calendar=calendar,
            snapshot_dir=root / "snapshots",
            repository_dir=ROOT,
        )
    marker = {
        "mode": "OFFLINE_GENERATED_SYNTHETIC_ONLY",
        "snapshot_id": snapshot.snapshot_id,
        "identity_digest": snapshot.identity_digest,
        "generator": "synthetic_fixture_v1",
        "files": [dict(f) for f in snapshot.files],
    }
    _write_once(snapshot.path / "OFFLINE_FIXTURE.json", marker)
    return snapshot


def _write_once(path, value):
    payload = (canonical_json(value) + "\n").encode()
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"immutable artifact changed: {path.name}")
        return
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def build_with_client(spec, client):
    if spec.kind != "llm_agent" or digest(spec.to_dict()) != PARTICIPANT_SHA256:
        raise ValueError("only the unchanged H2 v6 participant can receive a client")
    return LLMParticipant(**spec.params, llm_client=client)


class _JournalClient(LLMClient):
    """Durable logical-call bank; recovery uses the canonical replay matcher."""

    def __init__(self, db, slot, mock=None):
        super().__init__()
        self.db, self.slot, self.sequence = db, slot, 0
        self.session = None
        self.recorder = (
            None
            if mock is None
            else RecordingLLMClient(
                mock, provider="gemini", requested_model="gemini-3.8-flash"
            )
        )

    def begin_session(self, session):
        super().begin_session(session)
        self.session = str(pd.Timestamp(session).date())
        if self.recorder is not None:
            self.recorder.begin_session(session)

    async def generate(
        self,
        system_prompt,
        user_prompt,
        response_schema=None,
        options=None,
        *,
        metadata=None,
    ):
        meta = metadata or LLMCallMetadata(stage="UNDECLARED")
        request = LLMCallRequest(
            stage=meta.stage,
            analyst_id=meta.analyst_id,
            decision_session=self.session,
            provider="gemini",
            requested_model="gemini-3.8-flash",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        sequence = self.sequence
        self.sequence += 1
        row = self.db.execute(
            "SELECT identity, record FROM calls WHERE slot=? AND sequence=?",
            (self.slot, sequence),
        ).fetchone()
        if row is not None:
            if row[1] is None:
                raise ReplayMismatchError(
                    "uncertain reserved call; fail closed before inference"
                )
            records = load_trace((row[1] + "\n").encode())
            replay = ReplayLLMClient(
                records, provider="gemini", requested_model="gemini-3.8-flash"
            )
            replay.begin_session(self.session)
            response = await replay.generate(
                system_prompt, user_prompt, response_schema, options, metadata=metadata
            )
            replay.assert_complete()
            return response
        if self.recorder is None:
            raise ReplayMismatchError(
                f"partial recovery lacks exact call {self.slot}:{sequence}; no fresh inference"
            )
        self.db.execute(
            "INSERT INTO calls VALUES (?,?,?,NULL)",
            (self.slot, sequence, request.identity_digest),
        )
        self.db.commit()  # Reserve before mock invocation; uncertain gaps cannot be retried.
        try:
            return await self.recorder.generate(
                system_prompt, user_prompt, response_schema, options, metadata=metadata
            )
        finally:
            record = next(
                (r for r in self.recorder.records if r.sequence == sequence), None
            )
            if record is not None:
                self.db.execute(
                    "UPDATE calls SET record=? WHERE slot=? AND sequence=?",
                    (canonical_json(record.to_json_dict()), self.slot, sequence),
                )
                self.db.commit()  # Response durable before returning to the participant.

    def assert_complete(self):
        rows = self.db.execute(
            "SELECT sequence, record FROM calls WHERE slot=? ORDER BY sequence",
            (self.slot,),
        ).fetchall()
        if len(rows) != self.sequence or any(r[1] is None for r in rows):
            raise ReplayMismatchError(
                "call bank incomplete, uncertain or contains leftover calls"
            )


class OfflineEvaluationBatch:
    """Exactly three isolated mock realizations; no approval or live capability."""

    def __init__(self, root, snapshot, phase, *, mock_factory, validation=None):
        self.root = _safe_fixture_root(root)
        if phase not in PHASE_WINDOWS:
            raise ValueError("unknown phase")
        if snapshot.snapshot_id == RESERVED_SNAPSHOT:
            raise ValueError("real reserved snapshot forbidden before price access")
        _safe_fixture_root(snapshot.path)
        marker_path = snapshot.path / "OFFLINE_FIXTURE.json"
        if not marker_path.is_file():
            raise ValueError("generated synthetic fixture attestation required")
        marker = json.loads(marker_path.read_text())
        if (
            marker.get("mode") != "OFFLINE_GENERATED_SYNTHETIC_ONLY"
            or marker.get("generator") != "synthetic_fixture_v1"
            or marker.get("snapshot_id") != snapshot.snapshot_id
            or marker.get("identity_digest") != snapshot.identity_digest
        ):
            raise ValueError("synthetic attestation identity mismatch")
        verify_snapshot_integrity(snapshot)
        freeze = json.loads(
            (ROOT / "docs/evidence/cal_b4/protocol_freeze_v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.llm_spec = ParticipantSpec(**freeze["participant_spec"])
        if digest(self.llm_spec.to_dict()) != PARTICIPANT_SHA256:
            raise ValueError("frozen treatment changed")
        self.snapshot, self.phase, self.mock_factory = snapshot, phase, mock_factory
        self.equity_sessions = pd.DatetimeIndex(
            B3Calendar().sessions_between(
                pd.Timestamp(PHASE_WINDOWS[phase].start).date(),
                pd.Timestamp(PHASE_WINDOWS[phase].end).date(),
            )
        )
        self.plan = {
            "mode": "OFFLINE_SYNTHETIC_ONLY",
            "amendment_status": AMENDMENT_STATUS,
            "phase": phase,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_identity": snapshot.identity_digest,
            "participant_sha256": PARTICIPANT_SHA256,
            "R": 3,
            "evaluation": EVALUATION_WINDOWS[phase].to_dict(),
            "phase_window": vars(PHASE_WINDOWS[phase]),
            "costs": BASE_COSTS.to_dict(),
            "metrics": METRICS.to_dict(),
            "execution": EXECUTION.to_dict(),
            "initial_capital": CAPITAL,
            "benchmarks": [s.to_dict() for s in BENCHMARK_SPECS],
            "test": {
                "candidate": "A",
                "B": 5000,
                "alpha": 0.05,
                "seed": 20261008,
                "mean_block": 10,
            },
            "sources_sha256": source_hashes(),
        }
        self.plan_hash = digest(self.plan)
        self.validation = validation
        if phase == "FINAL_TEST":
            if validation is None:
                raise ValueError("Final requires complete Validation integrity evidence")
            validation.require_release(self.snapshot, source_hashes())
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "evaluation.sqlite")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS slots (slot TEXT PRIMARY KEY, state TEXT NOT NULL, seal TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS calls (slot TEXT, sequence INTEGER, identity TEXT NOT NULL, record TEXT, PRIMARY KEY(slot,sequence))"
        )
        old = self.db.execute("SELECT value FROM meta WHERE key='plan'").fetchone()
        if old is not None and old[0] != canonical_json(self.plan):
            self.db.close()
            raise ValueError(
                "batch identity changed; no tuning, rerun or reclassification"
            )
        self.db.execute(
            "INSERT OR IGNORE INTO meta VALUES ('plan',?)", (canonical_json(self.plan),)
        )
        self.db.commit()
        self._clients = []

    def close(self):
        self.db.close()

    def _check_plan(self):
        if (
            self.plan_hash != digest(self.plan)
            or self.plan["sources_sha256"] != source_hashes()
            or self.phase != self.plan["phase"]
            or self.snapshot.identity_digest != self.plan["snapshot_identity"]
            or digest(self.llm_spec.to_dict()) != PARTICIPANT_SHA256
        ):
            raise ValueError("evaluation identity changed; tuning forbidden")
        verify_snapshot_integrity(self.snapshot)

    def _spec(self, participant, spread=5):
        if spread not in (0, 5, 10, 20):
            raise ValueError("cost grid is fixed")
        return ExperimentSpec(
            snapshot_id=self.snapshot.snapshot_id,
            participant=participant,
            initial_capital=CAPITAL,
            costs=CostSpec(0, spread, 0.00032),
            metrics=METRICS,
            execution=EXECUTION,
            evaluation=EVALUATION_WINDOWS[self.phase],
        )

    def _context(self, slot):
        return RunContext(self.phase, f"OFFLINE_SYNTHETIC:{slot}")

    def _runner(self, spec, slot, client=None):
        return ExperimentRunner(
            spec,
            context=self._context(slot),
            snapshot_dir=self.snapshot.path.parent,
            runs_dir=self.root / "runs",
            repository_dir=ROOT,
            allow_dirty=True,
            boundaries=(PHASE_WINDOWS[self.phase],),
            participant_factory=None
            if client is None
            else lambda participant: build_with_client(participant, client),
        )

    def _path(self, slot):
        return self.root / "runs" / f"OFFLINE-{self.phase}-{slot}-{self.plan_hash[:12]}"

    def _load(self, slot, spec):
        row = self.db.execute(
            "SELECT state,seal FROM slots WHERE slot=?", (slot,)
        ).fetchone()
        if row is None or row[0] != "COMPLETE" or row[1] is None:
            raise ValueError(f"incomplete slot {slot}")
        path = self._path(slot)
        seal = json.loads(row[1])
        if set(seal) != {p.name for p in path.iterdir() if p.is_file()}:
            raise ValueError("sealed run files added or removed")
        for name, expected in seal.items():
            if Path(name).name != name or sha_file(path / name) != expected:
                raise ValueError("sealed run artifact changed")
        manifest = json.loads((path / "manifest.json").read_text())
        if (
            manifest["spec_hash"] != spec.spec_hash
            or manifest["experiment_spec"] != spec.to_dict()
            or manifest["run_context"] != self._context(slot).to_dict()
            or manifest["snapshot"]["identity_digest"] != self.snapshot.identity_digest
            or manifest["run_id"] != path.name
        ):
            raise ValueError("published scientific run identity differs")
        equity = pd.read_csv(
            path / "equity.csv",
            index_col="date",
            parse_dates=True,
            float_precision="round_trip",
        )["equity"]
        trades = [
            Trade(
                pd.Timestamp(r["date"]),
                r["type"],
                r["price"],
                r["quantity"],
                r["cost"],
                r["ticker"],
            )
            for r in pd.read_csv(
                path / "trades.csv", float_precision="round_trip"
            ).to_dict("records")
        ]
        backtest = BacktestResult(equity, trades, CAPITAL, float(equity.iloc[-1]))
        secondary = secondary_metrics(backtest, self.equity_sessions)
        return {
            "slot": slot,
            "path": str(path),
            "manifest": manifest,
            "backtest": backtest,
            "secondary": secondary,
        }

    def _run_slot(self, slot, spec, client=None):
        self._check_plan()
        row = self.db.execute("SELECT state FROM slots WHERE slot=?", (slot,)).fetchone()
        if row is not None and row[0] == "COMPLETE":
            return self._load(slot, spec)
        runner = self._runner(spec, slot, client)
        result = runner.run()
        require_execution_within_phase(
            result.evaluation.settlement_session, PHASE_WINDOWS[self.phase]
        )
        secondary_metrics(result.backtest, self.equity_sessions)
        if client is not None:
            client.assert_complete()
            journal_artifact = getattr(client, "journal_artifact", None)
            if journal_artifact is not None:
                result = replace(
                    result, artifacts=(*result.artifacts, journal_artifact())
                )
        result = replace(result, run_id=self._path(slot).name)
        if self._path(slot).exists():
            self._recover_published(result)
        else:
            runner.persist(result)
        self._check_plan()
        seal = {p.name: sha_file(p) for p in self._path(slot).iterdir() if p.is_file()}
        self.db.execute(
            "UPDATE slots SET state='COMPLETE',seal=? WHERE slot=?",
            (canonical_json(seal), slot),
        )
        self.db.commit()
        return self._load(slot, spec)

    def _recover_published(self, result):
        """Publication succeeded before slot sealing: verify exact replay, keep bytes."""
        path = self.root / "runs" / result.run_id
        manifest = json.loads((path / "manifest.json").read_text())
        if (
            manifest["experiment_spec"] != result.spec.to_dict()
            or manifest["spec_hash"] != result.spec_hash
            or manifest["run_context"] != result.context.to_dict()
            or manifest["evaluation_evidence"] != result.evaluation.to_dict()
            or manifest["snapshot"]["identity_digest"] != result.snapshot.identity_digest
            or manifest["metrics"] != dict(result.metrics)
            or manifest["final_equity"] != result.final_equity
        ):
            raise ValueError("published unsealed run differs from exact recovery")
        with tempfile.TemporaryDirectory(
            dir=self.root, prefix="offline-recovery-"
        ) as tmp:
            tmp = Path(tmp)
            _write_equity(result, tmp / "equity.csv")
            _write_trades(result, tmp / "trades.csv")
            for name in ("equity.csv", "trades.csv"):
                if (path / name).read_bytes() != (tmp / name).read_bytes():
                    raise ValueError(
                        "published financial artifact differs from exact recovery"
                    )
        expected_files = {"equity.csv", "trades.csv", "manifest.json"}
        for artifact in result.artifacts:
            expected_files.add(artifact.filename)
            data = (path / artifact.filename).read_bytes()
            description = manifest["participant_artifacts"][artifact.name]
            if hashlib.sha256(data).hexdigest() != description["sha256"]:
                raise ValueError("published participant artifact changed")
            if artifact.filename == "llm_calls.jsonl":

                def semantic(trace):
                    return [
                        (
                            r.request.identity(),
                            r.status,
                            r.validated_response,
                            r.error_type,
                            r.error_message,
                        )
                        for r in load_trace(trace)
                    ]

                if semantic(data) != semantic(artifact.content):
                    raise ValueError("published trace differs from exact recovery")
            elif data != artifact.content:
                raise ValueError("published decisions differ from exact recovery")
        if {p.name for p in path.iterdir()} != expected_files:
            raise ValueError("unexpected published artifact during recovery")

    @contextmanager
    def _lease(self):
        lock = self.root / "execution.lock"
        with lock.open("x") as stream:
            stream.write(f"offline-exclusive pid={os.getpid()}\n")
        try:
            with no_network():
                yield
        finally:
            lock.unlink()  # Own exclusive marker only; abandoned markers fail closed.

    def execute(self):
        with self._lease():
            self._check_plan()
            if self.phase == "FINAL_TEST":
                self.validation.require_release(self.snapshot, source_hashes())
            for j in range(1, 4):
                slot = f"L{j:02d}"
                row = self.db.execute(
                    "SELECT state FROM slots WHERE slot=?", (slot,)
                ).fetchone()
                if row is not None and row[0] == "COMPLETE":
                    self._load(slot, self._spec(self.llm_spec))
                    continue
                fresh = row is None
                if fresh:
                    mock = self.mock_factory(slot)
                    if (
                        not isinstance(mock, MockLLMClient)
                        or mock.calls
                        or any(mock is c for c in self._clients)
                    ):
                        raise ValueError(
                            "fresh isolated MockLLMClient required; no cache or live provider"
                        )
                    self._clients.append(mock)
                    self.db.execute(
                        "INSERT INTO slots VALUES (?,'STARTED',NULL)", (slot,)
                    )
                    self.db.commit()
                else:
                    mock = (
                        None  # No factory invocation / fresh inference during recovery.
                    )
                client = _JournalClient(self.db, slot, mock)
                self._run_slot(slot, self._spec(self.llm_spec), client)
            for participant in BENCHMARK_SPECS:
                slot = participant.kind
                self.db.execute(
                    "INSERT OR IGNORE INTO slots VALUES (?,'STARTED',NULL)", (slot,)
                )
                self.db.commit()
                self._run_slot(slot, self._spec(participant))
            return self.summary()

    def summary(self):
        self._check_plan()
        identities = {
            r[0]
            for r in self.db.execute(
                "SELECT slot FROM slots WHERE slot GLOB 'L[0-9][0-9]'"
            )
        }
        if identities != {"L01", "L02", "L03"}:
            raise ValueError("exactly three baseline run identities required")
        runs = [self._load(f"L{j:02d}", self._spec(self.llm_spec)) for j in range(1, 4)]
        benchmarks = [self._load(s.kind, self._spec(s)) for s in BENCHMARK_SPECS]
        series = {COLUMNS[0]: periodic_returns(benchmarks[0]["backtest"].equity_curve)}
        series.update(
            {
                COLUMNS[j]: periodic_returns(runs[j - 1]["backtest"].equity_curve)
                for j in range(1, 4)
            }
        )
        stats = phase_statistics(self.phase, series, self.equity_sessions[1:])
        return {
            "mode": "OFFLINE_SYNTHETIC_ONLY",
            "phase": self.phase,
            "plan_hash": self.plan_hash,
            "amendment_status": AMENDMENT_STATUS,
            "R": 3,
            "statistics": stats,
            "individual": [
                {
                    "slot": r["slot"],
                    "path": r["path"],
                    "metrics": r["manifest"]["metrics"],
                    "secondary": r["secondary"],
                }
                for r in runs
            ],
            "benchmarks": [
                {
                    "kind": b["slot"],
                    "path": b["path"],
                    "metrics": b["manifest"]["metrics"],
                    "secondary": b["secondary"],
                }
                for b in benchmarks
            ],
        }

    def require_release(self, snapshot, hashes):
        if self.phase != "VALIDATION":
            raise ValueError("release evidence must be Validation")
        if (
            snapshot.identity_digest != self.snapshot.identity_digest
            or hashes != self.plan["sources_sha256"]
        ):
            raise ValueError("Validation/Final identity mismatch")
        self.summary()  # Completeness, seals and identity; no performance thresholds.
        return True

    def _load_cost_disposition(self, identity):
        row = self.db.execute(
            "SELECT value FROM meta WHERE key=?", (identity,)
        ).fetchone()
        return None if row is None else json.loads(row[0])

    def _save_cost_disposition(self, identity, value):
        self.db.execute(
            "INSERT INTO meta VALUES (?,?)", (identity, canonical_json(value))
        )
        self.db.commit()

    def cost_sensitivity(self):
        """All predeclared dispositions; strict replay, no subset aggregation."""
        with self._lease():
            self._check_plan()
            self.summary()  # Baseline must be complete before descriptive scenarios.
            report = {}
            for spread in (0, 5, 10, 20):
                individual, benchmark_results = [], []
                for j in range(1, 4):
                    slot = f"L{j:02d}"
                    baseline = self._load(slot, self._spec(self.llm_spec))
                    if spread == 5:
                        individual.append(
                            {
                                "slot": slot,
                                "status": "BASELINE_REUSED",
                                "result": baseline,
                            }
                        )
                        continue
                    identity = f"{slot}-cost-{spread}"
                    disposition = self._load_cost_disposition(identity)
                    if disposition is not None:
                        value = disposition
                        if value["status"] == "COMPLETE_EXACT_REPLAY":
                            value["result"] = self._load(
                                identity, self._spec(self.llm_spec, spread)
                            )
                        individual.append(value)
                        continue
                    records = load_trace(
                        (Path(baseline["path"]) / "llm_calls.jsonl").read_bytes()
                    )
                    replay = ReplayLLMClient(
                        records, provider="gemini", requested_model="gemini-3.8-flash"
                    )
                    self.db.execute(
                        "INSERT OR IGNORE INTO slots VALUES (?,'STARTED',NULL)",
                        (identity,),
                    )
                    self.db.commit()
                    try:
                        result = self._run_slot(
                            identity, self._spec(self.llm_spec, spread), replay
                        )
                    except ReplayMismatchError as exc:
                        affected = replay.pending[0] if replay.pending else None
                        value = {
                            "slot": slot,
                            "status": INVALID_COST_REPLAY,
                            "metrics": None,
                            "reason": type(exc).__name__ + ": " + str(exc),
                            "affected_identity": None
                            if affected is None
                            else affected.request.identity_digest,
                            "affected_call": None
                            if affected is None
                            else affected.call_id,
                            "consumed_calls": replay.consumed,
                        }
                        self._save_cost_disposition(identity, value)
                        individual.append(value)
                    else:
                        value = {"slot": slot, "status": "COMPLETE_EXACT_REPLAY"}
                        self._save_cost_disposition(identity, value)
                        individual.append({**value, "result": result})
                for participant in BENCHMARK_SPECS:
                    slot = (
                        participant.kind
                        if spread == 5
                        else f"{participant.kind}-cost-{spread}"
                    )
                    self.db.execute(
                        "INSERT OR IGNORE INTO slots VALUES (?,'STARTED',NULL)", (slot,)
                    )
                    self.db.commit()
                    result = self._run_slot(slot, self._spec(participant, spread))
                    benchmark_results.append(result)
                complete = all("result" in r for r in individual)
                stats = None
                if complete:
                    from src.experiments.h2_evaluation import aggregate, aligned_returns

                    series = {
                        COLUMNS[0]: periodic_returns(
                            benchmark_results[0]["backtest"].equity_curve
                        )
                    }
                    series.update(
                        {
                            COLUMNS[j]: periodic_returns(
                                individual[j - 1]["result"]["backtest"].equity_curve
                            )
                            for j in range(1, 4)
                        }
                    )
                    stats = aggregate(aligned_returns(series, self.equity_sessions[1:]))
                report[str(spread)] = {
                    "statistics": stats,
                    "confirmatory_contrasts": 0,
                    "individual": [
                        {k: v for k, v in r.items() if k != "result"}
                        | (
                            {
                                "metrics": r["result"]["manifest"]["metrics"],
                                "secondary": r["result"]["secondary"],
                                "path": r["result"]["path"],
                            }
                            if "result" in r
                            else {}
                        )
                        for r in individual
                    ],
                    "benchmarks": [
                        {
                            "kind": b["slot"],
                            "metrics": b["manifest"]["metrics"],
                            "secondary": b["secondary"],
                            "path": b["path"],
                        }
                        for b in benchmark_results
                    ],
                }
            return report
