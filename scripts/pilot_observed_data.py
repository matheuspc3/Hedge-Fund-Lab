"""Versioned DATA-01 local input. No downloader, adjusted history or ledger writes."""

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pilot_market_data as old  # noqa: E402
from pilot_paper import b, bind  # noqa: E402

EVIDENCE = old.EVIDENCE_ROOT / "observed_v1"
EVIDENCE_SHA = "79ea81a13a7854baa8db4d6908fb9a2c2c4d5297d7254db9bd8d99b5db77f632"
BASE = ROOT / "data/platform/observed-market-v1"
IDENTITY = "HFL-OBSERVED-LOCAL-DATA-V1"
OBSERVED = "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED"
SYNTHETIC = "SYNTHETIC_TEST"
MAX_BYTES = 128 * 1024 * 1024


def evidence():
    raw = (EVIDENCE / "sources.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != EVIDENCE_SHA:
        raise ValueError("observed_evidence_version_mismatch")
    catalog = old.load_json(raw)
    for name, record in catalog["documents"].items():
        path = (EVIDENCE / name).resolve()
        if not path.is_relative_to(old.EVIDENCE_ROOT.resolve()):
            raise ValueError("evidence_path_escape")
        for field in ("url", "final_url"):
            url = urlsplit(record[field])
            if url.scheme != "https" or url.hostname not in (
                "b3.com.br",
                "www.b3.com.br",
                "bvmf.bmfbovespa.com.br",
                "www.ion.itau",
            ):
                raise ValueError("evidence_origin_unknown")
        old.instant(record["retrieved_at"])
        captured = path.read_bytes()
        if (
            len(captured) != record["bytes"]
            or hashlib.sha256(captured).hexdigest() != record["sha256"]
        ):
            raise ValueError("observed_evidence_bytes_mismatch")
    return catalog


def planned_days(start, end, weekdays, closures, additional):
    """Expand a documented regular rule and its segment-specific exceptions."""
    first, last = map(date.fromisoformat, (start, end))
    return sorted(
        {
            day.isoformat()
            for i in range((last - first).days + 1)
            if (day := first + timedelta(days=i)).weekday() in weekdays
            and day.isoformat() not in closures
        }
        | {d for d in additional if start <= d <= end}
    )


def calendar():
    rules = evidence()["rules"]
    return b.sealed(
        {
            "identity": "HFL-B3-CASH-EQUITIES-PLANNED-2026-V1",
            "nature": "DOCUMENTED_PLAN_NOT_OBSERVATION",
            "evidence_sha256": EVIDENCE_SHA,
            "coverage": rules["coverage"],
            "regular_basis": rules["regular_basis"],
            **{
                kind + "_sessions": planned_days(
                    *rules["coverage"],
                    rules["regular_weekdays"],
                    rules[kind]["closures"],
                    rules[kind]["additional_sessions"],
                )
                for kind in ("trading", "settlement")
            },
            "settlement_rule": rules["settlement"],
            "hours": rules["hours"],
            "observed_sessions": [],
            "official_activation": False,
        }
    )


def check_calendar(value):
    if value != calendar():
        raise ValueError("unverified_planned_calendar")
    return value["trading_sessions"]


def calendar_session(value, day):
    old.iso_day(day)
    days = check_calendar(value)
    if not value["coverage"][0] <= day <= value["coverage"][1]:
        raise ValueError("planned_calendar_coverage_insufficient")
    if day not in days:
        raise ValueError("not_a_planned_trading_session")
    return day


def next_session(value, day):
    calendar_session(value, day)
    days = value["trading_sessions"]
    index = bisect_right(days, day)
    if index == len(days):
        raise ValueError("planned_calendar_coverage_insufficient")
    return days[index]


def settlement_session(value, day):
    calendar_session(value, day)
    # Never count trading dates as a substitute for the clearing calendar.
    days = value["settlement_sessions"]
    index = bisect_right(days, day) + value["settlement_rule"]["cycle_business_days"] - 1
    if index >= len(days):
        raise ValueError("settlement_calendar_coverage_insufficient")
    return days[index]


def hours(value, day):
    calendar_session(value, day)
    schedule = value["hours"]
    start, end = schedule["reviewed_coverage"]
    return {
        "status": "PLANNED_WINDOWS" if start <= day <= end else "UNAVAILABLE_VIGENCY",
        "session": day,
        "schedule": schedule if start <= day <= end else None,
        "economic_instants_observed": False,
    }


def storage(path):
    path = Path(path).absolute()
    resolved = path.resolve()
    if (
        not path.is_relative_to(BASE)
        or not resolved.is_relative_to(BASE)
        or resolved == BASE
        or any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))
    ):
        raise ValueError("dedicated_observed_storage_required")
    return resolved


def input_path(path):
    path = old.local_path(path)
    if path.is_relative_to(ROOT / ".git"):
        raise ValueError("protected_input_or_output_path")
    return path


def bounded_read(path):
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("daily_file_too_large")
    return raw


def inspect_daily(raw, day, nature, original_name):
    """Inspect all dates/structure before any price parser can run."""
    if old.iso_day(day) <= "2026-10-13":
        raise ValueError("session_must_be_after_product_D0")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) != 1 or not members[0].filename.lower().endswith(".txt"):
            raise ValueError("single_daily_text_required")
        if members[0].file_size > MAX_BYTES:
            raise ValueError("daily_file_too_large")
        with archive.open(members[0]) as member:
            text = member.read(MAX_BYTES + 1)
        if len(text) > MAX_BYTES:
            raise ValueError("daily_file_too_large")
        lines = text.decode("latin-1").splitlines()
        if len(lines) < 3 or lines[0][:2] != "00" or lines[-1][:2] != "99":
            raise ValueError("daily_header_or_trailer_missing")
        marker = any(
            "SYNTHETIC" in v.upper()
            for v in (original_name, members[0].filename, lines[0])
        )
        if nature == OBSERVED:
            if marker:
                raise ValueError("fixture_cannot_be_registered_as_observed")
            header, trailer = lines[0], lines[-1]
            if (
                len(header) != 245
                or len(trailer) != 245
                or not re.fullmatch(r"COTAHIST\.\d{4}", header[2:15])
                or header[15:23].strip() != "BOVESPA"
                or trailer[2:31] != header[2:31]
                or not trailer[31:42].isdigit()
                or int(trailer[31:42]) != len(lines)
            ):
                raise ValueError("incompatible_daily_origin_envelope")
            generated = old.iso_day(f"{header[23:27]}-{header[27:29]}-{header[29:31]}")
            if generated < day or header[11:15] != day[:4]:
                raise ValueError("generation_date_or_year_incompatible")
        coverage = dict.fromkeys(old.UNIVERSE, False)
        for line in lines[1:-1]:
            if len(line) != 245 or line[:2] != "01":
                raise ValueError("invalid_daily_record")
            record_day = old.iso_day(f"{line[2:6]}-{line[6:8]}-{line[8:10]}")
            if record_day <= "2026-10-13":
                raise ValueError("session_must_be_after_product_D0")
            if record_day != day:
                raise ValueError("daily_file_session_mismatch")
            ticker = line[12:24].strip()
            if ticker in coverage:
                if (line[10:12], line[24:27], line[52:56].strip(), line[210:217]) != (
                    "02",
                    "010",
                    "R$",
                    "0000001",
                ):
                    raise ValueError("incompatible_instrument_currency_or_quote_factor")
                isin = line[230:242]
                if not re.fullmatch(r"BR[A-Z0-9]{9}[0-9]", isin):
                    raise ValueError("invalid_brazilian_instrument_isin")
                coverage[ticker] = True
        return {
            "file_session": day,
            "record_count": len(lines) - 2,
            "instrument_present": coverage,
            "synthetic_marker": marker,
            "session_evidence": "DAILY_FILE_REPORT_NOT_GLOBAL_CALENDAR_PROOF",
            "instrument_trade_evidence": "PRESENCE_ONLY; POSITIVE_VOLUME_VALIDATED_AT_IMPORT",
        }


def verify_acquisition(record):
    b.check_seal(record)
    if (
        set(record)
        != {
            "schema_version",
            "identity",
            "acquisition_id",
            "nature",
            "official_activation",
            "original_name",
            "original_sha256",
            "source_url",
            "declared_session",
            "inspection",
            "operator",
            "statement",
            "recorded_at",
            "obtained_at_declared",
            "obtaining_evidence",
            "limits",
            "sha256",
        }
        or record["identity"] != IDENTITY
        or record["schema_version"] != 1
        or type(record["schema_version"]) is not int
        or record["nature"] not in (OBSERVED, SYNTHETIC)
        or record["official_activation"] is not False
        or record["inspection"]["file_session"] != record["declared_session"]
        or (record["nature"] == OBSERVED and record["inspection"]["synthetic_marker"])
    ):
        raise ValueError("acquisition_identity_or_classification_invalid")
    b.key(record["acquisition_id"])
    if old.iso_day(record["declared_session"]) <= "2026-10-13":
        raise ValueError("session_must_be_after_product_D0")
    recorded = old.instant(record["recorded_at"])
    if (
        record["obtained_at_declared"] is not None
        and old.instant(record["obtained_at_declared"]) > recorded
    ):
        raise ValueError("acquisition_time_in_future")
    if record["nature"] == OBSERVED:
        url = urlsplit(record["source_url"])
        if url.scheme != "https" or url.hostname not in (
            "www.b3.com.br",
            "b3.com.br",
            "bvmf.bmfbovespa.com.br",
        ):
            raise ValueError("declared_b3_url_required")
        if (
            record["declared_session"]
            > recorded.astimezone(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        ):
            raise ValueError("future_session_cannot_be_observed")
    if not record["operator"].strip() or not record["statement"].strip():
        raise ValueError("operator_and_obtaining_statement_required")
    return record


def write_json(path, value):
    path = storage(path)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(old.canonical_json(value) + "\n")


def register(
    root,
    cid,
    file,
    day,
    nature,
    operator,
    url,
    statement,
    *,
    obtained_at=None,
    receipt_file=None,
):
    root = storage(root)
    b.key(cid)
    if nature not in (OBSERVED, SYNTHETIC):
        raise ValueError("explicit_acquisition_nature_required")
    path = input_path(file)
    raw = bounded_read(path)
    calendar_session(calendar(), day)
    inspection = inspect_daily(raw, day, nature, path.name)
    receipt_bytes = bounded_read(input_path(receipt_file)) if receipt_file else None
    record = b.sealed(
        {
            "schema_version": 1,
            "identity": IDENTITY,
            "acquisition_id": cid,
            "nature": nature,
            "official_activation": False,
            "original_name": path.name,
            "original_sha256": hashlib.sha256(raw).hexdigest(),
            "source_url": url,
            "declared_session": day,
            "inspection": inspection,
            "operator": operator,
            "statement": statement,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "obtained_at_declared": obtained_at,
            "obtaining_evidence": {
                "kind": "LOCAL_ATTACHMENT_NOT_AUTHENTICATED"
                if receipt_bytes
                else "OPERATOR_DECLARATION_ONLY",
                "sha256": hashlib.sha256(receipt_bytes).hexdigest()
                if receipt_bytes
                else None,
            },
            "limits": "Local hashes/format/operator statement do not authenticate B3 or authorize redistribution. Header generation date is not download/publication time.",
        }
    )
    verify_acquisition(record)
    destination = storage(root / "acquisitions" / cid)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    with storage(destination / "original.zip").open("xb") as handle:
        handle.write(raw)
    if receipt_bytes is not None:
        with storage(destination / "obtaining-evidence.bin").open("xb") as handle:
            handle.write(receipt_bytes)
    # The record is the completion marker; interrupted directories are never reused.
    write_json(destination / "acquisition.json", record)
    return record


def acquisition(root, cid):
    b.key(cid)
    directory = storage(storage(root) / "acquisitions" / cid)
    record = verify_acquisition(
        old.load_json(storage(directory / "acquisition.json").read_bytes())
    )
    raw = bounded_read(storage(directory / "original.zip"))
    if (
        record["acquisition_id"] != cid
        or hashlib.sha256(raw).hexdigest() != record["original_sha256"]
        or inspect_daily(
            raw, record["declared_session"], record["nature"], record["original_name"]
        )
        != record["inspection"]
    ):
        raise ValueError("acquisition_original_or_inspection_mismatch")
    receipt_sha = record["obtaining_evidence"]["sha256"]
    if (
        receipt_sha is not None
        and hashlib.sha256(
            bounded_read(storage(directory / "obtaining-evidence.bin"))
        ).hexdigest()
        != receipt_sha
    ):
        raise ValueError("obtaining_evidence_hash_mismatch")
    return record, directory / "original.zip"


def parser_version():
    return {
        **old.parser_version(),
        "adapter": "PILOT_OBSERVED_COTAHIST_RAW_V1",
        **{
            name: b.sha_file(ROOT / name)
            for name in (
                "scripts/pilot_market_data.py",
                "scripts/pilot_observed_data.py",
                "scripts/pilot_paper.py",
            )
        },
    }


check_bars = bind(old.check_bars, calendar_session=calendar_session)


def check_source(source, value):
    check_calendar(value)
    record = verify_acquisition(source["acquisition_record"])
    expected = {
        "source": "B3_COTAHIST_DOCUMENTED"
        if record["nature"] == OBSERVED
        else "SYNTHETIC_COTAHIST_FIXTURE",
        "nature": record["nature"],
        "basis": "RAW",
        "currency": "BRL",
        "instrument": "B3_SPOT_STANDARD_LOT_010_02",
        "format": "COTAHIST_DAILY_245",
        "file_session": record["declared_session"],
        "acquisition_id": record["acquisition_id"],
        "acquisition_record": record,
        **(
            {"acquisition_registry_sha256": record["sha256"]}
            if record["nature"] == OBSERVED
            else {}
        ),
    }
    if source != expected:
        raise ValueError("observed_source_or_acquisition_mismatch")


def linked_acquisition(record, cid, file_sha=None):
    if cid != record["acquisition_id"] or (
        file_sha is not None and file_sha != record["original_sha256"]
    ):
        raise ValueError("acquisition_file_or_id_mismatch")
    return verify_acquisition(record)


def verified_importer(record):
    return bind(
        old.import_file,
        INPUT_OPTIONS=old.INPUT_OPTIONS | {"acquisition_record"},
        local_path=lambda path: storage(path)
        if Path(path).resolve().is_relative_to(BASE)
        else input_path(path),
        check_calendar=check_calendar,
        check_source=check_source,
        calendar_session=calendar_session,
        check_bars=check_bars,
        acquisition_record=lambda cid, sha=None: linked_acquisition(record, cid, sha),
        EVIDENCE_SHA=record["sha256"],
        parser_version=parser_version,
        verify_bundle=verify_bundle,
    )


def verify_bundle(bundle, *, at=None):
    source = bundle["content"]["source"]
    record = verify_acquisition(source["acquisition_record"])
    if (
        record["original_sha256"] != bundle["content"]["original_sha256"]
        or bundle["content"]["parser"] != parser_version()
    ):
        raise ValueError("acquisition_file_or_id_mismatch")
    verifier = bind(
        old.verify_bundle,
        check_calendar=check_calendar,
        check_source=check_source,
        check_bars=check_bars,
        parser_version=parser_version,
        acquisition_record=lambda cid, sha: linked_acquisition(record, cid, sha),
    )
    content = verifier(bundle, at=at)
    if old.instant(bundle["import"]["imported_at"]) < old.instant(record["recorded_at"]):
        raise ValueError("import_before_acquisition_record")
    return content


def import_bundle(root, cid, name, *, previous=None):
    root = storage(root)
    b.key(name)
    record, path = acquisition(root, cid)
    value = calendar()
    directory = storage(root / "bundles")
    # ponytail: scan the small local catalog O(n); a per-session immutable index
    # is the upgrade if this becomes a long-running acquisition service.
    same_session = [
        load_bundle(root, file.stem)
        for file in sorted(directory.glob("*.json"))
        if old.load_json(storage(file).read_bytes())["content"]["selection"]["sessions"]
        == [record["declared_session"]]
    ]
    if previous is None and any(
        bundle["content"]["original_sha256"] != record["original_sha256"]
        for bundle in same_session
    ):
        raise ValueError("changed_daily_file_requires_explicit_previous")
    manifest = {
        "schema_version": 1,
        "file": str(path),
        "file_sha256": record["original_sha256"],
        "source": "B3_COTAHIST_DOCUMENTED"
        if record["nature"] == OBSERVED
        else "SYNTHETIC_COTAHIST_FIXTURE",
        "nature": record["nature"],
        "basis": "RAW",
        "currency": "BRL",
        "instrument": "B3_SPOT_STANDARD_LOT_010_02",
        "format": "COTAHIST_DAILY_245",
        "file_session": record["declared_session"],
        "acquisition_id": cid,
        "acquisition_record": record,
    }
    with tempfile.TemporaryDirectory(prefix="hfl-observed-input-") as temporary:
        manifest_path = Path(temporary) / "input.json"
        manifest_path.write_text(old.canonical_json(manifest), encoding="utf-8")
        bundle = verified_importer(record)(
            manifest_path, calendar=value, sessions=[record["declared_session"]]
        )
    if previous is not None:
        prior = load_bundle(root, previous)
        if any(
            bundle["content"]["revision"] > prior["content"]["revision"]
            for bundle in same_session
        ):
            raise ValueError("previous_is_not_latest_revision")
        before, current = verify_bundle(prior), bundle["content"]
        if (
            any(before[k] != current[k] for k in ("selection", "calendar", "parser"))
            or before["source"]["nature"] != current["source"]["nature"]
        ):
            raise ValueError("revision_scope_mismatch")
        if before["original_sha256"] == current["original_sha256"]:
            bundle["content"] = before
        else:
            current.update(
                revision=before["revision"] + 1, revision_of=prior["content_sha256"]
            )
        bundle["content_sha256"] = old.digest(bundle["content"])
        bundle = b.sealed({k: v for k, v in bundle.items() if k != "sha256"})
    verify_bundle(bundle)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_json(directory / (name + ".json"), bundle)
    return bundle


def load_bundle(root, name):
    b.key(name)
    bundle = old.load_json(
        storage(storage(root) / "bundles" / (name + ".json")).read_bytes()
    )
    verify_bundle(bundle)
    return bundle


prices = bind(old.prices, verify_bundle=verify_bundle)


def observations(root):
    directory = storage(storage(root) / "acquisitions")
    if not directory.exists():
        return []
    return [
        {
            "acquisition_id": record["acquisition_id"],
            "nature": record["nature"],
            "evidence_sha256": record["sha256"],
            **record["inspection"],
        }
        for child in sorted(directory.iterdir())
        if child.is_dir()
        for record, _path in [acquisition(root, child.name)]
        if record["nature"] == OBSERVED
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("calendar", "register", "import", "query", "observations")
    )
    parser.add_argument("--root", type=Path, default=BASE / "pilot")
    parser.add_argument("--session")
    parser.add_argument("--id")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--nature", choices=(OBSERVED, SYNTHETIC))
    parser.add_argument("--operator")
    parser.add_argument("--url")
    parser.add_argument("--statement")
    parser.add_argument("--obtained-at")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--previous")
    parser.add_argument("--phase", choices=("OPEN", "CLOSE"))
    parser.add_argument("--at")
    args = parser.parse_args()
    try:
        if args.action == "calendar":
            value = calendar()
            result = (
                value
                if not args.session
                else {
                    "planned_session": calendar_session(value, args.session),
                    "next_planned_session": next_session(value, args.session),
                    "planned_D_plus_2": settlement_session(value, args.session),
                    "hours": hours(value, args.session),
                    "observed_sessions": observations(args.root),
                }
            )
        elif args.action == "observations":
            result = {"observations": observations(args.root)}
        elif args.action == "register":
            if not all(
                (
                    args.id,
                    args.file,
                    args.session,
                    args.nature,
                    args.operator,
                    args.url,
                    args.statement,
                )
            ):
                parser.error(
                    "register requires --id --file --session --nature --operator --url --statement"
                )
            result = register(
                args.root,
                args.id,
                args.file,
                args.session,
                args.nature,
                args.operator,
                args.url,
                args.statement,
                obtained_at=args.obtained_at,
                receipt_file=args.receipt,
            )
        elif args.action == "import":
            if not args.id or not args.name:
                parser.error("import requires --id and --name")
            bundle = import_bundle(args.root, args.id, args.name, previous=args.previous)
            result = {
                "status": "LOCAL_BUNDLE_VERIFIED",
                "nature": bundle["content"]["source"]["nature"],
                "content_sha256": bundle["content_sha256"],
                "revision": bundle["content"]["revision"],
                "available_at": bundle["import"]["available_at"],
            }
        else:
            if not all((args.name, args.session, args.phase, args.at)):
                parser.error("query requires --name --session --phase --at")
            bundle = load_bundle(args.root, args.name)
            result = {
                "nature": bundle["content"]["source"]["nature"],
                "session": args.session,
                "phase": args.phase,
                "prices": prices(bundle, args.session, args.phase, at=args.at),
            }
        print(
            old.canonical_json(
                {
                    "official_activation": False,
                    "financial_integration_ready": False,
                    "result": result,
                }
            )
        )
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        ArithmeticError,
        zipfile.BadZipFile,
    ) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
