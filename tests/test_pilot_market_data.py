"""Small synthetic COTAHIST fixtures; no market downloads or protected H2 inputs.

Run: .venv/Scripts/python.exe -B -m unittest discover -s tests -p test_pilot_market_data.py -v
"""

import copy
import hashlib
import io
import json
import shutil
import socket
import sys
import tempfile
import unittest
import zipfile
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]

with patch.object(
    socket.socket, "connect", side_effect=AssertionError("network forbidden")
):
    import pilot_market_data as data

SESSIONS = ["2026-04-17", "2026-04-20", "2026-04-22", "2026-04-23", "2026-04-24"]
SELECTED = SESSIONS[:3]


def cotahist_line(
    ticker,
    day,
    *,
    opening=4000,
    high=4200,
    low=3900,
    close=4100,
    currency="R$",
    market="010",
    bdi="02",
    volume=100,
    quote_factor=None,
    isin=None,
):
    text = list(" " * 245)
    fields = {
        0: "01",
        2: day.replace("-", ""),
        10: bdi,
        12: ticker.ljust(12),
        24: market,
        52: currency.ljust(4),
        56: f"{opening:013d}",
        69: f"{high:013d}",
        82: f"{low:013d}",
        108: f"{close:013d}",
        152: f"{volume:018d}",
    }
    if quote_factor is not None:
        fields[210] = f"{quote_factor:07d}"
    if isin is not None:
        fields[230] = isin.ljust(12)
    for start, value in fields.items():
        text[start : start + len(value)] = value
    return "".join(text) + "\n"


def write_fixture(directory, lines=None, **overrides):
    """Fixture builder, also usable for the temporary CLI example."""
    directory = Path(directory)
    archive_path = directory / "SYNTHETIC_NOT_MARKET_DATA.zip"
    if lines is None:
        lines = [
            cotahist_line(ticker, day) for ticker in data.UNIVERSE for day in SELECTED
        ]
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "SYNTHETIC_NOT_MARKET_DATA.txt",
            "00SYNTHETIC TEST\n" + "".join(lines) + "99END\n",
        )
    manifest = {
        "schema_version": 1,
        "file": archive_path.name,
        "file_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "source": "SYNTHETIC_COTAHIST_FIXTURE",
        "nature": "SYNTHETIC_TEST",
        "basis": "RAW",
        "currency": "BRL",
        "instrument": "B3_SPOT_STANDARD_LOT_010_02",
        **overrides,
    }
    path = directory / "input.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    calendar_path = directory / "synthetic_calendar.json"
    calendar_path.write_text(
        json.dumps(
            {
                "nature": "SYNTHETIC_TEST",
                "source": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
                "sessions": SESSIONS,
            }
        ),
        encoding="utf-8",
    )
    return path, calendar_path


def reseal(bundle):
    bundle["content"]["normalized_sha256"] = data.digest(bundle["content"]["bars"])
    bundle["content_sha256"] = data.digest(bundle["content"])
    bundle["sha256"] = data.digest({k: v for k, v in bundle.items() if k != "sha256"})
    return bundle


class PilotDataChecks(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.network = self.stack.enter_context(
            patch.object(
                socket.socket, "connect", side_effect=AssertionError("network forbidden")
            )
        )
        self.stack.enter_context(
            patch.object(
                socket.socket,
                "connect_ex",
                side_effect=AssertionError("network forbidden"),
            )
        )
        self.stack.enter_context(
            patch(
                "urllib.request.urlopen", side_effect=AssertionError("download forbidden")
            )
        )
        self.stack.enter_context(
            patch("yfinance.download", side_effect=AssertionError("yfinance forbidden"))
        )
        self.directory = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="hfl-pilot-check-")
            )
        )
        self.manifest, self.calendar_path = write_fixture(self.directory)
        self.calendar = data.load_calendar(self.calendar_path)

    def imported(self, **kwargs):
        return data.import_file(
            self.manifest, calendar=self.calendar, sessions=SELECTED, **kwargs
        )

    def daily_fixture(self, extra=(), **bar_options):
        day = "2026-10-13"
        lines = [
            cotahist_line(
                t, day, quote_factor=1, isin=("BR" + t).ljust(12, "0"), **bar_options
            )
            for t in data.UNIVERSE
        ]
        manifest, calendar = write_fixture(
            self.directory,
            [*lines, *extra],
            format="COTAHIST_DAILY_245",
            file_session=day,
        )
        calendar.write_text(
            json.dumps(
                {
                    "nature": "SYNTHETIC_TEST",
                    "source": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
                    "sessions": [day, "2026-10-14", "2026-10-15"],
                }
            ),
            encoding="utf-8",
        )
        return manifest, data.load_calendar(calendar)

    def test_valid_five_assets_open_close_and_cli_end_to_end(self):
        output = self.directory / "bundle.json"
        with redirect_stdout(io.StringIO()) as printed:
            result = data.main(
                [
                    "--input",
                    str(self.manifest),
                    "--calendar",
                    str(self.calendar_path),
                    "--output",
                    str(output),
                    *[arg for d in SELECTED for arg in ("--session", d)],
                ]
            )
        self.assertEqual(result, 0)
        self.assertFalse(json.loads(printed.getvalue())["official_ingestion_ready"])
        bundle = json.loads(output.read_bytes())
        content = data.verify_bundle(bundle)
        self.assertEqual(len(content["bars"]), 15)
        self.assertEqual(content["source"]["nature"], "SYNTHETIC_TEST")
        self.assertEqual(content["source"]["basis"], "RAW")
        self.assertEqual(
            content["original_sha256"],
            hashlib.sha256(
                (self.directory / "SYNTHETIC_NOT_MARKET_DATA.zip").read_bytes()
            ).hexdigest(),
        )
        at = bundle["import"]["available_at"]
        self.assertEqual(
            data.prices(bundle, SELECTED[0], "OPEN", at=at),
            dict.fromkeys(data.UNIVERSE, "40.00"),
        )
        self.assertEqual(
            data.prices(bundle, SELECTED[0], "CLOSE", at=at),
            dict.fromkeys(data.UNIVERSE, "41.00"),
        )
        self.assertEqual(self.network.call_count, 0)

    def test_selection_is_explicit_and_missing_session_is_not_carried(self):
        bundle = data.import_file(
            self.manifest,
            calendar=self.calendar,
            sessions=[SELECTED[1]],
            tickers=["PETR4"],
        )
        self.assertEqual(len(bundle["content"]["bars"]), 1)
        with self.assertRaisesRegex(ValueError, "not_imported"):
            data.prices(bundle, SELECTED[0], "CLOSE", at=bundle["import"]["available_at"])
        with self.assertRaisesRegex(ValueError, "missing_or_unexpected_bar"):
            data.import_file(
                self.manifest, calendar=self.calendar, sessions=[SESSIONS[-1]]
            )

    def test_exact_cents_and_volume_survive_reused_float_parser(self):
        maximum = 9999999999999
        volume = 999999999999999999
        write_fixture(
            self.directory,
            [
                cotahist_line(
                    t,
                    day,
                    opening=maximum,
                    high=maximum,
                    low=maximum,
                    close=maximum,
                    volume=volume,
                )
                for t in data.UNIVERSE
                for day in SELECTED
            ],
        )
        bar = self.imported()["content"]["bars"][0]
        self.assertEqual(bar["OPEN"], "99999999999.99")
        self.assertEqual(bar["volume"], str(volume))

    def test_manifest_schema_and_duplicate_metadata_fields(self):
        for raw in ("[]", '{"source":"UNKNOWN","source":"SYNTHETIC_COTAHIST_FIXTURE"}'):
            self.manifest.write_text(raw, encoding="utf-8")
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.imported()
        write_fixture(self.directory, schema_version=True)
        with self.assertRaisesRegex(ValueError, "invalid_input_manifest"):
            self.imported()

    def test_missing_asset_or_price(self):
        lines = [cotahist_line(t, day) for t in data.UNIVERSE[:-1] for day in SELECTED]
        write_fixture(self.directory, lines)
        with self.assertRaisesRegex(ValueError, "missing_required_instrument"):
            self.imported()
        lines.append(cotahist_line("BBAS3", SELECTED[0], opening=0))
        write_fixture(self.directory, lines)
        with self.assertRaises(ValueError):
            self.imported()

    def test_conflicting_duplicate_is_rejected(self):
        lines = [cotahist_line(t, day) for t in data.UNIVERSE for day in SELECTED]
        lines.append(cotahist_line("PETR4", SELECTED[0], close=4150))
        write_fixture(self.directory, lines)
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            self.imported()

    def test_invalid_price_ohlc_and_no_trade(self):
        for kwargs in (
            {"opening": 0},
            {"close": -1},
            {"high": 3999},
            {"low": 4101},
            {"volume": 0},
        ):
            with self.subTest(kwargs=kwargs):
                lines = [
                    cotahist_line(t, day, **kwargs)
                    for t in data.UNIVERSE
                    for day in SELECTED
                ]
                write_fixture(self.directory, lines)
                with self.assertRaises(ValueError):
                    self.imported()

    def test_incompatible_instrument_currency_and_ticker(self):
        for kwargs in ({"market": "020"}, {"bdi": "96"}, {"currency": "USD"}):
            with self.subTest(kwargs=kwargs):
                write_fixture(
                    self.directory,
                    [
                        cotahist_line(t, day, **kwargs)
                        for t in data.UNIVERSE
                        for day in SELECTED
                    ],
                )
                with self.assertRaisesRegex(ValueError, "incompatible_cotahist"):
                    self.imported()
        with self.assertRaisesRegex(ValueError, "invalid_selection"):
            self.imported(tickers=["PETR4F"])

    def test_unknown_source_adjusted_and_mixed_nature_are_blocked(self):
        for override in (
            {"source": "UNKNOWN"},
            {"basis": "ADJUSTED"},
            {"nature": "REAL_UNVERIFIED"},
            {"instrument": "ETF"},
            {"adjusted_close": "40.00"},
        ):
            with self.subTest(override=override):
                write_fixture(self.directory, **override)
                with self.assertRaises(ValueError):
                    self.imported()

    def test_availability_is_import_bound_and_queries_do_not_mutate(self):
        bundle = self.imported()
        before = copy.deepcopy(bundle)
        at = bundle["import"]["available_at"]
        past = (datetime.fromisoformat(at) - timedelta(microseconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError, "data_not_yet_available"):
            data.prices(bundle, SELECTED[0], "OPEN", at=past)
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            data.verify_bundle(bundle, at="2026-04-24T18:00:00")
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            data.prices(bundle, SELECTED[0], "OPEN", at=None)
        data.verify_bundle(bundle, at=at)
        self.assertEqual(bundle, before)
        self.assertEqual(bundle["import"]["imported_at"], at)
        self.assertNotIn("published_at", bundle["import"])

    def test_synthetic_weekend_holiday_and_d_plus_two(self):
        self.assertEqual(data.next_session(self.calendar, "2026-04-17"), "2026-04-20")
        self.assertEqual(
            data.settlement_session(self.calendar, "2026-04-17"), "2026-04-22"
        )
        for day in ("2026-04-18", "2026-04-21", "2027-01-04"):
            with self.subTest(day=day), self.assertRaisesRegex(
                ValueError, "calendar_session_unavailable"
            ):
                data.calendar_session(self.calendar, day)
        for day in SESSIONS[-2:]:
            with self.subTest(day=day), self.assertRaisesRegex(
                ValueError, "coverage_insufficient"
            ):
                data.settlement_session(self.calendar, day)
        with self.assertRaisesRegex(ValueError, "coverage_insufficient"):
            data.next_session(self.calendar, SESSIONS[-1])

    def test_verified_calendar_cannot_be_extended_by_fixture(self):
        verified = data.load_calendar()
        self.assertEqual(verified["sessions"][-1], "2026-08-31")
        for day in ("2026-10-13", "2027-01-04"):
            with self.assertRaisesRegex(ValueError, "calendar_session_unavailable"):
                data.calendar_session(verified, day)
        fake = copy.deepcopy(verified)
        fake["sessions"].append("2026-10-13")
        fake["sha256"] = data.digest({k: v for k, v in fake.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "unverified_calendar"):
            data.calendar_session(fake, "2026-10-13")
        self.calendar_path.write_text(
            json.dumps(
                {"nature": "VERIFIED_B3_SESSIONS", "source": "B3", "sessions": SELECTED}
            )
        )
        with self.assertRaisesRegex(ValueError, "synthetic_calendar_required"):
            data.load_calendar(self.calendar_path)

    def test_reimport_identity_and_explicit_revision(self):
        first = self.imported()
        again = data.import_file(
            self.manifest,
            calendar=self.calendar,
            sessions=reversed(SELECTED),
            tickers=reversed(data.UNIVERSE),
        )
        self.assertEqual(first["content_sha256"], again["content_sha256"])
        self.assertNotEqual(first["sha256"], again["sha256"])
        same = self.imported(previous=first)
        self.assertEqual(first["content"], same["content"])
        lines = [
            cotahist_line(t, day, close=4150) for t in data.UNIVERSE for day in SELECTED
        ]
        write_fixture(self.directory, lines)
        corrected = self.imported(previous=first)
        self.assertEqual(corrected["content"]["revision"], 2)
        self.assertEqual(corrected["content"]["revision_of"], first["content_sha256"])
        self.assertNotEqual(corrected["content_sha256"], first["content_sha256"])
        self.assertNotEqual(
            corrected["content"]["normalized_sha256"],
            first["content"]["normalized_sha256"],
        )
        self.assertEqual(
            self.imported(previous=corrected)["content_sha256"],
            corrected["content_sha256"],
        )
        with self.assertRaisesRegex(ValueError, "revision_scope_mismatch"):
            self.imported(previous=first, tickers=["PETR4"])

    def test_input_hash_bundle_tampering_and_synthetic_classification(self):
        bundle = self.imported()
        bad = copy.deepcopy(bundle)
        bad["content"]["bars"][0]["CLOSE"] = "42.00"
        with self.assertRaisesRegex(ValueError, "integrity"):
            data.verify_bundle(bad)
        bad = copy.deepcopy(bundle)
        bad["content"]["source"].update(
            source="B3_COTAHIST_LOCAL", nature="REAL_UNVERIFIED"
        )
        with self.assertRaisesRegex(ValueError, "nature_mismatch"):
            data.verify_bundle(reseal(bad))
        raw = self.directory / "SYNTHETIC_NOT_MARKET_DATA.zip"
        raw.write_bytes(raw.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "original_file_hash_mismatch"):
            self.imported()

    def test_official_source_blocks_before_reading_market_file(self):
        write_fixture(
            self.directory, source="B3_COTAHIST_LOCAL", nature="REAL_UNVERIFIED"
        )
        verified = data.load_calendar()
        with patch.object(
            data,
            "read_cotahist",
            side_effect=AssertionError("must not parse real historical data"),
        ):
            with self.assertRaisesRegex(ValueError, "calendar_session_unavailable"):
                data.import_file(
                    self.manifest, calendar=verified, sessions=["2026-10-13"]
                )
            with self.assertRaisesRegex(ValueError, "real_history_before_pilot_blocked"):
                data.import_file(self.manifest, calendar=verified, sessions=SELECTED)

    def test_no_overwrite_or_protected_paths_and_cli_error(self):
        bundle = self.imported()
        output = self.directory / "bundle.json"
        data.write_bundle(output, bundle)
        original = output.read_bytes()
        with self.assertRaises(FileExistsError):
            data.write_bundle(output, bundle)
        self.assertEqual(original, output.read_bytes())
        with self.assertRaisesRegex(ValueError, "protected_input_or_output_path"):
            data.local_path(ROOT / "data" / "not-read.json")
        with redirect_stderr(io.StringIO()) as errors:
            result = data.main(
                [
                    "--input",
                    str(self.manifest),
                    "--session",
                    "2026-10-13",
                    "--output",
                    str(output),
                ]
            )
        self.assertEqual(result, 2)
        self.assertEqual(json.loads(errors.getvalue())["status"], "BLOCKED")
        self.assertEqual(original, output.read_bytes())

    def test_public_calendar_documents_are_verified_but_positive_coverage_is_blocked(
        self,
    ):
        calendar = data.load_calendar("b3-2026")
        self.assertEqual(calendar["document_coverage"], ["2026-01-01", "2026-12-31"])
        self.assertEqual(calendar["requested_coverage"], ["2026-10-13", "2026-11-30"])
        self.assertEqual(calendar["sessions"], [])
        self.assertEqual(calendar["observed_sessions"], [])
        for query in (data.calendar_session, data.next_session, data.settlement_session):
            with self.subTest(query=query.__name__), self.assertRaisesRegex(
                ValueError, "positive_session_coverage_unproven"
            ):
                query(calendar, "2026-10-13")
        with self.assertRaisesRegex(ValueError, "documented_non_session"):
            data.calendar_session(calendar, "2026-11-02")
        # The previously qualified, covered D+2 path remains independent.
        self.assertEqual(
            data.settlement_session(self.calendar, SELECTED[0]), "2026-04-22"
        )

    def test_calendar_document_tampering_missing_evidence_and_self_declaration(self):
        copy_root = self.directory / "evidence-copy"
        shutil.copytree(data.EVIDENCE_ROOT, copy_root)
        source_path = copy_root / "sources.json"
        source_raw = source_path.read_bytes()
        source_path.write_bytes(source_raw + b" ")
        with self.assertRaisesRegex(ValueError, "manifest_mismatch"):
            data.source_evidence(copy_root)
        source_path.write_bytes(source_raw)
        document = copy_root / "b3_calendar_041_2026.pdf"
        document.write_bytes(b"not a B3 document")
        with self.assertRaisesRegex(ValueError, "source_artifact_mismatch"):
            data.source_evidence(copy_root)
        document.unlink()
        with self.assertRaises(FileNotFoundError):
            data.source_evidence(copy_root)
        fake = data.load_calendar("b3-2026")
        fake["sessions"] = ["2026-10-13", "2026-10-14", "2026-10-15"]
        fake["status"] = "VERIFIED"
        fake["sha256"] = data.digest({k: v for k, v in fake.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "unverified_prospective_calendar"):
            data.calendar_session(fake, "2026-10-13")
        self.calendar_path.write_text(json.dumps(fake), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "synthetic_calendar_required"):
            data.load_calendar(self.calendar_path)

    def test_documented_daily_format_remains_a_synthetic_fixture(self):
        manifest, calendar = self.daily_fixture()
        bundle = data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])
        self.assertEqual(bundle["content"]["source"]["nature"], "SYNTHETIC_TEST")
        self.assertEqual(len(bundle["content"]["bars"]), 5)
        self.assertTrue(all(len(bar["isin"]) == 12 for bar in bundle["content"]["bars"]))
        self.assertEqual(
            data.prices(
                bundle, "2026-10-13", "OPEN", at=bundle["import"]["available_at"]
            ),
            dict.fromkeys(data.UNIVERSE, "40.00"),
        )
        self.assertEqual(data.source_evidence()["acquisitions"], {})

    def test_daily_file_rejects_pre_d0_other_instrument_before_price_parser(self):
        historical = cotahist_line("ABCD3", "2026-10-09")
        historical = historical[:56] + "X" * 65 + historical[121:]
        manifest, calendar = self.daily_fixture(extra=[historical])
        with patch.object(
            data,
            "read_cotahist",
            side_effect=AssertionError("price parser must not see history"),
        ) as parser:
            with self.assertRaisesRegex(ValueError, "real_history_before_pilot_blocked"):
                data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])
            parser.assert_not_called()

    def test_daily_file_cannot_smuggle_other_sessions_or_bad_quote_units(self):
        manifest, calendar = self.daily_fixture(
            extra=[cotahist_line("ABCD3", "2026-10-14")]
        )
        with self.assertRaisesRegex(ValueError, "daily_file_session_mismatch"):
            data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])
        for factor in (0, 1000):
            manifest, calendar = self.daily_fixture()
            body = data.load_json(manifest.read_bytes())
            lines = [
                cotahist_line(
                    t, "2026-10-13", quote_factor=factor, isin=("BR" + t).ljust(12, "0")
                )
                for t in data.UNIVERSE
            ]
            write_fixture(
                self.directory,
                lines,
                format=body["format"],
                file_session=body["file_session"],
            )
            with self.subTest(factor=factor), self.assertRaisesRegex(
                ValueError, "unsupported_quote_factor_or_isin"
            ):
                data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])

    def test_acquisition_manifest_is_not_source_authentication_or_promotion(self):
        manifest, calendar = self.daily_fixture()
        body = data.load_json(manifest.read_bytes())
        body["acquisition_id"] = "operator-self-declaration"
        manifest.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "acquisition_cannot_promote"):
            data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])
        body.update(
            source="B3_COTAHIST_DOCUMENTED", nature="ORIGIN_DOCUMENTED_NOT_AUTHENTICATED"
        )
        manifest.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "acquisition_not_in_verified_registry"):
            data.import_file(
                manifest, calendar=data.load_calendar(), sessions=["2026-10-13"]
            )

    def test_daily_availability_has_no_free_publication_override(self):
        manifest, calendar = self.daily_fixture()
        bundle = data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])
        receipt = bundle["import"]
        self.assertEqual(receipt["available_at"], receipt["imported_at"])
        bad = copy.deepcopy(bundle)
        bad["import"]["available_at"] = "2026-10-13T08:00:00-03:00"
        with self.assertRaisesRegex(ValueError, "unproven_availability"):
            data.verify_bundle(reseal(bad))
        body = data.load_json(manifest.read_bytes())
        body["published_at"] = "2026-10-13T08:00:00-03:00"
        manifest.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid_input_manifest"):
            data.import_file(manifest, calendar=calendar, sessions=["2026-10-13"])

    def test_previous_v1_bundle_remains_readable(self):
        bundle = self.imported()
        bundle["content"]["parser"]["adapter"] = "PILOT_COTAHIST_RAW_V1"
        data.verify_bundle(reseal(bundle))


if __name__ == "__main__":
    unittest.main()
