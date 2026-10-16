"""DATA-01: local COTAHIST -> immutable RAW bundle; no feed or ledger writes.

Run: python -B scripts/pilot_market_data.py --help
Input manifest and synthetic calendar schemas: docs/PILOTO_MULTIATIVOS_SPEC.md.
"""

import argparse
import hashlib
import io
import json
import sys
import tempfile
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

from src.artifacts import canonical_json  # noqa: E402
from src.pipeline.b3_official import read_cotahist  # noqa: E402
from src.pipeline.transform import validate_ohlcv  # noqa: E402

UNIVERSE = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
SOURCES = {
    "SYNTHETIC_COTAHIST_FIXTURE": "SYNTHETIC_TEST",
    "B3_COTAHIST_LOCAL": "REAL_UNVERIFIED",
    "B3_COTAHIST_DOCUMENTED": "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED",
}
OHLC = {"OPEN": "abertura", "HIGH": "maxima", "LOW": "minima", "CLOSE": "fechamento"}
EVIDENCE_ROOT = ROOT / "docs/evidence/pilot_market_data_2026"
EVIDENCE_SHA = "9f320be2884382635ba3fa4cea9597ccbca1470bbdfdf28abb8c9cb753003654"
SOURCE_FIELDS = {"source", "nature", "basis", "currency", "instrument"}
INPUT_OPTIONS = {"format", "file_session", "acquisition_id"}


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(raw):
    def unique(pairs):
        if len(pairs) != len(dict(pairs)):
            raise ValueError("duplicate_json_field")
        return dict(pairs)

    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def local_path(path):
    path = Path(path).resolve()
    if any(path.is_relative_to(ROOT / area) for area in ("data", "docs/evidence")):
        raise ValueError("protected_input_or_output_path")
    return path


def iso_day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("invalid_session_date")
    return value


def instant(value):
    if not isinstance(value, str):
        raise ValueError("timezone_required")
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("timezone_required")
    return result.astimezone(timezone.utc)


def parser_version():
    return {
        "adapter": "PILOT_COTAHIST_RAW_V2",
        **{
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("src/pipeline/b3_official.py", "src/pipeline/transform.py")
        },
    }


def source_evidence(root=EVIDENCE_ROOT):
    """Pinned capture + source bytes, not a caller's declaration of official origin."""
    # ponytail: O(total artifact bytes) per read; cache verified immutable captures if frequency grows.
    root = Path(root).resolve()
    raw = (root / "sources.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != EVIDENCE_SHA:
        raise ValueError("source_evidence_manifest_mismatch")
    evidence = load_json(raw)
    for name, record in evidence["documents"].items():
        path = (root / name).resolve()
        if path.parent != root:
            raise ValueError("invalid_evidence_path")
        for key in ("url", "final_url"):
            url = urlsplit(record[key])
            if url.scheme != "https" or url.hostname not in (
                "b3.com.br",
                "www.b3.com.br",
                "bvmf.bmfbovespa.com.br",
            ):
                raise ValueError("unknown_evidence_origin")
        instant(record["retrieved_at"])
        captured = path.read_bytes()
        if (
            len(captured) != record["bytes"]
            or hashlib.sha256(captured).hexdigest() != record["sha256"]
        ):
            raise ValueError("source_artifact_mismatch:" + name)
    return evidence


def acquisition_record(acquisition_id, file_sha=None):
    record = source_evidence()["acquisitions"].get(acquisition_id)
    if record is None:
        raise ValueError("acquisition_not_in_verified_registry")
    if file_sha is not None and record["file_sha256"] != file_sha:
        raise ValueError("acquisition_file_mismatch")
    return record


def prospective_calendar():
    body = {**source_evidence()["calendar"], "file_sha256": EVIDENCE_SHA}
    return {**body, "sha256": digest(body)}


def load_calendar(path=None):
    """Only the pinned calendar is verified; caller-supplied calendars are fixtures."""
    if str(path) == "b3-2026":
        result = prospective_calendar()
        check_calendar(result)
        return result
    if path is None:
        # Reuse the sealed coverage/hash check, never the rule-based extrapolation.
        from paper_ledger import CALENDAR_SHA, sessions

        body = {
            "nature": "VERIFIED_B3_SESSIONS",
            "source": "PINNED_B3_SESSION_LIST_2026",
            "file_sha256": CALENDAR_SHA,
            "sessions": list(sessions()),
        }
    else:
        raw = local_path(path).read_bytes()
        body = load_json(raw)
        if set(body) != {"nature", "source", "sessions"} or (
            body["nature"],
            body["source"],
        ) != ("SYNTHETIC_TEST", "SYNTHETIC_CALENDAR_NOT_OFFICIAL"):
            raise ValueError("synthetic_calendar_required")
        body["file_sha256"] = hashlib.sha256(raw).hexdigest()
    result = {**body, "sha256": digest(body)}
    check_calendar(result)
    return result


def check_calendar(calendar):
    if calendar.get("nature") == "B3_PUBLIC_CALENDAR_DOCUMENTATION":
        if calendar != prospective_calendar():
            raise ValueError("unverified_prospective_calendar")
        return calendar["sessions"]
    body = {k: v for k, v in calendar.items() if k != "sha256"}
    days = body["sessions"]
    if (
        set(body) != {"nature", "source", "sessions", "file_sha256"}
        or calendar["sha256"] != digest(body)
        or not isinstance(days, list)
        or not days
        or days != sorted({iso_day(day) for day in days})
    ):
        raise ValueError("invalid_calendar")
    if body["nature"] == "VERIFIED_B3_SESSIONS":
        from paper_ledger import CALENDAR_SHA, sessions

        if (
            body["source"] != "PINNED_B3_SESSION_LIST_2026"
            or body["file_sha256"] != CALENDAR_SHA
            or days != list(sessions())
        ):
            raise ValueError("unverified_calendar")
    elif (body["nature"], body["source"]) != (
        "SYNTHETIC_TEST",
        "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
    ):
        raise ValueError("unknown_calendar_source")
    return days


def calendar_session(calendar, day, offset=0):
    if type(offset) is not int or offset not in (0, 1, 2):
        raise ValueError("invalid_session_offset")
    days = check_calendar(calendar)
    if calendar["nature"] == "B3_PUBLIC_CALENDAR_DOCUMENTATION":
        if iso_day(day) in calendar["documented_closures"]:
            raise ValueError("documented_non_session:" + day)
        raise ValueError("prospective_positive_session_coverage_unproven:" + iso_day(day))
    if iso_day(day) not in days:
        raise ValueError("calendar_session_unavailable:" + day)
    index = days.index(day) + offset
    if index >= len(days):
        raise ValueError("calendar_coverage_insufficient")
    return days[index]


def next_session(calendar, day):
    return calendar_session(calendar, day, 1)


def settlement_session(calendar, day):
    return calendar_session(calendar, day, 2)


def check_source(source, calendar):
    if (
        not SOURCE_FIELDS <= set(source)
        or set(source) - SOURCE_FIELDS - INPUT_OPTIONS - {"acquisition_registry_sha256"}
        or (
            source["source"] not in SOURCES
            or source["nature"] != SOURCES[source["source"]]
            or source["basis"] != "RAW"
            or source["currency"] != "BRL"
            or source["instrument"] != "B3_SPOT_STANDARD_LOT_010_02"
        )
    ):
        raise ValueError("unknown_or_incompatible_source_basis_instrument")
    if ("format" in source) != ("file_session" in source):
        raise ValueError("daily_format_and_session_required_together")
    if "format" in source and (
        source["format"] != "COTAHIST_DAILY_245"
        or iso_day(source.get("file_session")) < "2026-10-13"
    ):
        raise ValueError("invalid_daily_format_or_session")
    if source["nature"] == "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED":
        if source.get("acquisition_registry_sha256") != EVIDENCE_SHA:
            raise ValueError("acquisition_registry_required")
        acquisition_record(source.get("acquisition_id"))
    elif {"acquisition_id", "acquisition_registry_sha256"} & set(source):
        raise ValueError("acquisition_cannot_promote_source_or_fixture")
    expected = (
        "SYNTHETIC_TEST"
        if source["nature"] == "SYNTHETIC_TEST"
        else "VERIFIED_B3_SESSIONS"
    )
    allowed = (
        {expected}
        if expected == "SYNTHETIC_TEST"
        else {expected, "B3_PUBLIC_CALENDAR_DOCUMENTATION"}
    )
    if calendar["nature"] not in allowed:
        raise ValueError("source_calendar_nature_mismatch")


def check_bars(bars, selection, calendar):
    tickers, days = selection["tickers"], selection["sessions"]
    if (
        not tickers
        or tickers != sorted(set(tickers))
        or set(tickers) - set(UNIVERSE)
        or not days
        or days != sorted(set(days))
    ):
        raise ValueError("invalid_selection")
    for day in days:
        calendar_session(calendar, day)
    expected = {(ticker, day) for ticker in tickers for day in days}
    keys = [(bar["ticker"], bar["session"]) for bar in bars]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate_or_conflicting_bar")
    if set(keys) != expected:
        raise ValueError("missing_or_unexpected_bar")
    if keys != sorted(keys):
        raise ValueError("bars_not_canonical")
    for ticker in tickers:
        rows = []
        for bar in (b for b in bars if b["ticker"] == ticker):
            if set(bar) not in (
                {"ticker", "session", "volume", *OHLC},
                {"ticker", "session", "volume", "isin", *OHLC},
            ):
                raise ValueError("invalid_bar_fields")
            if "isin" in bar and (
                len(bar["isin"]) != 12
                or not bar["isin"].isascii()
                or not bar["isin"].isalnum()
            ):
                raise ValueError("invalid_instrument_isin")
            for key in OHLC:
                price = bar[key]
                if (
                    not isinstance(price, str)
                    or not Decimal(price).is_finite()
                    or Decimal(price) <= 0
                ):
                    raise ValueError("invalid_price")
                if format(Decimal(price), ".2f") != price:
                    raise ValueError("price_must_be_canonical_cents")
            if (
                not isinstance(bar["volume"], str)
                or not bar["volume"].isdigit()
                or int(bar["volume"]) <= 0
            ):
                raise ValueError("session_without_trading")
            rows.append(
                {
                    **{v: float(bar[k]) for k, v in OHLC.items()},
                    "volume": float(bar["volume"]),
                }
            )
        validate_ohlcv(pd.DataFrame(rows, index=pd.DatetimeIndex(days)))


def verify_bundle(bundle, *, at=None):
    """Verify seals, schema, complete prices, calendar and temporal availability."""
    body = {k: v for k, v in bundle.items() if k != "sha256"}
    content, receipt = body["content"], body["import"]
    if (
        set(body) != {"content", "content_sha256", "import"}
        or bundle["sha256"] != digest(body)
        or body["content_sha256"] != digest(content)
        or set(content)
        != {
            "schema_version",
            "source",
            "selection",
            "original_sha256",
            "normalized_sha256",
            "parser",
            "calendar",
            "bars",
            "revision",
            "revision_of",
        }
        or type(content["schema_version"]) is not int
        or content["schema_version"] != 1
        or content["parser"]
        not in (
            parser_version(),
            {**parser_version(), "adapter": "PILOT_COTAHIST_RAW_V1"},
        )
        or content["normalized_sha256"] != digest(content["bars"])
        or type(content["revision"]) is not int
        or content["revision"] < 1
        or (content["revision"] == 1) != (content["revision_of"] is None)
    ):
        raise ValueError("bundle_integrity_or_version_failed")
    check_calendar(content["calendar"])
    check_source(content["source"], content["calendar"])
    check_bars(content["bars"], content["selection"], content["calendar"])
    if (
        content["source"]["nature"] != "SYNTHETIC_TEST"
        and min(content["selection"]["sessions"]) < "2026-10-13"
    ):
        raise ValueError("real_history_before_pilot_blocked")
    if content["source"].get("format") == "COTAHIST_DAILY_245" and (
        content["selection"]["sessions"] != [content["source"]["file_session"]]
        or any("isin" not in bar for bar in content["bars"])
    ):
        raise ValueError("daily_format_selection_or_instrument_mismatch")
    if content["source"]["nature"] == "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED":
        acquisition_record(
            content["source"]["acquisition_id"], content["original_sha256"]
        )
    available = instant(receipt["available_at"])
    if receipt[
        "availability_basis"
    ] != "IMPORT_TIME_CONSERVATIVE_BOUND" or available != instant(receipt["imported_at"]):
        raise ValueError("unproven_availability")
    if at is not None and instant(at) < available:
        raise ValueError("data_not_yet_available")
    return content


def import_file(manifest_path, *, calendar, sessions, tickers=UNIVERSE, previous=None):
    manifest_path = local_path(manifest_path)
    manifest_raw = manifest_path.read_bytes()
    manifest = load_json(manifest_raw)
    source = {k: manifest[k] for k in SOURCE_FIELDS}
    source.update({k: manifest[k] for k in INPUT_OPTIONS & set(manifest)})
    if (
        set(manifest) - SOURCE_FIELDS - INPUT_OPTIONS
        != {"schema_version", "file", "file_sha256"}
        or type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
    ):
        raise ValueError("invalid_input_manifest")
    if source["nature"] == "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED":
        source["acquisition_registry_sha256"] = EVIDENCE_SHA
    check_calendar(calendar)
    check_source(source, calendar)
    selection = {"sessions": sorted(set(sessions)), "tickers": sorted(set(tickers))}
    if (
        not selection["sessions"]
        or not selection["tickers"]
        or set(selection["tickers"]) - set(UNIVERSE)
    ):
        raise ValueError("invalid_selection")
    for day in selection["sessions"]:
        calendar_session(calendar, day)
    if source["nature"] != "SYNTHETIC_TEST" and min(selection["sessions"]) < "2026-10-13":
        raise ValueError("real_history_before_pilot_blocked")
    daily = source.get("format") == "COTAHIST_DAILY_245"
    if source["nature"] != "SYNTHETIC_TEST" and not daily:
        raise ValueError("real_input_requires_documented_daily_format")
    if daily and selection["sessions"] != [source["file_session"]]:
        raise ValueError("daily_file_selection_mismatch")
    path = local_path(manifest_path.parent / manifest["file"])
    # ponytail: snapshot ZIP in memory O(file size); immutable streaming spool if files outgrow RAM.
    raw = path.read_bytes()
    file_sha = hashlib.sha256(raw).hexdigest()
    if file_sha != manifest["file_sha256"]:
        raise ValueError("original_file_hash_mismatch")
    if source["nature"] == "ORIGIN_DOCUMENTED_NOT_AUTHENTICATED":
        acquisition_record(source["acquisition_id"], file_sha)
    volumes, isins = {}, {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != 1 or not names[0].lower().endswith(".txt"):
            raise ValueError("single_cotahist_text_member_required")
        with archive.open(names[0]) as member:
            for line in io.TextIOWrapper(member, encoding="latin-1"):
                if line[:2] != "01":
                    continue
                day = iso_day(f"{line[2:6]}-{line[6:8]}-{line[8:10]}")
                # Inspect dates for EVERY instrument before interpreting any price.
                if (daily or source["nature"] != "SYNTHETIC_TEST") and day < "2026-10-13":
                    raise ValueError("real_history_before_pilot_blocked")
                if daily and day != source["file_session"]:
                    raise ValueError("daily_file_session_mismatch")
                if line[12:24].strip() not in selection["tickers"]:
                    continue
                if day in selection["sessions"] and (
                    len(line.rstrip("\r\n")) != 245
                    or line[24:27] != "010"
                    or line[10:12] != "02"
                    or line[52:56].strip() != "R$"
                ):
                    raise ValueError("incompatible_cotahist_instrument_or_currency")
                if day in selection["sessions"]:
                    if daily:
                        isin = line[230:242].strip()
                        if (
                            line[210:217] != "0000001"
                            or len(isin) != 12
                            or not isin.isascii()
                            or not isin.isalnum()
                        ):
                            raise ValueError("unsupported_quote_factor_or_isin")
                        isins[line[12:24].strip(), day] = isin
                    # The reused parser represents volume as float; retain the exact integer.
                    volumes[line[12:24].strip(), day] = str(int(line[152:170]))
    bars = []
    with tempfile.TemporaryDirectory(prefix="hfl-pilot-input-") as temporary:
        frozen = Path(temporary) / "input.zip"
        frozen.write_bytes(raw)
        for ticker in selection["tickers"]:
            frame = read_cotahist(frozen, ticker)
            if frame.empty:
                raise ValueError("missing_required_instrument:" + ticker)
            frame = frame.loc[
                frame.index.strftime("%Y-%m-%d").isin(selection["sessions"])
            ]
            validate_ohlcv(frame)
            for day, row in frame.iterrows():
                bars.append(
                    {
                        "ticker": ticker,
                        "session": day.date().isoformat(),
                        **{
                            key: format(Decimal(str(row[column])), ".2f")
                            for key, column in OHLC.items()
                        },
                        "volume": volumes[ticker, day.date().isoformat()],
                        **(
                            {"isin": isins[ticker, day.date().isoformat()]}
                            if daily
                            else {}
                        ),
                    }
                )
    check_bars(bars, selection, calendar)
    content = {
        "schema_version": 1,
        "source": source,
        "selection": selection,
        "original_sha256": file_sha,
        "normalized_sha256": digest(bars),
        "parser": parser_version(),
        "calendar": calendar,
        "bars": bars,
        "revision": 1,
        "revision_of": None,
    }
    if previous is not None:
        old = verify_bundle(previous)
        if any(
            old[k] != content[k] for k in ("source", "selection", "calendar", "parser")
        ):
            raise ValueError("revision_scope_mismatch")
        if old["original_sha256"] == file_sha:
            content = old
        else:
            content.update(
                revision=old["revision"] + 1, revision_of=previous["content_sha256"]
            )
    imported_at = datetime.now(timezone.utc).isoformat()
    body = {
        "content": content,
        "content_sha256": digest(content),
        "import": {
            "imported_at": imported_at,
            "available_at": imported_at,
            "availability_basis": "IMPORT_TIME_CONSERVATIVE_BOUND",
            "manifest_path": str(manifest_path),
            "original_path": str(path),
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        },
    }
    bundle = {**body, "sha256": digest(body)}
    verify_bundle(bundle)
    return bundle


def prices(bundle, day, price_type, *, at):
    instant(at)
    if price_type not in ("OPEN", "CLOSE"):
        raise ValueError("price_type_must_be_OPEN_or_CLOSE")
    content = verify_bundle(bundle, at=at)
    if day not in content["selection"]["sessions"]:
        raise ValueError("price_session_not_imported")
    return {
        bar["ticker"]: bar[price_type] for bar in content["bars"] if bar["session"] == day
    }


def write_bundle(path, bundle):
    verify_bundle(bundle)
    with local_path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(bundle) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True, help="local JSON manifest pointing to a ZIP"
    )
    parser.add_argument("--session", action="append", required=True)
    parser.add_argument(
        "--ticker", action="append", help="default: all five pilot tickers"
    )
    parser.add_argument(
        "--calendar",
        type=Path,
        help="synthetic JSON, or b3-2026 (documented but positive coverage blocked); omit for historical coverage",
    )
    parser.add_argument(
        "--previous", type=Path, help="previous bundle for explicit correction/reimport"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="new file; never overwritten"
    )
    args = parser.parse_args(argv)
    try:
        previous = (
            load_json(local_path(args.previous).read_bytes()) if args.previous else None
        )
        bundle = import_file(
            args.input,
            calendar=load_calendar(args.calendar),
            sessions=args.session,
            tickers=args.ticker or UNIVERSE,
            previous=previous,
        )
        write_bundle(args.output, bundle)
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        ArithmeticError,
        zipfile.BadZipFile,
    ) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "LOCAL_BUNDLE_VERIFIED",
                "nature": bundle["content"]["source"]["nature"],
                "content_sha256": bundle["content_sha256"],
                "revision": bundle["content"]["revision"],
                "official_ingestion_ready": False,
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
