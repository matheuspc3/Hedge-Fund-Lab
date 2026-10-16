"""Exploratory advisory committees. No wallet, sizing, order or settlement path."""

import asyncio
import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from urllib import request

import numpy as np
import pandas as pd

from src.agents.features import canonical_metrics, dimensionless_features
from src.agents.llm_client import LLMCallMetadata, LLMClient
from src.agents.state import RiskVerdict
from src.agents.technical_analyst import (
    INDICATOR_KEYS,
    AnalystEnsembleConfig,
    create_technical_analyst_ensemble_node,
)
from src.agents.technical_evidence import allowed_evidence_codes, canonical_features
from src.artifacts import canonical_json
from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.daily_agent import _exclusive_state_lock
from src.experiments.h2_evaluation_manifest import CANDIDATE, read, sha_file
from src.experiments.h2_evaluation_offline import no_network
from src.experiments.h2_evaluation_production import CallBank, DurableGeminiClient
from src.pipeline.b3_official import (
    COTAHIST_URL,
    B3OfficialAdjustedExtractor,
    read_cotahist,
)
from src.pipeline.transform import DataTransformer, validate_ohlcv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/radar/hfl_multiasset_v1"
IDENTITY = "HFL-MULTIASSET-RADAR-V1"
EXAMPLES = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
GLOBAL_BUDGET_USD = 5.0
MIN_HISTORY = 200
MAX_OUTPUT = 8192
MODEL = "gemini-3.8-flash"
OPTIONS = {"temperature": 1.0, "thinking_level": "low", "max_output_tokens": MAX_OUTPUT}
RISK_PROMPT = """Você avalia risco consultivo de um ativo, sem carteira nem ordens.
Use apenas o consenso, as features e a volatilidade anualizada fornecidos.
Retorne RiskVerdict: APROVADO ou VETADO e análise objetiva em português.
Confiança é qualitativa. Não invente concentração, caixa, posições, drawdown
da carteira, capacidade de compra ou retorno esperado. A aprovação se refere
somente ao parecer técnico; a adequação à carteira permanece NÃO AVALIADA.
Não substitua os limites determinísticos. Não proponha quantidades ou pesos."""


def now():
    return pd.Timestamp.now(tz="America/Sao_Paulo")


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def tickers(values, *, empty=True):
    if not isinstance(values, list) or len(values) > 5 or (not values and not empty):
        raise ValueError("select_one_to_five_tickers")
    if any(not isinstance(v, str) for v in values):
        raise ValueError("invalid_ticker")
    result = [v.upper().removesuffix(".SA") for v in values]
    if len(set(result)) != len(result) or any(
        not re.fullmatch(r"[A-Z]{4}[3-8]", v) for v in result
    ):
        raise ValueError("invalid_or_duplicate_ticker")
    return result


def session(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("invalid_session")
    day = pd.Timestamp(value)
    if not B3Calendar().is_session(day.date()):
        raise ValueError("not_a_b3_session")
    return day


def last_closed(at=None):
    at = now() if at is None else at
    day = at.date() if at.hour >= 18 else at.date() - timedelta(days=1)
    return str(B3Calendar().sessions_between(day - timedelta(days=31), day)[-1])


def write(path, value, *, immutable=False):
    """fsync then same-directory atomic publication; never truncate a record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (canonical_json(value) + "\n").encode()
    if immutable and path.exists():
        if path.read_bytes() != data:
            raise ValueError("immutable_record_differs")
        return
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def event(folder, kind, **fields):
    payload = {"event": kind, "at": now().isoformat(), **fields}
    write(
        folder / "events" / (uuid.uuid4().hex + ".json"),
        {"payload": payload, "sha256": digest(payload)},
        immutable=True,
    )


def history(folder):
    events = []
    for path in (folder / "events").glob("*.json"):
        value = read(path)
        if digest(value["payload"]) != value["sha256"]:
            raise ValueError("event_integrity_failed")
        events.append(value["payload"])
    return sorted(events, key=lambda item: item["at"])


def frozen_sources():
    candidate = read(CANDIDATE)
    sources = candidate["sources_sha256"]
    if sha_file(CANDIDATE) != CANDIDATE.with_suffix(".sha256").read_text().strip():
        raise ValueError("original_manifest_changed")
    for name, expected in sources.items():
        if sha_file(ROOT / name) != expected:
            raise ValueError("original_source_changed")
    return {
        **sources,
        **{
            name: sha_file(ROOT / name)
            for name in (
                "scripts/multiasset_radar.py",
                "scripts/run_multiasset_radar.py",
                "dashboard/radar_api.py",
            )
        },
    }


def manifest(mode):
    return {
        "schema_version": 1,
        "identity": IDENTITY,
        "classification": "EXPLORATORY_ADVISORY_NOT_OA1_NOT_FINAL_TEST",
        "mode": mode,
        "model": MODEL,
        "technical": {
            "analyst_count": 5,
            "threshold": 0.6,
            "prompt_version": 5,
            "require_all_votes": True,
            "generation": OPTIONS,
        },
        "risk": {
            "prompt": RISK_PROMPT,
            "max_asset_volatility": 0.5,
            "portfolio_risk": "NOT_EVALUATED",
        },
        "minimum_history_sessions": MIN_HISTORY,
        "max_concurrent_tickers": 1,
        "max_concurrent_requests": 1,
        "max_http_attempts_per_call": 1,
        "global_budget_usd": GLOBAL_BUDGET_USD,
        "sources_sha256": frozen_sources(),
    }


def configure(values, root=OUTPUT):
    values = tickers(values)
    root = storage_root(root)
    with _exclusive_state_lock(root / "universe.json"):
        write(
            root / "universe.json",
            {
                "schema_version": 1,
                "identity": IDENTITY,
                "tickers": values,
                "updated_at": now().isoformat(),
            },
        )
    return values


class RadarExtractor(B3OfficialAdjustedExtractor):
    """Reuse original adjustment and corporate-event guards, isolated writable cache."""

    def _cotahist(self, year):
        if year in getattr(self, "paths", {}):
            return self.paths[year]
        scientific = ROOT / f"data/raw/cotahist/COTAHIST_A{year}.ZIP"
        path = (
            scientific
            if year < now().year and scientific.exists()
            else self.cache_dir / scientific.name
        )
        if path == self.cache_dir / scientific.name:
            url = request.Request(
                COTAHIST_URL.format(year=year), headers={"User-Agent": "Mozilla/5.0"}
            )
            with request.urlopen(url, timeout=600) as response:
                write(path, response.read())
        self.files[path.name] = sha_file(path)
        if not hasattr(self, "paths"):
            self.paths = {}
        self.paths[year] = path
        return path


def technical_input(bars):
    validate_ohlcv(bars)
    if len(bars) < MIN_HISTORY:
        raise ValueError("insufficient_history_200_sessions")
    if bars.index.tz is not None or not bars.index.equals(bars.index.normalize()):
        raise ValueError("invalid_bar_sessions")
    if (bars["volume"] <= 0).any():
        raise ValueError("session_without_trading")
    expected = pd.DatetimeIndex(
        B3Calendar().sessions_between(bars.index[0].date(), bars.index[-1].date())
    )
    if not bars.index.equals(expected):
        raise ValueError("missing_or_extra_b3_sessions")
    row = DataTransformer().calculate_indicators(bars).iloc[-1]
    features = canonical_features(
        dimensionless_features(
            float(row["fechamento"]),
            {k: float(row[k]) for k in INDICATOR_KEYS if pd.notna(row[k])},
        )
    )
    volatility = float(
        bars["fechamento"].pct_change().dropna().tail(21).std(ddof=1) * math.sqrt(252)
    )
    return features, canonical_metrics({"asset_volatility_21": volatility})


def synthetic_bars(end, offset=0):
    dates = pd.DatetimeIndex(
        B3Calendar().sessions_between((end - pd.Timedelta(days=450)).date(), end.date())
    )[-260:]
    steps = np.arange(len(dates))
    close = 30 + offset * 10 + steps * 0.02 + np.sin(steps / 8)
    return pd.DataFrame(
        {
            "abertura": close * 0.999,
            "maxima": close * 1.01,
            "minima": close * 0.99,
            "fechamento": close,
            "volume": np.full(len(dates), 1e6),
        },
        index=dates,
    )


def prepare(values, root=OUTPUT, *, end=None, mode="live", extractor=None, at=None):
    values = tickers(values, empty=False)
    if mode not in ("live", "synthetic"):
        raise ValueError("invalid_mode")
    at = now() if at is None else at
    end = session(end or last_closed(at))
    if end > pd.Timestamp(last_closed(at)):
        raise ValueError("session_not_closed")
    root = storage_root(root)
    results = []
    # ponytail: one local writer and one active batch. Distributed operation needs a transactional lock.
    with _exclusive_state_lock(root / "operation"):
        doc = manifest(mode)
        for index, ticker in enumerate(values):
            folder = root / "analyses" / ticker / str(end.date())
            try:
                if (folder / "input.json").exists():
                    frozen = read(folder / "input.json")
                    if frozen["manifest"] != doc:
                        raise ValueError("prepared_identity_differs")
                    checked_input(root, ticker, str(end.date()))
                else:
                    provider = extractor or RadarExtractor(
                        cache_dir=str(root / "cotahist")
                    )
                    if mode == "synthetic":
                        bars = synthetic_bars(end, index)
                        source = {"name": "SYNTHETIC_OFFLINE_NOT_MARKET_DATA"}
                        raw = {k: float(v) for k, v in bars.iloc[-1].items()}
                    else:
                        # User chooses a coverage interval of 450 days; no assumption of a 2016 listing.
                        bars = provider.download(
                            ticker + ".SA",
                            str((end - pd.Timedelta(days=450)).date()),
                            str(end.date()),
                        )
                        source = provider.source_description()
                        rawbars = read_cotahist(provider._cotahist(end.year), ticker)
                        raw = {k: float(v) for k, v in rawbars.loc[end].items()}
                    if bars.empty or bars.index[-1] != end:
                        raise ValueError("no_trading_on_reference_session")
                    features, metrics = technical_input(bars)
                    csv = bars.to_csv(lineterminator="\n").encode()
                    write(folder / "bars.csv", csv, immutable=True)
                    frozen = {
                        "schema_version": 1,
                        "identity": IDENTITY,
                        "ticker": ticker,
                        "session": str(end.date()),
                        "prepared_at": at.isoformat(),
                        "manifest": doc,
                        "manifest_sha256": digest(doc),
                        "history": {
                            "sha256": hashlib.sha256(csv).hexdigest(),
                            "start": str(bars.index[0].date()),
                            "bars": len(bars),
                        },
                        "adjusted_close": float(bars.iloc[-1]["fechamento"]),
                        "raw_bar": raw,
                        "source": source,
                        "features": features,
                        "risk_metrics": metrics,
                    }
                    write(folder / "input.json", frozen, immutable=True)
                    event(
                        folder, "PREPARED", input_sha256=sha_file(folder / "input.json")
                    )
                results.append(
                    {"ticker": ticker, "session": str(end.date()), "status": "PREPARED"}
                )
            except Exception as exc:
                # Each ticker commits independently; a sibling failure never deletes data.
                results.append(
                    {
                        "ticker": ticker,
                        "session": str(end.date()),
                        "status": "BLOCKED",
                        "error": type(exc).__name__ + ": " + str(exc),
                    }
                )
        write(
            root / "last_prepare.json",
            {"generated_at": now().isoformat(), "items": results},
        )
    return results


def storage_root(root):
    root = Path(root).resolve()
    protected = ("src", "data/forward", "data/runs", "data/snapshots", "data/raw")
    if root == ROOT or any(root.is_relative_to(ROOT / name) for name in protected):
        raise ValueError("radar_storage_must_be_isolated")
    return root


def folder_for(root, ticker, day):
    root = storage_root(root)
    folder = (
        root / "analyses" / tickers([ticker])[0] / str(session(day).date())
    ).resolve()
    if not folder.is_relative_to(root):
        raise ValueError("invalid_analysis_path")
    return folder


def checked_input(root, ticker, day):
    folder = folder_for(root, ticker, day)
    data = read(folder / "input.json")
    if (
        data["identity"] != IDENTITY
        or data["ticker"] != ticker
        or data["session"] != day
        or digest(data["manifest"]) != data["manifest_sha256"]
        or data["manifest"] != manifest(data["manifest"]["mode"])
        or sha_file(folder / "bars.csv") != data["history"]["sha256"]
    ):
        raise ValueError("frozen_input_or_identity_changed")
    bars = pd.read_csv(
        folder / "bars.csv", index_col=0, parse_dates=True, float_precision="round_trip"
    )
    features, metrics = technical_input(bars)
    if (
        str(bars.index[-1].date()) != day
        or features != data["features"]
        or metrics != data["risk_metrics"]
        or len(bars) != data["history"]["bars"]
        or float(bars.iloc[-1]["fechamento"]) != data["adjusted_close"]
    ):
        raise ValueError("frozen_features_differ")
    return data


def estimate(data):
    """Conservative byte bound (one token <= one UTF-8 byte), no automatic retry."""
    # Reserve 32k input tokens per request; the transport guard enforces the bound.
    # Upper rates also cover the announced 2027 increase; current estimate is separate.
    return {
        "calls_max": 6,
        "input_tokens_max_per_call": 32768,
        "output_tokens_max_per_call": MAX_OUTPUT,
        "usd_estimated": round(6 * (2500 * 0.75 + 800 * 3.75) / 1e6, 5),
        "usd_reserved": round(6 * (32768 * 1.5 + MAX_OUTPUT * 7.5) / 1e6, 6),
        "price_source": "https://ai.google.dev/gemini-api/docs/pricing",
        "price_checked": "2026-10-11",
        "currency": "USD",
        "estimated_tokens_note": "planning assumption, not observed usage",
        "paid": data["manifest"]["mode"] == "live",
    }


def budget_used(root):
    return sum(
        read(p)["usd_reserved"] for p in (Path(root) / "reservations").glob("*.json")
    )


def preflight(values, root=OUTPUT, *, day=None, max_usd=GLOBAL_BUDGET_USD, replay=False):
    values = tickers(values, empty=False)
    if (
        isinstance(max_usd, bool)
        or not isinstance(max_usd, (int, float))
        or not math.isfinite(max_usd)
        or not 0 < max_usd <= GLOBAL_BUDGET_USD
    ):
        raise ValueError("invalid_budget")
    day = str(session(day or last_closed()).date())
    items = []
    with no_network():
        for ticker in values:
            try:
                data = checked_input(root, ticker, day)
                folder = folder_for(root, ticker, day)
                if (
                    data["manifest"]["mode"] == "live"
                    and not replay
                    and not os.environ.get("GEMINI_API_KEY", "").strip()
                ):
                    raise ValueError("gemini_api_key_missing")
                if not replay and any(
                    (folder / name).exists()
                    for name in (
                        "claim.json",
                        "calls.sqlite",
                        "provider_journal.jsonl",
                        "result.json",
                        "failure.json",
                    )
                ):
                    raise ValueError("inference_already_reserved_replay_only")
                if replay and not (folder / "claim.json").exists():
                    raise ValueError("nothing_to_replay")
                items.append(
                    {
                        "ticker": ticker,
                        "session": day,
                        "ready": True,
                        "input_sha256": sha_file(folder / "input.json"),
                        "estimate": estimate(data),
                        "mode": data["manifest"]["mode"],
                    }
                )
            except (ValueError, OSError, KeyError) as exc:
                items.append(
                    {"ticker": ticker, "session": day, "ready": False, "error": str(exc)}
                )
    total = round(
        sum(
            i["estimate"]["usd_reserved"]
            for i in items
            if i["ready"] and i["mode"] == "live"
        ),
        6,
    )
    used = budget_used(root)
    result = {
        "identity": IDENTITY,
        "session": day,
        "items": items,
        "replay": replay,
        "max_usd": max_usd,
        "usd_reserved": 0 if replay else total,
        "global_budget_used": used,
        "global_budget_cap": GLOBAL_BUDGET_USD,
        "usd_estimated": 0
        if replay
        else round(
            sum(
                i["estimate"]["usd_estimated"]
                for i in items
                if i["ready"] and i["mode"] == "live"
            ),
            5,
        ),
        "ready": all(i["ready"] for i in items)
        and (replay or total <= max_usd and used + total <= GLOBAL_BUDGET_USD),
    }
    result["confirmation_token"] = digest(result)
    return result


class RadarGeminiClient(DurableGeminiClient):
    def begin_session(self, value):
        # New advisory identity has its own sessions, never an OA-1 phase/window.
        self.session = str(session(value).date())
        LLMClient.begin_session(self, value)

    def _transport(self, method, url, headers, body):
        if len(json.dumps(body, ensure_ascii=False).encode()) > 32768:
            raise ValueError("request_exceeds_reserved_token_bound")
        return super()._transport(method, url, headers, body)

    async def generate(self, *args, **kwargs):
        async with self.semaphore:
            return await super().generate(*args, **kwargs)


def fake_gemini(method, url, headers, body):
    """Fake native response exercising the real parser and durable journal."""
    payload = body
    prompt = json.loads(payload["contents"][0]["parts"][0]["text"])
    if "allowed_evidence_codes" in prompt:
        f = prompt["features"]
        direction = "COMPRA" if f["sma50_gap"] > 0 else "VENDA"
        response = {
            "signal": direction,
            "confidence": 0.7,
            "evidence": [
                {
                    "code": prompt["allowed_evidence_codes"][0],
                    "role": "SUPPORTS_" + direction,
                }
            ],
        }
    else:
        response = {
            "verdict": "APROVADO",
            "analysis": "Parecer sintético; adequação à carteira não avaliada.",
            "risk_metrics": {},
        }
    return json.dumps(
        {
            "candidates": [
                {
                    "content": {"parts": [{"text": json.dumps(response)}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 80,
                "thoughtsTokenCount": 20,
                "totalTokenCount": 200,
            },
            "modelVersion": MODEL,
            "responseId": "OFFLINE_FAKE",
        }
    ).encode()


async def committee(data, client):
    client.begin_session(data["session"])
    state = {
        "ticker": data["ticker"],
        "date": data["session"],
        "current_price": data["adjusted_close"],
        "features": data["features"],
        "errors": [],
    }
    node = create_technical_analyst_ensemble_node(
        client,
        AnalystEnsembleConfig(
            analyst_count=5,
            consensus_threshold=0.6,
            require_all_votes=True,
            temperature_min=1.0,
            temperature_max=1.0,
            prompt_version=5,
        ),
        OPTIONS,
    )
    technical = await node(state)
    if technical["errors"] or len(technical["technical_votes"]) != 5:
        raise ValueError("incomplete_or_invalid_committee")
    metrics = data["risk_metrics"]
    if metrics["asset_volatility_21"] > 0.5:
        risk = RiskVerdict(
            verdict="VETADO",
            analysis="Volatilidade do ativo acima de 50% anualizados.",
            risk_metrics=metrics,
        )
        source = "HARD_ASSET_VOLATILITY_RULE"
    else:
        risk = await client.generate(
            RISK_PROMPT,
            canonical_json(
                {
                    "technical_signal": technical["technical_signal"].model_dump(),
                    "features": data["features"],
                    "asset_risk_metrics": metrics,
                }
            ),
            RiskVerdict,
            OPTIONS,
            metadata=LLMCallMetadata(stage="risk_manager"),
        )
        risk.risk_metrics = metrics
        source = "ADVISORY_LLM"
    return {
        "votes": [v.model_dump(mode="json") for v in technical["technical_votes"]],
        "consensus": technical["technical_consensus"].model_dump(mode="json"),
        "technical_signal": technical["technical_signal"].model_dump(mode="json"),
        "risk": risk.model_dump(mode="json"),
        "risk_source": source,
        "portfolio_risk": "NOT_EVALUATED",
        "portfolio_manager": "NOT_INVOKED",
        "recommendation": technical["technical_signal"].signal
        if risk.verdict == "APROVADO"
        else "MANTER",
        "allowed_evidence_codes": allowed_evidence_codes(data["features"]),
    }


def run(
    values,
    token,
    root=OUTPUT,
    *,
    day=None,
    max_usd=GLOBAL_BUDGET_USD,
    authorize_paid=False,
    replay=False,
    transport=None,
):
    root = storage_root(root)
    with _exclusive_state_lock(root / "operation"):
        report = preflight(values, root, day=day, max_usd=max_usd, replay=replay)
        if not report["ready"] or token != report["confirmation_token"]:
            raise ValueError("preflight_or_confirmation_changed")
        if (
            not replay
            and any(i["mode"] == "live" for i in report["items"])
            and authorize_paid is not True
        ):
            raise ValueError("explicit_paid_authorization_required")
        if not replay:
            write(root / "reservations" / (token + ".json"), report, immutable=True)
        outcomes = []
        for item in report["items"]:
            ticker, day = item["ticker"], item["session"]
            folder = folder_for(root, ticker, day)
            bank = None
            try:
                data = checked_input(root, ticker, day)
                claim = {
                    "identity": IDENTITY,
                    "ticker": ticker,
                    "session": day,
                    "input_sha256": item["input_sha256"],
                    "batch_token": token,
                    "created_at": now().isoformat(),
                }
                if not replay:
                    write(folder / "claim.json", claim, immutable=True)
                    event(folder, "RESERVED", batch_token=token)
                else:
                    claim = read(folder / "claim.json")
                    if (
                        claim["input_sha256"] != item["input_sha256"]
                        or not (folder / "calls.sqlite").exists()
                    ):
                        raise ValueError("replay_claim_or_journal_missing")
                    if (folder / "result.sha256").exists():
                        outcomes.append(detail(ticker, day, root))
                        continue
                    event(folder, "OFFLINE_RECOVERY_STARTED")
                bank = CallBank(
                    folder / "calls.sqlite",
                    digest({"input": item["input_sha256"], "identity": IDENTITY}),
                    IDENTITY,
                )

                def gate(ticker=ticker, day=day, data=data):
                    if checked_input(root, ticker, day) != data:
                        raise ValueError("input_changed_before_transport")

                synthetic = item["mode"] == "synthetic"
                client = RadarGeminiClient(
                    bank,
                    "L01",
                    {"model": MODEL, "retry_attempts": 1, "retry_base_delay": 0},
                    fresh=not replay,
                    gate=gate,
                    transport=fake_gemini
                    if synthetic and transport is None
                    else transport,
                    synthetic=synthetic,
                )

                async def invoke(client=client, data=data):
                    client.semaphore = asyncio.Semaphore(1)
                    return await committee(data, client)

                if replay or synthetic:
                    with no_network():
                        result = asyncio.run(invoke())
                else:
                    result = asyncio.run(invoke())
                client.assert_complete()
                journal = bank.export("L01")
                records = [json.loads(line)["record"] for line in journal.splitlines()]
                usage = [r.get("token_usage") or {} for r in records]
                tokens = {
                    key: sum((u.get(key) or 0) for u in usage)
                    for key in (
                        "prompt_tokens",
                        "completion_tokens",
                        "thoughts_tokens",
                        "total_tokens",
                    )
                }
                rate = (0.75, 3.75) if now().year <= 2026 else (1.5, 7.5)
                cost = (
                    tokens["prompt_tokens"] * rate[0]
                    + (tokens["completion_tokens"] + tokens["thoughts_tokens"]) * rate[1]
                ) / 1e6
                result.update(
                    {
                        "schema_version": 1,
                        "identity": IDENTITY,
                        "ticker": ticker,
                        "session": day,
                        "mode": item["mode"],
                        "status": "COMPLETED",
                        "generated_at": claim["created_at"],
                        "completed_at": max(
                            pd.Timestamp(r["started_at"])
                            + pd.Timedelta(milliseconds=r["duration_ms"])
                            for r in records
                        ).isoformat(),
                        "input_sha256": item["input_sha256"],
                        "manifest_sha256": data["manifest_sha256"],
                        "history_sha256": data["history"]["sha256"],
                        "adjusted_close": data["adjusted_close"],
                        "raw_bar": data["raw_bar"],
                        "features": data["features"],
                        "source": data["source"],
                        "tokens": tokens,
                        "cost_usd": 0 if synthetic else cost,
                        "cost_basis": "provider tokens incl thinking; estimated billing, not invoice",
                        "provider_journal_sha256": hashlib.sha256(journal).hexdigest(),
                    }
                )
                write(folder / "provider_journal.jsonl", journal, immutable=True)
                write(folder / "result.json", result, immutable=True)
                write(
                    folder / "result.sha256",
                    (sha_file(folder / "result.json") + "\n").encode(),
                    immutable=True,
                )
                event(folder, "COMPLETED", result_sha256=sha_file(folder / "result.json"))
                outcomes.append(result)
            except Exception as exc:
                failure = {
                    "ticker": ticker,
                    "session": day,
                    "status": "FAILED_REPLAY_ONLY",
                    "error": type(exc).__name__,
                    "generated_at": now().isoformat(),
                }
                event(folder, "FAILED_REPLAY_ONLY", error=type(exc).__name__)
                write(folder / "failure.json", failure)
                outcomes.append(failure)
            finally:
                if bank is not None:
                    bank.close()
        return outcomes


def detail(ticker, day, root=OUTPUT):
    folder = folder_for(root, ticker, day)
    if not (folder / "result.sha256").exists():
        data = read(folder / "input.json")
        if sha_file(folder / "bars.csv") != data["history"]["sha256"]:
            raise ValueError("result_integrity_failed")
        votes, reserved = [], 0
        path = folder / "calls.sqlite"
        if path.exists():
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
                rows = db.execute(
                    "SELECT record,record_sha FROM calls WHERE slot='L01' ORDER BY sequence"
                ).fetchall()
            reserved = len(rows)
            for record, expected in rows:
                if record is None:
                    continue
                if hashlib.sha256(record.encode()).hexdigest() != expected:
                    raise ValueError("journal_record_integrity_failed")
                record = json.loads(record)
                if record["stage"] == "technical_analyst" and record["status"] == "ok":
                    votes.append(
                        {
                            "analyst_id": record["analyst_id"],
                            "signal": record["validated_response"],
                        }
                    )
        return {
            "identity": IDENTITY,
            "ticker": ticker,
            "session": day,
            "mode": data["manifest"]["mode"],
            "adjusted_close": data["adjusted_close"],
            "status": "FAILED_REPLAY_ONLY"
            if (folder / "claim.json").exists()
            else "PREPARED",
            "generated_at": data["prepared_at"],
            "votes": votes,
            "reserved_calls": reserved,
            "recommendation": None,
            "portfolio_risk": "NOT_EVALUATED",
            "history": history(folder),
        }
    result = read(folder / "result.json")
    if (
        sha_file(folder / "result.json") != (folder / "result.sha256").read_text().strip()
        or sha_file(folder / "provider_journal.jsonl")
        != result["provider_journal_sha256"]
        or sha_file(folder / "input.json") != result["input_sha256"]
        or sha_file(folder / "bars.csv") != result["history_sha256"]
    ):
        raise ValueError("result_integrity_failed")
    return {**result, "history": history(folder)}


def status(root=OUTPUT):
    root = storage_root(root)
    universe = (
        read(root / "universe.json")["tickers"]
        if (root / "universe.json").exists()
        else []
    )
    items = []
    for path in sorted((root / "analyses").glob("*/*/input.json"), reverse=True):
        ticker, day = path.parent.parent.name, path.parent.name
        try:
            items.append(detail(ticker, day, root))
        except (ValueError, OSError, KeyError, sqlite3.Error):
            items.append({"ticker": ticker, "session": day, "status": "INTEGRITY_ERROR"})
    return {
        "identity": IDENTITY,
        "universe": universe,
        "examples": list(EXAMPLES),
        "items": items,
        "global_budget_used": budget_used(root),
        "global_budget_cap": GLOBAL_BUDGET_USD,
        "last_closed_session": last_closed(),
        "last_prepare": read(root / "last_prepare.json")
        if (root / "last_prepare.json").exists()
        else None,
    }
