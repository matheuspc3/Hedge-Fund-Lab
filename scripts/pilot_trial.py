"""PAPER-03: explicit local CLI for a durable, exclusively synthetic rehearsal."""

import argparse
import os
import sqlite3
import sys
import tempfile
import uuid
from contextlib import ExitStack, closing, contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "dashboard")]

import pilot_api as api  # noqa: E402
import qualify_pilot_paper as q  # noqa: E402

p, b = q.pilot, q.b
BASE = ROOT / "data/platform/paper-synthetic"
IDENTITY = "HFL-PILOT-DURABLE-SYNTHETIC-V1"
EXTRA_SCHEMA = """
CREATE TABLE trial (body TEXT NOT NULL);
CREATE TABLE commands (
 command_id TEXT PRIMARY KEY, session TEXT NOT NULL UNIQUE, body TEXT NOT NULL
);
"""


def contained(path):
    """Only this dedicated area, including after resolution; no reparse points."""
    path = Path(path).absolute()
    resolved = path.resolve()
    if (
        not path.is_relative_to(BASE)
        or not resolved.is_relative_to(BASE)
        or resolved == BASE
        or any(part.is_symlink() or part.is_junction() for part in (path, *path.parents))
    ):
        raise ValueError("dedicated_synthetic_root_required")
    return resolved


def fingerprints():
    return {
        **p.fingerprints(),
        **{
            name: b.sha_file(ROOT / name)
            for name in (
                "scripts/pilot_trial.py",
                "scripts/qualify_pilot_paper.py",
                "tests/test_pilot_market_data.py",
            )
        },
    }


def connection(root, *, write=False):
    path = contained(contained(root) / "ledger.sqlite3")
    for suffix in ("-journal", "-wal", "-shm"):
        contained(path.with_name(path.name + suffix))
    conn = sqlite3.connect(
        path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True, timeout=30
    )
    if write:
        conn.execute("PRAGMA synchronous=FULL")
    return conn


class BorrowedConnection:
    """Let the original Store operate inside the caller's single transaction."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, *args):
        if sql not in ("BEGIN", "BEGIN IMMEDIATE"):
            return self.conn.execute(sql, *args)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass  # The enclosing session alone commits or rolls back.

    def close(self):
        pass  # The enclosing session owns the connection.


class Store(p.Store):
    def __init__(self, conn):
        self.conn = conn

    def connect(self, *, write=False):
        if write and not self.conn.in_transaction:
            raise ValueError("outer_transaction_required")
        return BorrowedConnection(self.conn)


def heads(ledgers):
    return {
        pid: {k: export["checkpoint"][k] for k in ("sequence", "head_sha256")}
        for pid, export in zip(q.WALLETS, ledgers, strict=True)
    }


def snapshot(conn):
    """Verify identity, physical schema, all commands/events and reconciliation."""
    expected = sqlite3.connect(":memory:")
    try:
        expected.executescript(p.ledger.SCHEMA + EXTRA_SCHEMA)
        schema_sql = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name"
        if (
            conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
            or conn.execute("PRAGMA user_version").fetchone() != (1,)
            or conn.execute(schema_sql).fetchall()
            != expected.execute(schema_sql).fetchall()
        ):
            raise ValueError("database_integrity_or_schema_failed")
    finally:
        expected.close()
    rows = conn.execute("SELECT body FROM trial").fetchall()
    if len(rows) != 1:
        raise ValueError("trial_identity_missing")
    meta = b.check_seal(q.data.load_json(rows[0][0]))
    if (
        meta["identity"] != IDENTITY
        or meta["schema_version"] != 1
        or type(meta["schema_version"]) is not int
        or meta["classification"] != "SYNTHETIC_TEST"
        or meta["official_activation"] is not False
        or meta["fingerprints"] != fingerprints()
        or str(uuid.UUID(meta["trial_id"])) != meta["trial_id"]
        or list(meta["bundles"]) != q.SESSIONS[:-1]
        or meta["calendar"]["nature"] != "SYNTHETIC_TEST"
    ):
        raise ValueError("trial_identity_classification_or_fingerprint_mismatch")
    q.data.check_calendar(meta["calendar"])
    for day, bundle in meta["bundles"].items():
        content = q.data.verify_bundle(bundle)
        if (
            content["source"]["nature"] != "SYNTHETIC_TEST"
            or content["selection"]["sessions"] != [day]
            or content["calendar"] != meta["calendar"]
            or set(content["selection"]["tickers"]) != set(q.data.UNIVERSE)
        ):
            raise ValueError("synthetic_complete_daily_inputs_required")
    for table in ("events", "checkpoints"):
        if {
            row[0] for row in conn.execute(f"SELECT DISTINCT portfolio_id FROM {table}")
        } != set(q.WALLETS):
            raise ValueError("wallet_catalog_mismatch")
    store = Store(conn)
    ledgers = [store.export(pid) for pid in q.WALLETS]
    receipts = []
    for cid, day, raw in conn.execute(
        "SELECT command_id,session,body FROM commands ORDER BY session"
    ):
        receipt = b.check_seal(q.data.load_json(raw))
        request = receipt["request"]
        if request != {"trial_id": meta["trial_id"], "command_id": cid, "session": day}:
            raise ValueError("command_index_or_identity_mismatch")
        b.key(cid)
        cutoff = {}
        for pid, export in zip(q.WALLETS, ledgers, strict=True):
            events = [e for e in export["events"] if e["session"] <= day]
            cutoff[pid] = {
                "sequence": len(events),
                "head_sha256": events[-1]["sha256"] if events else None,
            }
        if receipt["heads"] != cutoff:
            raise ValueError("command_event_heads_mismatch")
        receipts.append(receipt)
    days = [r["request"]["session"] for r in receipts]
    if not days or days != q.SESSIONS[: len(days)]:
        raise ValueError("session_order_or_completion_mismatch")
    for pid, export in zip(q.WALLETS, ledgers, strict=True):
        state = export["checkpoint"]["state"]
        if (
            state["parameters"] != p.test_parameters()
            or state["calendar"] != meta["calendar"]
            or [h["session"] for h in state["history"]] != days
            or [r["data_session"] for r in state["proposals"].values()] != days
            or set(state["validations"]) != set(state["proposals"])
            or set(state["authorizations"]) != set(state["proposals"])
            or state["last_economic_at"][:10] != days[-1]
            or p.reconciliation(state)["errors"]
            or not store.verify(pid)["ok"]
        ):
            raise ValueError("session_preconditions_or_reconciliation_failed")
        latest = next(
            r for r in state["proposals"].values() if r["data_session"] == days[-1]
        )
        if bool(latest["operations"]) != bool(state["intent"]) or (
            state["intent"] and state["intent"]["proposal_id"] != latest["record_id"]
        ):
            raise ValueError("session_intent_incomplete")
        for event in export["events"]:
            quote = event["payload"].get("quote")
            if quote and quote["bundle"] != meta["bundles"][quote["session"]]:
                raise ValueError("event_input_mismatch")
    if receipts[-1]["heads"] != heads(ledgers):
        raise ValueError("unconfirmed_event_tail")
    return {
        "metadata": meta,
        "commands": receipts,
        "ledgers": ledgers,
        "projection": p.projection(store, q.WALLETS),
    }


@contextmanager
def opened(root, *, write=False):
    root = contained(root)
    if write and contained(root / "restoration.json").exists():
        raise ValueError("restored_copy_is_inspection_only")
    with closing(connection(root, write=write)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield conn, snapshot(conn)


def receipt(conn, meta, cid, day):
    store = Store(conn)
    value = b.sealed(
        {
            "request": {"trial_id": meta["trial_id"], "command_id": cid, "session": day},
            "heads": heads([store.export(pid) for pid in q.WALLETS]),
        }
    )
    conn.execute(
        "INSERT INTO commands VALUES(?,?,?)", (cid, day, p.ledger.canonical(value))
    )
    return value


def initialize(root):
    root = contained(root)
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    # Exclusive directory creation makes an interrupted init visible, never reusable.
    # Keep DATA-01's original external/TEMP input guards. All normalized inputs
    # needed for continuation/replay are embedded in the database, not reimported.
    with tempfile.TemporaryDirectory(prefix="hfl-paper-trial-inputs-") as inputs:
        calendar, bundles = q.fixture_inputs(Path(inputs))
    meta = b.sealed(
        {
            "identity": IDENTITY,
            "schema_version": 1,
            "classification": "SYNTHETIC_TEST",
            "official_activation": False,
            "trial_id": str(uuid.uuid4()),
            "fingerprints": fingerprints(),
            "calendar": calendar,
            "bundles": bundles,
        }
    )
    path = contained(root / "ledger.sqlite3")
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA synchronous=FULL")
        conn.executescript(p.ledger.SCHEMA + EXTRA_SCHEMA)
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO trial VALUES(?)", (p.ledger.canonical(meta),))
            store = Store(conn)
            for pid, strategy in zip(q.WALLETS, (p.AGENTS, p.REFERENCE), strict=True):
                q.initialize(store, pid, strategy, calendar, bundles[q.SESSIONS[0]])
            q.advance_session(store, bundles, 0)
            receipt(conn, meta, "initialize", q.SESSIONS[0])
            result = snapshot(conn)
    return result


def advance(root, day, cid, *, fault=None):
    b.key(cid)
    with opened(root, write=True) as (conn, before):
        meta = before["metadata"]
        request = {"trial_id": meta["trial_id"], "command_id": cid, "session": day}
        prior = next(
            (r for r in before["commands"] if r["request"]["command_id"] == cid), None
        )
        if prior:
            if prior["request"] != request:
                raise ValueError("idempotency_conflict")
            return prior
        i = len(before["commands"])
        if i >= len(q.SESSIONS) - 1 or q.SESSIONS[i] != day:
            raise ValueError("next_synthetic_session_required")
        q.advance_session(Store(conn), meta["bundles"], i)
        result = receipt(conn, meta, cid, day)
        snapshot(conn)
        if fault:
            fault("before_commit")
    if fault:
        fault("after_commit")
    return result


def atomic_json(path, value, *, validate, fault=None):
    path = contained(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write((p.ledger.canonical(value) + "\n").encode())
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            f.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        validate(temporary.read_bytes())
        if fault:
            fault("before_replace")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def export(root, *, fault=None):
    # ponytail: serialize CLI publication with writers; for large ledgers use a
    # versioned snapshot pointer. GET never participates in this writer lock.
    with opened(root, write=True) as (_conn, state):
        artifact = b.sealed(
            {
                "schema_version": 1,
                "identity": api.IDENTITY,
                "classification": "SYNTHETIC_TEST",
                "official_activation": False,
                "ledgers": state["ledgers"],
                "projection": state["projection"],
            }
        )
        path = contained(contained(root) / "projection.json")
        atomic_json(
            path,
            artifact,
            validate=lambda raw: api.verified(raw, b.digest(p.fingerprints())),
            fault=fault,
        )
    return path


def backup(root, name):
    b.key(name)
    root = contained(root)
    destination = contained(root / "backups" / name)
    with opened(root) as (conn, state):
        destination.mkdir(parents=True, exist_ok=False, mode=0o700)
        path = contained(destination / "ledger.sqlite3")
        with closing(sqlite3.connect(path)) as target:
            conn.backup(target)
            target.execute("BEGIN")
            copied = snapshot(target)
            if copied != state:
                raise ValueError("backup_snapshot_mismatch")
        manifest = b.sealed(
            {
                "identity": IDENTITY,
                "classification": "SYNTHETIC_TEST",
                "official_activation": False,
                "metadata": state["metadata"],
                "heads": heads(state["ledgers"]),
                "snapshot_sha256": b.digest(state),
                "database_sha256": b.sha_file(path),
            }
        )
        atomic_json(
            destination / "manifest.json",
            manifest,
            validate=lambda raw: b.check_seal(q.data.load_json(raw)),
        )
    return destination


def restore(source, root, compare_root):
    source, root, compare_root = map(contained, (source, root, compare_root))
    manifest = b.check_seal(
        q.data.load_json(contained(source / "manifest.json").read_bytes())
    )
    if (
        manifest["identity"] != IDENTITY
        or manifest["classification"] != "SYNTHETIC_TEST"
        or manifest["official_activation"] is not False
        or manifest["database_sha256"] != b.sha_file(contained(source / "ledger.sqlite3"))
    ):
        raise ValueError("backup_incomplete_incompatible_or_corrupt")
    with opened(source) as (backup_conn, saved), opened(compare_root) as (_conn, current):
        if (
            saved["metadata"] != manifest["metadata"]
            or heads(saved["ledgers"]) != manifest["heads"]
            or b.digest(saved) != manifest["snapshot_sha256"]
            or saved["metadata"] != current["metadata"]
            or saved["commands"] != current["commands"][: len(saved["commands"])]
        ):
            raise ValueError("backup_identity_or_history_mismatch")
        for old, new in zip(saved["ledgers"], current["ledgers"], strict=True):
            if old["events"] != new["events"][: len(old["events"])]:
                raise ValueError("backup_event_prefix_mismatch")
        root.mkdir(parents=True, exist_ok=False, mode=0o700)
        report = b.sealed(
            {
                "status": "CURRENT" if saved == current else "STALE",
                "inspection_only": True,
                "official_activation": False,
                "snapshot_sha256": b.digest(saved),
                "backup_heads": heads(saved["ledgers"]),
                "current_heads_at_comparison": heads(current["ledgers"]),
                "missing_sessions": [
                    r["request"]["session"]
                    for r in current["commands"][len(saved["commands"]) :]
                ],
            }
        )
        # Mark isolation before copying, including if the process is interrupted.
        atomic_json(
            root / "restoration.json",
            report,
            validate=lambda raw: b.check_seal(q.data.load_json(raw)),
        )
        with closing(sqlite3.connect(contained(root / "ledger.sqlite3"))) as target:
            backup_conn.backup(target)
            target.execute("BEGIN")
            if snapshot(target) != saved:
                raise ValueError("restored_full_snapshot_mismatch")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("init", "verify", "advance", "export", "backup", "restore")
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--session")
    parser.add_argument("--command-id")
    parser.add_argument("--name")
    parser.add_argument("--from-backup", type=Path)
    parser.add_argument("--compare-root", type=Path)
    args = parser.parse_args()
    try:
        with ExitStack() as stack:
            q.offline(stack)
            if args.action == "init":
                state = initialize(args.root)
            elif args.action == "verify":
                with opened(args.root) as (_conn, state):
                    pass
            elif args.action == "advance":
                if not args.session or not args.command_id:
                    parser.error("advance requires --session and --command-id")
                print(
                    p.ledger.canonical(advance(args.root, args.session, args.command_id))
                )
                return 0
            elif args.action == "export":
                print(export(args.root))
                return 0
            elif args.action == "backup":
                if not args.name:
                    parser.error("backup requires --name")
                print(backup(args.root, args.name))
                return 0
            else:
                if not args.from_backup or not args.compare_root:
                    parser.error("restore requires --from-backup and --compare-root")
                print(
                    p.ledger.canonical(
                        restore(args.from_backup, args.root, args.compare_root)
                    )
                )
                return 0
            print(
                p.ledger.canonical(
                    {
                        "trial_id": state["metadata"]["trial_id"],
                        "classification": "SYNTHETIC_TEST",
                        "official_activation": False,
                        "sessions": [r["request"]["session"] for r in state["commands"]],
                        "heads": heads(state["ledgers"]),
                        "wallets": [
                            {"portfolio_id": w["portfolio_id"], "summary": w["summary"]}
                            for w in state["projection"]["wallets"]
                        ],
                    }
                )
            )
    except (
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        IndexError,
        ArithmeticError,
        OSError,
        sqlite3.Error,
    ) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
