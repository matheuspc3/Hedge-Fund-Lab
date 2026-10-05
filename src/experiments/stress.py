"""Stress Probing do H2 (Amendment 6, ``STRESS_PROBING_FREEZE_V1``).

O Stress não tem autoridade de calibração: tenta falsificar o comportamento do
sistema JÁ congelado, exercita mercado adverso e confere contratos causais e de
risco. Resultado financeiro é DIAGNOSTIC / DEVELOPMENT EVIDENCE ONLY e nunca
escolhe parâmetro. Os únicos gates são de integridade/contrato (S-A, S-T, S-C,
S-R).

```text
domínio      2018-01-12..2024-02-28, snapshot corrigido
universo     os 20 estratos NÃO-CAL-B do Amendment 2, fronteiras exatas
janela       um estrato completo:
               decisões   primeira .. penúltima sessão do estrato
               liquidação última sessão do estrato (execução + marcação)
               no_order_execution_may_cross_stress_window_boundary: a janela é
               declarada como fronteira ao runner (``boundaries``), que recusa
               liquidação fora dela antes de construir o participante e corta
               os dados de mercado na última sessão
seleção      só dados de MERCADO, só sessões DENTRO de cada estrato elegível;
             4 categorias nesta ordem, uma janela cada; ordem adversa, empate
             -> menor stratum_id; vencedor já escolhido -> próximo do ranking
R            3 repetições live independentes por janela, sem seed (12 runs)
```
"""

import asyncio
import hashlib
import math
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

import pandas as pd

from src.agents.features import canonical_number
from src.agents.llm_client import MockLLMClient
from src.agents.risk_manager import RiskConfig, RiskManager
from src.agents.state import RiskVerdict, TechnicalSignal
from src.artifacts import canonical_json
from src.experiments.anchors import (
    ANCHOR_SNAPSHOT_ID,
    ANCHOR_WINDOW,
    CAL_A_DISCRIMINATION,
    CAL_A_SELECTED_CONFIG,
    CAL_A_SELECTION_BASIS,
    CAL_B_STRATA,
    STRATA,
    Stratum,
)
from src.experiments.hardening import (
    H2_FROZEN_THINKING_LEVEL,
    H_REAL_SESSIONS,
    h2_freeze_v1_params,
)
from src.experiments.phases import (
    SEQUENTIAL_DEV_DISCRIMINATION,
    SEQUENTIAL_DEV_SELECTED_CONFIG,
    SEQUENTIAL_DEV_SELECTION_BASIS,
    PhaseWindow,
)

STRESS_PROBING_FREEZE = "STRESS_PROBING_FREEZE_V1"
STRESS_SNAPSHOT_ID = ANCHOR_SNAPSHOT_ID
STRESS_DOMAIN = ANCHOR_WINDOW
STRESS_TICKER = "PETR4.SA"

#: Universo de seleção: os 20 estratos que não são CAL-B. CAL-B fica FORA:
#: nenhuma métrica de seleção, decisão, liquidação ou performance sobre ele.
STRESS_ELIGIBLE_STRATA: tuple[Stratum, ...] = tuple(
    s for s in STRATA if s.stratum_id not in CAL_B_STRATA
)

#: Ordem fixa das categorias -> (métrica de mercado, ordem adversa decrescente?).
STRESS_CATEGORIES: tuple[tuple[str, str, bool], ...] = (
    ("MAX_DRAWDOWN", "market_max_drawdown", True),
    ("MAX_REALIZED_VOLATILITY", "realized_volatility", True),
    ("WORST_DAILY_RETURN", "worst_daily_return", False),
    ("MAX_ABS_OVERNIGHT_GAP", "max_abs_overnight_gap", True),
)
STRESS_WINDOW_COUNT = len(STRESS_CATEGORIES)
STRESS_TIE_BREAK = "LOWEST_STRATUM_ID"
STRESS_REPETITIONS = 3
STRESS_BOUNDARY_INVARIANT = "no_order_execution_may_cross_stress_window_boundary"

#: H2 congelado, nada recalibrado: freeze v1 (LOW) + CAL-A + Sequential Dev.
STRESS_FROZEN_PARAMS: Mapping[str, Any] = MappingProxyType({
    "ticker": STRESS_TICKER,
    **h2_freeze_v1_params(H2_FROZEN_THINKING_LEVEL),
    "volatility_window": CAL_A_SELECTED_CONFIG["volatility_window"],
    "risk_max_volatility": CAL_A_SELECTED_CONFIG["risk_max_volatility"],
    "risk_max_drawdown": SEQUENTIAL_DEV_SELECTED_CONFIG["risk_max_drawdown"],
})

#: Os três valores calibrados vieram do fallback de empate do protocolo, não de
#: desempenho superior.
CALIBRATION_PROVENANCE: Mapping[str, str] = MappingProxyType({
    "CAL_A_DISCRIMINATION": CAL_A_DISCRIMINATION,
    "CAL_A_SELECTION_BASIS": CAL_A_SELECTION_BASIS,
    "SEQUENTIAL_DEV_DISCRIMINATION": SEQUENTIAL_DEV_DISCRIMINATION,
    "SEQUENTIAL_DEV_SELECTION_BASIS": SEQUENTIAL_DEV_SELECTION_BASIS,
})

#: Gates de integridade/contrato. Não existe threshold de retorno, Sharpe,
#: Sortino, MDD ou turnover: perder dinheiro no Stress é evidência válida.
STRESS_GATES: Mapping[str, str] = MappingProxyType({
    "S-A": "final technical/provider failures == 0 (retry recuperado não conta)",
    "S-T": "MAX_TOKENS / length truncations == 0",
    "S-C": "0 ordens fora da janela, 0 retorno futuro, 0 decisão/ordem em CAL-B, "
           "0 acesso a Validation/Final",
    "S-R": "toda COMPRA com drawdown canônico > 0.25 ou volatilidade canônica > 0.40 "
           "termina em regra dura ANTES do LLM de risco; sem ocorrência -> NOT_EXERCISED",
})


# ── Compromisso das janelas ──────────────────────────────────────

#: Preenchidos SÓ pelo commit de compromisso, a partir de
#: ``docs/evidence/stress/selection.json`` calculado no commit do freeze. Vazio,
#: ``scripts/run_stress.py run`` recusa qualquer chamada ao provedor.
STRESS_FREEZE_COMMIT: str | None = "6a64c34e23509ea080ba761421a6b0b91476b856"
#: Commit em que ``select`` calculou ``selection.json`` (filho do freeze; só
#: corrige a serialização da proveniência do snapshot).
STRESS_SELECTION_COMMIT: str | None = "2b4f578439091636bd7b753c8ef4356b39fe6001"
STRESS_SELECTION_EVIDENCE = "docs/evidence/stress/selection.json"
STRESS_SELECTED_WINDOWS: tuple[Mapping[str, Any], ...] = (
    MappingProxyType({"stress_id": "S1", "category": "MAX_DRAWDOWN", "stratum_id": 11,
                      "start": "2020-02-07", "last_decision": "2020-04-22", "end": "2020-04-23"}),
    MappingProxyType({"stress_id": "S2", "category": "MAX_REALIZED_VOLATILITY", "stratum_id": 2,
                      "start": "2018-03-29", "last_decision": "2018-06-11", "end": "2018-06-12"}),
    MappingProxyType({"stress_id": "S3", "category": "WORST_DAILY_RETURN", "stratum_id": 29,
                      "start": "2023-10-02", "last_decision": "2023-12-12", "end": "2023-12-13"}),
    MappingProxyType({"stress_id": "S4", "category": "MAX_ABS_OVERNIGHT_GAP", "stratum_id": 4,
                      "start": "2018-08-24", "last_decision": "2018-11-06", "end": "2018-11-07"}),
)


# ── Seleção market-only ──────────────────────────────────────────


def stratum_frame(frame: pd.DataFrame, stratum: Stratum) -> pd.DataFrame:
    """Barras do estrato elegível, e só elas; recusa CAL-B e sessão estranha."""
    if stratum.stratum_id in CAL_B_STRATA:
        raise ValueError(f"stratum {stratum.stratum_id} is CAL-B: outside the Stress universe")
    window = frame.loc[pd.Timestamp(stratum.first) : pd.Timestamp(stratum.last)]
    days = {str(day.date()) for day in window.index}
    if len(window) != stratum.size or days & set(H_REAL_SESSIONS):
        raise ValueError(f"stratum {stratum.stratum_id} sessions differ from the frozen domain")
    return window


def market_stress_metrics(window: pd.DataFrame) -> dict[str, float]:
    """M1-M4 sobre o close/open científico ajustado, só dentro da janela."""
    close = window["fechamento"].astype(float)
    returns = close.pct_change().dropna()
    gaps = (window["abertura"].astype(float) / close.shift(1) - 1.0).dropna()
    metrics = {
        "market_max_drawdown": float((1.0 - close / close.cummax()).max()),
        "realized_volatility": float(returns.std(ddof=1) * math.sqrt(252)),
        "worst_daily_return": float(returns.min()),
        "max_abs_overnight_gap": float(gaps.abs().max()),
    }
    if not all(math.isfinite(v) for v in metrics.values()):
        raise ValueError("non-finite market stress metric")
    return metrics


def rankings(metrics: Mapping[int, Mapping[str, float]]) -> dict[str, list[int]]:
    """Ranking adverso por categoria; empate -> menor stratum_id."""
    return {
        category: sorted(metrics, key=lambda sid: (-metrics[sid][key] if desc else metrics[sid][key], sid))
        for category, key, desc in STRESS_CATEGORIES
    }


def select_stress_windows(ranked: Mapping[str, Sequence[int]]) -> list[tuple[str, int]]:
    """Primeiro estrato ainda não escolhido de cada categoria, na ordem fixa."""
    chosen: list[tuple[str, int]] = []
    for category, _, _ in STRESS_CATEGORIES:
        used = {sid for _, sid in chosen}
        chosen.append((category, next(sid for sid in ranked[category] if sid not in used)))
    return chosen


def ranking_digest(ranking: Sequence[int], metrics: Mapping[int, Mapping[str, float]], key: str) -> str:
    """SHA-256 do ranking completo de uma categoria, com os escores."""
    rows = [[sid, metrics[sid][key]] for sid in ranking]
    return hashlib.sha256(canonical_json(rows).encode("utf-8")).hexdigest()


def stress_boundary(stress_id: str, stratum: Stratum) -> PhaseWindow:
    """A janela de Stress como fronteira do runner: o estrato inteiro."""
    if stratum.stratum_id in CAL_B_STRATA:
        raise ValueError(f"stratum {stratum.stratum_id} is CAL-B: outside the Stress universe")
    return PhaseWindow(f"STRESS_{stress_id}", stratum.first, stratum.last)


# ── Probes determinísticos do contrato de risco ──────────────────

#: (nome, sinal, drawdown bruto, volatilidade bruta, regra esperada).
#: Regra esperada ``None`` + sinal COMPRA = nenhuma regra dura veta e o LLM de
#: risco é consultado; ``"AUTO_APPROVE"`` = VENDA/MANTER aprovados sem LLM.
#: Os valores 0.2499996/0.2500004/0.2500006 (e os de volatilidade) testam a
#: quantização de 6 casas: a regra vê o valor canônico.
RISK_PROBE_CASES: tuple[tuple[str, str, float, float, str | None], ...] = (
    ("dd_0.249999", "COMPRA", 0.249999, 0.20, None),
    ("dd_0.250000", "COMPRA", 0.250000, 0.20, None),
    ("dd_0.250001", "COMPRA", 0.250001, 0.20, "DRAWDOWN"),
    ("dd_raw_0.2499996_canon_0.250000", "COMPRA", 0.2499996, 0.20, None),
    ("dd_raw_0.2500004_canon_0.250000", "COMPRA", 0.2500004, 0.20, None),
    ("dd_raw_0.2500006_canon_0.250001", "COMPRA", 0.2500006, 0.20, "DRAWDOWN"),
    ("vol_0.399999", "COMPRA", 0.0, 0.399999, None),
    ("vol_0.400000", "COMPRA", 0.0, 0.400000, None),
    ("vol_0.400001", "COMPRA", 0.0, 0.400001, "VOLATILITY"),
    ("vol_raw_0.3999996_canon_0.400000", "COMPRA", 0.0, 0.3999996, None),
    ("vol_raw_0.4000004_canon_0.400000", "COMPRA", 0.0, 0.4000004, None),
    ("vol_raw_0.4000006_canon_0.400001", "COMPRA", 0.0, 0.4000006, "VOLATILITY"),
    ("buy_both_breached_volatility_first", "COMPRA", 0.30, 0.50, "VOLATILITY"),
    ("sell_dd_breached", "VENDA", 0.30, 0.20, "AUTO_APPROVE"),
    ("sell_vol_breached", "VENDA", 0.0, 0.50, "AUTO_APPROVE"),
    ("sell_both_breached", "VENDA", 0.30, 0.50, "AUTO_APPROVE"),
    ("hold_dd_breached", "MANTER", 0.30, 0.20, "AUTO_APPROVE"),
    ("hold_vol_breached", "MANTER", 0.0, 0.50, "AUTO_APPROVE"),
    ("hold_both_breached", "MANTER", 0.30, 0.50, "AUTO_APPROVE"),
)


def risk_contract_probes() -> list[dict[str, Any]]:
    """Roda cada caso no ``RiskManager`` congelado com um LLM de risco contável.

    Sem performance financeira e sem escolher nada: só o contrato das regras
    duras (``>`` sobre o valor canônico) e se o LLM de risco foi chamado.
    """
    config = RiskConfig(
        max_volatility=STRESS_FROZEN_PARAMS["risk_max_volatility"],
        max_drawdown=STRESS_FROZEN_PARAMS["risk_max_drawdown"],
        max_concentration=STRESS_FROZEN_PARAMS["risk_max_concentration"],
    )
    rows = []
    for name, signal, drawdown, volatility, expected in RISK_PROBE_CASES:
        llm = MockLLMClient({RiskVerdict: RiskVerdict(verdict="APROVADO", analysis="probe")})
        state = {
            "technical_signal": TechnicalSignal(signal=signal, justification="probe", confidence=0.5),
            "current_drawdown": drawdown,
            "recent_volatility": volatility,
            "equity": 100_000.0,
            "current_price": 10.0,
            "position": 0.0,
        }
        result = asyncio.run(RiskManager(llm, config).evaluate(state))  # type: ignore[arg-type]
        source, rule = result["risk_source"], result["risk_rule"]
        if expected is None:
            ok = source == "LLM" and len(llm.calls) == 1
        elif expected == "AUTO_APPROVE":
            ok = source == "AUTO_APPROVE" and result["risk_verdict"].verdict == "APROVADO" and not llm.calls
        else:
            ok = source == "HARD_RULE" and rule == expected and not llm.calls
        rows.append({
            "case": name,
            "signal": signal,
            "raw_drawdown": drawdown,
            "raw_volatility": volatility,
            "canonical_drawdown": canonical_number(drawdown),
            "canonical_volatility": canonical_number(volatility),
            "expected": expected or "NO_HARD_VETO_LLM_CONSULTED",
            "risk_source": source,
            "risk_rule": rule,
            "verdict": result["risk_verdict"].verdict,
            "llm_risk_calls": len(llm.calls),
            "pass": ok,
        })
    return rows
