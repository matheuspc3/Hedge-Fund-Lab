"""Preservation check under the data lifecycle policy; historical baselines are never edited.

Every file pinned by ``docs/evidence/*/preservation_baseline.json`` that differs now is
classified by ``POLICY``:

  OPERATIONAL  authorized mutable state (cache, last-batch pointer, job, selection)
  LEDGER       evolves only through its original runner; verify with that runner
  VIOLATION    immutable evidence (inputs, manifests, decisions, journals, claims,
               authorizations, sealed demos, scientific records) changed or missing

Usage (PowerShell, project root):
  scripts/check_preservation.py                 read-only; exit 2 on any VIOLATION
  scripts/check_preservation.py --snapshot F    WRITES F: hashes before an authorized operation
  scripts/check_preservation.py --since F       read-only before/after against snapshot F
"""

import argparse
import fnmatch
import glob
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: Areas covered by --snapshot: the original Radar root, the prospective ledgers, the
#: run registry and every registered run root (V7.3), read from the registry if valid.
SNAPSHOT_AREAS = (
    "data/radar/hfl_multiasset_v1",
    "data/forward",
    "data/radar/registry.json",
)
CACHE = "Cache de download do COTAHIST do ano corrente; cada input congelado registra o SHA que usou e nunca é relido do cache."
POLICY = (
    (
        "OPERATIONAL",
        "data/radar/*/last_prepare.json",
        "Relatório da última chamada de prepare; não é índice nem autoridade sobre inputs.",
    ),
    ("OPERATIONAL", "data/radar/*/job.json", "Estado do job da API Radar."),
    (
        "OPERATIONAL",
        "data/radar/registry.json",
        "Índice operacional das execuções Radar; não é autoridade sobre os registros selados.",
    ),
    ("OPERATIONAL", "data/radar/*/universe.json", "Seleção de ativos do operador."),
    ("OPERATIONAL", "data/radar/*/cotahist/COTAHIST_A*.ZIP", CACHE),
    ("OPERATIONAL", "data/forward/h2_v6_paper/cotahist/COTAHIST_A*.ZIP", CACHE),
    (
        "OPERATIONAL",
        "data/forward/h2_v6_dashboard/*.json",
        "Estado de jobs e resumo de testes da UI.",
    ),
    (
        "LEDGER",
        "data/forward/h2_v6_paper/state.json",
        "Ledger H2 + Buy & Hold; conferir com scripts/check_platform.py (integridade H2).",
    ),
    (
        "LEDGER",
        "data/forward/h2_v6_supervised/state.json",
        "Ledger supervisionado; conferir com scripts/run_h2_v6_supervised.py verify.",
    ),
    (
        "LEDGER",
        "data/forward/h2_v6_benchmarks/*/state.json",
        "Ledger determinístico; evolui só pelo runner de benchmarks.",
    ),
)


def classify(path):
    for category, pattern, reason in POLICY:
        if fnmatch.fnmatchcase(path, pattern):
            return category, reason
    return "VIOLATION", "Evidência imutável."


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def baselines(root=ROOT):
    """Historical baselines vs. current files; only reads."""
    report = {"baselines": {}, "changes": {}}
    for name in sorted(
        glob.glob(str(root / "docs/evidence/*/preservation_baseline.json"))
    ):
        pinned = json.loads(Path(name).read_text(encoding="utf-8"))
        changed = 0
        for path, expected in pinned.items():
            current = sha(root / path)
            if current == expected:
                continue
            changed += 1
            category, reason = classify(path)
            entry = report["changes"].setdefault(
                path,
                {
                    "category": category,
                    "reason": reason,
                    "current": current,
                    "before": {},
                },
            )
            entry["before"][Path(name).parent.name] = expected
        report["baselines"][Path(name).parent.name] = {
            "files": len(pinned),
            "changed": changed,
        }
    report["violations"] = sorted(
        p for p, c in report["changes"].items() if c["category"] == "VIOLATION"
    )
    return report


def areas(root=ROOT):
    try:
        runs = json.loads((root / "data/radar/registry.json").read_text(encoding="utf-8"))
        extra = [e["path"] for e in runs["runs"].values()]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        extra = []  # no registry: the fixed areas still cover the original root
    return list(dict.fromkeys([*SNAPSHOT_AREAS, *extra]))


def snapshot(root=ROOT):
    files, covered = {}, areas(root)
    for area in covered:
        target = root / area
        for path in sorted(target.rglob("*")) if target.is_dir() else [target]:
            if path.is_file() and path.suffix != ".lock":
                files[path.relative_to(root).as_posix()] = sha(path)
    return {"areas": covered, "files": files}


def since(before, root=ROOT):
    """Before/after of an operation: new files are allowed, existing immutables are not."""
    after = snapshot(root)["files"]
    changes = []
    for path in sorted(set(before["files"]) | set(after)):
        old, new = before["files"].get(path), after.get(path)
        if old == new:
            continue
        category, reason = classify(path)
        covered = any(
            path == area or path.startswith(area.rstrip("/") + "/")
            for area in before.get("areas", SNAPSHOT_AREAS)
        )
        if old is None and category == "VIOLATION":
            # An area that joined the snapshot later (e.g. a newly registered run) may
            # hold files older than the operation: their history is in the baselines.
            category, reason = (
                ("NEW", "Registro novo; passa a ser imutável.")
                if covered
                else (
                    "UNCOVERED_BEFORE",
                    "Área fora do snapshot anterior; conferir pelos baselines.",
                )
            )
        changes.append(
            {
                "path": path,
                "category": category,
                "reason": reason,
                "before": old,
                "after": new,
            }
        )
    return {
        "changes": changes,
        "violations": [c["path"] for c in changes if c["category"] == "VIOLATION"],
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--snapshot", type=Path)
    group.add_argument("--since", type=Path)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.snapshot:
        if args.snapshot.exists():
            raise SystemExit("snapshot exists; choose a new path (never overwritten)")
        args.snapshot.write_text(json.dumps(snapshot(), indent=1), encoding="utf-8")
        print(f"snapshot: {args.snapshot}")
        return
    report = (
        since(json.loads(args.since.read_text(encoding="utf-8")))
        if args.since
        else baselines()
    )
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if report["violations"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
