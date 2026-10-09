"""Candidate identity and post-CAL-B4 preservation; never creates human consent."""

import hashlib
import importlib.metadata
import json
import platform
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd

from src.backtesting.b3_calendar import B3Calendar
from src.experiments.h2_evaluation import (
    BASE_COSTS,
    BENCHMARK_SPECS,
    CAPITAL,
    EVALUATION_WINDOWS,
    EXECUTION,
    METRICS,
    PARTICIPANT_SHA256,
    PHASE_WINDOWS,
    RESERVED_SNAPSHOT,
    digest,
)

ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "812f908"
HISTORICAL_COMMIT = "9d8636a4581a51229dd911d0863ef32551e7adb7"
CAL_FREEZE = "docs/evidence/cal_b4/protocol_freeze_v1.json"
CAL_RUN = "docs/evidence/cal_b4/run_20261008T221200Z"
PATCH_PATHS = ("src/experiments/participants.py", "src/experiments/runner.py")
CANDIDATE = ROOT / "docs/evidence/h2_v6_evaluation/system_freeze_candidate.json"
DOCUMENTS = (
    "docs/H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md",
    "docs/H2_V6_EVALUATION_AMENDMENT_DELIBERATION.md",
    "docs/H2_V6_EVALUATION_OFFLINE_QUALIFICATION.md",
    "docs/H2_V6_FREEZE_READINESS_REVIEW.md",
    "docs/H2_V6_ACADEMIC_APPROVAL_SUMMARY.md",
    "docs/H2_V6_ACADEMIC_APPROVAL_SUMMARY.pdf",
    "docs/evidence/h2_v6_evaluation/qualification_offline.json",
)
CALENDAR = "docs/evidence/calendar/b3_official_sessions_2016-01-04_2026-08-31.txt"


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def repository_path(relative):
    path = (ROOT / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(ROOT):
        raise ValueError("manifest paths must stay inside the repository")
    return path


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def historical_bytes(path, expected):
    data = git("show", f"{HISTORICAL_COMMIT}:{path}")
    if hashlib.sha256(data).hexdigest() != expected:
        # Git stored LF while the frozen runner bytes used CRLF. Only accept
        # this representation if it reproduces the exact historical digest.
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"historical source cannot be reproduced: {path}")
    return data


def verify_preservation(permitted=None):
    historical_bytes(CAL_FREEZE, sha_file(ROOT / CAL_FREEZE))
    frozen = read(ROOT / CAL_FREEZE)
    changes = {}
    for path, expected in frozen["source_and_scientific_artifact_sha256"].items():
        observed = sha_file(repository_path(path))
        if observed == expected:
            continue
        if path not in PATCH_PATHS:
            raise ValueError(f"historical source/artifact changed: {path}")
        historical_bytes(path, expected)
        if permitted is not None and permitted.get(path) != observed:
            raise ValueError(f"unapproved infrastructure drift: {path}")
        changes[path] = {"before_sha256": expected, "after_sha256": observed}
    if permitted is not None and set(permitted) != set(changes):
        raise ValueError("permitted infrastructure patch inventory differs")
    if digest(frozen["participant_spec"]) != PARTICIPANT_SHA256:
        raise ValueError("H2 v6 treatment identity changed")
    if (
        sha_file(ROOT / CAL_RUN / "review/PRIMARY_AUTHOR.json")
        != ("33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733")
        or read(ROOT / CAL_RUN / "status.json")["status"]
        != "CAL_B4_PASS — SANITY CHECK ONLY"
    ):
        raise ValueError("CAL-B4 review/status differs")
    return {
        "historical_files": len(frozen["source_and_scientific_artifact_sha256"]),
        "unchanged_historical_files": len(frozen["source_and_scientific_artifact_sha256"])
        - len(changes),
        "permitted_infrastructure_patch": changes,
    }


def environment():
    from src.config import settings

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "timezone": "America/Sao_Paulo",
        "sqlite_version": sqlite3.sqlite_version,
        "sqlite_synchronous": "FULL",
        "llm_timeout": settings.llm_timeout,
        "packages": dict(
            sorted(
                (d.metadata["Name"].lower(), d.version)
                for d in importlib.metadata.distributions()
                if d.metadata["Name"]
            )
        ),
    }


def protocol():
    frozen = read(ROOT / CAL_FREEZE)
    sessions = {
        phase: [
            str(d)
            for d in B3Calendar().sessions_between(
                pd.Timestamp(w.start).date(), pd.Timestamp(w.end).date()
            )
        ]
        for phase, w in PHASE_WINDOWS.items()
    }
    return {
        "treatment_version": 6,
        "participant_spec": frozen["participant_spec"],
        "participant_sha256": PARTICIPANT_SHA256,
        "initial_capital": CAPITAL,
        "cash_return": 0,
        "long_only": True,
        "execution": EXECUTION.to_dict(),
        "costs": BASE_COSTS.to_dict(),
        "cost_grid": [0, 5, 10, 20],
        "metrics": METRICS.to_dict(),
        "sharpe_version": 1,
        "sharpe_ddof": 1,
        "sharpe_min_std": 1e-15,
        "turnover": "executed_absolute_notional/initial_capital",
        "sortino_degenerate_economic_value": None,
        "hypotheses": {
            "H0_2": "delta <= 0",
            "HA_2": "delta > 0",
            "estimand": "mean(three individual LLM Sharpes)-B&H Sharpe",
            "scope": "conditional on observed LLM trajectories",
        },
        "test": {
            "candidate": "A",
            "B": 5000,
            "alpha": 0.05,
            "rng": "PCG64",
            "seed": 20261008,
            "mean_block": 10,
            "rank": 4751,
            "ties": ">=",
            "p_correction": "+1",
            "degenerate": "INCONCLUSIVE_DEGENERATE; p/lower=null",
            "hash_bytes": {"indices": "<i8", "roots": "<f8"},
        },
        "R": 3,
        "aggregation": "arithmetic mean of individual Sharpes",
        "benchmarks": [
            {"spec": s.to_dict(), "sha256": digest(s.to_dict())} for s in BENCHMARK_SPECS
        ],
        "windows": {
            p: {
                "phase_window": vars(PHASE_WINDOWS[p]),
                "evaluation": EVALUATION_WINDOWS[p].to_dict(),
                "sessions": sessions[p],
                "settlement": sessions[p][-1],
            }
            for p in PHASE_WINDOWS
        },
        "run_identities": {
            p: [f"H2-V6:{p}:L{j:02d}" for j in range(1, 4)] for p in PHASE_WINDOWS
        },
        "production_output_roots": {
            p: f"data/runs/h2_v6_evaluation/{p}" for p in PHASE_WINDOWS
        },
        "release": "complete sealed Validation R3 + all benchmarks + identical identity; no performance gate",
        "cost_policy": "exact replay only; baseline reused; no subset; operational errors fail closed",
        "cost_closure": "all 24 dispositions per phase; separate from primary release",
        "journal": "FULL SQLite reservation before transport; raw bytes and record before delivery; replay-only recovery",
        "recovery": "uncertain reservation fails closed; no replacement votes/runs; no remote exactly-once claim",
        "snapshot": {
            "id": RESERVED_SNAPSHOT,
            "identity": "b4cf39fc761f251d2dd18e787008345aaf02bd9e19f913390c510338b84ee7d4",
            "ticker": "PETR4.SA",
            "csv_sha256": "7b6a0018191028ecea2ee66785c27f771a721aa4a96c4953ca87ac6d688c3ffa",
        },
    }


def source_paths():
    sources = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py"))
    sources += [
        "scripts/run_h2_v6_evaluation.py",
        "scripts/qualify_h2_v6_production.py",
        "scripts/qualify_h2_v6_evaluation.py",
        "scripts/check_h2_v6_evaluation_proposal.py",
        "pyproject.toml",
        "poetry.lock",
        CALENDAR,
    ]
    return sources


def historical_binding_paths():
    bindings = [
        CAL_FREEZE,
        "docs/evidence/cal_b4/guards_freeze.json",
        "docs/evidence/cal_b4/PROTOCOL_FREEZE_V1.md",
    ]
    bindings += [
        p.relative_to(ROOT).as_posix() for p in (ROOT / CAL_RUN).rglob("*") if p.is_file()
    ]
    return sorted(bindings)


def make_candidate():
    preservation = verify_preservation()
    sources, bindings = source_paths(), historical_binding_paths()
    return {
        "schema_version": 1,
        "kind": "H2_V6_EVALUATION_SYSTEM_FREEZE_CANDIDATE",
        "state": "CANDIDATE / NOT APPROVED / NOT FROZEN",
        "live_authorized": False,
        "approvals": {"author": None, "coauthor": None, "advisor": None},
        "freeze_record": None,
        "phase_authorizations": {p: None for p in PHASE_WINDOWS},
        "baseline_commit": HISTORICAL_COMMIT,
        "engineering_base_commit": BASE_COMMIT,
        "documents_sha256": {p: sha_file(ROOT / p) for p in DOCUMENTS},
        "sources_sha256": {p: sha_file(ROOT / p) for p in sources},
        "historical_bindings_sha256": {p: sha_file(ROOT / p) for p in sorted(bindings)},
        "preservation": preservation,
        "infrastructure_diff": {
            "path": "docs/evidence/h2_v6_evaluation/post_cal_b4_infrastructure.diff",
            "sha256": sha_file(
                ROOT / "docs/evidence/h2_v6_evaluation/post_cal_b4_infrastructure.diff"
            ),
        },
        "environment": environment(),
        "protocol": protocol(),
        "qualification_mode": "generated synthetic fixtures + fake native transport only",
        "self_verification": "external SHA256 sidecar; never embeds its own digest",
    }


def verify_manifest(path, expected_sha256, *, clean=True):
    if sha_file(path) != expected_sha256:
        raise ValueError("evaluation manifest digest differs")
    document = read(path)
    candidate = document.get("state") == "CANDIDATE / NOT APPROVED / NOT FROZEN"
    if (
        document.get("kind")
        != (
            "H2_V6_EVALUATION_SYSTEM_FREEZE_CANDIDATE"
            if candidate
            else "H2_V6_EVALUATION_SYSTEM_FREEZE_MANIFEST"
        )
        or document.get("state")
        not in ("CANDIDATE / NOT APPROVED / NOT FROZEN", "APPROVED / FROZEN")
        or document.get("baseline_commit") != HISTORICAL_COMMIT
        or document.get("engineering_base_commit") != BASE_COMMIT
    ):
        raise ValueError("manifest state/kind/baseline differs")
    if document.get("schema_version") != 1 or document.get("protocol") != protocol():
        raise ValueError("evaluation protocol/treatment drift")
    for group, paths in (
        ("documents_sha256", DOCUMENTS),
        ("sources_sha256", source_paths()),
        ("historical_bindings_sha256", historical_binding_paths()),
    ):
        if set(document.get(group, {})) != set(paths):
            raise ValueError("manifest hash inventory incomplete or unexpected")
    for group in ("documents_sha256", "sources_sha256", "historical_bindings_sha256"):
        if not document.get(group):
            raise ValueError("missing manifest hash inventory")
        for relative, expected in document[group].items():
            if sha_file(repository_path(relative)) != expected:
                raise ValueError(f"manifest source/artifact drift: {relative}")
    if document["environment"] != environment():
        raise ValueError("evaluation environment differs")
    permitted = {
        p: d["after_sha256"]
        for p, d in document["preservation"]["permitted_infrastructure_patch"].items()
    }
    if verify_preservation(permitted) != document["preservation"]:
        raise ValueError("historical preservation evidence differs")
    diff = document["infrastructure_diff"]
    if sha_file(repository_path(diff["path"])) != diff["sha256"]:
        raise ValueError("infrastructure diff changed")
    if repository_path(diff["path"]).read_bytes() != git(
        "diff", "--no-ext-diff", "--binary", BASE_COMMIT, "--", *PATCH_PATHS
    ):
        raise ValueError("infrastructure diff does not describe the current patch")
    if clean and git("status", "--porcelain").strip():
        raise ValueError("evaluation requires a clean repository")
    return document


def require_authorization(document, manifest_sha, phase, authorization, *, synthetic):
    if phase not in PHASE_WINDOWS:
        raise ValueError("explicit Validation or Final phase required")
    auth = read(authorization)
    required = {
        "kind": "H2_V6_SYNTHETIC_PHASE_AUTHORIZATION"
        if synthetic
        else "H2_V6_EVALUATION_PHASE_AUTHORIZATION",
        "phase": phase,
        "manifest_sha256": manifest_sha,
        "participant_sha256": PARTICIPANT_SHA256,
        "R": 3,
        "run_identities": document["protocol"]["run_identities"][phase],
        "window": document["protocol"]["windows"][phase],
        "host": "generativelanguage.googleapis.com",
        "authorized": True,
        "synthetic_only": synthetic,
    }
    if any(auth.get(k) != v for k, v in required.items()):
        raise ValueError(
            "specific phase authorization differs; development/CAL-B4 never suffice"
        )
    if synthetic:
        if document["state"] != "CANDIDATE / NOT APPROVED / NOT FROZEN" or (
            document["live_authorized"]
            or document["freeze_record"] is not None
            or any(v is not None for v in document["approvals"].values())
        ):
            raise ValueError(
                "synthetic qualification cannot manufacture approvals or freeze"
            )
    else:
        if document["state"] != "APPROVED / FROZEN" or not document["live_authorized"]:
            raise ValueError(
                "candidate is NOT APPROVED/NOT FROZEN; real execution forbidden"
            )
        for role in ("author", "coauthor", "advisor"):
            ref = document["approvals"].get(role)
            if not ref or sha_file(repository_path(ref["path"])) != ref["sha256"]:
                raise ValueError("formal human approval missing or changed")
            approval = read(repository_path(ref["path"]))
            if (
                approval.get("kind") != "H2_V6_EVALUATION_AMENDMENT_MANIFESTATION"
                or approval.get("role") != role
                or approval.get("manifestation")
                != ("ACKNOWLEDGE_AND_AGREE" if role == "advisor" else "APPROVE")
                or approval.get("proposal_sha256")
                != document["documents_sha256"][DOCUMENTS[0]]
                or approval.get("deliberation_sha256")
                != document["documents_sha256"][DOCUMENTS[1]]
                or not approval.get("signature_reference")
                or not approval.get("signatory")
                or not approval.get("recorded_by_human")
            ):
                raise ValueError("human manifestation does not cover this amendment")
        ref = document.get("freeze_record")
        if not ref or sha_file(repository_path(ref["path"])) != ref["sha256"]:
            raise ValueError("explicit System Freeze record missing or changed")
        freeze = read(repository_path(ref["path"]))
        if (
            freeze.get("kind") != "H2_V6_SYSTEM_FREEZE_RECORD"
            or freeze.get("state") != "SYSTEM_FREEZE_COMPLETE"
            or freeze.get("protocol_sha256") != digest(document["protocol"])
            or freeze.get("sources_sha256") != digest(document["sources_sha256"])
            or freeze.get("approvals_sha256")
            != {
                r: document["approvals"][r]["sha256"]
                for r in ("author", "coauthor", "advisor")
            }
            or not freeze.get("authorized_by_human")
        ):
            raise ValueError("freeze record does not cover this identity")
        if not auth.get("accepts_normal_api_charges") or not auth.get(
            "scientific_payloads_only"
        ):
            raise ValueError("phase egress consent incomplete")
        if (
            auth.get("output_relative_path")
            != document["protocol"]["production_output_roots"][phase]
        ):
            raise ValueError(
                "phase authorization must bind the unique scientific output root"
            )
    return auth
