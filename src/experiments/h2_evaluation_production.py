"""H2 v6 evaluation integration. Candidates permit only generated-data qualification.

Shares the qualified slot publication/statistics/replay implementation; never
uses its synthetic constructor, registry bridge or allow_dirty escape live.
"""

import base64
import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

from src.agents.llm_client import (
    GeminiLLMClient,
    LLMClient,
    ProviderTransportError,
    RetryingLLMClient,
)
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
from src.artifacts import RunArtifact, canonical_json
from src.backtesting.b3_calendar import B3Calendar
from src.experiments.context import RunContext
from src.experiments.h2_evaluation import (
    BENCHMARK_SPECS,
    EVALUATION_WINDOWS,
    INVALID_COST_REPLAY,
    PARTICIPANT_SHA256,
    PHASE_WINDOWS,
    RESERVED_SNAPSHOT,
    digest,
)
from src.experiments.h2_evaluation_manifest import (
    ROOT,
    protocol,
    read,
    require_authorization,
    sha_file,
    verify_manifest,
)
from src.experiments.h2_evaluation_offline import (
    OfflineEvaluationBatch,
    build_with_client,
)
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import ParticipantSpec
from src.pipeline.snapshot import verify_snapshot_integrity

QUALIFIED_STATUS = "H2_V6 EVALUATION PRODUCTION PATH QUALIFIED OFFLINE — AWAITING FORMAL APPROVAL AND SYSTEM FREEZE"
_PENDING_CALL = ContextVar("h2_v6_pending_call", default=None)


class JournalIntegrityError(RuntimeError):
    """Local durability/integrity failure; never a transient provider retry."""


class SyntheticTransport:
    """Explicit in-process fake native HTTP transport, used only by qualification."""

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, method, url, headers, body):
        return self.callback(method, url, headers, body)


class CallBank:
    def __init__(self, path, manifest_sha, phase):
        self.manifest_sha, self.phase = manifest_sha, phase
        self.lock = threading.RLock()
        if Path(path).exists():
            with sqlite3.connect(path) as existing:
                tables = {
                    r[0]
                    for r in existing.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                if tables != {"reservations", "identity", "calls", "attempts"}:
                    raise JournalIntegrityError(
                        "existing call bank schema lost or corrupted; no reconstruction"
                    )
                if existing.execute("SELECT value FROM identity").fetchall() != [
                    (canonical_json({"manifest_sha256": manifest_sha, "phase": phase}),)
                ]:
                    raise JournalIntegrityError(
                        "existing call bank identity missing or differs"
                    )
                reservations = existing.execute(
                    "SELECT slot,count FROM reservations"
                ).fetchall()
                if (
                    len(reservations) != 3
                    or {r[0] for r in reservations} != {"L01", "L02", "L03"}
                    or any(r[1] < 0 for r in reservations)
                ):
                    raise JournalIntegrityError(
                        "existing reservation ledger missing or corrupted"
                    )
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS reservations(slot TEXT PRIMARY KEY,count INTEGER NOT NULL)"
        )
        for slot in ("L01", "L02", "L03"):
            self.db.execute("INSERT OR IGNORE INTO reservations VALUES (?,0)", (slot,))
        self.db.execute("CREATE TABLE IF NOT EXISTS identity(value TEXT NOT NULL)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS calls(slot TEXT, sequence INTEGER, request TEXT NOT NULL, identity TEXT NOT NULL, raw BLOB, raw_sha TEXT, record TEXT, record_sha TEXT, PRIMARY KEY(slot,sequence))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS attempts(slot TEXT, sequence INTEGER, attempt INTEGER, evidence TEXT NOT NULL, sha TEXT NOT NULL, PRIMARY KEY(slot,sequence,attempt))"
        )
        identity = canonical_json({"manifest_sha256": manifest_sha, "phase": phase})
        old = self.db.execute("SELECT value FROM identity").fetchall()
        if old and old != [(identity,)]:
            self.db.close()
            raise JournalIntegrityError("call bank belongs to another phase/manifest")
        if not old:
            self.db.execute("INSERT INTO identity VALUES (?)", (identity,))
        self.db.commit()

    def close(self):
        self.db.close()

    def _commit(self, sql, args, *, reservation_slot=None):
        with self.lock:
            try:
                self.db.execute(sql, args)
                if reservation_slot is not None:
                    self.db.execute(
                        "UPDATE reservations SET count=count+1 WHERE slot=?",
                        (reservation_slot,),
                    )
                self.db.commit()
            except (sqlite3.Error, OSError) as exc:
                self.db.rollback()
                raise JournalIntegrityError(
                    "journal commit failed; no response delivery"
                ) from exc

    def row(self, slot, sequence):
        with self.lock:
            row = self.db.execute(
                "SELECT request,identity,raw,raw_sha,record,record_sha FROM calls WHERE slot=? AND sequence=?",
                (slot, sequence),
            ).fetchone()
        if row is not None:
            if digest(json.loads(row[0])) != row[1]:
                raise JournalIntegrityError("journal request identity corrupted")
            for data, expected in ((row[2], row[3]), (row[4], row[5])):
                if (data is None) != (expected is None) or (
                    data is not None
                    and hashlib.sha256(
                        data.encode() if isinstance(data, str) else data
                    ).hexdigest()
                    != expected
                ):
                    raise JournalIntegrityError("journal response hash corrupted")
        return row

    def reserve(self, slot, sequence, request, *, fresh):
        row = self.row(slot, sequence)
        identity = canonical_json(request.identity())
        if row is not None:
            if row[0] != identity or row[1] != request.identity_digest:
                raise ReplayMismatchError("reserved scientific request identity differs")
            return row
        if not fresh:
            raise ReplayMismatchError(
                "recovery has no exact call; fresh inference forbidden"
            )
        self._commit(
            "INSERT INTO calls(slot,sequence,request,identity) VALUES (?,?,?,?)",
            (slot, sequence, identity, request.identity_digest),
            reservation_slot=slot,
        )
        return self.row(slot, sequence)

    def never_reserved(self, slot):
        with self.lock:
            count = self.db.execute(
                "SELECT count FROM reservations WHERE slot=?", (slot,)
            ).fetchone()
            rows = self.db.execute(
                "SELECT count(*) FROM calls WHERE slot=?", (slot,)
            ).fetchone()[0]
            attempts = self.db.execute(
                "SELECT count(*) FROM attempts WHERE slot=?", (slot,)
            ).fetchone()[0]
        if count is None or count[0] != rows:
            raise JournalIntegrityError("reservation ledger missing or corrupted")
        return count[0] == 0 and attempts == 0

    def attempt(self, slot, sequence, number, evidence):
        data = canonical_json(evidence)
        self._commit(
            "INSERT OR REPLACE INTO attempts VALUES (?,?,?,?,?)",
            (slot, sequence, number, data, hashlib.sha256(data.encode()).hexdigest()),
        )

    def envelope(self, slot, sequence, raw):
        if not isinstance(raw, bytes):
            raise JournalIntegrityError(
                "native transport must return exact response bytes"
            )
        self._commit(
            "UPDATE calls SET raw=?,raw_sha=? WHERE slot=? AND sequence=?",
            (raw, hashlib.sha256(raw).hexdigest(), slot, sequence),
        )

    def response(self, slot, sequence, record):
        data = canonical_json(record.to_json_dict())
        self._commit(
            "UPDATE calls SET record=?,record_sha=? WHERE slot=? AND sequence=?",
            (data, hashlib.sha256(data.encode()).hexdigest(), slot, sequence),
        )

    def attempt_count(self, slot, sequence):
        with self.lock:
            return self.db.execute(
                "SELECT count(*) FROM attempts WHERE slot=? AND sequence=?",
                (slot, sequence),
            ).fetchone()[0]

    def export(self, slot):
        with self.lock:
            sequences = [
                r[0]
                for r in self.db.execute(
                    "SELECT sequence FROM calls WHERE slot=? ORDER BY sequence", (slot,)
                )
            ]
        if sequences != list(range(len(sequences))):
            raise JournalIntegrityError("call bank sequences are incomplete")
        with self.lock:
            count = self.db.execute(
                "SELECT count FROM reservations WHERE slot=?", (slot,)
            ).fetchone()
        if count is None or count[0] != len(sequences):
            raise JournalIntegrityError("reservation ledger differs from call inventory")
        records = []
        for sequence in sequences:
            row = self.row(slot, sequence)
            if row[4] is None:
                raise JournalIntegrityError("uncertain or undelivered call in journal")
            record = load_trace((row[4] + "\n").encode())[0]
            if (
                record.request.identity_digest != row[1]
                or record.sequence != sequence
                or (record.status == "ok" and row[2] is None)
            ):
                raise JournalIntegrityError(
                    "validated record differs from reserved/raw identity"
                )
            with self.lock:
                attempts = self.db.execute(
                    "SELECT evidence,sha FROM attempts WHERE slot=? AND sequence=? ORDER BY attempt",
                    (slot, sequence),
                ).fetchall()
            if any(
                hashlib.sha256(data.encode()).hexdigest() != sha for data, sha in attempts
            ):
                raise JournalIntegrityError("attempt journal corrupted")
            records.append(
                {
                    "manifest_sha256": self.manifest_sha,
                    "phase": self.phase,
                    "run": slot,
                    "sequence": sequence,
                    "request": json.loads(row[0]),
                    "request_identity": row[1],
                    "raw_base64": None
                    if row[2] is None
                    else base64.b64encode(row[2]).decode(),
                    "raw_sha256": row[3],
                    "record": json.loads(row[4]),
                    "record_sha256": row[5],
                    "attempts": [json.loads(a[0]) for a in attempts],
                }
            )
        return ("\n".join(canonical_json(r) for r in records) + "\n").encode()


class DurableGeminiClient(LLMClient):
    def __init__(
        self, bank, slot, params, *, fresh, gate, transport=None, synthetic=False
    ):
        super().__init__()
        self.bank, self.slot, self.fresh, self.gate = bank, slot, fresh, gate
        self.sequence, self.session = 0, None
        self.native = GeminiLLMClient(
            model=params["model"],
            api_key="OFFLINE_SYNTHETIC_NO_SECRET" if synthetic or not fresh else None,
            base_url=GeminiLLMClient.DEFAULT_BASE_URL,
            transport=transport,
        )
        self.delegate = self.native.transport if fresh else None
        self.native.transport = self._transport
        self.client = (
            RetryingLLMClient(
                self.native,
                max_attempts=params["retry_attempts"],
                base_delay=params["retry_base_delay"],
            )
            if fresh
            else self.native
        )

    def begin_session(self, session):
        self.session = str(pd.Timestamp(session).date())
        if not (
            EVALUATION_WINDOWS[self.bank.phase].decision_start
            <= self.session
            <= EVALUATION_WINDOWS[self.bank.phase].decision_end
        ):
            raise ValueError("call session outside authorized decision phase")
        super().begin_session(session)

    def _transport(self, method, url, headers, body):
        slot, sequence = _PENDING_CALL.get()
        endpoint = urlsplit(url)
        if (
            method != "POST"
            or url != self.native._endpoint_url()
            or (
                endpoint.scheme != "https"
                or endpoint.netloc != "generativelanguage.googleapis.com"
                or endpoint.query
                or endpoint.fragment
            )
        ):
            raise JournalIntegrityError(
                "transport endpoint differs from native frozen runtime"
            )
        self.gate()
        row = self.bank.row(slot, sequence)
        if row is None:
            raise JournalIntegrityError("transport has no durable reservation")
        if row[2] is not None and not self.fresh:
            return row[2]
        if not self.fresh or self.delegate is None:
            raise JournalIntegrityError(
                "uncertain reserved response; no replacement transport"
            )
        number = self.bank.attempt_count(slot, sequence) + 1
        self.bank.attempt(slot, sequence, number, {"state": "RESERVED_BEFORE_TRANSPORT"})
        try:
            raw = self.delegate(method, url, headers, body)
        except Exception as exc:
            message = (
                str(exc).replace(self.native.api_key, "[REDACTED]")
                if self.native.api_key
                else str(exc)
            )
            self.bank.attempt(
                slot,
                sequence,
                number,
                {
                    "state": "TRANSPORT_ERROR",
                    "type": type(exc).__name__,
                    "message": message,
                    "http_status": getattr(exc, "status", None),
                    "retry_after": getattr(exc, "retry_after", None),
                },
            )
            raise
        if self.native.api_key and self.native.api_key.encode() in raw:
            raise JournalIntegrityError(
                "secret echoed in provider response; not persisted"
            )
        self.bank.envelope(
            slot, sequence, raw
        )  # FULL commit before parsing/schema validation.
        self.bank.attempt(
            slot,
            sequence,
            number,
            {
                "state": "ENVELOPE_DURABLE",
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_base64": base64.b64encode(raw).decode(),
            },
        )
        return raw

    async def generate(
        self,
        system_prompt,
        user_prompt,
        response_schema=None,
        options=None,
        *,
        metadata=None,
    ):
        if (
            self.session is None
            or metadata is None
            or metadata.stage
            not in ("technical_analyst", "risk_manager", "portfolio_manager")
        ):
            raise JournalIntegrityError("scientific session/stage must be explicit")
        expected_schema = {
            "technical_analyst": "TechnicalEvidenceResponse",
            "risk_manager": "RiskVerdict",
            "portfolio_manager": "PortfolioAction",
        }[metadata.stage]
        if schema_name(response_schema) != expected_schema:
            raise JournalIntegrityError("scientific stage/schema differs")
        request = LLMCallRequest(
            stage=metadata.stage,
            analyst_id=metadata.analyst_id,
            decision_session=self.session,
            provider="gemini",
            requested_model=self.native.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        sequence = self.sequence
        self.sequence += 1
        row = self.bank.reserve(self.slot, sequence, request, fresh=self.fresh)
        if row[4] is None:
            if not self.fresh and row[2] is None:
                raise JournalIntegrityError("uncertain reserved response; fail closed")
            recorder = RecordingLLMClient(
                self.client, provider="gemini", requested_model=self.native.model
            )
            recorder.begin_session(self.session)
            token = _PENDING_CALL.set((self.slot, sequence))
            try:
                try:
                    await recorder.generate(
                        system_prompt,
                        user_prompt,
                        response_schema,
                        options,
                        metadata=metadata,
                    )
                except JournalIntegrityError:
                    raise  # Do not convert a local durability failure to a replayable provider error.
                except ProviderTransportError as exc:
                    if not self.fresh:
                        raise JournalIntegrityError(
                            "durable envelope remains transport-invalid; uncertain retry cannot be resumed"
                        ) from exc
                except Exception:
                    pass  # The canonical record preserves the original scientific failure.
                record = replace(
                    recorder.records[0],
                    sequence=sequence,
                    attempt_count=self.bank.attempt_count(self.slot, sequence)
                    or recorder.records[0].attempt_count,
                    error_message=None
                    if recorder.records[0].error_message is None
                    else recorder.records[0].error_message.replace(
                        self.native.api_key, "[REDACTED]"
                    )
                    if self.native.api_key
                    else recorder.records[0].error_message,
                )
                self.bank.response(self.slot, sequence, record)
            finally:
                _PENDING_CALL.reset(token)
            row = self.bank.row(self.slot, sequence)
        replay = ReplayLLMClient(
            load_trace((row[4] + "\n").encode()),
            provider="gemini",
            requested_model=self.native.model,
        )
        replay.begin_session(self.session)
        response = await replay.generate(
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )
        replay.assert_complete()
        return response

    def assert_complete(self):
        data = self.bank.export(self.slot)
        if len(data.splitlines()) != self.sequence:
            raise JournalIntegrityError("run call bank missing or contains extra calls")

    def journal_artifact(self):
        return RunArtifact(
            name="provider_journal",
            filename="provider_journal.jsonl",
            schema_version=1,
            content=self.bank.export(self.slot),
        )


class EvaluationBatch(OfflineEvaluationBatch):
    """Reuse slot publication/metrics/cost replay, with productive guards and bank."""

    def __init__(
        self,
        root,
        snapshot,
        phase,
        *,
        manifest,
        manifest_sha256,
        authorization,
        transport_factory=None,
        validation_checkpoint=None,
    ):
        self.root = Path(root).resolve()
        self.manifest_path, self.manifest_sha = Path(manifest), manifest_sha256
        self.authorization_path = Path(authorization)
        self.authorization_sha = sha_file(self.authorization_path)
        self.document = verify_manifest(manifest, manifest_sha256)
        if phase not in PHASE_WINDOWS:
            raise ValueError("explicit evaluation phase required")
        self.synthetic = self.document["state"] == "CANDIDATE / NOT APPROVED / NOT FROZEN"
        require_authorization(
            self.document,
            self.manifest_sha,
            phase,
            authorization,
            synthetic=self.synthetic,
        )
        self.phase, self.snapshot = phase, snapshot
        if self.synthetic:
            if (
                snapshot.snapshot_id == RESERVED_SNAPSHOT
                or snapshot.path.resolve().is_relative_to(ROOT / "data")
            ):
                raise ValueError("reserved data forbidden before price access")
            marker = read(snapshot.path / "OFFLINE_FIXTURE.json")
            if (
                marker.get("generator") != "synthetic_fixture_v1"
                or marker.get("identity_digest") != snapshot.identity_digest
            ):
                raise ValueError("generated fixture attestation required")
            if transport_factory is None:
                raise ValueError(
                    "candidate qualification requires explicit fake transport"
                )
        elif (
            snapshot.snapshot_id != RESERVED_SNAPSHOT
            or snapshot.identity_digest != protocol()["snapshot"]["identity"]
        ):
            raise ValueError("frozen scientific snapshot differs")
        if not self.synthetic and (
            transport_factory is not None
            or self.root
            != (
                ROOT / self.document["protocol"]["production_output_roots"][phase]
            ).resolve()
        ):
            raise ValueError(
                "real phase requires the unique authorized output root and native transport"
            )
        for forbidden in (ROOT / "data/snapshots", ROOT / "docs/evidence/cal_b4"):
            if self.root.is_relative_to(forbidden):
                raise ValueError("evaluation output cannot overwrite reserved artifacts")
        verify_snapshot_integrity(snapshot)
        self.llm_spec = ParticipantSpec(**self.document["protocol"]["participant_spec"])
        self.plan = {
            "manifest_sha256": self.manifest_sha,
            "phase": phase,
            "snapshot_identity": snapshot.identity_digest,
            "sources_sha256": self.document["sources_sha256"],
            "R": 3,
        }
        self.plan_hash = digest(self.plan)
        self.validation_checkpoint = validation_checkpoint
        if phase == "FINAL_TEST":
            self._verify_checkpoint()  # Before output creation or participant construction.
        self.equity_sessions = pd.DatetimeIndex(
            B3Calendar().sessions_between(
                pd.Timestamp(PHASE_WINDOWS[phase].start).date(),
                pd.Timestamp(PHASE_WINDOWS[phase].end).date(),
            )
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(
            self.root / "evaluation.sqlite", check_same_thread=False
        )
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS slots(slot TEXT PRIMARY KEY,state TEXT NOT NULL,seal TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS dispositions(spread INTEGER,participant TEXT,state TEXT NOT NULL,detail TEXT,PRIMARY KEY(spread,participant))"
        )
        old = self.db.execute("SELECT value FROM meta WHERE key='plan'").fetchone()
        if old and old[0] != canonical_json(self.plan):
            self.db.close()
            raise ValueError("phase/batch identity changed; no rerun or tuning")
        self.db.execute(
            "INSERT OR IGNORE INTO meta VALUES ('plan',?)", (canonical_json(self.plan),)
        )
        for spread in (0, 5, 10, 20):
            for participant in (
                *("L01", "L02", "L03"),
                *(s.kind for s in BENCHMARK_SPECS),
            ):
                self.db.execute(
                    "INSERT OR IGNORE INTO dispositions VALUES (?,?,'PENDING',NULL)",
                    (spread, participant),
                )
        self.db.commit()
        if (
            not (self.root / "provider.sqlite").exists()
            and self.db.execute("SELECT count(*) FROM slots").fetchone()[0]
        ):
            self.db.close()
            raise JournalIntegrityError(
                "existing batch lost its call bank; cannot infer again"
            )
        self.bank = CallBank(self.root / "provider.sqlite", self.manifest_sha, phase)
        self.transport_factory, self._transports = transport_factory, []

    def close(self):
        self.bank.close()
        self.db.close()

    def _check_authority(self):
        if (
            sha_file(self.manifest_path) != self.manifest_sha
            or sha_file(self.authorization_path) != self.authorization_sha
        ):
            raise JournalIntegrityError("manifest or phase authorization changed")
        require_authorization(
            self.document,
            self.manifest_sha,
            self.phase,
            self.authorization_path,
            synthetic=self.synthetic,
        )

    def _check_plan(self):
        self._check_authority()
        if (
            self.plan_hash != digest(self.plan)
            or digest(self.llm_spec.to_dict()) != PARTICIPANT_SHA256
        ):
            raise ValueError("batch/treatment identity changed")
        verify_manifest(self.manifest_path, self.manifest_sha)
        verify_snapshot_integrity(self.snapshot)

    def _context(self, slot):
        return RunContext(self.phase, f"H2-V6:{self.manifest_sha}:{slot}")

    def _path(self, slot):
        return self.root / "runs" / f"H2-V6-{self.phase}-{slot}-{self.plan_hash[:12]}"

    def _runner(self, spec, slot, client=None):
        return ExperimentRunner(
            spec,
            context=self._context(slot),
            snapshot_dir=self.snapshot.path.parent,
            runs_dir=self.root / "runs",
            repository_dir=ROOT,
            boundaries=(PHASE_WINDOWS[self.phase],),
            participant_factory=None
            if client is None
            else lambda p: build_with_client(p, client),
        )

    def _load(self, slot, spec):
        result = super()._load(slot, spec)
        if any(not p.is_file() for p in self._path(slot).iterdir()):
            raise JournalIntegrityError("unexpected directory in sealed run")
        if slot in ("L01", "L02", "L03"):
            if (
                self._path(slot) / "provider_journal.jsonl"
            ).read_bytes() != self.bank.export(slot):
                raise JournalIntegrityError("published journal differs from durable bank")
        return result

    @contextmanager
    def _lease(self):
        lock = self.root / "execution.lock"
        with lock.open("x") as stream:
            stream.write(f"h2-v6-exclusive pid={os.getpid()}\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            yield
        finally:
            lock.unlink()
        # ponytail: exclusive file fails closed after process death. Investigate
        # abandoned locks manually; upgrade to OS leases only if availability needs it.

    def execute(self):
        with self._lease():
            self._check_plan()
            if self.phase == "FINAL_TEST":
                self._verify_checkpoint()
            for slot in ("L01", "L02", "L03"):
                row = self.db.execute(
                    "SELECT state FROM slots WHERE slot=?", (slot,)
                ).fetchone()
                if row and row[0] == "COMPLETE":
                    self._load(slot, self._spec(self.llm_spec))
                    continue
                fresh = self.bank.never_reserved(slot)
                if row is None and not fresh:
                    raise JournalIntegrityError(
                        "consumed call bank lost its slot metadata"
                    )
                transport = None
                if fresh:
                    self.db.execute(
                        "INSERT OR IGNORE INTO slots VALUES (?,'STARTED',NULL)", (slot,)
                    )
                    self.db.commit()
                    transport = (
                        self.transport_factory(slot) if self.transport_factory else None
                    )
                    if self.synthetic and not isinstance(transport, SyntheticTransport):
                        raise ValueError("candidate requires a fresh SyntheticTransport")
                    if transport is not None and any(
                        transport is t for t in self._transports
                    ):
                        raise ValueError(
                            "scientific slots cannot share a transport realization"
                        )
                    self._transports.append(transport)
                client = DurableGeminiClient(
                    self.bank,
                    slot,
                    self.llm_spec.params,
                    fresh=fresh,
                    gate=self._check_authority,
                    transport=transport,
                    synthetic=self.synthetic,
                )
                self._run_slot(slot, self._spec(self.llm_spec), client)
            for spec in BENCHMARK_SPECS:
                self.db.execute(
                    "INSERT OR IGNORE INTO slots VALUES (?,'STARTED',NULL)", (spec.kind,)
                )
                self.db.commit()
                self._run_slot(spec.kind, self._spec(spec))
            self._sync_dispositions()
            return self.summary()

    def summary(self):
        return {
            **super().summary(),
            "mode": "PRODUCTION_PATH_QUALIFIED_WITH_SYNTHETIC_DATA"
            if self.synthetic
            else "SCIENTIFIC_EVALUATION",
            "manifest_sha256": self.manifest_sha,
        }

    def checkpoint(self):
        if self.phase != "VALIDATION":
            raise ValueError("only Validation can issue a primary integrity checkpoint")
        self.summary()  # No performance condition and no descriptive-cost gate.
        path = self.root / "validation_release.json"
        hashes = {
            str(p.relative_to(self.root)): sha_file(p)
            for slot in ("L01", "L02", "L03", *(s.kind for s in BENCHMARK_SPECS))
            for p in self._path(slot).iterdir()
            if p.is_file()
        }
        value = {
            "kind": "H2_V6_VALIDATION_INTEGRITY_RELEASE",
            "phase": self.phase,
            "manifest_sha256": self.manifest_sha,
            "snapshot_identity": self.snapshot.identity_digest,
            "plan_hash": self.plan_hash,
            "R": 3,
            "artifacts_sha256": hashes,
            "performance_gate": False,
            "synthetic_only": self.synthetic,
        }
        from src.experiments.h2_evaluation_offline import _write_once

        _write_once(path, value)
        _write_once(path.with_suffix(".sha256.json"), {"sha256": sha_file(path)})
        return path

    def _verify_checkpoint(self):
        if self.validation_checkpoint is None:
            raise ValueError("Final requires a durable complete Validation checkpoint")
        path = Path(self.validation_checkpoint)
        if sha_file(path) != read(path.with_suffix(".sha256.json"))["sha256"]:
            raise ValueError("Validation checkpoint hash differs")
        value = read(path)
        if read(self.authorization_path).get("validation_checkpoint_sha256") != sha_file(
            path
        ):
            raise ValueError(
                "Final authorization is not bound to the Validation checkpoint"
            )
        if (
            value.get("kind") != "H2_V6_VALIDATION_INTEGRITY_RELEASE"
            or value.get("phase") != "VALIDATION"
            or (
                value.get("manifest_sha256") != self.manifest_sha
                or value.get("snapshot_identity") != self.snapshot.identity_digest
                or value.get("R") != 3
                or value.get("performance_gate") is not False
                or value.get("synthetic_only") != self.synthetic
            )
        ):
            raise ValueError("Validation/Final checkpoint identity differs")
        expected_slots = {"L01", "L02", "L03", *(s.kind for s in BENCHMARK_SPECS)}
        validation_plan_hash = digest({**self.plan, "phase": "VALIDATION"})
        if value["plan_hash"] != validation_plan_hash:
            raise ValueError("Validation plan differs")
        paths = {
            s: path.parent / "runs" / f"H2-V6-VALIDATION-{s}-{validation_plan_hash[:12]}"
            for s in expected_slots
        }
        inventories = {str(p.relative_to(path.parent)) for p in paths.values()}
        actual = {str(Path(p).parent) for p in value["artifacts_sha256"]}
        if actual != inventories:
            raise ValueError("Validation checkpoint misses runs/benchmarks")
        for relative, expected in value["artifacts_sha256"].items():
            target = (path.parent / relative).resolve()
            if (
                not target.is_relative_to(path.parent.resolve())
                or sha_file(target) != expected
            ):
                raise ValueError("Validation artifact corrupted")
        with sqlite3.connect(path.parent / "evaluation.sqlite") as db:
            for slot in expected_slots:
                state = db.execute(
                    "SELECT state,seal FROM slots WHERE slot=?", (slot,)
                ).fetchone()
                run = paths[slot]
                if not state or state[0] != "COMPLETE" or not state[1]:
                    raise ValueError("Validation slot incomplete")
                seal = json.loads(state[1])
                if set(seal) != {p.name for p in run.iterdir()} or any(
                    sha_file(run / name) != sha for name, sha in seal.items()
                ):
                    raise ValueError("Validation seal corrupted")
        if not (path.parent / "provider.sqlite").is_file():
            raise ValueError("Validation call bank missing")
        bank = CallBank(path.parent / "provider.sqlite", self.manifest_sha, "VALIDATION")
        try:
            for slot in ("L01", "L02", "L03"):
                if (paths[slot] / "provider_journal.jsonl").read_bytes() != bank.export(
                    slot
                ):
                    raise ValueError("Validation journal corrupted")
        finally:
            bank.close()

    def require_release(self, snapshot, hashes):
        if (
            self.phase != "VALIDATION"
            or snapshot.identity_digest != self.snapshot.identity_digest
            or hashes != self.plan["sources_sha256"]
        ):
            raise ValueError("Validation release identity differs")
        self.checkpoint()
        return True

    def _sync_dispositions(self):
        for spread, participant in self.db.execute(
            "SELECT spread,participant FROM dispositions"
        ).fetchall():
            slot = participant if spread == 5 else f"{participant}-cost-{spread}"
            value = None if spread == 5 else self._load_cost_disposition(slot)
            state = self.db.execute(
                "SELECT state FROM slots WHERE slot=?", (slot,)
            ).fetchone()
            if value:
                detail = value
                status = detail["status"]
            elif state and state[0] == "COMPLETE":
                status, detail = (
                    (
                        "BASELINE_REUSED"
                        if spread == 5
                        else "COMPLETE_EXACT_REPLAY"
                        if participant.startswith("L0")
                        else "COMPLETE_DETERMINISTIC"
                    ),
                    {"slot": slot},
                )
            else:
                status, detail = (
                    "PENDING",
                    {"reason": "phase descriptive closure incomplete"},
                )
            self.db.execute(
                "UPDATE dispositions SET state=?,detail=? WHERE spread=? AND participant=?",
                (status, canonical_json(detail), spread, participant),
            )
        self.db.commit()

    def _load_cost_disposition(self, identity):
        value = super()._load_cost_disposition(identity)
        seal = self.db.execute(
            "SELECT value FROM meta WHERE key=?", (identity + ":sha256",)
        ).fetchone()
        if (value is None) != (seal is None) or (
            value is not None and digest(value) != seal[0]
        ):
            raise JournalIntegrityError("cost disposition lost or corrupted")
        return value

    def _save_cost_disposition(self, identity, value):
        self.db.execute(
            "INSERT INTO meta VALUES (?,?)", (identity, canonical_json(value))
        )
        self.db.execute(
            "INSERT INTO meta VALUES (?,?)", (identity + ":sha256", digest(value))
        )
        self.db.commit()  # Disposition and digest share the same FULL transaction.

    def cost_sensitivity(self):
        try:
            result = super().cost_sensitivity()
        except Exception:
            self._sync_dispositions()
            raise  # Operational/corruption failures never become descriptive N/A.
        self._sync_dispositions()
        states = self.db.execute("SELECT state FROM dispositions").fetchall()
        allowed = {
            "BASELINE_REUSED",
            "COMPLETE_EXACT_REPLAY",
            "COMPLETE_DETERMINISTIC",
            INVALID_COST_REPLAY,
        }
        if len(states) != 24 or any(s[0] not in allowed for s in states):
            raise JournalIntegrityError("descriptive cost closure incomplete")
        from src.experiments.h2_evaluation_offline import _write_once

        _write_once(
            self.root / "cost_closure.json",
            {
                "manifest_sha256": self.manifest_sha,
                "phase": self.phase,
                "status": "COMPLETE_DISPOSITIONS",
                "report": result,
            },
        )
        return result
