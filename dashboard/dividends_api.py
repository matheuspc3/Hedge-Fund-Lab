"""DP-30 proventos: B3 official cash dividends of the 5 assets, kept as sealed snapshots.

Source: B3 "sistemaswebb3-listados" GetListedSupplementCompany (one call per issuer,
about the last 12 months, with data-com, payment date and ISIN per share class).
One immutable sealed JSON per fetch whose events changed + a mutable latest pointer:
<market base>/dividends/<TICKER>/<sha256>.json and latest.json.
"""

import base64
import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import market_base_api as base

b, radar = base.b, base.radar
IDENTITY = "HFL-DIVIDENDS-B3-V1"
SOURCE = "B3 — proventos em dinheiro"
URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
    "GetListedSupplementCompany/"
)
KINDS = {"DIVIDENDO": "DIVIDENDO", "JRS CAP PROPRIO": "JCP"}
JCP_NET = Decimal("0.85")  # ponytail: flat 15% IR, no exempt holders or other rates
# ISIN[6:11] of the tracked class: ON = ACNOR, PN = ACNPR (BBAS also lists A04/A05
# instruments that are not the ticker's share). ponytail: no units (11) / other classes.
CLASSES = {"3": "ACNOR", "4": "ACNPR"}


def folder(ticker):
    return base.ROOT / "dividends" / b.ticker(ticker)


def day(text):
    return datetime.strptime(text, "%d/%m/%Y").date().isoformat()


def normalize(raw, ticker):
    """B3 bytes -> sorted events of that ticker's share class. Anything odd raises."""
    issuer, shape = ticker[:4], CLASSES[ticker[4]]
    data = json.loads(raw)
    company = [c for c in data if isinstance(c, dict) and c.get("code") == issuer]
    if len(company) != 1 or not isinstance(company[0].get("cashDividends"), list):
        raise ValueError("dividends_unexpected_shape")
    events = []
    for r in company[0]["cashDividends"]:
        isin = r["isinCode"]
        if not isinstance(isin, str) or isin[:6] != "BR" + issuer:
            raise ValueError("dividends_isin_mismatch")
        if isin[6:11] != shape:
            continue  # another share class / instrument
        try:
            value = Decimal(r["rate"].replace(".", "").replace(",", "."))
            paid = r["paymentDate"].strip()
            approved = r["approvedOn"].strip()
            event = {
                "ticker": ticker,
                "kind": KINDS.get(r["label"], "OUTRO"),
                "label": r["label"],
                "data_com": day(r["lastDatePrior"]),
                "payment_date": day(paid) if paid else None,
                "value_per_share": format(value.normalize(), "f"),
                "approved_on": day(approved) if approved else None,
            }
        except (ValueError, InvalidOperation, AttributeError, TypeError) as e:
            raise ValueError(f"dividends_invalid_record: {e}") from e
        if not value.is_finite() or value <= 0:
            raise ValueError("dividends_value_not_positive")
        if event["payment_date"] and event["payment_date"] < event["data_com"]:
            raise ValueError("dividends_payment_before_data_com")
        events.append(event)
    return sorted(
        events,
        key=lambda e: (
            e["data_com"],
            e["payment_date"] or "9",
            e["kind"],
            e["value_per_share"],
        ),
    )


def snapshot(ticker):
    """Latest verified snapshot or None."""
    pointer = folder(ticker) / "latest.json"
    if not pointer.exists():
        return None
    key = b.check_seal(radar.read(pointer))["snapshot"]
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
        raise ValueError("invalid_dividends_snapshot")
    record = b.check_seal(radar.read(folder(ticker) / (key + ".json")))
    if (
        record["sha256"] != key
        or record["ticker"] != ticker
        or record["identity"] != IDENTITY
    ):
        raise ValueError("dividends_snapshot_identity_mismatch")
    return record


def events(ticker):
    return (snapshot(ticker) or {}).get("events", [])


def fetched_at(tickers):
    return max((s["fetched_at"] for t in tickers if (s := snapshot(t))), default=None)


def refresh(ticker, fetch):
    payload = base64.b64encode(
        json.dumps(
            {"issuingCompany": ticker[:4], "language": "pt-br"}, separators=(",", ":")
        ).encode()
    ).decode()
    url = URL + payload
    raw = fetch(url)
    if raw is None:
        return "NOT_PUBLISHED"
    found = normalize(raw, ticker)
    if snapshot(ticker) and snapshot(ticker)["events"] == found:
        return "UNCHANGED"  # no daily duplicate files
    record = b.sealed(
        {
            "identity": IDENTITY,
            "ticker": ticker,
            "url": url,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "fetched_at": radar.now().isoformat(),
            "events": found,
        }
    )
    radar.write(folder(ticker) / (record["sha256"] + ".json"), record, immutable=True)
    radar.write(folder(ticker) / "latest.json", b.sealed({"snapshot": record["sha256"]}))
    return "WRITTEN"


def update(fetch=None):
    fetch = fetch or base.fetch_http
    out = {}
    for ticker in base.TICKERS:
        try:  # one bad issuer never aborts the others
            out[ticker] = refresh(ticker, fetch)
        except Exception as e:
            out[ticker] = f"FAILED: {type(e).__name__}: {e}"
    return out


def entitlements(wallet, today):
    """Per event of a held ticker: quantity at the end of the data-com session."""
    import portfolio_history_api as hist  # circular: it reports these numbers

    held = {t["ticker"] for t in wallet["trades"]}
    quantity = {}

    def qty(ticker, at):
        if (at, ticker) not in quantity:
            positions = hist.historical_wallet(wallet, at)["positions"]
            quantity[at, ticker] = sum(
                (b.dec(p["quantity"]) for p in positions if p["ticker"] == ticker), b.ZERO
            )
        return quantity[at, ticker]

    out = []
    for ticker in sorted(held):
        for e in events(ticker):
            if e["data_com"] < wallet["start_date"]:
                continue
            estimate = e["data_com"] > today
            q = qty(ticker, today if estimate else e["data_com"])
            if q == 0:
                continue
            value = b.dec(e["value_per_share"])
            net = q * value * (JCP_NET if e["kind"] == "JCP" else 1)
            paid = e["payment_date"]
            state = (
                "PREVISTO"
                if estimate
                else "RECEBIDO"
                if paid and paid <= today
                else "A_RECEBER"
            )
            out.append(
                {
                    **{
                        k: e[k]
                        for k in ("ticker", "kind", "label", "data_com", "payment_date")
                    },
                    "value_per_share": e["value_per_share"],
                    "quantity": str(q),
                    "gross": str(b.money(q * value)),
                    "net": str(b.money(net)),
                    "state": state,
                    "estimate": estimate,
                }
            )
    return out


def booked(wallet):
    """Keys of the DIVIDEND ledger entries already in the wallet."""
    return {
        (d["ticker"], d["data_com"], d["payment_date"], d["kind"])
        for d in wallet["dividends"]
    }


def total(items, state):
    return str(
        b.money(sum((b.dec(e["net"]) for e in items if e["state"] == state), b.ZERO))
    )


def on(items, session):
    """(received, receivable) net amounts as of a session; data-com <= session only."""
    got = [e for e in items if e["data_com"] <= session]
    paid = lambda e: e["payment_date"] and e["payment_date"] <= session  # noqa: E731
    return (
        b.money(sum((b.dec(e["net"]) for e in got if paid(e)), b.ZERO)),
        b.money(sum((b.dec(e["net"]) for e in got if not paid(e)), b.ZERO)),
    )


def book_received(today, wallets=None):
    """DP-30 A: book every RECEBIDO event not yet in each wallet's ledger (idempotent)."""
    import manual_portfolio_api as manual  # circular like entitlements

    entries = []
    if wallets is None:
        # Rule histories must catch up before determining historical entitlements.
        wallets = [
            w
            for w in (manual.get({})["wallets"] if manual.path().exists() else [])
            if w.get("strategy") not in manual.RULE_STRATEGIES
        ]
    for wallet in wallets:
        done = booked(wallet)
        for e in entitlements(wallet, today):
            if (
                e["state"] != "RECEBIDO"
                or (e["ticker"], e["data_com"], e["payment_date"], e["kind"]) in done
            ):
                continue
            snap = snapshot(e["ticker"])
            entries.append(
                (
                    manual.request(
                        {
                            "kind": "DIVIDEND",
                            "wallet": wallet["id"],
                            "dividend": {
                                k: e[k]
                                for k in (
                                    "ticker",
                                    "kind",
                                    "data_com",
                                    "payment_date",
                                    "quantity",
                                    "gross",
                                    "net",
                                )
                            },
                        }
                    ),
                    {"snapshot_sha256": snap["sha256"], "url": snap["url"]},
                )
            )
    return manual.book_dividends(entries)
