"""DATA-01 extension checks. Test inputs stay synthetic; no observed ZIP supplied."""

import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import ExitStack, redirect_stderr
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests"), str(ROOT / "dashboard")]

import pilot_observed_data as d  # noqa: E402
import qualify_pilot_paper as q  # noqa: E402
from test_pilot_market_data import cotahist_line  # noqa: E402

DAY = "2026-10-14"


class ObservedDataChecks(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        q.offline(self.stack)
        d.BASE.mkdir(parents=True, exist_ok=True)
        self.root = Path(
            self.stack.enter_context(tempfile.TemporaryDirectory(dir=d.BASE))
        )
        self.external = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="hfl-observed-check-")
            )
        )
        self.file = self.external / "SYNTHETIC_DAILY.zip"
        self.lines = [
            cotahist_line(ticker, DAY, quote_factor=1, isin="BRTEST000001")
            for ticker in d.old.UNIVERSE
        ]
        self.archive(self.lines)

    def archive(self, lines, path=None):
        path = path or self.file
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "SYNTHETIC_DAILY.txt", "00SYNTHETIC TEST\n" + "".join(lines) + "99END\n"
            )
        return path

    def register(self, cid="first", **kwargs):
        params = {
            "file": self.file,
            "day": DAY,
            "nature": d.SYNTHETIC,
            "operator": "SYNTHETIC_TEST_OPERATOR",
            "url": "https://www.b3.com.br/",
            "statement": "Explicitly synthetic fixture, not a downloaded observation.",
        }
        return d.register(self.root, cid, **{**params, **kwargs})

    def imported(self):
        self.register()
        return d.import_bundle(self.root, "first", "bundle")

    def test_documented_plan_is_separate_from_observation_and_instrument_trading(self):
        value = d.calendar()
        self.assertEqual(value["coverage"], ["2026-10-13", "2026-12-31"])
        self.assertEqual(value["observed_sessions"], [])
        self.assertEqual(d.calendar_session(value, DAY), DAY)
        self.assertEqual(d.next_session(value, DAY), "2026-10-15")
        self.assertEqual(d.settlement_session(value, DAY), "2026-10-16")
        self.register()
        self.assertEqual(d.observations(self.root), [])
        self.assertEqual(d.calendar()["observed_sessions"], [])

    def test_holidays_weekends_segment_exceptions_and_settlement_coverage(self):
        value = d.calendar()
        for day in (
            "2026-10-17",
            "2026-11-02",
            "2026-11-20",
            "2026-12-24",
            "2026-12-25",
            "2026-12-31",
        ):
            with self.subTest(day=day), self.assertRaisesRegex(
                ValueError, "not_a_planned"
            ):
                d.calendar_session(value, day)
        # US/CSD2 exclusions are not exclusions for listed cash equities.
        for day in ("2026-11-09", "2026-11-11", "2026-11-24", "2026-11-26"):
            self.assertEqual(d.calendar_session(value, day), day)
        self.assertEqual(d.settlement_session(value, "2026-11-19"), "2026-11-24")
        self.assertEqual(d.settlement_session(value, "2026-11-30"), "2026-12-02")
        with self.assertRaisesRegex(ValueError, "settlement_calendar_coverage"):
            d.settlement_session(value, "2026-12-30")
        with self.assertRaisesRegex(ValueError, "calendar_coverage"):
            d.next_session(value, "2026-12-30")
        with self.assertRaisesRegex(ValueError, "calendar_coverage"):
            d.calendar_session(value, "2027-01-04")

    def test_clearing_exception_counts_clearing_days_instead_of_trading_days(self):
        value = d.calendar()
        value["settlement_sessions"].remove("2026-10-16")
        # Isolated algorithm mutation check, not a new claimed B3 exception.
        with patch.object(d, "check_calendar", return_value=value["trading_sessions"]):
            self.assertEqual(d.next_session(value, DAY), "2026-10-15")
            self.assertEqual(d.settlement_session(value, DAY), "2026-10-19")
        self.assertEqual(
            d.planned_days(
                "2026-10-14",
                "2026-10-18",
                [0, 1, 2, 3, 4],
                ["2026-10-15"],
                ["2026-10-17"],
            ),
            ["2026-10-14", "2026-10-16", "2026-10-17"],
        )

    def test_hours_are_versioned_and_not_extrapolated(self):
        value = d.calendar()
        current = d.hours(value, DAY)
        self.assertEqual(current["status"], "PLANNED_WINDOWS")
        self.assertEqual(current["schedule"]["effective_from"], "2026-03-09")
        self.assertEqual(current["schedule"]["phases"]["CONTINUOUS"], ["10:00", "16:55"])
        for day in ("2026-10-15", "2026-11-03"):
            self.assertEqual(d.hours(value, day)["status"], "UNAVAILABLE_VIGENCY")
        self.assertFalse(current["economic_instants_observed"])

    def test_tampered_calendar_and_document_version_fail_closed(self):
        value = d.calendar()
        value["trading_sessions"].append("2026-11-20")
        value = d.b.sealed({k: v for k, v in value.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "unverified_planned"):
            d.calendar_session(value, DAY)
        with patch.object(d, "EVIDENCE_SHA", "0" * 64), self.assertRaisesRegex(
            ValueError, "version_mismatch"
        ):
            d.calendar()

    def test_fixture_cannot_register_or_reseal_itself_as_observed(self):
        with self.assertRaisesRegex(ValueError, "fixture_cannot"):
            self.register(nature=d.OBSERVED)
        record = self.register()
        record["nature"] = d.OBSERVED
        record = d.b.sealed({k: v for k, v in record.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "classification_invalid"):
            d.verify_acquisition(record)

    def test_absent_acquisition_mismatched_hash_and_receipt_tampering(self):
        with self.assertRaises(FileNotFoundError):
            d.import_bundle(self.root, "missing", "bundle")
        receipt = self.external / "receipt.txt"
        receipt.write_text("SYNTHETIC_TEST obtaining evidence", encoding="utf-8")
        record = self.register(receipt_file=receipt)
        self.assertEqual(
            record["obtaining_evidence"]["kind"], "LOCAL_ATTACHMENT_NOT_AUTHENTICATED"
        )
        evidence = self.root / "acquisitions/first/obtaining-evidence.bin"
        evidence.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "evidence_hash_mismatch"):
            d.import_bundle(self.root, "first", "bundle")
        evidence.write_bytes(receipt.read_bytes())
        raw = self.root / "acquisitions/first/original.zip"
        raw.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "original_or_inspection_mismatch"):
            d.import_bundle(self.root, "first", "bundle")

    def test_all_dates_checked_before_parser_including_other_instruments(self):
        for day in ("2026-10-12", "2026-10-13", "2026-10-15"):
            self.archive([*self.lines, cotahist_line("OTHER3", day)])
            with self.subTest(day=day), patch.object(
                d.old,
                "read_cotahist",
                side_effect=AssertionError("price parser too early"),
            ), self.assertRaises(ValueError):
                self.register()

    def test_metadata_currency_factor_isin_and_duplicate_validation(self):
        for field, value in (
            ("currency", "USD"),
            ("quote_factor", 1000),
            ("isin", "XXTEST000001"),
            ("market", "020"),
            ("bdi", "96"),
        ):
            params = {"quote_factor": 1, "isin": "BRTEST000001"}
            params[field] = value
            self.archive([cotahist_line("PETR4", DAY, **params), *self.lines[1:]])
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.register()
        self.archive([*self.lines, self.lines[0]])
        self.register()
        with self.assertRaisesRegex(ValueError, "duplic"):
            d.import_bundle(self.root, "first", "bundle")

    def test_missing_asset_zero_volume_and_invalid_ohlc_are_unavailable(self):
        self.archive(self.lines[:-1])
        record = self.register()
        self.assertFalse(record["inspection"]["instrument_present"]["BBAS3"])
        with self.assertRaisesRegex(ValueError, "missing_required_instrument"):
            d.import_bundle(self.root, "first", "missing")
        for cid, params in (("volume", {"volume": 0}), ("ohlc", {"high": 3800})):
            self.archive(
                [
                    cotahist_line(
                        "PETR4", DAY, quote_factor=1, isin="BRTEST000001", **params
                    ),
                    *self.lines[1:],
                ]
            )
            self.register(cid)
            with self.assertRaises(ValueError):
                d.import_bundle(self.root, cid, cid)
        self.assertFalse((self.root / "bundles").exists())

    def test_bundle_reuses_raw_parser_and_distinguishes_open_close(self):
        with patch.object(d.old, "read_cotahist", wraps=d.old.read_cotahist) as parser:
            bundle = self.imported()
        self.assertEqual(parser.call_count, 5)
        at = bundle["import"]["available_at"]
        self.assertEqual(d.prices(bundle, DAY, "OPEN", at=at)["PETR4"], "40.00")
        self.assertEqual(d.prices(bundle, DAY, "CLOSE", at=at)["PETR4"], "41.00")
        self.assertEqual(bundle["content"]["source"]["basis"], "RAW")
        self.assertEqual(bundle["content"]["source"]["nature"], d.SYNTHETIC)
        with self.assertRaises(ValueError):
            d.old.verify_bundle(bundle)
        with self.assertRaisesRegex(ValueError, "OPEN_or_CLOSE"):
            d.prices(bundle, DAY, "ADJUSTED", at=at)

    def test_temporal_availability_does_not_use_operator_download_declaration(self):
        past = (d.datetime.now(d.timezone.utc) - timedelta(hours=1)).isoformat()
        self.register(obtained_at=past)
        bundle = d.import_bundle(self.root, "first", "bundle")
        self.assertGreater(
            d.old.instant(bundle["import"]["available_at"]), d.old.instant(past)
        )
        self.assertEqual(
            bundle["import"]["available_at"], bundle["import"]["imported_at"]
        )
        with self.assertRaisesRegex(ValueError, "not_yet_available"):
            d.prices(bundle, DAY, "OPEN", at=past)
        record = copy.deepcopy(bundle["content"]["source"]["acquisition_record"])
        record["published_at"] = past
        record = d.b.sealed({k: v for k, v in record.items() if k != "sha256"})
        with self.assertRaises(ValueError):
            d.verify_acquisition(record)

    def test_correction_requires_previous_preserves_originals_and_reimport_identity(self):
        first = self.imported()
        repeated = d.import_bundle(self.root, "first", "repeat")
        self.assertEqual(first["content_sha256"], repeated["content_sha256"])
        original_bytes = (self.root / "bundles/bundle.json").read_bytes()
        self.archive(
            [
                cotahist_line(
                    "PETR4", DAY, close=4150, quote_factor=1, isin="BRTEST000001"
                ),
                *self.lines[1:],
            ]
        )
        self.register("correction")
        with self.assertRaisesRegex(ValueError, "explicit_previous"):
            d.import_bundle(self.root, "correction", "no-previous")
        correction = d.import_bundle(self.root, "correction", "v2", previous="bundle")
        self.assertEqual(correction["content"]["revision"], 2)
        self.assertEqual(correction["content"]["revision_of"], first["content_sha256"])
        self.assertEqual((self.root / "bundles/bundle.json").read_bytes(), original_bytes)
        with self.assertRaisesRegex(ValueError, "not_latest_revision"):
            d.import_bundle(self.root, "correction", "bad-parent", previous="bundle")

    def test_no_overwrite_protected_paths_and_classification_conflicts(self):
        self.imported()
        with self.assertRaises(FileExistsError):
            self.register()
        with self.assertRaises(FileExistsError):
            d.import_bundle(self.root, "first", "bundle")
        for path in (
            ROOT / "data/radar",
            ROOT / "data/forward",
            ROOT / "data/raw",
            ROOT / "docs/evidence",
            ROOT / ".git",
            ROOT / "data/platform/paper-synthetic",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                d.storage(path)
        with self.assertRaises(ValueError):
            d.input_path(ROOT / "data/raw/not-opened.zip")
        with patch.object(Path, "is_junction", return_value=True), self.assertRaises(
            ValueError
        ):
            d.storage(self.root)

    def test_record_source_url_operator_and_generation_are_not_authentication(self):
        record = self.register()
        self.assertEqual(
            record["obtaining_evidence"]["kind"], "OPERATOR_DECLARATION_ONLY"
        )
        self.assertIn("do not authenticate", record["limits"])
        for key in ("operator", "statement"):
            altered = {**record, key: ""}
            altered = d.b.sealed({k: v for k, v in altered.items() if k != "sha256"})
            with self.assertRaises(ValueError):
                d.verify_acquisition(altered)

    def test_real_header_structure_is_checked_without_claiming_a_real_acquisition(self):
        # A known synthetic byte stream with an invalid claimed envelope must fail.
        raw = self.file.read_bytes()
        with self.assertRaises(ValueError):
            d.inspect_daily(raw, DAY, d.OBSERVED, "COTAHIST_D14102026.ZIP")
        with self.assertRaisesRegex(ValueError, "daily_header_or_trailer"):
            bad = io.BytesIO()
            with zipfile.ZipFile(bad, "w") as archive:
                archive.writestr("test.txt", "".join(self.lines))
            d.inspect_daily(bad.getvalue(), DAY, d.SYNTHETIC, "test.zip")

    def test_cli_local_processes_register_import_query_no_observed_claim(self):
        # Block networking even in each fresh CLI interpreter.
        runner = "import sys,runpy,socket;socket.socket.connect=lambda *a: (_ for _ in ()).throw(AssertionError('network forbidden'));sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"

        def cli(action, *arguments):
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    runner,
                    str(ROOT / "scripts/pilot_observed_data.py"),
                    action,
                    "--root",
                    str(self.root),
                    *arguments,
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            response = json.loads(result.stdout)
            self.assertFalse(response["financial_integration_ready"])
            return response["result"]

        cli(
            "register",
            "--id",
            "cli",
            "--file",
            str(self.file),
            "--session",
            DAY,
            "--nature",
            d.SYNTHETIC,
            "--operator",
            "SYNTHETIC_TEST_OPERATOR",
            "--url",
            "https://www.b3.com.br/",
            "--statement",
            "Synthetic test, not observed",
        )
        imported = cli("import", "--id", "cli", "--name", "cli")
        queried = cli(
            "query",
            "--name",
            "cli",
            "--session",
            DAY,
            "--phase",
            "CLOSE",
            "--at",
            imported["available_at"],
        )
        self.assertEqual(queried["nature"], d.SYNTHETIC)
        self.assertEqual(queried["prices"]["PETR4"], "41.00")
        self.assertEqual(cli("observations")["observations"], [])

    def test_cli_missing_acquisition_fails_without_reconstructing_input(self):
        error = io.StringIO()
        with patch.object(
            sys,
            "argv",
            [
                "pilot_observed_data.py",
                "import",
                "--root",
                str(self.root),
                "--id",
                "absent",
                "--name",
                "bundle",
            ],
        ), redirect_stderr(error):
            self.assertEqual(d.main(), 2)
        self.assertIn("BLOCKED", error.getvalue())

    def test_existing_exports_and_durable_trial_still_read_without_writes(self):
        import pilot_api
        import pilot_trial

        path = ROOT / "data/platform/pilot-demo.json"
        trial = ROOT / "data/platform/paper-synthetic/paper03-20261014"
        if not path.is_file() or not (trial / "ledger.sqlite3").is_file():
            self.skipTest(
                "Existing operator artifacts are not installed in this checkout"
            )
        before = path.read_bytes()
        artifact, states = pilot_api.read_demo(path)
        self.assertEqual(artifact["classification"], d.SYNTHETIC)
        self.assertEqual(len(states), 2)
        database = trial / "ledger.sqlite3"
        db_sha = d.b.sha_file(database)
        with pilot_trial.opened(trial) as (_conn, state):
            self.assertEqual(len(state["commands"]), 8)
            self.assertEqual(
                state["metadata"]["trial_id"], "ee3314b4-7264-4497-ba38-9873d792f752"
            )
        self.assertEqual(d.b.sha_file(database), db_sha)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
