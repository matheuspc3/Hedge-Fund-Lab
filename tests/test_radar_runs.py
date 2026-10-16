"""V7.3: Radar runs registry, cross-run budget, run-aware UI/API and Global PM origin.

Temporary roots and registries only, except the read-only checks of the real
incident and recovery runs. No external network, no Gemini key, no paid call.
"""

import hashlib
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from contextlib import closing
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import check_preservation as lifecycle  # noqa: E402
import multiasset_radar as radar  # noqa: E402
import network_scope  # noqa: E402
import platform_api as api  # noqa: E402
import radar_runs as runs  # noqa: E402
import server  # noqa: E402

from src.agents.llm_client import GeminiLLMClient, _http_json_transport  # noqa: E402
from src.experiments import h2_evaluation_offline as offline  # noqa: E402

DAY = "2026-10-09"
FIVE = ["PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3"]
SOCKET = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection)
INCIDENT = "INCIDENT_2026_10_12_NETWORK_GUARD"


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """Process socket state restored; the real provider transport always fails."""
    for owner, name, value in (
        (socket.socket, "connect", SOCKET[0]),
        (socket.socket, "connect_ex", SOCKET[1]),
        (socket, "create_connection", SOCKET[2]),
    ):
        monkeypatch.setattr(owner, name, value)
    for module in list(sys.modules.values()):
        if getattr(module, "no_network", None) in (
            offline.no_network,
            network_scope.no_network,
        ):
            monkeypatch.setattr(module, "no_network", module.no_network)
    monkeypatch.setattr(offline, "no_network", network_scope.SEALED)
    monkeypatch.setattr(
        GeminiLLMClient, "_default_transport", lambda *a: pytest.fail("real Gemini used")
    )
    monkeypatch.setenv("GEMINI_API_KEY", "offline-placeholder-never-sent")
    yield
    socket.socket.connect, socket.socket.connect_ex, socket.create_connection = SOCKET


@pytest.fixture
def lab(tmp_path, monkeypatch):
    """A private data/radar with its own registry; the real one is never touched."""
    base = (tmp_path / "radar").resolve()
    base.mkdir()
    monkeypatch.setattr(runs, "RADAR_DIR", base)
    monkeypatch.setattr(runs, "REGISTRY", base / "registry.json")
    return base


def bars(volatile=False):
    frame = radar.synthetic_bars(pd.Timestamp(DAY))
    if volatile:  # alternating 6% moves: 21-day volatility far above the 50% limit
        swing = pd.Series(
            [1.06 if i % 2 else 0.94 for i in range(len(frame))], frame.index
        )
        close = frame["fechamento"] * swing
        frame = frame.assign(
            abertura=close * 0.999,
            maxima=close * 1.01,
            minima=close * 0.99,
            fechamento=close,
        )
    prices = ["abertura", "maxima", "minima", "fechamento"]
    return frame.assign(**frame[prices].round(2))  # official B3 prices are in cents


def freeze(root, ticker, frame, mode):
    class Extractor:
        def download(self, *args):
            return frame

        def source_description(self):
            return {"name": "FAKE_OFFICIAL_SOURCE_OFFLINE"}

        def _cotahist(self, year):
            return self

    original = radar.read_cotahist
    radar.read_cotahist = lambda *args: frame
    try:
        [item] = radar.prepare([ticker], root, end=DAY, mode=mode, extractor=Extractor())
    finally:
        radar.read_cotahist = original
    assert item["status"] == "PREPARED", item


def prepare(root, tickers, volatile=(), mode="live"):
    for ticker in tickers:
        freeze(root, ticker, bars(ticker in volatile), mode)


def batch(root, tickers, transport=radar.fake_gemini):
    token = radar.preflight(tickers, root, day=DAY)["confirmation_token"]
    return radar.run(
        tickers, token, root, day=DAY, authorize_paid=True, transport=transport
    )


def register(run_id, folder, **kwargs):
    kwargs.setdefault("session", DAY)
    kwargs.setdefault("universe", FIVE)
    return runs.register(run_id, "data/radar/" + folder, **kwargs)


def tree(path):
    return {
        p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(path).rglob("*")
        if p.is_file() and p.suffix != ".lock"
    }


def incident_and_recovery(lab):
    """A completed-reserve 'old' run (5 x 0.663552) and an empty recovery instance."""
    prepare(lab / "old", FIVE)
    batch(lab / "old", FIVE)
    register("radar-old", "old", existing=True, incident=INCIDENT)
    register("radar-new", "new", budget_usd=3.32, instance_of="radar-old", select=True)
    prepare(lab / "new", FIVE)
    return runs.load()


# 1-7 Registry --------------------------------------------------------------------------


def test_registry_lists_runs_and_selection(lab):
    prepare(lab / "a", FIVE)
    register("radar-a", "a", existing=True)
    register("radar-b", "b", instance_of="radar-a", select=True)
    data = runs.load()
    assert list(data["runs"]) == ["radar-a", "radar-b"] and data["selected"] == "radar-b"
    assert (
        data["revision"] == 2
        and [h["action"] for h in data["history"]] == ["REGISTER"] * 2
    )
    states = {r["id"]: r["state"] for r in runs.overview()["runs"]}
    assert states == {"radar-a": "AWAITING_AUTHORIZATION", "radar-b": "BLOCKED"}
    b = runs.run("radar-b")
    assert (
        b["treatment"] == runs.run("radar-a")["treatment"]
        and b["instance_of"] == "radar-a"
    )
    with pytest.raises(ValueError, match="already_registered"):
        register("radar-c", "a", existing=True)  # aliasing the same root


def test_valid_and_unknown_run_selection(lab):
    prepare(lab / "a", ["PETR4"])
    prepare(lab / "b", ["VALE3"])
    register("radar-a", "a", existing=True, universe=["PETR4"])
    register("radar-b", "b", existing=True, universe=["VALE3"])
    view = api.get("radar-view", {"run": "radar-b"})
    assert [i["ticker"] for i in view["items"]] == ["VALE3"]  # never the other run
    assert view["run"]["id"] == "radar-b" and view["mutation_available"] is False
    for bad in ("radar-zzz", "../a", "data/radar/a", "", "RADAR-A"):
        with pytest.raises(ValueError, match="unknown_radar_run"):
            api.get("radar-view", {"run": bad})
    with pytest.raises(ValueError):
        api.get("radar-view", {"run": "radar-a", "path": "x"})


@pytest.mark.parametrize(
    "path",
    [
        "data/radar/../forward",
        "data/radar/a/../../forward",
        "data/forward/h2_v6_paper",
        "data/radar/a/b",
        "C:/Windows",
        "//server/share",
        "data/radar/..",
        "data/radar/a\\..\\b",
    ],
)
def test_path_traversal_refused(lab, path):
    with pytest.raises(ValueError, match="run_path"):
        runs.root_of({"path": path})
    with pytest.raises(ValueError):
        runs.register("radar-x", path, DAY, FIVE)


def test_symlink_or_junction_escaping_storage_refused(lab, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = lab / "evil"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError:
        _winapi = pytest.importorskip("_winapi")
        try:
            _winapi.CreateJunction(str(outside), str(link))
        except OSError:
            pytest.skip("no symlink or junction support")
    with pytest.raises(ValueError, match="run_path_escapes_radar_storage"):
        runs.root_of({"path": "data/radar/evil"})
    with pytest.raises(ValueError, match="escapes"):
        register("radar-evil", "evil", existing=True)
    assert not runs.REGISTRY.exists()


def test_corrupted_or_missing_registry_fails_safe(lab, monkeypatch):
    with pytest.raises(ValueError, match="registry_unavailable"):
        runs.load()
    prepare(lab / "a", ["PETR4"])
    register("radar-a", "a", existing=True, universe=["PETR4"])
    good = runs.REGISTRY.read_bytes()
    original = api.radar_api.ROOT
    for damaged in (
        b"{not json",
        good.replace(b'"budget_usd":5.0', b'"budget_usd":50.0'),  # seal no longer matches
        json.dumps({**json.loads(good), "sha256": "0" * 64}).encode(),
    ):
        runs.REGISTRY.write_bytes(damaged)
        with pytest.raises(ValueError, match="registry_corrupted"):
            runs.load()
        assert runs.bind(api.radar_api) is None
        assert api.radar_api.ROOT == original  # no other (paid) run is picked
        with pytest.raises(ValueError, match="registry_corrupted"):
            api.get("radar-view", {"run": "radar-a"})
        with pytest.raises(ValueError, match="registry_corrupted"):
            api.radar_post_gate(
                "prepare", {"tickers": ["PETR4"], "session": DAY}, ["radar-a"]
            )
    # A resealed registry with a path escape or an aliased root is still refused.
    data = json.loads(good)
    data["runs"]["radar-a"]["path"] = "data/radar/../forward"
    runs.REGISTRY.write_text(json.dumps(runs.sealed(data)))
    with pytest.raises(ValueError, match="run_path_not_allowed"):
        runs.load()
    data = json.loads(good)
    data["runs"]["radar-b"] = {**data["runs"]["radar-a"], "id": "radar-b"}
    runs.REGISTRY.write_text(json.dumps(runs.sealed(data)))
    with pytest.raises(ValueError, match="registry_root_aliased"):
        runs.load()


def test_incident_run_is_read_only(lab):
    data = incident_and_recovery(lab)
    old = runs.run("radar-old", data)
    assert old["accepts_new_calls"] is False and old["incident"]["id"] == INCIDENT
    for command in ("prepare", "run", "universe"):
        with pytest.raises(ValueError, match="run_not_accepting_new_calls"):
            runs.gate("radar-old", command, FIVE, DAY, data)
    # An incident can never be re-labelled as accepting calls, even by editing the file.
    raw = json.loads(runs.REGISTRY.read_text())
    raw["runs"]["radar-old"]["accepts_new_calls"] = True
    runs.REGISTRY.write_text(json.dumps(runs.sealed(raw)))
    with pytest.raises(ValueError, match="registry_incident_must_be_read_only"):
        runs.load()
    with pytest.raises(ValueError):
        runs.register("radar-z", "data/radar/z", DAY, FIVE, incident="UNKNOWN_INCIDENT")


# 8-11 Ledgers and budget ---------------------------------------------------------------


def test_independent_ledgers_claims_and_budgets(lab):
    before_old = tree(lab / "old") if (lab / "old").exists() else None
    data = incident_and_recovery(lab)
    assert before_old is None
    old_tree = tree(lab / "old")
    report = runs.budget("radar-new", data)
    rows = {r["run"]: r for r in report["runs"]}
    assert rows["radar-old"]["usd_reserved"] == pytest.approx(3.31776)
    assert rows["radar-new"]["usd_reserved"] == 0 and report["run_reserved_usd"] == 0
    assert radar.budget_used(lab / "new") == 0  # the sealed per-root ledger is separate
    assert not list((lab / "new").rglob("claim.json"))  # nothing copied
    assert report["planned"]["tickers"] == FIVE
    assert report["planned"]["usd_reserved"] == pytest.approx(3.31776)
    assert report["aggregate_exposure_usd"] == pytest.approx(6.63552)
    assert report["within_run_budget"] and not report["within_aggregate_cap"]
    assert tree(lab / "old") == old_tree  # consulting another run never writes
    # A new instance can never start from a root that already holds claims or results.
    shutil.copytree(lab / "old" / "analyses", lab / "copy" / "analyses")
    with pytest.raises(ValueError, match="new_run_root_must_be_empty"):
        register("radar-copy", "copy")
    with pytest.raises(ValueError, match="already_registered"):
        register("radar-alias", "old")


def test_aggregate_budget_cannot_be_bypassed_silently(lab):
    data = incident_and_recovery(lab)
    with pytest.raises(ValueError, match="aggregate_budget_authorization_required"):
        runs.gate(
            "radar-new",
            "run",
            FIVE,
            DAY,
            data,
            report=radar.preflight(FIVE, lab / "new", day=DAY, max_usd=3.32),
        )
    assert runs.status(runs.run("radar-new", data), data)["state"] == "INPUTS_READY"
    with pytest.raises(ValueError, match="budget_changed_review_again"):
        runs.authorize_budget("radar-new", "0" * 64)
    token = runs.budget("radar-new", data)["budget_token"]
    record = runs.authorize_budget("radar-new", token)
    assert record["exceeds_original_local_limit"] is True
    assert {r["run"]: r["usd_reserved"] for r in record["runs"]}[
        "radar-old"
    ] == pytest.approx(3.31776)
    assert (
        runs.status(runs.run("radar-new", data), data)["state"]
        == "AWAITING_AUTHORIZATION"
    )
    report = radar.preflight(FIVE, lab / "new", day=DAY, max_usd=3.32)
    runs.gate("radar-new", "run", FIVE, DAY, data, report=report)
    # The old reserve is neither released nor copied by the authorization.
    assert radar.budget_used(lab / "old") == pytest.approx(3.31776)
    assert radar.budget_used(lab / "new") == 0
    # The run's own budget still binds: a smaller run budget refuses the batch.
    raw = json.loads(runs.REGISTRY.read_text())
    raw["runs"]["radar-new"]["budget_usd"] = 1.0
    runs.REGISTRY.write_text(json.dumps(runs.sealed(raw)))
    with pytest.raises(ValueError, match="run_budget_exceeded"):
        runs.gate("radar-new", "run", FIVE, DAY, runs.load(), report=report)


def test_any_exposure_change_invalidates_the_budget_authorization(lab):
    data = incident_and_recovery(lab)
    runs.authorize_budget("radar-new", runs.budget("radar-new", data)["budget_token"])
    prepare(lab / "other", ["PETR4"])
    register("radar-other", "other", existing=True, universe=["PETR4"])
    batch(lab / "other", ["PETR4"])  # another run reserves money afterwards
    data = runs.load()
    auth = runs.budget("radar-new", data)["authorization"]
    assert auth == {"state": "STALE", "required": True}
    with pytest.raises(ValueError, match="aggregate_budget_authorization_required"):
        runs.gate(
            "radar-new",
            "run",
            FIVE,
            DAY,
            data,
            report=radar.preflight(FIVE, lab / "new", day=DAY, max_usd=3.32),
        )


def test_restricted_asset_plans_no_risk_call(lab):
    prepare(lab / "a", ["PETR4", "BBAS3"], volatile={"BBAS3"})
    register("radar-a", "a", existing=True, universe=["PETR4", "BBAS3"])
    data = runs.load()
    inv = runs.inventory(runs.run("radar-a", data))
    assert {i["ticker"]: i["restricted"] for i in inv["items"]} == {
        "PETR4": False,
        "BBAS3": True,
    }
    plan = runs.budget("radar-a", data)["planned"]
    assert (plan["calls_max"], plan["calls_planned"]) == (12, 11)
    [_, bbas3] = batch(lab / "a", ["PETR4", "BBAS3"])
    assert bbas3["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"  # restriction preserved
    assert runs.inventory(runs.run("radar-a", data))["items"][1]["calls_reserved"] == 5


# Comparison ----------------------------------------------------------------------------


def test_economic_comparison_levels_and_block(lab):
    prepare(lab / "a", ["PETR4"])
    register("radar-a", "a", existing=True, universe=["PETR4"])
    shutil.copytree(lab / "a" / "analyses", lab / "b" / "analyses")
    register("radar-b", "b", existing=True, universe=["PETR4"], instance_of="radar-a")
    data = runs.load()
    same = runs.compare(runs.run("radar-b", data), runs.run("radar-a", data))
    assert same["items"][0]["status"] == "IDENTICAL" and not same["material"]
    folder = lab / "b" / "analyses" / "PETR4" / DAY
    frame = pd.read_csv(folder / "bars.csv", index_col=0, float_precision="round_trip")
    frame.iloc[:10, :4] *= 1 + 3e-7  # provider float noise, below the factor tolerance
    noisy = frame.to_csv(lineterminator="\n").encode()
    (folder / "bars.csv").write_bytes(noisy)
    frozen = json.loads((folder / "input.json").read_text())
    frozen["history"]["sha256"] = hashlib.sha256(noisy).hexdigest()
    (folder / "input.json").write_text(json.dumps(frozen))
    near = runs.compare(runs.run("radar-b", data), runs.run("radar-a", data))["items"][0]
    assert near["status"] == "EQUIVALENT_WITHIN_TOLERANCE"
    assert near["differences"]["adjusted_series_sessions_differing"] == 10
    frozen["raw_bar"]["fechamento"] += 0.01  # a different official price is material
    (folder / "input.json").write_text(json.dumps(frozen))
    result = runs.compare(runs.run("radar-b", data), runs.run("radar-a", data))
    assert result["material"] and result["items"][0]["checks"]["raw_bar"] is False


def test_material_divergence_blocks_paid_run(lab, monkeypatch):
    prepare(lab / "a", ["PETR4"])
    prepare(lab / "b", ["PETR4"])
    register("radar-a", "a", existing=True, universe=["PETR4"], read_only=True)
    register("radar-b", "b", existing=True, universe=["PETR4"], instance_of="radar-a")
    data = runs.load()
    monkeypatch.setattr(
        runs,
        "compare",
        lambda *a: {"material": True, "items": [], "reference": "radar-a"},
    )
    status = runs.status(runs.run("radar-b", data), data)
    assert status["state"] == "BLOCKED"
    assert status["reasons"] == ["material_divergence_from_reference_run"]
    with pytest.raises(ValueError, match="run_blocked_material_divergence"):
        runs.gate(
            "radar-b",
            "run",
            ["PETR4"],
            DAY,
            data,
            report=radar.preflight(["PETR4"], lab / "b", day=DAY),
        )


# Real recovery run (read-only) ----------------------------------------------------------

REAL = ROOT / "data/radar/registry.json"
real = pytest.mark.skipif(
    not REAL.exists(), reason="local registry absent (clean checkout)"
)


@real
def test_real_recovery_has_five_official_inputs_equivalent_to_original():
    data = runs.load(REAL)
    entry = runs.run("radar-2026-10-09-recovery-01", data)
    inv = runs.inventory(entry)
    assert inv["inputs"] == 5 and not inv["errors"] and inv["claims"] == 0
    assert inv["usd_reserved"] == 0 and not list(
        (runs.root_of(entry) / "reservations").glob("*")
    )
    for ticker in FIVE:
        frozen = radar.checked_input(runs.root_of(entry), ticker, DAY)
        assert frozen["manifest"]["mode"] == "live"
        assert frozen["manifest_sha256"] == entry["treatment"]["manifest_sha256"]
        assert frozen["source"]["name"] == "b3_cotahist_ohlcv+yfinance_adjustment_factor"
    comparison = runs.compare(entry, runs.run("radar-2026-10-09-original", data))
    assert not comparison["material"]
    assert {i["status"] for i in comparison["items"]} <= {
        "IDENTICAL",
        "EQUIVALENT_WITHIN_TOLERANCE",
    }


@real
def test_real_itub4_bonus_normalized_and_bbas3_restricted():
    data = runs.load(REAL)
    new = runs.root_of(runs.run("radar-2026-10-09-recovery-01", data))
    old = runs.root_of(runs.run("radar-2026-10-09-original", data))
    itub = [radar.read(r / "analyses/ITUB4" / DAY / "input.json") for r in (new, old)]
    events = [i["source"]["corporate_events"] for i in itub]
    assert events[0]["events"] == events[1]["events"]
    assert [e["type"] for e in events[0]["events"]] == ["BONIFICACAO"]
    assert (
        events[0]["module_sha256"] == events[1]["module_sha256"]
    )  # same V7.2 normalizer
    assert events[0]["module_sha256"] == radar.sha_file(
        ROOT / "scripts/radar_corporate_events.py"
    )
    bbas = radar.read(new / "analyses/BBAS3" / DAY / "input.json")
    assert (
        bbas["risk_metrics"]["asset_volatility_21"]
        > bbas["manifest"]["risk"]["max_asset_volatility"]
    )
    plan = runs.budget("radar-2026-10-09-recovery-01", data)["planned"]
    assert (plan["calls_max"], plan["calls_planned"]) == (30, 29)


EVIDENCE = ROOT / "docs/evidence/hfl_radar_v73/incident_root_sha256.json"


@pytest.mark.skipif(
    not (ROOT / "data/radar/hfl_multiasset_v1").exists() or not EVIDENCE.exists(),
    reason="incident root or V7.3 evidence absent",
)
def test_real_incident_records_all_preserved():
    pinned = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    root = ROOT / "data/radar/hfl_multiasset_v1"
    current = {f"data/radar/hfl_multiasset_v1/{k}": v for k, v in tree(root).items()}
    changed = sorted(
        p for p in set(pinned) | set(current) if pinned.get(p) != current.get(p)
    )
    assert [p for p in changed if lifecycle.classify(p)[0] == "VIOLATION"] == []
    assert len([p for p in pinned if p.endswith("claim.json")]) == 5
    assert len([p for p in pinned if p.endswith("failure.json")]) == 5
    assert len([p for p in pinned if "/reservations/" in p]) == 1


# 16-20 Global PM ------------------------------------------------------------------------


@pytest.fixture
def global_lab(lab, tmp_path, monkeypatch):
    monkeypatch.setattr(api.pm, "OUTPUT", (tmp_path / "global").resolve())
    jobs = api.GlobalJobs((tmp_path / "jobs").resolve())
    monkeypatch.setattr(api, "GLOBAL_JOBS", jobs)
    prepare(lab / "a", FIVE)
    batch(lab / "a", FIVE)
    register("radar-a", "a", existing=True, read_only=True)
    return jobs


def wait(jobs):
    for _ in range(600):
        if not jobs.active:
            return
        threading.Event().wait(0.05)
    pytest.fail("global job did not finish")


def global_payload(selection, **extra):
    return {
        "id": "v7-" + os.urandom(16).hex(),
        "mode": selection["mode"],
        "session": selection["session"],
        "tickers": selection["selected"],
        "capital": "100000",
        "confirm_hypothetical": True,
        "ack_fixture_policy": True,
        "radar_run": selection["radar_run"]["id"],
        "opinion_hashes": selection["opinion_hashes"],
        **extra,
    }


def test_radar_to_global_pm_same_run_and_frozen_origin(global_lab, lab):
    query = {"run": "radar-a", "session": DAY, "tickers": ",".join(FIVE)}
    selection = api.get("radar-selection", query)
    assert selection["status"] == "READY_FOR_CONTEXT_PREPARATION"
    assert set(selection["opinion_hashes"]) == set(FIVE)
    payload = global_payload(selection)
    global_lab.start("prepare", payload)
    wait(global_lab)
    detail = api.public_global(payload["id"])
    assert detail["state"] == "PREPARED", detail.get("native_state")
    origin = detail["radar_origin"]
    assert origin["state"] == "VERIFIED" and origin["radar_run"]["id"] == "radar-a"
    assert (
        origin["radar_run"]["session"] == DAY
        and origin["radar_run"]["mode"] == "CONSULTATIVE_SANDBOX"
    )
    assert {t: o["opinion_sha256"] for t, o in origin["opinions"].items()} == selection[
        "opinion_hashes"
    ]
    assert (
        origin["opinions"]["PETR4"]["input_ref"]
        == f"data/radar/a/analyses/PETR4/{DAY}/input.json"
    )
    frozen = (global_lab.root / "radar_origins" / (payload["id"] + ".json")).read_bytes()
    # Changing the selected run later never touches a frozen context or its origin.
    prepare(lab / "b", FIVE)
    register("radar-b", "b", existing=True, select=True)
    assert (
        api.public_global(payload["id"])["radar_origin"]["radar_run"]["id"] == "radar-a"
    )
    assert (
        global_lab.root / "radar_origins" / (payload["id"] + ".json")
    ).read_bytes() == frozen
    # A context whose origin disappeared or diverges is not accepted for inference.
    path = global_lab.root / "radar_origins" / (payload["id"] + ".json")
    path.unlink()
    assert (
        api.radar_origin(
            payload["id"], api.global_api.public_detail(api.analysis_root(payload["id"]))
        )["state"]
        == "MISSING"
    )


def test_global_pm_refuses_mixed_session_source_stale_or_incomplete(global_lab, lab):
    query = {"run": "radar-a", "session": DAY, "tickers": ",".join(FIVE)}
    selection = api.get("radar-selection", query)
    with pytest.raises(ValueError, match="session_differs_from_radar_run"):
        api.get("radar-selection", {**query, "session": "2026-10-08"})
    with pytest.raises(ValueError, match="session_differs_from_radar_run"):
        global_lab.start("prepare", global_payload(selection, session="2026-10-08"))
    with pytest.raises(ValueError, match="synthetic_official_mix"):
        global_lab.start("prepare", global_payload(selection, mode="SYNTHETIC_DEMO"))
    stale = {**selection["opinion_hashes"], "PETR4": "f" * 64}
    with pytest.raises(ValueError, match="radar_selection_changed_review_again"):
        global_lab.start("prepare", global_payload(selection, opinion_hashes=stale))
    with pytest.raises(ValueError, match="radar_run_required"):
        global_lab.start(
            "prepare",
            {
                k: v
                for k, v in global_payload(selection).items()
                if k not in ("radar_run", "opinion_hashes")
            },
        )
    # Fewer than five complete opinions: selection and prepare stay blocked.
    prepare(lab / "c", FIVE)
    batch(lab / "c", FIVE[:4])
    register("radar-c", "c", existing=True)
    partial = api.get("radar-selection", {**query, "run": "radar-c"})
    assert partial["missing"] == ["BBAS3"] and partial["status"] == "INSUFFICIENT_DATA"
    with pytest.raises(ValueError):
        global_lab.start(
            "prepare",
            global_payload(
                {
                    **partial,
                    "opinion_hashes": {**partial["opinion_hashes"], "BBAS3": "0" * 64},
                }
            ),
        )
    assert not list(api.pm.OUTPUT.glob("v7-*/context.json"))
    # A synthetic input inside an official run is an integrity error, never mixed in.
    prepare(lab / "c", ["ELET3"], mode="synthetic")
    raw = json.loads(runs.REGISTRY.read_text())
    raw["runs"]["radar-c"]["universe"] = ["PETR4", "ELET3"]
    runs.REGISTRY.write_text(json.dumps(runs.sealed(raw)))
    inv = runs.inventory(runs.run("radar-c"))
    assert "ELET3:synthetic_official_mix" in inv["errors"]


# 21-29 API, guard and gates --------------------------------------------------------------


def test_get_routes_have_no_side_effects(global_lab, lab):
    before = tree(lab)
    for command, query in (
        ("radar-runs", {}),
        ("radar-view", {"run": "radar-a"}),
        ("radar-readiness", {"run": "radar-a", "session": DAY, "tickers": "PETR4,BBAS3"}),
        ("radar-detail", {"run": "radar-a", "ticker": "PETR4", "session": DAY}),
        ("radar-selection", {"run": "radar-a", "session": DAY, "tickers": "PETR4"}),
    ):
        api.get(command, query)
    runs.preflight("radar-a")
    assert tree(lab) == before


def test_preflight_makes_no_call_and_writes_nothing(lab):
    data = incident_and_recovery(lab)
    before = tree(lab / "new")
    report = runs.preflight("radar-new", registry=data)
    assert report["provider_calls"] == 0 and report["gate"] == "BLOCKED"
    assert report["blockers"] == ["aggregate_budget_authorization_required"]
    assert report["budget"]["planned"]["calls_planned"] == 30
    assert report["radar_preflight"]["ready"] is True  # the sealed check alone would pass
    assert tree(lab / "new") == before
    assert not list((lab / "new").rglob("claim.json"))


def test_replay_of_recoverable_run_needs_no_budget_and_sends_nothing(lab):
    prepare(lab / "a", ["PETR4"])
    register("radar-a", "a", existing=True, universe=["PETR4"])

    def refuse(*args):
        raise RuntimeError("offline qualification forbids network")

    batch(lab / "a", ["PETR4"], transport=refuse)
    data = runs.load()
    assert runs.status(runs.run("radar-a", data), data)["state"] == "RECOVERY_REQUIRED"
    report = radar.preflight(["PETR4"], lab / "a", day=DAY, replay=True)
    runs.gate("radar-a", "run", ["PETR4"], DAY, data, report=report)
    claim = (lab / "a/analyses/PETR4" / DAY / "claim.json").read_bytes()
    [item] = radar.run(
        ["PETR4"],
        report["confirmation_token"],
        lab / "a",
        day=DAY,
        replay=True,
        transport=lambda *a: pytest.fail("replay transmitted"),
    )
    assert item["status"] == "FAILED_REPLAY_ONLY"
    assert (lab / "a/analyses/PETR4" / DAY / "claim.json").read_bytes() == claim


def test_failure_and_unknown_billing_are_represented(lab):
    prepare(lab / "a", ["PETR4", "VALE3"])

    def guard(*args):
        raise RuntimeError("offline qualification forbids network")

    def drop(*args):
        raise ConnectionResetError("dropped")

    batch(lab / "a", ["PETR4"], transport=guard)
    batch(lab / "a", ["VALE3"], transport=drop)
    register("radar-a", "a", existing=True, universe=["PETR4", "VALE3"])
    inv = runs.inventory(runs.run("radar-a"))
    outcomes = {i["ticker"]: i["outcome"] for i in inv["items"]}
    assert outcomes["PETR4"]["billing"] == "NO_SEND_EVIDENCE"
    assert outcomes["VALE3"]["billing"] == "UNKNOWN"
    forensic = sorted(b["forensic"] for b in inv["reservations"])
    assert forensic == [
        "LOCAL_BLOCK_BEFORE_CONNECT_BILLING_UNCONFIRMED",
        "UNCERTAIN_UNKNOWN",
    ]
    assert (
        inv["usd_billed_confirmed"] is None and inv["usd_observed_provider_tokens"] == 0
    )
    assert inv["usd_reserved_uncertain"] == inv["usd_reserved"]  # reserved, not billed
    public = runs.public(runs.run("radar-a"), runs.load())
    assert (
        public["state"] == "RECOVERY_REQUIRED" and public["usd_billed_confirmed"] is None
    )
    assert "dropped" not in json.dumps(public)  # codes only


def test_two_overlapping_scoped_guards_leave_nothing_behind():
    network_scope.install()
    installed = (
        socket.socket.connect,
        socket.socket.connect_ex,
        socket.create_connection,
    )
    with closing(socket.socket()) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(8)
        port = listener.getsockname()[1]
        a_in, b_in, a_out = threading.Event(), threading.Event(), threading.Event()
        seen = {}

        def a():
            with network_scope.no_network():
                a_in.set()
                b_in.wait(10)
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=5)
                except RuntimeError as exc:
                    seen["a"] = str(exc)
            a_out.set()

        def b():
            a_in.wait(10)
            with network_scope.no_network():
                b_in.set()
                a_out.wait(10)

        threads = [threading.Thread(target=a), threading.Thread(target=b)]
        [t.start() for t in threads]
        free = socket.create_connection(("127.0.0.1", port), timeout=5)  # third thread
        free.close()
        [t.join(10) for t in threads]
        assert seen == {"a": "offline qualification forbids network"}
        assert (
            socket.socket.connect,
            socket.socket.connect_ex,
            socket.create_connection,
        ) == installed
        socket.create_connection(("127.0.0.1", port), timeout=5).close()
    assert network_scope.qualified()


def test_install_refuses_active_patch_and_qualification_detects_regression():
    with offline.no_network():  # the sealed, process-wide guard is active
        with pytest.raises(RuntimeError, match="network_patch_active_at_install"):
            network_scope.install()
    assert not network_scope.qualified()
    network_scope.install()
    created = socket.create_connection
    network_scope.install()  # restart in the same process: no double wrapping
    assert socket.create_connection is created and network_scope.qualified()
    socket.socket.connect = SOCKET[0]  # something replaced one attribute later
    assert not network_scope.qualified()


def test_offline_get_does_not_block_paid_worker_on_selected_run(lab):
    network_scope.install()
    seen = []

    class Fake(server.http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            payload = radar.fake_gemini("POST", self.path, {}, body)
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    httpd = server.http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    prepare(lab / "a", ["PETR4"])
    register("radar-a", "a", existing=True, universe=["PETR4"])
    inside, release = threading.Event(), threading.Event()

    def get():  # a GET's offline check held open while the worker transmits
        with network_scope.no_network():
            api.get(
                "radar-readiness", {"run": "radar-a", "session": DAY, "tickers": "PETR4"}
            )
            inside.set()
            release.wait(30)

    reader = threading.Thread(target=get)
    reader.start()
    assert inside.wait(30)
    try:
        [item] = batch(
            lab / "a",
            ["PETR4"],
            transport=lambda m, u, h, b: _http_json_transport(
                m, f"http://127.0.0.1:{port}/g", {}, b, 10
            ),
        )
    finally:
        release.set()
        reader.join(30)
        httpd.shutdown()
        httpd.server_close()
    assert item["status"] == "COMPLETED" and len(seen) == 6


@pytest.fixture
def http_lab(lab, monkeypatch):
    calls = []
    monkeypatch.setattr(api.radar_api, "post", lambda c, p: calls.append(c) or {"ok": c})
    monkeypatch.setattr(api.radar_api, "ROOT", lab / "new")
    httpd = server.ReusableTCPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def post(command, payload, run=None, platform=False):
        headers = {
            "Origin": f"http://127.0.0.1:{port}",
            "Content-Type": "application/json",
            "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
        }
        if run:
            headers["X-HFL-Radar-Run"] = run
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        c.request(
            "POST",
            ("/api/platform/" if platform else "/api/radar/") + command,
            json.dumps(payload),
            headers,
        )
        response = c.getresponse()
        result = response.status, json.loads(response.read())
        c.close()
        return result

    post.calls = calls
    yield post
    httpd.shutdown()
    httpd.server_close()


def test_web_budget_review_validates_scope_ceiling_and_snapshot(
    lab, http_lab, monkeypatch
):
    data = incident_and_recovery(lab)
    monkeypatch.setattr(api.radar_api, "ACTIVE", False)
    money = api.get("radar-budget", {"run": "radar-new"})
    assert money["read_only"] and money["authorization"]["state"] == "ABSENT"
    body = {
        "run": "radar-new",
        "budget_token": money["budget_token"],
        "max_aggregate_usd": 10,
        "confirm": True,
    }
    before = tree(lab / "old")
    for change in (
        {"confirm": False},
        {"confirm": 1},
        {"max_aggregate_usd": True},
        {"max_aggregate_usd": -1},
        {"max_aggregate_usd": float("nan")},
        {"max_aggregate_usd": 5},
        {"budget_token": "0" * 64},
        {"run": "radar-old"},
        {"extra": True},
    ):
        status, _ = http_lab(
            "radar-budget-authorization", body | change, run="radar-new", platform=True
        )
        assert status == 400
    assert (
        http_lab("radar-budget-authorization", body, run="radar-old", platform=True)[0]
        == 400
    )
    assert not (lab / "new/budget_authorizations").exists()
    monkeypatch.setattr(api.radar_api, "ACTIVE", True)
    assert (
        http_lab("radar-budget-authorization", body, run="radar-new", platform=True)[0]
        == 400
    )
    monkeypatch.setattr(api.radar_api, "ACTIVE", False)
    status, result = http_lab(
        "radar-budget-authorization", body, run="radar-new", platform=True
    )
    assert status == 201 and result["provider_calls"] == 0
    assert result["authorized_exposure_usd"] == money["aggregate_exposure_usd"]
    assert runs.budget("radar-new", data)["authorization"]["state"] == "VALID"
    assert tree(lab / "old") == before and http_lab.calls == []
    assert not list((lab / "new").rglob("claim.json"))
    assert radar.budget_used(lab / "new") == 0


def run_payload(**extra):
    return {
        "tickers": FIVE,
        "session": DAY,
        "max_usd": 3.32,
        "replay": False,
        "confirmation_token": "x",
        "authorize_paid": True,
        "confirm": True,
        **extra,
    }


def test_paid_post_blocked_without_run_header_isolation_or_budget(lab, http_lab):
    incident_and_recovery(lab)
    status, body = http_lab("run", run_payload())
    assert (status, body["error"]) == (400, "radar_run_header_mismatch_reload_page")
    status, body = http_lab("run", run_payload(), run="radar-old")
    assert body["error"] == "radar_run_header_mismatch_reload_page"
    status, body = http_lab("run", run_payload(), run="radar-new")
    assert body["error"] == "network_isolation_not_qualified_restart_server"
    network_scope.install()
    status, body = http_lab("run", run_payload(), run="radar-new")
    assert body["error"] == "aggregate_budget_authorization_required"
    status, body = http_lab(
        "prepare", {"tickers": ["ELET3"], "session": DAY, "mode": "live"}, run="radar-new"
    )
    assert body["error"] == "selection_outside_run_identity"
    status, body = http_lab(
        "prepare", {"tickers": FIVE, "session": DAY, "mode": "synthetic"}, run="radar-new"
    )
    assert body["error"] == "synthetic_official_mix"
    assert http_lab.calls == []  # the sealed runner was never reached
    status, body = http_lab(
        "prepare", {"tickers": FIVE, "session": DAY, "mode": "live"}, run="radar-new"
    )
    assert (status, http_lab.calls) == (200, ["prepare"])
    assert not list((lab / "new").rglob("claim.json"))


def test_incident_root_is_never_a_write_target(lab, http_lab, monkeypatch):
    incident_and_recovery(lab)
    monkeypatch.setattr(api.radar_api, "ROOT", lab / "old")
    network_scope.install()
    for command, payload in (
        ("prepare", {"tickers": FIVE, "session": DAY, "mode": "live"}),
        ("run", run_payload()),
    ):
        assert (
            http_lab(command, payload, run="radar-old")[1]["error"]
            == "run_not_accepting_new_calls"
        )
    assert (
        http_lab("universe", {"tickers": ["PETR4"]})[1]["error"]
        == "run_not_accepting_new_calls"
    )
    assert http_lab.calls == []
    assert api.radar_view("radar-old")["mutation_available"] is False


def test_server_binds_only_a_selected_run_that_accepts_calls(lab, monkeypatch):
    incident_and_recovery(lab)
    monkeypatch.setattr(api.radar_api, "ROOT", radar.OUTPUT)
    assert runs.bind(api.radar_api) == "radar-new"
    assert api.radar_api.ROOT == lab / "new"
    assert api.radar_view("radar-new")["mutation_available"] is True
    runs.select("radar-old")
    monkeypatch.setattr(api.radar_api, "ROOT", radar.OUTPUT)
    assert runs.bind(api.radar_api) is None and api.radar_api.ROOT == radar.OUTPUT


def test_readiness_does_not_reuse_old_blocks_during_new_prepare(lab, monkeypatch):
    root = lab / "preparing"
    prepare(root, ["PETR4"])
    radar.write(
        root / "last_prepare.json",
        {
            "generated_at": "2026-10-14T03:02:00-03:00",
            "items": [
                {
                    "ticker": t,
                    "session": DAY,
                    "status": "BLOCKED",
                    "error": "no adjustment factor",
                }
                for t in ["PETR4", "VALE3"]
            ],
        },
    )
    job = {"command": "prepare", "status": "RUNNING"}
    monkeypatch.setattr(api, "radar_job", lambda root: job)
    report = api.radar_readiness(DAY, ["PETR4", "VALE3"], root)
    petr, vale = report["items"]
    assert petr["input_state"] == "FROZEN" and report["inputs_ready"] == 1
    assert vale["input_state"] == vale["preflight"] == "PREPARING"
    assert vale["error"] is None and "aguarde" in vale["action"]
    job["status"] = "COMPLETED"
    blocked = api.radar_readiness(DAY, ["VALE3"], root)["items"][0]
    assert blocked["input_state"] == "BLOCKED_DATA"
    assert blocked["error"] == "no adjustment factor"
    assert "Fator de ajuste Yahoo indisponível" in blocked["action"]
    assert "não confirmado pela B3" not in blocked["action"]


def test_snapshot_classifies_registry_and_late_covered_areas(tmp_path):
    (tmp_path / "data/radar/r").mkdir(parents=True)
    (tmp_path / "data/radar/registry.json").write_text(
        json.dumps({"runs": {"x": {"path": "data/radar/r"}}})
    )
    (tmp_path / "data/radar/r/input.json").write_text("{}")
    before = {"areas": ["data/forward"], "files": {}}
    report = lifecycle.since(before, tmp_path)
    categories = {c["path"]: c["category"] for c in report["changes"]}
    assert categories == {
        "data/radar/registry.json": "OPERATIONAL",
        "data/radar/r/input.json": "UNCOVERED_BEFORE",
    }
    assert report["violations"] == []


# 15 UI: switching runs cancels the previous run's pending requests ------------------------


def test_radar_page_run_switch_cancels_pending_and_never_mixes_runs():
    script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const fields={},pending=[];
function element(id){return fields[id]??={id,value:'',checked:false,disabled:false,hidden:false,textContent:'',innerHTML:'',dataset:{},max:'',tabIndex:0,listeners:{},classList:{toggle(){}},addEventListener(k,f){this.listeners[k]=f},querySelectorAll(){return []},closest(){return element(id+'-label')},scrollIntoView(){},focus(){},replaceChildren(){this.innerHTML=''}}}
const document={getElementById:element};
function fetch(url,options={}){return new Promise((resolve,reject)=>{const req={url,options,reply:(data,ok=true)=>resolve({ok,json:async()=>data})};options.signal?.addEventListener('abort',()=>reject(Object.assign(new Error('aborted'),{name:'AbortError'})));pending.push(req)})}
function take(part){const i=pending.findIndex(r=>r.url.includes(part));assert.ok(i>=0,'missing '+part+' in '+pending.map(r=>r.url));return pending.splice(i,1)[0]}
const tick=()=>new Promise(r=>setImmediate(r));
const ctx=vm.createContext({document,fetch,URLSearchParams,AbortController,location:{search:'',hash:''},history:{replaceState(){}},setTimeout,clearTimeout,setInterval(){return 1},clearInterval(){},console});
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=()=>{};ctx.PopStateEvent=class {};
vm.runInContext(fs.readFileSync(require('node:path').join(require('node:path').dirname(process.argv[1]),'market-ui.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const run=(id,mode='CONSULTATIVE_SANDBOX')=>({id,mode,session:'2026-10-09',universe:['PETR4'],state:'INPUTS_READY',reasons:[],opinions:0,incident:null,selected:id==='radar-b',source:'B3',classification:'OFFICIAL',same_treatment_as:null,prepared_at:null,inputs:1,claims:0,failures:0,calls_reserved:0,responses_recorded:0,budget_usd:3.32,usd_reserved:0,usd_reserved_uncertain:0,usd_observed_provider_tokens:0,budget:null,comparison:null});
const view=id=>({run:run(id),items:[{ticker:'PETR4',session:'2026-10-09',mode:'live',status:'PREPARED',adjusted_close:1,generated_at:null}],universe:['PETR4'],examples:[],last_closed_session:'2026-10-09',job:null,csrf_token:'c',network_isolation:true,mutation_available:id==='radar-b',runner:'radar-b',last_prepare:null});
(async()=>{
 take('/api/platform/radar-runs').reply({selected:'radar-b',runs:[run('radar-a'),run('radar-b')]});await tick();
 const slowB=take('radar-view?run=radar-b');
 element('radar-run').value='radar-a';element('radar-run').listeners.change();await tick();
 assert.equal(slowB.options.signal.aborted,true);
 take('radar-view?run=radar-a').reply(view('radar-a'));await tick();
 const readinessA=take('radar-readiness');assert.ok(readinessA.url.includes('run=radar-a'));
 element('radar-run').value='radar-b';element('radar-run').listeners.change();await tick();
 assert.equal(readinessA.options.signal.aborted,true);
 take('radar-view?run=radar-b').reply(view('radar-b'));await tick();
 take('radar-readiness').reply({summary:'s',run:'radar-b',session:'2026-10-09',global_pm_ready:false,items:[],prepare_command:'cmd'});await tick();
 assert.ok(element('run-card').innerHTML.includes('radar-b'));assert.ok(!element('run-card').innerHTML.includes('radar-a'));
 assert.equal(element('prepare').disabled,false);
 element('preflight').listeners.click();await tick();
 take('radar-readiness').reply({summary:'s',run:'radar-b',session:'2026-10-09',items:[],prepare_command:'cmd'});await tick();
 const post=take('/api/radar/preflight');
 assert.equal(post.options.headers['X-HFL-Radar-Run'],'radar-b');
 element('radar-run').value='radar-a';element('radar-run').listeners.change();await tick();
 assert.equal(post.options.signal.aborted,true);
 take('radar-view?run=radar-a').reply(view('radar-a'));await tick();
 assert.equal(element('prepare').disabled,true);
 // A previous failure must not appear as the result of the new, running preparation.
 const oldFailure={generated_at:'2026-10-14T03:02:00-03:00',items:[{ticker:'PETR4',session:'2026-10-13',status:'BLOCKED',error:'no adjustment factor'}]};
 element('radar-run').value='radar-b';element('radar-run').listeners.change();await tick();
 take('radar-view?run=radar-b').reply({...view('radar-b'),job:{command:'prepare',status:'RUNNING'},last_prepare:oldFailure});await tick();
 take('radar-readiness').reply({summary:'s',run:'radar-b',session:'2026-10-09',items:[],prepare_command:'cmd'});await tick();
 assert.equal(element('error').hidden,true);
 const refresh=vm.runInContext('refresh()',ctx);
 take('radar-view?run=radar-b').reply({...view('radar-b'),last_prepare:oldFailure});await tick();
 take('radar-readiness').reply({summary:'s',run:'radar-b',session:'2026-10-09',items:[],prepare_command:'cmd'});await refresh;
 assert.equal(element('error').hidden,false);assert.match(element('error').textContent,/14\/10\/2026/);
 assert.ok(!element('error').textContent.includes('bonificação'));
 console.log('run switch, abort and run-scoped writes: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result = subprocess.run(
        [shutil.which("node") or "node", "-e", script, str(ROOT / "dashboard/radar.js")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_radar_page_registry_unavailable_is_an_empty_blocked_state():
    script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const fields={},pending=[];
function element(id){return fields[id]??={id,value:'',disabled:false,hidden:true,textContent:'',innerHTML:'',dataset:{},listeners:{},classList:{toggle(){}},addEventListener(k,f){this.listeners[k]=f},querySelectorAll(){return [element(id+'-input')]},closest(){return element(id+'-label')}}}
function fetch(url,options={}){return new Promise(resolve=>pending.push({url,reply:(data,ok)=>resolve({ok,json:async()=>data})}))}
const ctx=vm.createContext({document:{getElementById:element},fetch,URLSearchParams,AbortController,location:{search:'',hash:''},history:{replaceState(){}},setTimeout,clearTimeout,setInterval,clearInterval,console});
ctx.window=ctx;ctx.addEventListener=()=>{};ctx.dispatchEvent=()=>{};ctx.PopStateEvent=class {};
vm.runInContext(fs.readFileSync(require('node:path').join(require('node:path').dirname(process.argv[1]),'market-ui.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
(async()=>{
 pending.shift().reply({error:'registry_corrupted'},false);await new Promise(r=>setTimeout(r,20));
 assert.equal(pending.length,0);  // no run is picked and no view is requested
 assert.equal(element('radar-run').disabled,true);
 assert.equal(element('prepare').disabled,true);assert.equal(element('preflight').disabled,true);
 assert.equal(element('add-form-input').disabled,true);
 assert.match(element('error').textContent,/corrompido/);assert.equal(element('error').hidden,false);
 console.log('registry unavailable: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result = subprocess.run(
        [shutil.which("node") or "node", "-e", script, str(ROOT / "dashboard/radar.js")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_radar_budget_authorization_is_reviewed_in_ui_before_paid_confirmation():
    result = subprocess.run(
        [
            shutil.which("node") or "node",
            str(ROOT / "tests/radar_budget_ui_check.js"),
            str(ROOT / "dashboard/radar.js"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
