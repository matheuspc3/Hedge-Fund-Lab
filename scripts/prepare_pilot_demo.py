"""Explicit offline preparation of the home demo; never invoked by HTTP."""

import argparse
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "dashboard")]

import pilot_api as api  # noqa: E402


def prepare(path):
    path = Path(path).resolve()
    if path.exists():
        api.read_demo(path)
        return path  # Valid evidence is reused, never overwritten silently.
    import qualify_pilot_paper as qualifier

    with ExitStack() as stack:
        qualifier.offline(stack)
        with tempfile.TemporaryDirectory(prefix="hfl-paper-home-") as temporary:
            root = Path(temporary)
            projection = qualifier.run(root)
            store = qualifier.pilot.Store(root / "ledger.sqlite3")
            artifact = api.b.sealed(
                {
                    "schema_version": 1,
                    "identity": api.IDENTITY,
                    "classification": "SYNTHETIC_TEST",
                    "official_activation": False,
                    "projection": projection,
                    "ledgers": [store.export(pid) for pid in qualifier.WALLETS],
                }
            )
            api.verified(
                api.pilot.ledger.canonical(artifact).encode(),
                api.b.digest(api.pilot.fingerprints()),
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(api.pilot.ledger.canonical(artifact) + "\n")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=api.demo_path())
    args = parser.parse_args()
    print("SYNTHETIC_TEST · exportação verificada:", prepare(args.output))
