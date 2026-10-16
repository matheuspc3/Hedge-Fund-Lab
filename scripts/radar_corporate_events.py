"""Radar data normalization for B3 bonificações, plus read-only diagnosis.

Root cause of the ITUB4 block (V7.1 diagnosis): with ``auto_adjust=False``
yfinance still back-adjusts ``Close`` for splits, and Yahoo books a B3
bonificação as a split (ITUB4: 1.03 on 2025-12-26, 1.10 on 2025-03-18).
COTAHIST is nominal, so ``Close(yf) / fechamento`` is 1/1.03 before the
ex-date and the original guard in ``src/pipeline/b3_official.py`` refuses it.

This extractor restores yfinance's nominal ``Close`` only for share-count events
that B3 confirms as a bonificação on the very same session (ESPECI ex-marker with
"B" and a new distribution number, DISMES), checks both boundary sessions, and
then applies the original checks with the original tolerances. Desdobramentos,
grupamentos or events without that confirmation stay blocked, as before.
``Adj Close`` is untouched, so ``Adj Close / Close`` becomes the total-return
factor including the event; raw nominal bars and volume are never changed.

``install()`` makes this the Radar default extractor in the calling process. The
UI server calls it at startup and ``prepare`` below calls it before the very same
``radar.prepare`` call that the Radar API worker makes: one preparation path.

Commands (PowerShell, project root):
  diagnose  read-only: network read of yfinance + local COTAHIST, stdout JSON
  prepare   WRITES Radar inputs (new folders only), last_prepare.json and the
            current-year COTAHIST cache of that root; never calls Gemini.
            Same effect as the "Preparar dados" button of /radar.
"""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiasset_radar as radar

from src.pipeline.b3_official import (
    FACTOR_NEIGHBOR_TOLERANCE,
    SPLIT_GUARD_TOLERANCE,
    read_cotahist,
)
from src.pipeline.transform import validate_ohlcv

NAME = "RADAR_CORPORATE_EVENTS_V2"
#: The sealed V4 extractor, captured before any ``install()``.
ORIGINAL = radar.RadarExtractor


def b3_markers(path, symbol):
    """Official ESPECI and DISMES per session (standard lot, cash market)."""
    rows = {}
    with zipfile.ZipFile(path) as archive, archive.open(archive.namelist()[0]) as handle:
        for line in io.TextIOWrapper(handle, encoding="latin-1"):
            if (
                line[:2] == "01"
                and line[24:27] == "010"
                and line[10:12] == "02"
                and line[12:24].strip() == symbol
            ):
                day = pd.Timestamp(f"{line[2:6]}-{line[6:8]}-{line[8:10]}")
                rows[day] = {
                    "especi": " ".join(line[39:49].split()),
                    "dismes": line[242:245],
                }
    return rows


def year_ratio(close, raw):
    both = close.reindex(raw.index).dropna()
    ratio = (both / raw.loc[both.index, "fechamento"]).groupby(both.index.year).median()
    return {int(k): float(v) for k, v in ratio.items()}


def bonus_marker(especi):
    """B3 ex-marker (second ESPECI token, e.g. EB, EDB, EJB) announcing a bonificação."""
    tokens = especi.split()
    return len(tokens) > 1 and tokens[1].startswith("E") and "B" in tokens[1][1:]


class CorporateEventExtractor(ORIGINAL):
    def __init__(self, cache_dir):
        super().__init__(cache_dir=cache_dir)
        self.events, self.checks, self.current = {}, {}, None

    def download(self, ticker, start, end):
        # Mirrors B3OfficialAdjustedExtractor.download; the only difference is the
        # B3-corroborated restoration of yfinance's nominal Close before the guard.
        self.current = ticker
        first, last = self._parse_interval(start, end)
        symbol = ticker.removesuffix(".SA")
        years = range(first.year, last.year + 1)
        raw = pd.concat([read_cotahist(self._cotahist(year), symbol) for year in years])
        raw = raw.loc[(raw.index >= first) & (raw.index <= last)]
        raw = raw[raw["volume"] > 0]
        if raw.empty:
            raise ValueError(f"no official B3 bars for {symbol} in {start}..{end}")

        yahoo = yf.download(
            ticker,
            start=first.strftime("%Y-%m-%d"),
            end=(last + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
            actions=True,
        )
        if isinstance(yahoo.columns, pd.MultiIndex):
            yahoo.columns = [column[0] for column in yahoo.columns]
        yahoo = yahoo[(yahoo["Volume"] > 0) & (yahoo["Close"] > 0)]
        splits = yahoo.get("Stock Splits", pd.Series(dtype=float))
        splits = splits[(splits > 0) & (splits != 1) & (splits.index > raw.index[0])]
        check = {"ratio_before": year_ratio(yahoo["Close"], raw), "events": []}
        self.checks[ticker] = check

        nominal = yahoo["Close"].copy()
        if len(splits):
            markers = {}
            for year in years:
                markers.update(b3_markers(self._cotahist(year), symbol))
            # Latest first: an earlier boundary is checked with every later event restored.
            for day, ratio in sorted(splits.items(), reverse=True):
                before = raw.index[raw.index < day]
                if day not in raw.index or not len(before):
                    raise ValueError(f"corporate event {day.date()} not a B3 session")
                prior, mark = markers.get(before[-1]), markers.get(day)
                if not prior or not mark or prior["dismes"] == mark["dismes"]:
                    raise ValueError(
                        f"corporate event {day.date()} not corroborated by B3 DISMES"
                    )
                if not bonus_marker(mark["especi"]) or ratio <= 1:
                    raise ValueError(
                        f"corporate event {day.date()} not a B3-confirmed bonificação"
                    )
                nominal.loc[nominal.index < day] *= float(ratio)
                check["events"].append(
                    {
                        "ex_date": str(day.date()),
                        "type": "BONIFICACAO",
                        "yfinance_split_ratio": float(ratio),
                        "price_factor_before_ex_date": 1 / float(ratio),
                        "b3_especi": mark["especi"],
                        "b3_dismes": [prior["dismes"], mark["dismes"]],
                        "b3_close": [
                            float(raw.loc[before[-1], "fechamento"]),
                            float(raw.loc[day, "fechamento"]),
                        ],
                    }
                )
                # The event date itself must line up, not only the yearly median.
                for edge in (before[-1], day):
                    value = nominal.get(edge)
                    if (
                        value is None
                        or not np.isfinite(value)
                        or abs(value / raw.loc[edge, "fechamento"] - 1)
                        > SPLIT_GUARD_TOLERANCE
                    ):
                        raise ValueError(
                            f"corporate event boundary mismatch at {edge.date()}"
                        )
        check["events"].sort(key=lambda e: e["ex_date"])
        self.events[ticker] = check["events"]

        check["ratio_after"] = year_ratio(nominal, raw)
        ratio = pd.Series(check["ratio_after"], dtype=float)
        if (ratio - 1).abs().max() > SPLIT_GUARD_TOLERANCE:
            raise ValueError(
                f"split-like mismatch between yfinance and B3 closes: {check['ratio_after']}"
            )
        factor = (yahoo["Adj Close"] / nominal).reindex(raw.index)

        inherited = []
        values = factor.to_numpy(copy=True)
        for i in np.flatnonzero(np.isnan(values)):
            if (
                i == 0
                or i == len(values) - 1
                or np.isnan(values[i - 1])
                or np.isnan(values[i + 1])
            ):
                raise ValueError(f"no adjustment factor around {raw.index[i].date()}")
            if abs(values[i - 1] / values[i + 1] - 1) > FACTOR_NEIGHBOR_TOLERANCE:
                raise ValueError(
                    f"adjustment factor changes around {raw.index[i].date()}; "
                    "a corporate event there makes inheritance unsafe"
                )
            values[i] = values[i - 1]
            inherited.append(str(raw.index[i].date()))
        self.inherited_factors[ticker] = inherited

        frame = raw.copy()
        for column in ("abertura", "maxima", "minima", "fechamento"):
            frame[column] = raw[column] * values
        frame.index.name = "Date"
        validate_ohlcv(frame)
        return frame

    def source_description(self):
        # Per-ticker provenance, as when the original prepare builds one extractor per ticker.
        source = super().source_description()
        return {
            **source,
            "inherited_factors": {
                self.current: self.inherited_factors.get(self.current, [])
            },
            "corporate_events": {
                "normalization": NAME,
                "rule": "yfinance split restored to nominal Close only for a B3 bonificação: ESPECI ex-marker with B and DISMES change on the ex-date",
                "module_sha256": radar.sha_file(Path(__file__)),
                "events": self.events.get(self.current, []),
            },
        }


def install():
    """Make the normalizer the Radar default extractor in this process (idempotent)."""
    # ponytail: rebinds one module global because the sealed radar_api cannot pass
    # extractor=. Ceiling: every in-process caller of radar.RadarExtractor gets it;
    # upgrade path: an explicit extractor parameter when radar_api is next resealed.
    radar.RadarExtractor = CorporateEventExtractor


def diagnose(values, day, cache):
    """Read-only qualification of each ticker; compares with prepared official inputs."""
    end = radar.session(day)
    first = end - pd.Timedelta(days=450)
    extractor = CorporateEventExtractor(cache_dir=str(cache.parent))
    extractor.paths = {end.year: cache}  # local file only: no COTAHIST download
    extractor.files[cache.name] = radar.sha_file(cache)
    report = {
        "identity": NAME,
        "session": str(end.date()),
        "read_only": True,
        "radar_manifest_sha256": radar.digest(radar.manifest("live")),
        "items": [],
    }
    for ticker in radar.tickers(values, empty=False):
        item = {"ticker": ticker}
        try:
            bars = extractor.download(ticker + ".SA", str(first.date()), str(end.date()))
            item.update(extractor.checks.get(ticker + ".SA", {}))
            features, metrics = radar.technical_input(bars)
            csv = bars.to_csv(lineterminator="\n").encode()
            official = radar.OUTPUT / "analyses" / ticker / str(end.date()) / "input.json"
            existing = radar.read(official) if official.exists() else None
            original = ORIGINAL(cache_dir=str(cache.parent))
            original.paths = extractor.paths
            try:
                same = original.download(
                    ticker + ".SA", str(first.date()), str(end.date())
                ).equals(bars)
            except ValueError as exc:
                same = "ORIGINAL_BLOCKS: " + str(exc)
            item.update(
                status="ELIGIBLE" if bars.index[-1] == end else "NO_TRADING_ON_SESSION",
                last_session=str(bars.index[-1].date()),
                bars=len(bars),
                history_start=str(bars.index[0].date()),
                minimum_history=radar.MIN_HISTORY,
                features=len(features),
                risk_metrics=metrics,
                bars_sha256=hashlib.sha256(csv).hexdigest(),
                inherited_factors=extractor.inherited_factors.get(ticker + ".SA", []),
                original_extractor_identical_bars=same,
                official_input=None
                if existing is None
                else {
                    "bars_sha256": existing["history"]["sha256"],
                    "identical_bars": existing["history"]["sha256"]
                    == hashlib.sha256(csv).hexdigest(),
                    "features_identical": existing["features"] == features,
                    # Provider revisions of Adj Close show up here, not in the logic.
                    "max_relative_close_difference": float(
                        (
                            pd.read_csv(
                                official.with_name("bars.csv"),
                                index_col=0,
                                parse_dates=True,
                                float_precision="round_trip",
                            )["fechamento"]
                            / bars["fechamento"]
                            - 1
                        )
                        .abs()
                        .max()
                    ),
                    "prepared_at": existing["prepared_at"],
                },
            )
        except (ValueError, KeyError, OSError) as exc:
            item.update(extractor.checks.get(ticker + ".SA", {}))
            item.update(status="BLOCKED", error=type(exc).__name__ + ": " + str(exc))
        report["items"].append(item)
    report["cotahist_sha256"] = dict(sorted(extractor.files.items()))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("diagnose", "prepare"))
    parser.add_argument("--tickers", nargs="*", default=list(radar.EXAMPLES))
    parser.add_argument("--session", required=True)
    parser.add_argument("--root", type=Path, default=radar.OUTPUT)
    parser.add_argument("--mode", choices=("live", "synthetic"), default="live")
    parser.add_argument(
        "--cotahist",
        type=Path,
        default=radar.OUTPUT / "cotahist/COTAHIST_A2026.ZIP",
        help="diagnose only: existing local current-year file",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.command == "diagnose":
        result = diagnose(args.tickers, args.session, args.cotahist)
    else:
        install()  # then exactly the Radar API worker call
        result = radar.prepare(args.tickers, args.root, end=args.session, mode=args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    items = result["items"] if isinstance(result, dict) else result
    if any(i.get("status") == "BLOCKED" for i in items):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
