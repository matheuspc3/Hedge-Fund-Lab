"""Offline V7.2: one normalized Radar preparation path for the UI and the CLI.

Fake nominal COTAHIST (with B3 ESPECI/DISMES markers) and a fake yfinance that
follows Yahoo's convention (Close back-adjusted for splits). No network, no Gemini.
"""

import http.client
import json
import socket
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import check_preservation as lifecycle  # noqa: E402
import multiasset_global_pm as pm  # noqa: E402
import multiasset_radar as radar  # noqa: E402
import platform_api  # noqa: E402
import radar_api  # noqa: E402
import radar_corporate_events as rce  # noqa: E402
import server  # noqa: E402

from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

DAY = "2026-10-09"
TICKERS = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
SESSIONS = radar.synthetic_bars(pd.Timestamp(DAY)).index  # 260 real B3 sessions
EX, EX2 = SESSIONS[150], SESSIONS[60]
ITUB4_BONUS = {"ITUB4": [(EX, 1.03, "EB")]}
CONNECT = socket.create_connection


def nominal(ticker):
    """Official nominal bars; BBAS3 alternates ±4%/day (21d volatility ≈ 0.63)."""
    if ticker == "BBAS3":
        close = 30 * np.cumprod(1 + 0.04 * np.where(np.arange(len(SESSIONS)) % 2, 1, -1))
        bars = pd.DataFrame(
            {
                "abertura": close * 0.999,
                "maxima": close * 1.01,
                "minima": close * 0.99,
                "fechamento": close,
                "volume": np.full(len(SESSIONS), 1e6),
            },
            index=SESSIONS,
        )
    else:
        index = TICKERS.index(ticker) if ticker in TICKERS else 0
        bars = radar.synthetic_bars(pd.Timestamp(DAY), index)
    return bars.round(2)


def market(folder, events=None, missing=None):
    """COTAHIST 2025/2026 zips: ex-marker on each ex-date, DISMES +1 per event."""
    events, missing = events or {}, missing or {}
    folder.mkdir(parents=True, exist_ok=True)
    body = {2025: "00HEADER\n", 2026: "00HEADER\n"}
    cents = lambda v: f"{round(v * 100):013d}"  # noqa: E731
    for ticker in sorted(set(TICKERS) | set(events)):
        own = events.get(ticker, [])
        for day, row in nominal(ticker).iterrows():
            if day in missing.get(ticker, []):
                continue
            marker = next((m for ex, _, m in own if ex == day), "")
            text = "01" + day.strftime("%Y%m%d") + "02" + ticker.ljust(12) + "010"
            text = text.ljust(39) + f"PN  {marker:<4}N1"
            text = text.ljust(56) + "".join(
                cents(row[k]) for k in ("abertura", "maxima", "minima", "fechamento")
            )
            text = text.ljust(108) + cents(row["fechamento"])
            text = text.ljust(152) + f"{int(row['volume']):018d}"
            body[day.year] += (
                text.ljust(242) + f"{100 + sum(ex <= day for ex, _, _ in own):03d}\n"
            )
    paths = {}
    for year, text in body.items():
        paths[year] = folder / f"COTAHIST_A{year}.ZIP"
        with zipfile.ZipFile(paths[year], "w") as archive:
            archive.writestr(f"COTAHIST_A{year}.TXT", text.encode("latin-1"))
    return paths


def consistent(events):
    """Yahoo book entries matching B3: (Close step date, booked date, step, booked ratio)."""
    return {t: [(ex, ex, r, r) for ex, r, _ in evs] for t, evs in events.items()}


def yahoo(book):
    def download(ticker, *args, **kwargs):
        symbol = ticker.removesuffix(".SA")
        close = nominal(symbol)["fechamento"].copy()
        splits = pd.Series(0.0, index=close.index)
        for step, booked, ratio, booked_ratio in book.get(symbol, []):
            close[close.index < step] /= ratio
            if booked is not None:
                splits[booked] = booked_ratio
        return pd.DataFrame(
            {
                "Close": close,
                "Adj Close": close * 0.98,
                "Volume": 1e6,
                "Stock Splits": splits,
            }
        )

    return download


def fake(base, paths):
    """Same class, preset local COTAHIST instead of the B3 download."""

    class Fake(base):
        def __init__(self, cache_dir):
            super().__init__(cache_dir=cache_dir)
            self.paths = dict(paths)

    return Fake


@pytest.fixture
def lab(tmp_path, monkeypatch):
    """Isolated official-like root wired as the UI process would be after install()."""

    def build(events=None, book=None, missing=None):
        paths = market(tmp_path / "b3", events, missing)
        monkeypatch.setattr(
            rce.yf, "download", yahoo(consistent(events or {}) if book is None else book)
        )
        monkeypatch.setattr(
            radar, "RadarExtractor", radar.RadarExtractor
        )  # restored after test
        monkeypatch.setattr(
            rce, "CorporateEventExtractor", fake(rce.CorporateEventExtractor, paths)
        )
        build.original = fake(rce.ORIGINAL, paths)
        return tmp_path / "data/radar/hfl_multiasset_v1"

    with no_network():
        yield build


def lab_download(ticker="ITUB4"):
    extractor = rce.CorporateEventExtractor(cache_dir="unused-cache")
    return extractor, extractor.download(ticker + ".SA", "2025-07-16", DAY)


def api_prepare(root, tickers, monkeypatch):
    rce.install()
    monkeypatch.setattr(radar_api, "ROOT", root)
    radar_api.post("prepare", {"tickers": list(tickers), "session": DAY, "mode": "live"})
    deadline = time.monotonic() + 60
    while radar_api.ACTIVE and time.monotonic() < deadline:
        time.sleep(0.02)
    assert radar.read(root / "job.json")["status"] == "COMPLETED"
    return {i["ticker"]: i for i in radar.read(root / "last_prepare.json")["items"]}


def cli_prepare(root, tickers, monkeypatch, capsys):
    argv = ["radar_corporate_events.py", "prepare", "--session", DAY, "--root", str(root)]
    monkeypatch.setattr(sys, "argv", [*argv, "--tickers", *tickers])
    try:
        rce.main()
    except SystemExit as exc:
        assert exc.code == 1  # some ticker blocked
    return {i["ticker"]: i for i in json.loads(capsys.readouterr().out)}


def tree(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.suffix != ".lock"
    }


def readiness(root, monkeypatch, tickers=TICKERS):
    monkeypatch.setattr(platform_api.global_api, "OFFICIAL_RADAR", root)
    return platform_api.radar_readiness(DAY, list(tickers), root)


# Normalizer -------------------------------------------------------------------


def test_install_is_the_ui_startup_path(monkeypatch):
    monkeypatch.setattr(radar, "RadarExtractor", radar.RadarExtractor)
    assert radar.RadarExtractor is rce.ORIGINAL  # importing the server changes nothing

    class Stop(server.ReusableTCPServer):
        def __init__(self, *args):
            pass

        def __exit__(self, *args):
            pass

        def serve_forever(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(server, "ReusableTCPServer", Stop)
    monkeypatch.setattr(sys, "argv", ["server.py", "0"])
    # The socket scope is covered, with restoration, in test_radar_network_isolation.
    monkeypatch.setattr(server.network_scope, "install", lambda: None)
    server.main()
    assert radar.RadarExtractor is rce.CorporateEventExtractor
    assert issubclass(rce.CorporateEventExtractor, rce.ORIGINAL)


def test_confirmed_bonus_total_return_and_raw_prices(lab):
    lab(ITUB4_BONUS)
    extractor, frame = lab_download()
    raw = nominal("ITUB4")
    expected = raw["fechamento"] * 0.98
    expected[expected.index < EX] /= 1.03  # continuous total-return series
    assert frame["fechamento"].to_numpy() == pytest.approx(expected.to_numpy(), rel=1e-12)
    assert frame["volume"].equals(raw["volume"])  # official quantity never adjusted
    radar.technical_input(frame)
    event = extractor.events["ITUB4.SA"][0]
    assert event["type"] == "BONIFICACAO" and event["b3_especi"] == "PN EB N1"
    assert event["b3_dismes"] == ["100", "101"]
    assert event["price_factor_before_ex_date"] == pytest.approx(1 / 1.03)
    with pytest.raises(ValueError, match="split-like mismatch"):
        lab.original(cache_dir="unused-cache").download("ITUB4.SA", "2025-07-16", DAY)


@pytest.mark.parametrize(
    "ticker,marker,ratio",
    [("MGLU3", "EB", 1.05), ("KLBN4", "EDB", 1.01), ("RADL3", "EJB", 1.02)],
)
def test_other_b3_bonus_markers(lab, ticker, marker, ratio):
    lab({ticker: [(EX, ratio, marker)]})
    extractor, _ = lab_download(ticker)
    assert extractor.events[ticker + ".SA"][0]["yfinance_split_ratio"] == ratio


def test_two_bonuses_in_the_window(lab):
    lab({"ITUB4": [(EX2, 1.10, "EB"), (EX, 1.03, "EB")]})
    extractor, frame = lab_download()
    expected = nominal("ITUB4")["fechamento"] * 0.98
    expected[expected.index < EX] /= 1.03
    expected[expected.index < EX2] /= 1.10
    assert frame["fechamento"].to_numpy() == pytest.approx(expected.to_numpy(), rel=1e-12)
    assert [e["ex_date"] for e in extractor.events["ITUB4.SA"]] == [
        str(EX2.date()),
        str(EX.date()),
    ]


@pytest.mark.parametrize(
    "events,book,missing,message",
    [
        # Yahoo split, but B3 shows no new distribution on that session.
        ({}, {"ITUB4": [(EX, EX, 1.03, 1.03)]}, None, "not corroborated by B3 DISMES"),
        # B3 distribution change for a dividend (EJ), not a bonificação.
        ({"ITUB4": [(EX, 1.03, "EJ")]}, None, None, "not a B3-confirmed bonificação"),
        # Grupamento-like ratio is never treated as a bonificação.
        ({"ITUB4": [(EX, 0.5, "EB")]}, None, None, "not a B3-confirmed bonificação"),
        # Yahoo dates the event one session late.
        (
            {"ITUB4": [(EX, 1.03, "EB")]},
            {"ITUB4": [(SESSIONS[151], EX, 1.03, 1.03)]},
            None,
            "boundary mismatch",
        ),
        # Booked factor incompatible with the observed price step.
        (
            {"ITUB4": [(EX, 1.03, "EB")]},
            {"ITUB4": [(EX, EX, 1.03, 1.05)]},
            None,
            "boundary mismatch",
        ),
        # Close adjusted without any booked event.
        ({}, {"ITUB4": [(EX, None, 1.03, None)]}, None, "split-like mismatch"),
        # Event on a session where B3 has no bar for the asset.
        ({"ITUB4": [(EX, 1.03, "EB")]}, None, {"ITUB4": [EX]}, "not a B3 session"),
    ],
)
def test_unconfirmed_or_inconsistent_events_stay_blocked(
    lab, events, book, missing, message
):
    lab(events, book, missing)
    with pytest.raises(ValueError, match=message):
        lab_download()


# One preparation path ------------------------------------------------------------


def test_cli_and_api_prepare_identically(lab, tmp_path, monkeypatch, capsys):
    root = lab(ITUB4_BONUS)
    cli = cli_prepare(tmp_path / "cli", TICKERS, monkeypatch, capsys)
    api = api_prepare(root, TICKERS, monkeypatch)
    assert {t: i["status"] for t, i in cli.items()} == dict.fromkeys(TICKERS, "PREPARED")
    assert api == cli
    for ticker in TICKERS:
        a = radar.checked_input(root, ticker, DAY)
        b = radar.checked_input(tmp_path / "cli", ticker, DAY)
        assert {**a, "prepared_at": None} == {**b, "prepared_at": None}
        assert a["source"]["corporate_events"]["normalization"] == rce.NAME
    events = radar.checked_input(root, "ITUB4", DAY)["source"]["corporate_events"][
        "events"
    ]
    assert [e["ex_date"] for e in events] == [str(EX.date())]


def test_four_existing_inputs_plus_itub4(lab, monkeypatch):
    root = lab(ITUB4_BONUS)
    # The four official inputs of 11/10 came from the original extractor.
    monkeypatch.setattr(radar, "RadarExtractor", lab.original)
    first = radar.prepare(list(TICKERS), root, end=DAY, mode="live")
    assert [i["status"] for i in first] == ["PREPARED"] * 2 + ["BLOCKED"] + [
        "PREPARED"
    ] * 2
    assert "split-like mismatch" in first[2]["error"]
    before = lifecycle.snapshot(root.parents[2])

    assert api_prepare(root, ["ITUB4"], monkeypatch)["ITUB4"]["status"] == "PREPARED"
    after = lifecycle.since(before, root.parents[2])
    assert after["violations"] == []
    changed = {
        c["path"].split("hfl_multiasset_v1/")[1]: c["category"] for c in after["changes"]
    }
    assert {k for k, v in changed.items() if v == "OPERATIONAL"} == {
        "last_prepare.json",
        "job.json",
    }
    assert all(k.startswith("analyses/ITUB4/") for k, v in changed.items() if v == "NEW")

    # The pointer only reports the last call; visibility comes from the inputs.
    assert [i["ticker"] for i in radar.read(root / "last_prepare.json")["items"]] == [
        "ITUB4"
    ]
    assert len(radar.status(root)["items"]) == 5
    report = readiness(root, monkeypatch)
    assert report["summary"] == "5 inputs prontos; 0/5 pareceres oficiais"
    states = {i["ticker"]: i for i in report["items"]}
    assert (
        states["ITUB4"]["input"]["normalization"]["state"] == "NORMALIZED_CONFIRMED_EVENT"
    )
    assert (
        states["PETR4"]["input"]["normalization"]["extractor"]
        == "ORIGINAL_V4_GUARD_PASSED"
    )
    assert states["BBAS3"]["input"]["risk"]["restricted"] is True
    assert all(
        i["risk_verdict"] is None and i["opinion"] == "PENDING" for i in report["items"]
    )
    assert report["global_pm_ready"] is False
    with pytest.raises(ValueError, match="complete_radar_opinion_required"):
        pm.load_opinions(root, list(TICKERS), DAY, "CONSULTATIVE_SANDBOX", pm.now())
    monkeypatch.setenv("GEMINI_API_KEY", "offline-placeholder-never-sent")
    batch = radar.preflight(list(TICKERS), root, day=DAY)
    assert batch["ready"] and batch["usd_reserved"] == 3.31776
    assert (
        lifecycle.since(before, root.parents[2])["changes"] == after["changes"]
    )  # reads only


def test_partial_failure_idempotency_cache_and_frozen_inputs(lab, monkeypatch):
    root = lab({"VALE3": [(EX, 1.03, "EJ")]})  # VALE3: event not confirmed as bonificação
    items = api_prepare(root, ["PETR4", "VALE3"], monkeypatch)
    assert items["PETR4"]["status"] == "PREPARED"
    assert items["VALE3"]["status"] == "BLOCKED"
    assert "not a B3-confirmed bonificação" in items["VALE3"]["error"]
    assert not (root / "analyses/VALE3").exists()

    frozen = {k: v for k, v in tree(root).items() if k.startswith("analyses/")}
    api_prepare(root, ["PETR4"], monkeypatch)  # repeat: reused, never rewritten
    assert {k: v for k, v in tree(root).items() if k.startswith("analyses/")} == frozen

    # A mutable cache never becomes an authority over a frozen input.
    (root / "cotahist").mkdir(exist_ok=True)
    (root / "cotahist/COTAHIST_A2026.ZIP").write_bytes(b"not a zip")
    radar.checked_input(root, "PETR4", DAY)
    assert api_prepare(root, ["PETR4"], monkeypatch)["PETR4"]["status"] == "PREPARED"

    bars = radar.folder_for(root, "PETR4", DAY) / "bars.csv"
    bars.write_bytes(bars.read_bytes() + b"\n")
    tampered = bars.read_bytes()
    assert api_prepare(root, ["PETR4"], monkeypatch)["PETR4"]["status"] == "BLOCKED"
    assert bars.read_bytes() == tampered  # refused, not "repaired" by overwriting
    assert (
        readiness(root, monkeypatch, ["PETR4"])["items"][0]["state"] == "INTEGRITY_ERROR"
    )


def test_bbas3_individual_risk_is_preserved(lab, monkeypatch):
    root = lab()
    api_prepare(root, ["BBAS3"], monkeypatch)
    item = readiness(root, monkeypatch, ["BBAS3"])["items"][0]
    assert (
        item["input"]["risk"]["asset_volatility_21"]
        > item["input"]["risk"]["limit"]
        == 0.5
    )
    assert item["risk_verdict"] is None  # prepared data is not a favourable risk opinion
    monkeypatch.setenv("GEMINI_API_KEY", "offline-placeholder-never-sent")
    token = radar.preflight(["BBAS3"], root, day=DAY)["confirmation_token"]
    [result] = radar.run(
        ["BBAS3"], token, root, day=DAY, authorize_paid=True, transport=radar.fake_gemini
    )
    assert result["risk"]["verdict"] == "VETADO"
    assert result["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"
    assert result["recommendation"] == "MANTER"
    report = readiness(root, monkeypatch, ["BBAS3", "PETR4"])
    bbas3 = report["items"][0]
    assert (bbas3["state"], bbas3["risk_verdict"]) == ("ELIGIBLE", "VETADO")
    assert report["summary"] == "1 inputs prontos; 1/2 pareceres oficiais"
    assert report["global_pm_ready"] is False


def test_prepare_endpoint_security_and_get_without_writes(lab, monkeypatch):
    root = lab(ITUB4_BONUS)
    rce.install()
    monkeypatch.setattr(radar_api, "ROOT", root)
    monkeypatch.setattr(platform_api.global_api, "OFFICIAL_RADAR", root)
    with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        port = httpd.server_address[1]

        def request(method, path, headers=None, body=None):
            with pytest.MonkeyPatch.context() as m:
                m.setattr(socket, "create_connection", CONNECT)
                c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                c.request(method, path, body, headers or {})
                status = c.getresponse().status
                c.close()
            return status

        payload = json.dumps({"tickers": ["ITUB4"], "session": DAY, "mode": "live"})
        origin = {
            "Origin": f"http://127.0.0.1:{port}",
            "Content-Type": "application/json",
        }
        for headers in (
            origin,
            {**origin, "X-CSRF-Token": "wrong"},
            {"Content-Type": "application/json"},
        ):
            assert request("POST", "/api/radar/prepare", headers, payload) == 403
        assert not (root / "analyses").exists()
        api_prepare(root, ["ITUB4"], monkeypatch)
        before = tree(root)
        path = f"/api/platform/radar-readiness?session={DAY}&tickers=ITUB4,PETR4"
        assert request("GET", path) == 200
        assert request("GET", "/api/platform/radar-view?mode=CONSULTATIVE_SANDBOX") == 200
        httpd.shutdown()
    assert tree(root) == before


# Lifecycle policy ------------------------------------------------------------------


def test_lifecycle_policy_classifies_changes(tmp_path):
    pinned = {
        "data/radar/r/last_prepare.json": "operational",
        "data/radar/r/cotahist/COTAHIST_A2026.ZIP": "cache",
        "data/forward/h2_v6_paper/state.json": "ledger",
        "data/radar/r/analyses/A/2026-10-09/input.json": "frozen",
        "data/radar/r/analyses/A/2026-10-09/claim.json": "claim",
    }
    for name, text in pinned.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text)
    baseline = {n: lifecycle.sha(tmp_path / n) for n in pinned}
    folder = tmp_path / "docs/evidence/old"
    folder.mkdir(parents=True)
    (folder / "preservation_baseline.json").write_text(json.dumps(baseline))
    for name in pinned:
        (tmp_path / name).write_text("changed")
    (tmp_path / "data/radar/r/analyses/A/2026-10-09/claim.json").unlink()
    report = lifecycle.baselines(tmp_path)
    categories = {p: c["category"] for p, c in report["changes"].items()}
    assert categories == {
        "data/radar/r/last_prepare.json": "OPERATIONAL",
        "data/radar/r/cotahist/COTAHIST_A2026.ZIP": "OPERATIONAL",
        "data/forward/h2_v6_paper/state.json": "LEDGER",
        "data/radar/r/analyses/A/2026-10-09/input.json": "VIOLATION",
        "data/radar/r/analyses/A/2026-10-09/claim.json": "VIOLATION",
    }
    assert report["changes"]["data/radar/r/last_prepare.json"]["before"] == {
        "old": baseline["data/radar/r/last_prepare.json"]
    }
    assert json.loads((folder / "preservation_baseline.json").read_text()) == baseline
