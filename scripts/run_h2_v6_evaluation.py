"""Candidate preparation/preflight and guarded future evaluation entrypoint.

There is no synthetic authorization generator and no candidate-to-live switch.
Candidates cannot execute this run command, access prices or create clients.
"""

# ruff: noqa: E402 -- standalone entrypoint establishes repository imports.
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments.h2_evaluation_manifest import (
    BASE_COMMIT,
    CANDIDATE,
    PATCH_PATHS,
    git,
    make_candidate,
    require_authorization,
    sha_file,
    verify_manifest,
)
from src.experiments.h2_evaluation_production import EvaluationBatch
from src.pipeline.snapshot import load_dataset_snapshot


def prepare_candidate():
    directory = CANDIDATE.parent
    directory.mkdir(parents=True, exist_ok=True)
    patch = git("diff", "--no-ext-diff", "--binary", BASE_COMMIT, "--", *PATCH_PATHS)
    (directory / "post_cal_b4_infrastructure.diff").write_bytes(patch)
    value = make_candidate()
    if (
        CANDIDATE.exists()
        and json.loads(CANDIDATE.read_text(encoding="utf-8"))["state"] != value["state"]
    ):
        raise ValueError("never overwrite an approved/frozen manifest")
    CANDIDATE.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    CANDIDATE.with_suffix(".sha256").write_text(
        sha_file(CANDIDATE) + "\n", encoding="ascii", newline="\n"
    )
    return {
        "state": value["state"],
        "manifest_sha256": sha_file(CANDIDATE),
        "infrastructure_diff_sha256": hashlib.sha256(patch).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("candidate", "preflight", "run"))
    parser.add_argument("--manifest", type=Path, default=CANDIDATE)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--phase", choices=("VALIDATION", "FINAL_TEST"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--validation-checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "candidate":
        print(json.dumps(prepare_candidate(), ensure_ascii=False))
        return
    if not args.manifest_sha256 or not args.phase or not args.authorization:
        parser.error(
            "explicit manifest digest, phase and phase authorization are required"
        )
    document = verify_manifest(args.manifest, args.manifest_sha256)
    require_authorization(
        document, args.manifest_sha256, args.phase, args.authorization, synthetic=False
    )
    # Only an independently approved/frozen manifest and real phase consent can
    # reach snapshot loading. No such record is produced by candidate preparation.
    if args.command == "preflight":
        print("Phase authorization and frozen identity verified; no execution")
        return
    if args.output is None:
        parser.error("explicit output directory required")
    snapshot = load_dataset_snapshot(
        ROOT / "data/snapshots" / document["protocol"]["snapshot"]["id"]
    )
    batch = EvaluationBatch(
        args.output,
        snapshot,
        args.phase,
        manifest=args.manifest,
        manifest_sha256=args.manifest_sha256,
        authorization=args.authorization,
        validation_checkpoint=args.validation_checkpoint,
    )
    try:
        result = batch.execute()
        result["costs"] = batch.cost_sensitivity()
        if args.phase == "VALIDATION":
            result["release_checkpoint"] = str(batch.checkpoint())
        print(json.dumps(result, ensure_ascii=False))
    finally:
        batch.close()


if __name__ == "__main__":
    main()
