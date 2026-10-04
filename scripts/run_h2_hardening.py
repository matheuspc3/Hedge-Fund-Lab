"""Diagnostic Hardening (e passada B0) do H2 sob o METHODOLOGICAL FREEZE V1.

Executa ``H = 8 H_syn + 4 H_real`` com a spec congelada
(``h2_freeze_v1_params``) e o ``thinking_level`` dado pela escada. Nada é
liquidado: nenhum retorno, P&L ou métrica financeira é calculado. Os gates
G-A, G-T, G-I e G-F vêm de ``diagnostic_metrics``/``gate_flags``.

Uso::

    python scripts/run_h2_hardening.py --mode hardening --thinking-level low
    python scripts/run_h2_hardening.py --mode b0 --thinking-level low

A credencial vem só de ``GEMINI_API_KEY`` (ambiente ou ``.env`` local,
ignorado pelo git); nunca é impressa nem gravada, e cabeçalhos HTTP nunca
entram na evidência.
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.llm_client import (  # noqa: E402
    GeminiLLMClient,
    RetryingLLMClient,
    _http_json_transport,
)
from src.agents.llm_trace import load_trace  # noqa: E402
from src.agents.participant import LLMParticipant  # noqa: E402
from src.artifacts import canonical_json  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FREEZE_V1_GATES,
    H2_FREEZE_VERSION,
    H_REAL_RESERVED_AT_FREEZE,
    H_REAL_SESSIONS,
    H_REAL_SNAPSHOT_ID,
    H_REAL_SNAPSHOT_IDENTITY_DIGEST,
    H_REAL_TICKER,
    H_SYN_PAYLOAD_DIGESTS,
    H_SYN_VERSION,
    HardeningAbortedError,
    diagnostic_metrics,
    gate_flags,
    h2_freeze_v1_params,
    h_real_states,
    run_hardening,
    scientific_payload_digest,
    synthetic_states,
)
from src.experiments.spec import ParticipantSpec  # noqa: E402
from src.pipeline.snapshot import (  # noqa: E402
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)

REPETITIONS = {"hardening": 5, "b0": 1}
EVIDENCE_ROOT = ROOT / "docs" / "evidence" / "h2"


def load_key() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        value = dotenv_values(ROOT / ".env").get("GEMINI_API_KEY")
        if value:
            os.environ["GEMINI_API_KEY"] = value
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("BLOCKED - NO API KEY")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


class AttemptLog:
    """Transporte real que registra cada tentativa HTTP, sanitizada.

    Cabeçalhos (onde vive a credencial) nunca são lidos; do erro ficam tipo,
    status, ``retry_after`` e o começo da mensagem do provedor.
    """

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.attempts: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def __call__(self, method: str, url: str, headers: dict[str, str], body: dict[str, Any]):
        started = time.perf_counter()
        entry: dict[str, Any] = {}
        try:
            raw = _http_json_transport(method, url, headers, body, self.timeout)
            entry.update({"outcome": "http_200"})
            return raw
        except Exception as exc:
            entry.update(
                {
                    "outcome": type(exc).__name__,
                    "status": getattr(exc, "status", None),
                    "retry_after": getattr(exc, "retry_after", None),
                    "message": str(exc)[:200],
                }
            )
            raise
        finally:
            entry["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 1)
            with self._lock:
                self.attempts.append(entry)
                done = len(self.attempts)
            if entry["outcome"] != "http_200" or done % 25 == 0:
                print(f"  attempt {done}: {entry['outcome']} {entry.get('status') or ''}", flush=True)


def build_states():
    states = list(synthetic_states())
    for state in states:
        name = state.state_id.split(":", 1)[1]
        if scientific_payload_digest(state) != H_SYN_PAYLOAD_DIGESTS[name]:
            sys.exit(f"H_syn digest mismatch for {name}: refusing to run")
    snapshot = load_dataset_snapshot(ROOT / "data" / "snapshots" / H_REAL_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    if snapshot.identity_digest != H_REAL_SNAPSHOT_IDENTITY_DIGEST:
        sys.exit("H_real snapshot identity mismatch: refusing to run")
    frame = load_snapshot_frames(snapshot, (H_REAL_TICKER,))[H_REAL_TICKER]
    # h_real_states recusa qualquer payload diferente do congelado.
    states += list(h_real_states(frame, H_REAL_RESERVED_AT_FREEZE))
    return states


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(REPETITIONS), required=True)
    parser.add_argument("--thinking-level", required=True)
    args = parser.parse_args()

    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("working tree has tracked changes: commit before a scientific run")
    commit = git("rev-parse", "HEAD")
    load_key()

    params = h2_freeze_v1_params(args.thinking_level)
    capability = LLMParticipant.preflight(params, scientific=True)
    states = build_states()
    repetitions = REPETITIONS[args.mode]
    log = AttemptLog(timeout=120.0)
    started = datetime.now(timezone.utc)
    counter = {"n": 0}

    def factory(ticker: str) -> LLMParticipant:
        counter["n"] += 1
        print(f"treatment {counter['n']}/{len(states) * repetitions} ({ticker})", flush=True)
        client = RetryingLLMClient(
            GeminiLLMClient(model=params["model"], transport=log),
            max_attempts=params["retry_attempts"],
            base_delay=params["retry_base_delay"],
        )
        return LLMParticipant(ticker, llm_client=client, **params)

    aborted: HardeningAbortedError | None = None
    try:
        outcomes = run_hardening(states, factory, repetitions=repetitions)
    except HardeningAbortedError as exc:
        aborted, outcomes = exc, exc.outcomes
    finished = datetime.now(timezone.utc)

    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    out = EVIDENCE_ROOT / f"{args.mode}_{args.thinking_level}_{stamp}"
    (out / "traces").mkdir(parents=True, exist_ok=True)

    decisions, records = [], []
    for outcome in outcomes:
        name = f"{outcome.state_id.replace(':', '_')}__r{outcome.repetition}"
        (out / "traces" / f"{name}.jsonl").write_bytes(outcome.trace.content)
        records.extend(load_trace(outcome.trace.content))
        ticker = H_REAL_TICKER if outcome.state_id.startswith("real:") else "SYN"
        decisions.append(
            {
                "state_id": outcome.state_id,
                "repetition": outcome.repetition,
                "error": outcome.error,
                "reason": outcome.reason,
                "decision": None if outcome.record is None else outcome.record.to_json_dict(ticker),
                "trace_file": f"traces/{name}.jsonl",
            }
        )
    (out / "decisions.jsonl").write_text(
        "".join(canonical_json(line) + "\n" for line in decisions), encoding="utf-8"
    )
    (out / "attempts.jsonl").write_text(
        "".join(canonical_json(line) + "\n" for line in log.attempts), encoding="utf-8"
    )

    metrics = diagnostic_metrics(outcomes)
    flags = gate_flags(metrics, H2_FREEZE_V1_GATES)
    gates = {
        "G-A": {"value": metrics["failure_count"], "threshold": "== 0", "pass": not flags["contract_failures"]},
        "G-T": {"value": metrics["max_tokens_count"], "threshold": "== 0", "pass": not flags["truncated_outputs"]},
        "G-I": {"value": metrics["total_hold_rate"], "threshold": "< 0.90", "pass": not flags["degenerate_inactive"]},
        "G-F": {"value": metrics["same_state_flip_rate"], "threshold": "<= 0.10", "pass": not flags["degenerate_unstable"]},
    }
    usage = Counter()
    for record in records:
        for key, value in (record.token_usage or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                usage[key] += value
    latencies = sorted(a["latency_ms"] for a in log.attempts)
    operational = {
        "logical_calls": len(records),
        "logical_calls_by_stage": dict(Counter(r.request.stage for r in records)),
        "http_attempts": len(log.attempts),
        "recovered_retries": sum(r.attempt_count - 1 for r in records if r.status == "ok"),
        # Backoff agendado pela política (base * 2^k por retry); um 429 com
        # Retry-After/RetryInfo substitui o termo e aparece em attempts.jsonl.
        "backoff_seconds_scheduled": sum(
            params["retry_base_delay"] * 2**k
            for r in records
            for k in range(r.attempt_count - 1)
        ),
        "retry_after_seconds_requested": sum(
            a["retry_after"] for a in log.attempts if a.get("retry_after")
        ),
        "final_error_calls": sum(1 for r in records if r.status == "error"),
        "attempt_outcomes": dict(Counter(a["outcome"] for a in log.attempts)),
        "http_status_counts": dict(Counter(str(a.get("status")) for a in log.attempts if a.get("status"))),
        "http_429": sum(1 for a in log.attempts if a.get("status") == 429),
        "http_503": sum(1 for a in log.attempts if a.get("status") == 503),
        "transient_error_rate": (
            sum(1 for a in log.attempts if a["outcome"] != "http_200") / len(log.attempts)
            if log.attempts
            else None
        ),
        "attempt_latency_ms": {
            "p50": latencies[len(latencies) // 2] if latencies else None,
            "p90": latencies[int(len(latencies) * 0.9)] if latencies else None,
            "max": latencies[-1] if latencies else None,
        },
        "token_usage_totals": dict(usage),
        "cost": "not computed: no pricing source is recorded in the repository",
        "wall_clock_seconds": round((finished - started).total_seconds(), 1),
    }
    manifest = {
        "kind": f"H2_{args.mode.upper()}",
        "freeze": H2_FREEZE_VERSION,
        "financial_metrics": "none computed (no settlement)",
        "started_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "finished_utc": finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": commit,
        "python": platform.python_version(),
        "participant_params": params,
        "participant_spec_sha256": {
            ticker: hashlib.sha256(
                canonical_json(ParticipantSpec("llm_agent", {"ticker": ticker, **params}).to_dict()).encode()
            ).hexdigest()
            for ticker in ("SYN", H_REAL_TICKER)
        },
        "capability": {
            "status": capability.status,
            "qualified": list(capability.qualified),
            "model": capability.model,
        },
        "runtime": {"provider": "gemini", "api": "v1beta models.generateContent"},
        "resolved_models": dict(Counter(r.resolved_model for r in records)),
        "H": {
            "H_SYN_VERSION": H_SYN_VERSION,
            "H_syn_payload_digests": dict(H_SYN_PAYLOAD_DIGESTS),
            "H_real_ticker": H_REAL_TICKER,
            "H_real_sessions": list(H_REAL_SESSIONS),
            "H_real_snapshot_id": H_REAL_SNAPSHOT_ID,
            "H_real_snapshot_identity_digest": H_REAL_SNAPSHOT_IDENTITY_DIGEST,
            "states": [state.state_id for state in states],
            "repetitions": repetitions,
        },
        "aborted": None if aborted is None else str(aborted),
        "diagnostics": metrics,
        "gates": gates,
        "gates_pass": all(item["pass"] for item in gates.values()) and aborted is None,
        "operational": operational,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    print(out.as_posix())
    print(json.dumps({"gates": gates, "operational": operational}, indent=2, default=str))


if __name__ == "__main__":
    main()
