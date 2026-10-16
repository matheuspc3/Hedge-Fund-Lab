"""PAPER-03 checks: real processes, SQLite recovery and atomic publication."""

import copy
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "dashboard")]

import pilot_trial as t  # noqa: E402

q, b = t.q, t.b
D0, D1, D2 = q.SESSIONS[:3]


def read(root):
    with t.opened(root) as (_conn, state):
        return state


def cli(root, action, *arguments):
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts/pilot_trial.py"),
        action,
        "--root",
        str(root),
        *arguments,
    ]


class TrialChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        q.offline(cls.stack)
        t.BASE.mkdir(parents=True, exist_ok=True)
        cls.container = Path(
            cls.stack.enter_context(
                tempfile.TemporaryDirectory(dir=t.BASE, prefix="checks-")
            )
        )
        cls.template = cls.container / "template"
        cls.initial = t.initialize(cls.template)
        cls.addClassCleanup(cls.stack.close)

    def setUp(self):
        self.directory = Path(
            self.enterContext(tempfile.TemporaryDirectory(dir=self.container))
        )
        self.root = self.directory / "trial"
        self.root.mkdir()
        with closing(t.connection(self.template)) as source, closing(
            sqlite3.connect(self.root / "ledger.sqlite3")
        ) as target:
            source.backup(target)

    def command(self, day=D1, cid="day-04"):
        return t.advance(self.root, day, cid)

    def run_cli(self, action, *arguments, root=None, ok=True):
        result = subprocess.run(
            cli(root or self.root, action, *arguments),
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return result.stdout

    def edit(self, sql, parameters=()):
        with closing(t.connection(self.root, write=True)) as conn, conn:
            conn.execute(sql, parameters)

    def test_process_continuity_full_scenario_backup_restore_api_and_retry(self):
        fresh = self.directory / "acceptance"
        initial = json.loads(self.run_cli("init", root=fresh))
        first_ids = read(fresh)["ledgers"]
        for day in q.SESSIONS[1:3]:
            self.run_cli(
                "advance", "--session", day, "--command-id", "advance-" + day, root=fresh
            )
        resumed = json.loads(self.run_cli("verify", root=fresh))
        self.assertEqual(initial["trial_id"], resumed["trial_id"])
        self.assertEqual(len(resumed["sessions"]), 3)
        # Every CLI invocation has ended; continuation opens another process.
        for day in q.SESSIONS[3:-1]:
            self.run_cli(
                "advance", "--session", day, "--command-id", "advance-" + day, root=fresh
            )
        final = read(fresh)
        for start, end in zip(first_ids, final["ledgers"], strict=True):
            self.assertEqual(start["events"], end["events"][: len(start["events"])])
        with tempfile.TemporaryDirectory(prefix="hfl-paper-original-") as original:
            expected = q.run(Path(original))
        # Same original engine/scenario, including all positions, history and trades.
        # UUIDs, recorded_at and import receipts are intentionally independent.
        for actual, wanted in zip(
            final["projection"]["wallets"], expected["wallets"], strict=True
        ):
            self.assertEqual(actual["summary"], wanted["summary"])
            self.assertEqual(
                [
                    {k: v for k, v in h.items() if k != "quote_sha256"}
                    for h in actual["history"]
                ],
                [
                    {k: v for k, v in h.items() if k != "quote_sha256"}
                    for h in wanted["history"]
                ],
            )
            variable = {"authorization_id", "available_at", "bundle_sha256"}
            self.assertEqual(
                [
                    {k: v for k, v in trade.items() if k not in variable}
                    for trade in actual["trades"]
                ],
                [
                    {k: v for k, v in trade.items() if k not in variable}
                    for trade in wanted["trades"]
                ],
            )
        self.run_cli("export", root=fresh)
        path = fresh / "projection.json"
        with patch.dict(os.environ, {"HFL_PILOT_DEMO": str(path)}), patch.object(
            t, "connection", side_effect=AssertionError("SQLite on GET")
        ), patch.object(q, "run", side_effect=AssertionError("qualifier on GET")):
            view = t.api.get({"demo": "1"})
            self.assertTrue(view["read_only"])
            self.assertEqual(view["classification"], "SYNTHETIC_TEST")
            with self.assertRaises(ValueError):
                t.api.get({"demo": "1", "root": str(fresh)})
        self.run_cli("backup", "--name", "complete", root=fresh)
        restored = self.directory / "restored"
        report = json.loads(
            self.run_cli(
                "restore",
                "--from-backup",
                str(fresh / "backups/complete"),
                "--compare-root",
                str(fresh),
                root=restored,
            )
        )
        self.assertEqual(report["status"], "CURRENT")
        self.assertEqual(
            read(restored), final
        )  # Full IDs, events, checkpoints, commands and inputs.
        self.run_cli(
            "advance",
            "--session",
            q.SESSIONS[-2],
            "--command-id",
            "advance-" + q.SESSIONS[-2],
            root=fresh,
        )
        self.assertEqual(read(fresh), final)

    def test_explicit_create_and_root_containment_preserve_old_temp_guard(self):
        with self.assertRaises(FileExistsError):
            t.initialize(self.root)
        for path in (
            ROOT / "data/forward/h2_v6_paper",
            ROOT / "data/radar",
            ROOT / "data/global_pm",
            ROOT / "data/portfolio",
            ROOT / "docs/evidence",
            ROOT / ".git",
            t.BASE,
            self.root / "../../../../escape",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                t.contained(path)
        with self.assertRaises(ValueError):
            t.p.Store(self.root / "ledger.sqlite3", writable=True)
        with patch.object(Path, "is_junction", return_value=True), self.assertRaises(
            ValueError
        ):
            t.contained(self.root)
        with patch.object(Path, "resolve", return_value=ROOT / ".git"), self.assertRaises(
            ValueError
        ):
            t.contained(self.root)

    def test_retry_and_conflicting_identifier(self):
        first = self.command()
        before = read(self.root)
        self.assertEqual(self.command(), first)
        self.assertEqual(read(self.root), before)
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.command(D2)
        with self.assertRaisesRegex(ValueError, "next_synthetic_session"):
            self.command(D1, "another-id")

    def test_order_missing_inputs_and_unconfirmed_partial_state_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "next_synthetic_session"):
            self.command(D2)
        original = read(self.root)
        # A failure midway through the second wallet rolls back the first as well.
        prepare = q.prepare

        def incomplete(store, pid, *args, **kwargs):
            if pid == q.WALLETS[1]:
                raise ValueError("missing_complete_daily_input")
            return prepare(store, pid, *args, **kwargs)

        with patch.object(q, "prepare", side_effect=incomplete), self.assertRaisesRegex(
            ValueError, "missing_complete"
        ):
            self.command()
        self.assertEqual(read(self.root), original)
        meta = copy.deepcopy(original["metadata"])
        del meta["bundles"][D1]
        meta = b.sealed({k: v for k, v in meta.items() if k != "sha256"})
        self.edit("UPDATE trial SET body=?", (t.p.ledger.canonical(meta),))
        with self.assertRaises(ValueError):
            self.command()

    def test_before_commit_rollback_and_lost_ack_after_commit(self):
        original = read(self.root)

        def before(stage):
            if stage == "before_commit":
                raise RuntimeError("before_commit")

        with self.assertRaisesRegex(RuntimeError, "before_commit"):
            t.advance(self.root, D1, "day-04", fault=before)
        self.assertEqual(read(self.root), original)

        def after(stage):
            if stage == "after_commit":
                raise RuntimeError("lost_ack")

        with self.assertRaisesRegex(RuntimeError, "lost_ack"):
            t.advance(self.root, D1, "day-04", fault=after)
        committed = read(self.root)
        self.command()
        self.assertEqual(read(self.root), committed)

    def test_killed_process_rolls_back_whole_session(self):
        code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pilot_trial as t
def fault(stage):
    if stage == 'before_commit':
        print('READY', flush=True)
        sys.stdin.readline()
t.advance(Path(sys.argv[2]), '2026-11-04', 'day-04', fault=fault)
"""
        original = read(self.root)
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", code, str(ROOT / "scripts"), str(self.root)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            # Poll the pipe in a small helper thread, with a bounded main wait.
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=1) as pool:
                ready = pool.submit(child.stdout.readline)
                try:
                    self.assertEqual(ready.result(timeout=60).strip(), "READY")
                finally:
                    child.kill()
            child.communicate(timeout=15)
            self.assertNotEqual(child.returncode, 0)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=15)
        self.assertEqual(read(self.root), original)
        self.command()

    def test_process_dies_after_commit_retry_keeps_exact_ids(self):
        code = """
import os,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pilot_trial as t
def fault(stage):
    if stage == 'after_commit':
        os._exit(23)
t.advance(Path(sys.argv[2]), '2026-11-04', 'day-04', fault=fault)
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ROOT / "scripts"), str(self.root)],
            capture_output=True,
            timeout=90,
        )
        self.assertEqual(result.returncode, 23, result.stderr)
        committed = read(self.root)
        self.run_cli("advance", "--session", D1, "--command-id", "day-04")
        self.assertEqual(read(self.root), committed)

    def test_concurrent_process_commands_commit_once(self):
        command = cli(self.root, "advance", "--session", D1, "--command-id", "concurrent")
        children = [
            subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            for _ in range(2)
        ]
        try:
            results = [child.communicate(timeout=90) for child in children]
            self.assertEqual([child.returncode for child in children], [0, 0], results)
            self.assertEqual(json.loads(results[0][0]), json.loads(results[1][0]))
            self.assertEqual(len(read(self.root)["commands"]), 2)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=15)

    def test_concurrent_different_commands_cannot_complete_session_twice(self):
        children = [
            subprocess.Popen(
                cli(self.root, "advance", "--session", D1, "--command-id", cid),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for cid in ("first", "second")
        ]
        try:
            results = [child.communicate(timeout=90) for child in children]
            self.assertCountEqual(
                [child.returncode for child in children], [0, 2], results
            )
            self.assertEqual(len(read(self.root)["commands"]), 2)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=15)

    def test_checkpoint_tampering_blocks_resume_backup_and_export(self):
        t.export(self.root)
        published = (self.root / "projection.json").read_bytes()
        self.edit("UPDATE checkpoints SET body='{}'")
        for action in (
            lambda: self.command(),
            lambda: t.export(self.root),
            lambda: t.backup(self.root, "bad"),
        ):
            with self.assertRaises((ValueError, KeyError)):
                action()
        self.assertEqual((self.root / "projection.json").read_bytes(), published)

    def test_identity_schema_fingerprints_event_and_command_tampering(self):
        original = read(self.root)
        for field, value in (
            ("identity", "other"),
            ("classification", "REAL"),
            ("official_activation", True),
            ("fingerprints", {}),
        ):
            meta = {k: v for k, v in original["metadata"].items() if k != "sha256"}
            meta[field] = value
            self.edit("UPDATE trial SET body=?", (t.p.ledger.canonical(b.sealed(meta)),))
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.command()
        self.edit(
            "UPDATE trial SET body=?", (t.p.ledger.canonical(original["metadata"]),)
        )
        self.edit("DROP TRIGGER immutable_update")
        with self.assertRaisesRegex(ValueError, "schema_failed"):
            self.command()
        self.edit(
            "CREATE TRIGGER immutable_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable_event'); END"
        )
        self.edit("UPDATE commands SET body='{}'")
        with self.assertRaises(ValueError):
            self.command()

    def test_altered_event_is_rejected_with_schema_and_checkpoint_intact(self):
        event = copy.deepcopy(self.initial["ledgers"][0]["events"][0])
        event["payload"]["parameters"]["capital"] = "1.00"
        self.edit("DROP TRIGGER immutable_update")
        self.edit(
            "UPDATE events SET body=? WHERE event_id=?",
            (json.dumps(event), event["event_id"]),
        )
        self.edit(
            "CREATE TRIGGER immutable_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable_event'); END"
        )
        with self.assertRaisesRegex(
            ValueError, "database_event_index_mismatch|record_hash_mismatch"
        ):
            self.command()

    def test_backup_incomplete_corrupt_incompatible_and_existing_restore(self):
        saved = t.backup(self.root, "valid")
        restored = self.directory / "restored"
        t.restore(saved, restored, self.root)
        with self.assertRaises(FileExistsError):
            t.restore(saved, restored, self.root)
        with self.assertRaises(FileExistsError):
            t.restore(saved, self.root, self.root)
        manifest_path = saved / "manifest.json"
        original = manifest_path.read_bytes()
        manifest_path.unlink()
        with self.assertRaises(FileNotFoundError):
            t.restore(saved, self.directory / "missing", self.root)
        meta = json.loads(original)
        meta["metadata"]["fingerprints"] = {}
        meta = b.sealed({k: v for k, v in meta.items() if k != "sha256"})
        manifest_path.write_text(t.p.ledger.canonical(meta), encoding="utf-8")
        with self.assertRaises(ValueError):
            t.restore(saved, self.directory / "incompatible", self.root)
        manifest_path.write_bytes(original)
        with (saved / "ledger.sqlite3").open("ab") as f:
            f.write(b"corruption")
        with self.assertRaises(ValueError):
            t.restore(saved, self.directory / "corrupt", self.root)

    def test_old_backup_is_explicitly_stale_and_cannot_publish_or_advance(self):
        saved = t.backup(self.root, "old")
        self.command()
        current = read(self.root)
        restored = self.directory / "old-restored"
        report = t.restore(saved, restored, self.root)
        self.assertEqual(report["status"], "STALE")
        self.assertEqual(report["missing_sessions"], [D1])
        self.assertEqual(read(self.root), current)
        self.assertEqual(read(restored), self.initial)
        for action in (
            lambda: t.export(restored),
            lambda: t.advance(restored, D1, "new"),
        ):
            with self.assertRaisesRegex(ValueError, "inspection_only"):
                action()

    def test_atomic_export_validation_failure_and_replacement(self):
        path = t.export(self.root)
        original = path.read_bytes()
        self.command()

        def fail(stage):
            self.assertEqual(stage, "before_replace")
            self.assertEqual(path.read_bytes(), original)
            t.api.read_demo(path)  # The old artifact remains fully valid.
            raise RuntimeError("publication_interrupted")

        with self.assertRaisesRegex(RuntimeError, "publication_interrupted"):
            t.export(self.root, fault=fail)
        self.assertEqual(path.read_bytes(), original)
        with patch.object(
            t.api, "verified", side_effect=ValueError("invalid_new_export")
        ), self.assertRaises(ValueError):
            t.export(self.root)
        self.assertEqual(path.read_bytes(), original)
        replace = os.replace

        def observe(source, destination):
            self.assertEqual(Path(destination).read_bytes(), original)
            t.api.read_demo(Path(source))
            replace(source, destination)
            self.assertNotEqual(Path(destination).read_bytes(), original)

        with patch.object(os, "replace", side_effect=observe):
            t.export(self.root)
        self.assertFalse(list(self.root.glob("*.tmp")))
        artifact, _states = t.api.read_demo(path)
        self.assertEqual(artifact["projection"], read(self.root)["projection"])

    def test_concurrent_backup_is_a_verified_session_boundary(self):
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=2) as pool:
            save = pool.submit(t.backup, self.root, "racing")
            advance = pool.submit(self.command)
            saved = save.result(timeout=60)
            advance.result(timeout=60)
        copied = read(saved)
        self.assertIn(len(copied["commands"]), (1, 2))
        restored = self.directory / "racing-restored"
        report = t.restore(saved, restored, self.root)
        self.assertIn(report["status"], ("CURRENT", "STALE"))
        self.assertEqual(read(restored), copied)


if __name__ == "__main__":
    unittest.main()
