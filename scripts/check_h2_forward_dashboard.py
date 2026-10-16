"""Verify bytes captured before dashboard work; never rewrites the baseline."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs/evidence/h2_forward_dashboard/protected_before.json"


def check():
    files = json.loads(BASELINE.read_text(encoding="utf-8"))
    changed = []
    for name, expected in files.items():
        path = ROOT / name
        digest = hashlib.sha256()
        if path.is_file():
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        if not path.is_file() or digest.hexdigest() != expected:
            changed.append(name)
    assert not changed, f"Protected bytes changed: {changed}"
    print(
        f"PROTECTED HASHES OK: {len(files)} files, including original 09/10 forward records"
    )


if __name__ == "__main__":
    check()
