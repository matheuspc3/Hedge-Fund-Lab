"""Local asynchronous command gate. Durable run claims fail closed after a crash."""

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import subprocess
import threading
import time
from contextlib import closing

import forward_api as api

fwd = api.fwd
OPERATIONS = api.ROOT / "data/forward/h2_v6_dashboard"


class Conflict(ValueError):
    pass


class Jobs:
    def __init__(self, root=OPERATIONS, forward_root=api.OUTPUT):
        self.root, self.forward_root = root, forward_root
        self.csrf = secrets.token_urlsafe(32)
        self.secret = secrets.token_bytes(32)
        self.active = set()
        self.mutex = threading.Lock()

    def _invoke(self, command, confirm=None):
        args = [
            sys_python(),
            "-B",
            str(api.ROOT / "scripts/run_h2_v6_forward.py"),
            command,
        ]
        if command == "run":
            args += ["--confirm", confirm]
        # Only fixed commands and the server-verified 12-hex hash reach the runner.
        return subprocess.run(
            args,
            cwd=api.ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=3600,
        )

    def _preflight(self, own_job=None):
        process = self._invoke("preflight")
        raw, _ = json.JSONDecoder().raw_decode(process.stdout.lstrip())
        checks = {k: v is True for k, v in raw["checks"].items()}
        model_params = (raw.get("identity") or {}).get("params") or api.read(
            fwd.CANDIDATE
        )["protocol"]["participant_spec"]["params"]
        # Error strings and stdout can contain provider details. Only gate booleans
        # and known scientific/model fields are exposed over HTTP.
        report = {
            "ready": raw["ready"] is True
            and process.returncode == 0
            and all(checks.values()),
            "checks": checks,
            "calendar": api.pick(
                raw.get("calendar"),
                "decision_session",
                "target_session",
                "target_open_deadline",
            ),
            "input": api.pick(raw.get("input"), "sha256", "close_used", "fetched_at"),
            "model": api.pick(
                model_params,
                "model",
                "temperature",
                "thinking_level",
            ),
            "identity_verified": checks.get("treatment_identity", False),
            "runner_sha256": (raw.get("identity") or {}).get("runner_sha256"),
            "estimate": api.pick(
                raw.get("estimate_per_session"),
                "usd_expected",
                "usd_prudent_budget",
                "usd_theoretical_ceiling",
                "logical_calls_expected",
                "logical_calls_max",
                "http_attempts_max",
                "price_note",
            ),
        }
        session = api.session_name(report["calendar"]["decision_session"])
        folder = self.forward_root / "sessions" / session
        if (folder / "decision.json").exists():
            report["state"] = "DECISION_EXISTS"
            report["ready"] = False
        elif (
            (api.read(self.root / f"run-{session}.json") or {}).get("job")
            not in (None, own_job)
        ) or (folder / "provider.sqlite").exists():
            report["state"] = "RECOVERY_REQUIRED"
            report["ready"] = False
        else:
            report["state"] = "READY" if report["ready"] else "NOT_READY"
        return report

    def _binding(self, report):
        return {
            "session": report["calendar"]["decision_session"],
            "sha256": report["input"]["sha256"],
            "deadline": report["calendar"]["target_open_deadline"],
            "runner_sha256": report.get("runner_sha256"),
            "ledger": fwd.sha_file(self.forward_root / "state.json")
            if (self.forward_root / "state.json").exists()
            else None,
        }

    def _token(self, report):
        payload = json.dumps(
            {**self._binding(report), "expires": time.time() + 600},
            sort_keys=True,
            separators=(",", ":"),
        )
        return (
            payload
            + "."
            + hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        )

    def _verify(self, token):
        if not isinstance(token, str) or len(token) > 2048:
            raise Conflict("invalid_confirmation")
        try:
            payload, signature = token.rsplit(".", 1)
            valid = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, valid):
                raise ValueError("signature")
            value = json.loads(payload)
            api.session_name(value["session"])
            if value["expires"] <= time.time() or fwd.now() >= fwd.pd.Timestamp(
                value["deadline"]
            ):
                raise ValueError("expired")
            folder = self.forward_root / "sessions" / value["session"]
            if fwd.sha_file(folder / "input.json") != value["sha256"]:
                raise ValueError("changed input")
            ledger = self.forward_root / "state.json"
            if value["ledger"] != (fwd.sha_file(ledger) if ledger.exists() else None):
                raise ValueError("changed ledger")
            if value["session"] != str(fwd.last_closed_session(fwd.now()).date()):
                raise ValueError("changed session")
            if value.get("runner_sha256") and value["runner_sha256"] != fwd.sha_file(
                api.ROOT / "scripts/run_h2_v6_forward.py"
            ):
                raise ValueError("changed runner")
            return value
        except (ValueError, KeyError, OSError, TypeError) as exc:
            raise Conflict("stale_or_invalid_confirmation; repeat_preflight") from exc

    def _save(self, job):
        path = self.root / f"job-{job['id']}.json"
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(job, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows can transiently deny replacement while a status reader closes.
        # Keep the old complete record and retry briefly; persistent errors escape.
        for attempt in range(20):
            try:
                temporary.replace(path)
                break
            except PermissionError:
                if os.name != "nt" or attempt == 19:
                    raise
                time.sleep(0.01)

    def start(self, command, token=None):
        if command not in ("prepare", "preflight", "run", "benchmarks"):
            raise ValueError("invalid_command")
        with self.mutex:
            self.root.mkdir(parents=True, exist_ok=True)
            lock = self.root / "operation.lock"
            binding = self._verify(token) if command == "run" else None
            session = (
                binding["session"]
                if binding
                else str(fwd.last_closed_session(fwd.now()).date())
            )
            folder = self.forward_root / "sessions" / session
            if command == "run" and (folder / "decision.json").exists():
                raise Conflict("decision_exists; consultation_only")
            if command == "run" and (self.root / f"run-{session}.json").exists():
                raise Conflict("session_already_claimed; recovery_required")
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                raise Conflict(
                    "operation_busy_or_recovery_required; consult_status"
                ) from exc
            job = {
                "id": secrets.token_hex(16),
                "command": command,
                "session": session,
                "state": "RUNNING",
                "stage": "Processo solicitado; aguardando runner",
                "started_at": fwd.now().isoformat(),
            }
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump({"job": job["id"], "pid": os.getpid()}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                if command == "run":
                    # ponytail: one durable claim per session, never automatically
                    # retried. Upgrade recovery through audited CLI replay, not HTTP.
                    with (self.root / f"run-{session}.json").open(
                        "x", encoding="utf-8"
                    ) as stream:
                        json.dump({"job": job["id"], **binding}, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                self._save(job)
                self.active.add(job["id"])
                threading.Thread(
                    target=self._work, args=(job, binding), daemon=True
                ).start()
            except BaseException:
                lock.unlink(missing_ok=True)
                raise
            return job

    def _benchmarks(self):
        import run_h2_v6_forward_benchmarks as benchmarks

        results = {}
        for strategy in benchmarks.STRATEGIES:
            result = subprocess.run(
                [
                    sys_python(),
                    "-B",
                    str(api.ROOT / "scripts/run_h2_v6_forward_benchmarks.py"),
                    strategy,
                ],
                cwd=api.ROOT,
                capture_output=True,
                shell=False,
                timeout=600,
            )
            results[strategy] = (
                "SYNCED"
                if result.returncode == 0
                else "NOT_COMPARABLE_OR_BLOCKED; consult_local_runner"
            )
        return results

    def _work(self, job, binding):
        try:
            if job["command"] == "preflight":
                report = self._preflight()
                if report["ready"]:
                    report["confirmation_token"] = self._token(report)
                job.update(state="COMPLETE", report=report, stage=report["state"])
            elif job["command"] == "benchmarks":
                job.update(
                    state="COMPLETE",
                    benchmarks=self._benchmarks(),
                    stage="Benchmarks determinísticos verificados",
                )
            else:
                if binding:
                    report = self._preflight(own_job=job["id"])
                    if not report["ready"] or self._binding(report) != {
                        k: binding[k]
                        for k in (
                            "session",
                            "sha256",
                            "deadline",
                            "ledger",
                            "runner_sha256",
                        )
                    }:
                        raise Conflict("preflight_changed; no_provider_call")
                job["stage"] = (
                    "Runner em execução; progresso confirmado pelo journal"
                    if binding
                    else "Runner prepare: obtendo e congelando dados oficiais"
                )
                self._save(job)
                result = self._invoke(
                    job["command"], binding["sha256"][:12] if binding else None
                )
                if result.returncode:
                    job.update(
                        state="FAILED",
                        error="runner_failed; consult_local_diagnostics; no_automatic_retry",
                        exit_code=result.returncode,
                    )
                else:
                    job.update(
                        state="COMPLETE", stage="Runner concluído; consulte registros"
                    )
            job["finished_at"] = fwd.now().isoformat()
        except Exception:
            job.update(
                state="FAILED",
                error="operation_failed; consult_local_diagnostics; recovery_is_offline",
                finished_at=fwd.now().isoformat(),
            )
        finally:
            self._save(job)
            with self.mutex:
                self.active.discard(job["id"])
                (self.root / "operation.lock").unlink(missing_ok=True)

    def status(self, job_id=None):
        if job_id is not None and not re.fullmatch(r"[0-9a-f]{32}", job_id):
            raise ValueError("invalid_job")
        if job_id:
            job = api.read(self.root / f"job-{job_id}.json")
        else:
            paths = sorted(
                self.root.glob("job-*.json"), key=lambda p: p.stat().st_mtime_ns
            )
            job = api.read(paths[-1]) if paths else None
        if job:
            job = dict(job)
            if (job.get("report") or {}).get("ready"):
                try:
                    self._verify(job["report"].get("confirmation_token"))
                    if (
                        self.forward_root / "sessions" / job["session"] / "decision.json"
                    ).exists():
                        raise Conflict("decision_exists")
                except Conflict:
                    job["report"] = {
                        **job["report"],
                        "ready": False,
                        "state": "STALE_PREFLIGHT",
                        "confirmation_token": None,
                    }
            if job["state"] == "RUNNING":
                job["recovery_note"] = (
                    "Se o processo foi interrompido, mantenha o bloqueio e examine o journal local; nunca reinicie uma chamada paga pelo HTTP."
                )
                job["progress"] = (
                    progress(
                        self.forward_root
                        / "sessions"
                        / job["session"]
                        / "provider.sqlite"
                    )
                    if job["command"] == "run"
                    else None
                )
        return {
            "job": job,
            "busy": (self.root / "operation.lock").exists(),
            "csrf_token": self.csrf,
        }


def progress(path):
    if not path.is_file():
        return {"reserved": 0, "recorded": 0, "stages": []}
    try:
        with closing(
            sqlite3.connect(
                path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True, timeout=0.2
            )
        ) as db:
            rows = db.execute(
                "SELECT sequence, record IS NOT NULL, json_extract(record, '$.stage'), json_extract(record, '$.status') FROM calls ORDER BY sequence"
            ).fetchall()
        return {
            "reserved": len(rows),
            "recorded": sum(r[1] for r in rows),
            "stages": [
                {"sequence": r[0], "stage": r[2], "status": r[3], "recorded": bool(r[1])}
                for r in rows
            ],
        }
    except sqlite3.Error:
        return {
            "unavailable": True,
            "message": "Journal temporariamente indisponível; consulte novamente.",
        }


def sys_python():
    import sys

    return sys.executable


JOBS = Jobs()
