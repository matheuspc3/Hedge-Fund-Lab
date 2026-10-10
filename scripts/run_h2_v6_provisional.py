"""H2 v6 Validation — rota operacional provisória autorizada somente pelo autor (OA-1).

NÃO é aprovação acadêmica, System Freeze nem ratificação: coautor e orientador
continuam pendentes e o candidato continua CANDIDATE / NOT APPROVED / NOT FROZEN.
Reutiliza o caminho produtivo qualificado (CallBank, DurableGeminiClient,
publicação, selos, custos) sem alterar nenhum byte inventariado no candidato.
Final Test não existe nesta rota.

    preflight  offline; confere identidades e mostra estimativa. Nenhuma chamada.
    authorize  o AUTOR registra aceite de OA-1 e consentimento de egress/cobrança.
    run        Validation R=3 real (Gemini). Exige autorização commitada e --confirm.
    audit      reverifica selos/journal/release e grava o checkpoint provisório.
"""

# ruff: noqa: E402 -- standalone entrypoint establishes repository imports.
import argparse
import datetime
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.artifacts import canonical_json
from src.backtesting.b3_calendar import B3Calendar
from src.experiments.context import RunContext
from src.experiments.h2_evaluation import (
    BENCHMARK_SPECS,
    PARTICIPANT_SHA256,
    PHASE_WINDOWS,
    RESERVED_SNAPSHOT,
    digest,
)
from src.experiments.h2_evaluation_manifest import (
    CANDIDATE,
    read,
    sha_file,
    verify_manifest,
)
from src.experiments.h2_evaluation_offline import _write_once
from src.experiments.h2_evaluation_production import (
    CallBank,
    EvaluationBatch,
    JournalIntegrityError,
)
from src.experiments.spec import ParticipantSpec
from src.pipeline.snapshot import load_dataset_snapshot, verify_snapshot_integrity

AMENDMENT_ID = "H2-V6-OA1"
AMENDMENT = ROOT / "docs/H2_V6_OPERATIONAL_AMENDMENT_OA1.md"
EVIDENCE = ROOT / "docs/evidence/h2_v6_provisional"
AUTHORIZATION = EVIDENCE / "AUTHOR_AUTHORIZATION_OA1.json"
CHECKPOINT = EVIDENCE / "VALIDATION_PROVISIONAL_CHECKPOINT.json"
OUTPUT = "data/runs/h2_v6_provisional/VALIDATION"
KIND = "H2_V6_AUTHOR_PROVISIONAL_OPERATIONAL_AUTHORIZATION"
MODE = "AUTHOR_PROVISIONAL_OPERATIONAL — NOT ACADEMICALLY RATIFIED"
PHASE = "VALIDATION"
SLOTS = ("L01", "L02", "L03")

# Estimativa: médias por chamada única das runs sequential-dev v6 e CAL-B4
# (tokens de saída incluem thoughts). Preço Gemini 3.8 Flash, tier pago padrão,
# introdutório até 2026-12-31 (ai.google.dev "What's new", consultado 2026-10-09);
# de 2027-01-01 em diante, 1.50/7.50. Reconfirmar no painel de billing.
PRICE_PER_M = {"input": 0.75, "output": 3.75}
CALLS_PER_SESSION = {
    "expected": 5.2,
    "max": 7,
}  # 5 técnicos + Risk/Portfolio quando acionados
TOKENS = {"input": 1100, "output": 190}  # média ponderada observada por chamada
MAX_OUTPUT_TOKENS, MAX_ATTEMPTS = 8192, 6


def candidate_sha():
    return CANDIDATE.with_suffix(".sha256").read_text(encoding="ascii").strip()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def expected_authorization(document, manifest_sha):
    protocol = document["protocol"]
    return {
        "kind": KIND,
        "amendment_id": AMENDMENT_ID,
        "amendment_sha256": sha_file(AMENDMENT),
        "runner_sha256": sha_file(__file__),
        "manifest_sha256": manifest_sha,
        "participant_sha256": PARTICIPANT_SHA256,
        "phase": PHASE,
        "R": 3,
        "run_identities": protocol["run_identities"][PHASE],
        "window": protocol["windows"][PHASE],
        "snapshot": protocol["snapshot"],
        "host": "generativelanguage.googleapis.com",
        "output_relative_path": OUTPUT,
        "role": "author",
        "accepts_operational_amendment": True,
        "accepts_normal_api_charges": True,
        "scientific_payloads_only": True,
        "final_test_authorized": False,
        "academic_ratification": False,
    }


def check_authorization(document, manifest_sha, path):
    auth = read(path)
    differs = [
        k
        for k, v in expected_authorization(document, manifest_sha).items()
        if auth.get(k) != v
    ]
    if differs:
        raise ValueError(f"OA-1 authorization does not cover this identity: {differs}")
    if auth.get("recorded_by_human") is not True or not auth.get("signatory"):
        raise ValueError("OA-1 authorization must be recorded by the author")
    return auth


def write_authorization(document, manifest_sha, signatory, path=AUTHORIZATION):
    value = {
        **expected_authorization(document, manifest_sha),
        "signatory": signatory,
        "recorded_by_human": True,
        "recorded_at": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "git_head": git("rev-parse", "HEAD").stdout.strip(),
        "statement": (
            "Autorizo, como autor e somente em meu nome, a execução operacional "
            "provisória da Validation H2 v6 (R=3) sob OA-1, com egress para a Gemini "
            "API e cobrança normal. Não é aprovação do coautor nem do orientador, "
            "não é System Freeze e não autoriza Final Test."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return path


class ProvisionalValidationBatch(EvaluationBatch):
    """Caminho produtivo qualificado com identidade, guard e raiz próprios de OA-1."""

    def __init__(self, snapshot, manifest_sha256, authorization, root=ROOT / OUTPUT):
        self.root = Path(root).resolve()
        self.manifest_path, self.manifest_sha = CANDIDATE, manifest_sha256
        self.authorization_path = Path(authorization)
        self.authorization_sha = sha_file(self.authorization_path)
        self.document = verify_manifest(CANDIDATE, manifest_sha256)
        self.phase, self.snapshot, self.synthetic = PHASE, snapshot, False
        self.validation_checkpoint = None
        self._check_authority()
        self._require_inputs()
        verify_snapshot_integrity(snapshot)
        self.llm_spec = ParticipantSpec(**self.document["protocol"]["participant_spec"])
        self.plan = {
            "mode": MODE,
            "amendment_id": AMENDMENT_ID,
            "manifest_sha256": manifest_sha256,
            "phase": PHASE,
            "snapshot_identity": snapshot.identity_digest,
            "sources_sha256": self.document["sources_sha256"],
            "R": 3,
        }
        self.plan_hash = digest(self.plan)
        self.equity_sessions = pd.DatetimeIndex(
            B3Calendar().sessions_between(
                pd.Timestamp(PHASE_WINDOWS[PHASE].start).date(),
                pd.Timestamp(PHASE_WINDOWS[PHASE].end).date(),
            )
        )
        # ponytail: store setup mirrors EvaluationBatch.__init__ instead of
        # refactoring it, so the qualified inventory bytes stay identical.
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
            for participant in (*SLOTS, *(s.kind for s in BENCHMARK_SPECS)):
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
        try:
            self.bank = CallBank(self.root / "provider.sqlite", manifest_sha256, PHASE)
        except Exception:
            self.db.close()
            raise
        self.transport_factory, self._transports = None, []

    def _require_inputs(self):
        if (
            self.snapshot.snapshot_id != RESERVED_SNAPSHOT
            or self.snapshot.identity_digest
            != self.document["protocol"]["snapshot"]["identity"]
        ):
            raise ValueError("frozen scientific snapshot differs")
        if self.root != (ROOT / OUTPUT).resolve():
            raise ValueError("OA-1 writes only to its own provisional output root")
        head = read(self.authorization_path).get("git_head", "")
        if not head or git("merge-base", "--is-ancestor", head, "HEAD").returncode:
            raise ValueError("OA-1 authorization was not recorded on this history")

    def _check_authority(self):
        # Runs before every transport, like the production gate it replaces.
        if (
            sha_file(self.manifest_path) != self.manifest_sha
            or sha_file(self.authorization_path) != self.authorization_sha
        ):
            raise JournalIntegrityError("manifest or OA-1 authorization changed")
        check_authorization(self.document, self.manifest_sha, self.authorization_path)

    def _context(self, slot):
        return RunContext(PHASE, f"{AMENDMENT_ID}:{self.manifest_sha}:{slot}")

    def _path(self, slot):
        return self.root / "runs" / f"H2-V6-OA1-{PHASE}-{slot}-{self.plan_hash[:12]}"

    def summary(self):
        return {
            **super().summary(),
            "mode": MODE,
            "amendment_id": AMENDMENT_ID,
            "academic_ratification": False,
            "final_test_authorized": False,
        }


def estimate(document):
    window = document["protocol"]["windows"][PHASE]
    sessions = sum(s <= window["evaluation"]["decision_end"] for s in window["sessions"])
    expected = round(sessions * CALLS_PER_SESSION["expected"] * 3)
    ceiling = sessions * CALLS_PER_SESSION["max"] * 3
    cost = (
        expected * TOKENS["input"] * PRICE_PER_M["input"]
        + expected * TOKENS["output"] * PRICE_PER_M["output"]
    ) / 1e6
    worst = (
        ceiling
        * MAX_ATTEMPTS
        * (
            TOKENS["input"] * PRICE_PER_M["input"]
            + MAX_OUTPUT_TOKENS * PRICE_PER_M["output"]
        )
        / 1e6
    )
    return {
        "decision_sessions_per_run": sessions,
        "runs": 3,
        "logical_calls_expected": expected,
        "logical_calls_max": ceiling,
        "http_attempts_max": ceiling * MAX_ATTEMPTS,
        "tokens_expected": {
            "input": expected * TOKENS["input"],
            "output_incl_thoughts": expected * TOKENS["output"],
        },
        "usd_expected": round(cost, 2),
        "usd_prudent_budget": round(cost * 2.5, 2),
        "usd_theoretical_ceiling": round(worst, 2),
        "price_per_million_tokens_usd": PRICE_PER_M,
        # ~3.5 s/sessão: 5 técnicos em paralelo (~2.9 s) + Risk/Portfolio ocasionais.
        "wall_time_expected_minutes": round(sessions * 3 * 3.5 / 60),
    }


def load_key():
    """Só GEMINI_API_KEY, só neste processo, nunca impressa."""
    if not os.environ.get("GEMINI_API_KEY"):
        from dotenv import dotenv_values

        value = dotenv_values(ROOT / ".env").get("GEMINI_API_KEY")
        if value:
            os.environ["GEMINI_API_KEY"] = value
    return bool(os.environ.get("GEMINI_API_KEY"))


def output_state():
    root = ROOT / OUTPUT
    if not (root / "evaluation.sqlite").exists():
        return "NOT_STARTED"
    if (root / "execution.lock").exists():
        return "LOCKED - running or abandoned; investigate before anything else"
    uri = (root / "evaluation.sqlite").as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        return dict(db.execute("SELECT slot,state FROM slots").fetchall())


def preflight():
    sha = candidate_sha()
    document = verify_manifest(
        CANDIDATE, sha
    )  # hashes, ambiente, preservação, árvore limpa
    report = {
        "manifest": {
            "path": str(CANDIDATE.relative_to(ROOT)),
            "sha256": sha,
            "state": document["state"],
            "academic_approvals": document["approvals"],
            "verified": "sources, documents, CAL-B4 bindings, environment, clean tree",
        },
        "git_head": git("rev-parse", "HEAD").stdout.strip(),
        "amendment": {"id": AMENDMENT_ID, "sha256": sha_file(AMENDMENT)},
        "runner_sha256": sha_file(__file__),
        "model": {
            k: document["protocol"]["participant_spec"]["params"][k]
            for k in (
                "provider",
                "model",
                "temperature",
                "max_output_tokens",
                "thinking_level",
                "analyst_count",
                "retry_attempts",
                "retry_base_delay",
            )
        },
        "phase": PHASE,
        "window": document["protocol"]["windows"][PHASE]["evaluation"],
        "run_identities": document["protocol"]["run_identities"][PHASE],
        "output": OUTPUT,
        "output_state": output_state(),
        "snapshot_present": (ROOT / "data/snapshots" / RESERVED_SNAPSHOT).is_dir(),
        "gemini_api_key_present": load_key(),
        "estimate": estimate(document),
        "final_test": "BLOCKED - not reachable through OA-1",
    }
    try:
        auth = check_authorization(document, sha, AUTHORIZATION)
        report["authorization"] = {
            "state": "VALID",
            "signatory": auth["signatory"],
            "recorded_at": auth["recorded_at"],
            "sha256": sha_file(AUTHORIZATION),
        }
        report["command"] = (
            ".venv\\Scripts\\python.exe -B scripts/run_h2_v6_provisional.py run "
            f"--confirm {sha_file(AUTHORIZATION)[:12]}"
        )
    except FileNotFoundError:
        report["authorization"] = {"state": "ABSENT - awaiting author"}
        report["command"] = (
            ".venv\\Scripts\\python.exe -B scripts/run_h2_v6_provisional.py authorize "
            f'--signatory "<nome completo>" --confirm "AUTORIZO OA-1 VALIDATION {sha_file(AMENDMENT)[:12]}"'
        )
    except ValueError as exc:
        report["authorization"] = {"state": "INVALID", "reason": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    ready = (
        report["authorization"]["state"] == "VALID"
        and report["snapshot_present"]
        and report["gemini_api_key_present"]
        and report["output_state"] == "NOT_STARTED"
    )
    print("\nPREFLIGHT:", "READY" if ready else "NOT READY - no execution possible")
    return 0 if ready else 2


def open_batch():
    sha = candidate_sha()
    check_authorization(verify_manifest(CANDIDATE, sha), sha, AUTHORIZATION)
    snapshot = load_dataset_snapshot(ROOT / "data/snapshots" / RESERVED_SNAPSHOT)
    return ProvisionalValidationBatch(snapshot, sha, AUTHORIZATION)


def seal(batch, path=CHECKPOINT):
    """Reverify the sealed phase and write the write-once provisional checkpoint."""
    root = batch.root
    summary = batch.summary()  # recarrega selos, journal == bank, identidade
    if (root / "summary.json").read_bytes() != (canonical_json(summary) + "\n").encode():
        raise ValueError("persisted summary differs from sealed artifacts")
    release = root / "validation_release.json"
    if sha_file(release) != read(root / "validation_release.sha256.json")["sha256"]:
        raise ValueError("validation release hash differs")
    for relative, expected in read(release)["artifacts_sha256"].items():
        if sha_file(root / relative) != expected:
            raise ValueError(f"sealed artifact corrupted: {relative}")
    states = batch.db.execute("SELECT state FROM dispositions").fetchall()
    if len(states) != 24 or any(s[0] == "PENDING" for s in states):
        raise ValueError("cost dispositions incomplete")
    value = {
        "kind": "H2_V6_OA1_VALIDATION_PROVISIONAL_CHECKPOINT",
        "mode": MODE,
        "academic_ratification": False,
        "final_test_authorized": False,
        "manifest_sha256": batch.manifest_sha,
        "authorization_sha256": batch.authorization_sha,
        "amendment_sha256": sha_file(AMENDMENT),
        "runner_sha256": sha_file(__file__),
        "plan_hash": batch.plan_hash,
        "output_relative_path": OUTPUT,
        "files_sha256": {
            name: sha_file(root / name)
            for name in (
                "summary.json",
                "cost_closure.json",
                "validation_release.json",
                "provider.sqlite",
            )
        },
        "artifacts_sha256": read(release)["artifacts_sha256"],
        "statistics": summary["statistics"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_once(path, value)
    return path


def audit():
    batch = open_batch()
    try:
        path = seal(batch)
    finally:
        batch.close()
    print(
        json.dumps({"checkpoint": str(path.relative_to(ROOT)), "sha256": sha_file(path)})
    )
    print("Commit the checkpoint: git add docs/evidence/h2_v6_provisional && git commit")


def complete(batch):
    """Validation R=3, persisted summary, 24 cost dispositions, integrity release."""
    summary = batch.execute()
    _write_once(batch.root / "summary.json", summary)
    batch.cost_sensitivity()
    batch.checkpoint()
    return summary


def run(confirm):
    if not AUTHORIZATION.is_file() or confirm != sha_file(AUTHORIZATION)[:12]:
        raise SystemExit(
            "--confirm must equal the first 12 hex of the authorization SHA256"
        )
    if not load_key():
        raise SystemExit("GEMINI_API_KEY absent; refusing before any reservation")
    batch = open_batch()
    try:
        complete(batch)
    finally:
        batch.close()
    audit()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=("preflight", "authorize", "run", "audit"))
    parser.add_argument("--signatory")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.command == "preflight":
        raise SystemExit(preflight())
    if args.command == "authorize":
        expected = f"AUTORIZO OA-1 VALIDATION {sha_file(AMENDMENT)[:12]}"
        if not args.signatory or args.confirm != expected:
            parser.error(f'authorize requires --signatory and --confirm "{expected}"')
        sha = candidate_sha()
        path = write_authorization(verify_manifest(CANDIDATE, sha), sha, args.signatory)
        print(f"Recorded {path.relative_to(ROOT)} sha256={sha_file(path)}")
        print("Next: git add it, commit, then run preflight again.")
        return
    if args.command == "run":
        run(args.confirm)
        return
    audit()


if __name__ == "__main__":
    main()
