"""Diagnóstico de liquidez nominal que sustenta o CostSpec (protocolo §10).

LIQUIDITY DIAGNOSTIC EVIDENCE — NOT SCIENTIFIC MARKET INPUT.

A série daqui (yfinance ``auto_adjust=False``) é separada da série científica
(``auto_adjust=True``) e nunca é consumida pelo backtest. A regra abaixo foi
declarada antes do primeiro cálculo e ratificada com o CostSpec: mudá-la
exige nova ``METHOD_VERSION`` e nova ratificação, não uma nova execução.

Uso: python scripts/analyze_nominal_liquidity.py [--output caminho.json]
"""

import argparse
import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline.snapshot import _git_metadata  # noqa: E402

METHOD_VERSION = "costspec-nominal-liquidity-v1"
LABEL = "LIQUIDITY DIAGNOSTIC EVIDENCE — NOT SCIENTIFIC MARKET INPUT"
SYMBOLS = (
    "ABEV3.SA",
    "BBAS3.SA",
    "BBDC4.SA",
    "CMIG4.SA",
    "ITUB4.SA",
    "PETR4.SA",
    "RENT3.SA",
    "SUZB3.SA",
    "VALE3.SA",
    "WEGE3.SA",
)
START = "2016-01-01"
END = "2026-08-04"  # inclusivo
MINIMUM_HISTORY_SESSIONS = 504
ROLLING_SESSIONS = 252
ORDER_NOTIONAL_BRL = 100_000.0
# Eventos conhecidos: Close * Volume não pode quebrar pelo fator do evento.
SPLIT_EVENTS = (
    ("BBAS3.SA", "2024-04-16", 2.0),
    ("WEGE3.SA", "2021-04-28", 2.0),
    ("RENT3.SA", "2017-11-23", 3.0),
)
SPLIT_WINDOW_SESSIONS = 20
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "costspec_liquidity_check.json"


def download(symbol: str) -> pd.DataFrame:
    import yfinance as yf

    end_exclusive = (pd.Timestamp(END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    history = yf.Ticker(symbol).history(
        start=START, end=end_exclusive, auto_adjust=False, actions=True
    )
    if history is None or history.empty:
        raise RuntimeError(f"yfinance retornou série vazia para {symbol}")
    index = pd.DatetimeIndex(history.index)
    if index.tz is not None:
        index = cast(pd.DatetimeIndex, index.tz_localize(None))
    history.index = pd.DatetimeIndex(
        [cast(pd.Timestamp, pd.Timestamp(value)).normalize() for value in index]
    )
    return history


def eligible_sessions(frames: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Calendário comum de barras completas, a partir da 504ª sessão."""
    complete = [
        set(df.index[(df["Open"] > 0) & (df["Close"] > 0)]) for df in frames.values()
    ]
    common = sorted(set.intersection(*complete))
    return pd.DatetimeIndex(common[MINIMUM_HISTORY_SESSIONS - 1 :])


def liquidity(frame: pd.DataFrame, eligible: pd.DatetimeIndex) -> dict:
    fv = (frame["Close"] * frame["Volume"]).reindex(eligible)
    fv = fv[fv > 0]  # exclui volume zero e sessão ausente (NaN)
    rolling = fv.rolling(ROLLING_SESSIONS).median().dropna()
    worst = float(rolling.min())
    return {
        "sessions_used": int(len(fv)),
        "sessions_excluded_zero_volume": int(len(eligible) - len(fv)),
        "median_eligible_adv_brl": round(float(fv.median()), 2),
        "latest_252_median_adv_brl": round(
            float(fv.iloc[-ROLLING_SESSIONS:].median()), 2
        ),
        "worst_252_median_adv_brl": round(worst, 2),
        "worst_252_window_end": rolling.idxmin().date().isoformat(),
        "order_to_median_adv": round(ORDER_NOTIONAL_BRL / float(fv.median()), 8),
        "order_to_worst_adv": round(ORDER_NOTIONAL_BRL / worst, 8),
    }


def split_check(frame: pd.DataFrame, symbol: str, session: str, ratio: float) -> dict:
    """Close * Volume é invariante ao evento se Close e Volume usam o mesmo fator."""
    event = pd.Timestamp(session)
    splits = frame["Stock Splits"]
    recorded = float(cast(float, splits.get(event, 0.0)))

    def median_fv(bars: pd.DataFrame) -> float:
        fv = bars["Close"] * bars["Volume"]
        return float(fv[fv > 0].median())

    before = median_fv(
        cast(pd.DataFrame, frame.loc[frame.index < event]).tail(SPLIT_WINDOW_SESSIONS)
    )
    after = median_fv(
        cast(pd.DataFrame, frame.loc[frame.index >= event]).head(SPLIT_WINDOW_SESSIONS)
    )
    change = after / before
    # ponytail: heurística de escala — a quebra conta como artificial quando a
    # variação fica mais perto do fator do evento que de 1 (|log| >= log(k)/2).
    # Teto: mudança real de liquidez >= sqrt(k) na janela vira falso alarme;
    # upgrade: comparar com o volume financeiro oficial da B3.
    coherent = (
        math.isclose(recorded, ratio) and abs(math.log(change)) < math.log(ratio) / 2
    )
    return {
        "symbol": symbol,
        "session": session,
        "expected_ratio": ratio,
        "recorded_ratio": recorded,
        "window_sessions": SPLIT_WINDOW_SESSIONS,
        "median_fv_before_brl": round(before, 2),
        "median_fv_after_brl": round(after, 2),
        "fv_change": round(change, 6),
        "coherent": coherent,
    }


def content_sha256(document: dict) -> str:
    canonical = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_evidence(frames: dict[str, pd.DataFrame], provider_version: str) -> dict:
    eligible = eligible_sessions(frames)
    tickers = {symbol: liquidity(frame, eligible) for symbol, frame in frames.items()}
    worst_symbol = max(tickers, key=lambda s: tickers[s]["order_to_worst_adv"])
    checks = [
        split_check(frames[symbol], symbol, session, ratio)
        for symbol, session, ratio in SPLIT_EVENTS
    ]
    source_ok = all(check["coherent"] for check in checks)
    document = {
        "label": LABEL,
        "method_version": METHOD_VERSION,
        "purpose": "EXPERIMENT_PROTOCOL.md §10 — ADV check do CostSpec",
        "calculation_date": date.today().isoformat(),
        "provenance": {
            **_git_metadata(ROOT),
            "script": "scripts/analyze_nominal_liquidity.py",
            # LF-normalizado: o checkout no Windows pode trocar os finais de linha.
            "script_sha256": hashlib.sha256(
                Path(__file__).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
        },
        "provider": "yfinance",
        "provider_version": provider_version,
        "auto_adjust": False,
        "requested_symbols": list(frames),
        "requested_start": START,
        "requested_end_inclusive": END,
        "daily_financial_volume": "Close * Volume; volume zero e sessão ausente excluídos",
        "calendar": "sessões com barra completa (Open > 0 e Close > 0) em todos os símbolos",
        "minimum_history_sessions": MINIMUM_HISTORY_SESSIONS,
        "rolling_sessions": ROLLING_SESSIONS,
        "eligible_start": cast(pd.Timestamp, eligible[0]).date().isoformat(),
        "eligible_end": cast(pd.Timestamp, eligible[-1]).date().isoformat(),
        "eligible_sessions": int(len(eligible)),
        "order_notional_brl": ORDER_NOTIONAL_BRL,
        "provider_sanity": {
            "status": "PASS" if source_ok else "LIQUIDITY DIAGNOSTIC SOURCE UNSUITABLE",
            "split_checks": checks,
        },
        "tickers": tickers,
        "worst_case": {
            "ticker": worst_symbol,
            "worst_252_median_adv_brl": tickers[worst_symbol]["worst_252_median_adv_brl"],
            "order_to_worst_adv": tickers[worst_symbol]["order_to_worst_adv"],
            "rolling_window_end": tickers[worst_symbol]["worst_252_window_end"],
        },
        "content_sha256_method": (
            "sha256 do JSON canônico (sort_keys, separadores compactos, UTF-8) "
            "deste documento sem o campo content_sha256"
        ),
    }
    document["content_sha256"] = content_sha256(document)
    return document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnóstico de liquidez nominal do CostSpec."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    import yfinance as yf

    frames = {symbol: download(symbol) for symbol in SYMBOLS}
    evidence = build_evidence(frames, yf.__version__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    worst = evidence["worst_case"]
    print(
        f"{evidence['provider_sanity']['status']} · pior caso {worst['ticker']}: "
        f"{worst['order_to_worst_adv']:.4%} de R$ {worst['worst_252_median_adv_brl'] / 1e6:.1f} mi "
        f"(janela até {worst['rolling_window_end']}) -> {args.output}"
    )
    if evidence["provider_sanity"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
