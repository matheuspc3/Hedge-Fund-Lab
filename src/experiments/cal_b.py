"""CAL-B do H2 (Amendment 7, ``CAL_B_PROTOCOL_FREEZE_V1``): sanity check one-shot.

Não é teste de performance e não tem autoridade de tuning. Cada uma das 10
âncoras comprometidas recebe UMA realização live (com o SC interno N = 5),
decidida só com o information set até ``close(t)``. Nenhuma execução em
``open(t+1)``, nenhum preço posterior, nenhum retorno, P&L, Sharpe, Sortino,
MDD ou accuracy: a decisão e o intent são validados estruturalmente.

Gates automáticos: CB-A (completude), CB-S (schema/contrato), CB-C
(causalidade), CB-R (risco duro), CB-D (degeneração, ``total_hold_rate >=
0.90`` do Hardening). Depois deles, auditoria humana independente dos dois
autores (alucinação material e coerência rationale/ação) sobre o pacote
comportamental. O pré-filtro léxico daqui só aponta trechos para os revisores;
ele não aprova nem reprova nada.
"""

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

from src.agents.participant import FAILURE_CAUSES, RISK_VETO_CAUSES
from src.agents.state import PortfolioAction, RiskVerdict, TechnicalSignal
from src.agents.technical_analyst import build_prompt, system_prompt_for
from src.experiments.hardening import HOLD_RATE_CAUSES, H2_FREEZE_V1_GATES
from src.experiments.stress import STRESS_FROZEN_PARAMS
from src.experiments.treatment import stress_v2_params

CAL_B_PROTOCOL_FREEZE = "CAL_B_PROTOCOL_FREEZE_V1"
#: A configuração final de desenvolvimento é exatamente a do Stress.
CAL_B_FROZEN_PARAMS: Mapping[str, Any] = STRESS_FROZEN_PARAMS
CAL_B_INITIAL_CAPITAL = 100_000.0
#: Última data que a CAL-B pode tocar (fim do domínio de desenvolvimento).
CAL_B_MAX_SESSION = "2024-02-28"

#: Mesmo threshold estrutural do Hardening, sem threshold novo.
CAL_B_MAX_TOTAL_HOLD_RATE = H2_FREEZE_V1_GATES.max_total_hold_rate

CAL_B_PASS = "CAL_B_PASS — SANITY CHECK ONLY"
CAL_B_FAIL = "CAL_B_FAIL — HOLDOUT CONSUMED"
CAL_B_INVALID = "CAL_B_INVALID — PARTIAL HOLDOUT CONSUMED"
CAL_B_REVIEW_DISAGREEMENT = "CAL_B_REVIEW_DISAGREEMENT"
#: Estado intermediário (não final): gates automáticos passaram e a revisão
#: humana dos dois autores ainda não foi concluída.
CAL_B_AWAITING_HUMAN_REVIEW = "CAL_B_AWAITING_HUMAN_REVIEW"

SCHEMAS = {"TechnicalSignal": TechnicalSignal, "RiskVerdict": RiskVerdict, "PortfolioAction": PortfolioAction}
#: Campo de texto visível de cada schema (o único auditado; nada de hidden CoT).
RATIONALE_FIELDS = {"TechnicalSignal": "justification", "RiskVerdict": "analysis", "PortfolioAction": "reasoning"}

#: Pré-filtro léxico congelado ANTES da execução. Só sinaliza trechos para os
#: autores; a classificação PASS/FAIL é humana. Casa sem diferenciar caixa.
PRESCREEN_LEXICON: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "asset_identity": (r"\bpetr", r"petrobras", r"\bticker\b", r"\bb3\b", r"bovespa", r"ibovespa", r"estatal"),
    "calendar": (r"\b(19|20)\d{2}\b", r"\b(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|"
                 r"setembro|outubro|novembro|dezembro)\b", r"covid", r"pandemia"),
    "absolute_price": (r"r\$", r"\breais\b"),
    "external_information": (r"not[ií]cia", r"balan[çc]o", r"trimestr", r"dividend", r"\bjuros\b", r"selic",
                             r"infla[çc][ãa]o", r"d[óo]lar", r"c[âa]mbio", r"petr[óo]leo", r"\bbrent\b", r"\bopep\b",
                             r"governo", r"elei[çc]", r"pol[íi]tic", r"\bmacro", r"\bfed\b", r"guerra",
                             r"fundamentos?\b", r"lucro"),
    "volume": (r"\bvolume\b", r"liquidez"),
    "future": (r"amanh[ãa]", r"retorno futuro", r"pre[çc]o futuro"),
})


def prescreen(text: str) -> list[dict[str, str]]:
    """Trechos do texto visível que casam com o léxico (só sinalização)."""
    hits = []
    for category, patterns in PRESCREEN_LEXICON.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                hits.append({"category": category, "pattern": pattern, "match": match.group(0)})
    return hits


def hold_rates(final_causes: Sequence[str]) -> dict[str, Any]:
    """Taxas de HOLD com os códigos congelados do Hardening (NOOP fora)."""
    causes = Counter(final_causes)
    total = len(final_causes)
    rates: dict[str, Any] = {
        name: (sum(causes[c] for c in members) / total if total else None)
        for name, members in HOLD_RATE_CAUSES.items()
    }
    rates["total_hold_rate"] = sum(rates.values()) if total else None
    rates["total_holds"] = sum(causes[c] for members in HOLD_RATE_CAUSES.values() for c in members)
    rates["decisions"] = total
    rates["degenerate_inactive"] = total > 0 and rates["total_hold_rate"] >= CAL_B_MAX_TOTAL_HOLD_RATE
    return rates


def anchor_issues(
    anchor: str,
    decision: Mapping[str, Any] | None,
    records: Sequence[Any],
    expected_features: Mapping[str, float],
    expected_volatility: float,
    history_last_session: str,
    params: Mapping[str, Any] = CAL_B_FROZEN_PARAMS,
) -> dict[str, list[str]]:
    """Problemas por gate de UMA âncora, só de campos estruturados e do trace."""
    p = params
    issues: dict[str, list[str]] = {gate: [] for gate in ("CB-A", "CB-S", "CB-C", "CB-R")}
    if decision is None:
        issues["CB-A"].append("no decision record")
        return issues
    cause = decision["final_cause"]
    if cause is None or cause in FAILURE_CAUSES:
        issues["CB-A"].append(f"final_cause {cause}")
    if any(r.status != "ok" for r in records):
        issues["CB-A"].append("final failed provider call")

    # CB-S: quorum, schemas, contratos, nenhum fallback silencioso, truncamento.
    s = issues["CB-S"]
    technical = [r for r in records if r.request.stage == "technical_analyst"]
    if len(technical) != p["analyst_count"] or decision["valid_votes"] != p["analyst_count"]:
        s.append("incomplete quorum")
    if decision["analyst_count"] != p["analyst_count"] or decision["consensus_threshold"] != p["consensus_threshold"]:
        s.append("ensemble config differs from the freeze")
    if cause in ("INVALID_RESPONSE", "INVALID_INPUT"):
        s.append(f"final_cause {cause}")
    if decision["input_violations"]:
        s.append("missing scientific inputs")
    if decision["errors"] or decision["failures"]:
        s.append("errors/failures recorded (silent fallback)")
    if decision["risk_rule"] in ("INVALID_RESPONSE", "MISSING_SIGNAL", "MISSING_METRICS"):
        s.append(f"risk_rule {decision['risk_rule']}")
    if decision["portfolio_rule"] in ("DIRECTION_INVERSION", "INVALID_RESPONSE", "MISSING_INPUT"):
        s.append(f"portfolio_rule {decision['portfolio_rule']}")
    for r in records:
        if r.finish_reason != "STOP":
            s.append(f"{r.call_id}: finish_reason {r.finish_reason} (truncation/abnormal stop)")
        if r.resolved_model != p["model"]:
            s.append(f"{r.call_id}: resolved_model {r.resolved_model}")
        transport = dict(r.transport_options)
        if transport != {"max_output_tokens": p["max_output_tokens"], "temperature": p["temperature"],
                         "thinking_level": p["thinking_level"]}:
            s.append(f"{r.call_id}: transport options {transport}")
        try:
            SCHEMAS[r.request.response_schema].model_validate(r.validated_response)
        except Exception as exc:  # schema violation
            s.append(f"{r.call_id}: schema violation {type(exc).__name__}")
    expected_system = system_prompt_for({"features": dict(expected_features)},  # type: ignore[typeddict-item]
                                        p.get("technical_prompt_version", 1))
    if any(r.request.system_prompt != expected_system for r in technical):
        s.append("technical system prompt differs from the frozen treatment version")

    # CB-C: tudo ancorado em t, payload igual ao recalculado só com dados até t.
    c = issues["CB-C"]
    if history_last_session != anchor or anchor > CAL_B_MAX_SESSION:
        c.append(f"history ends at {history_last_session}, anchor {anchor}")
    if decision["decision_session"] != anchor:
        c.append("decision session differs from anchor")
    expected_prompt = build_prompt({"features": dict(expected_features)})  # type: ignore[typeddict-item]
    for r in records:
        if r.request.decision_session != anchor:
            c.append(f"{r.call_id}: session {r.request.decision_session}")
        if r.request.stage == "technical_analyst" and r.request.user_prompt != expected_prompt:
            c.append(f"{r.call_id}: technical payload differs from features recomputed up to t")
        if r.request.stage == "technical_analyst" and any(
                token in r.request.system_prompt + r.request.user_prompt for token in (anchor, p["ticker"].split(".")[0], "R$")):
            c.append(f"{r.call_id}: ticker/date/absolute price reached the technical prompt")
        if r.request.stage == "risk_manager":
            metrics = json.loads(r.request.user_prompt).get("risk_metrics")
            if metrics != {"current_concentration": 0.0, "current_drawdown": 0.0,
                           "recent_volatility": expected_volatility}:
                c.append(f"{r.call_id}: risk metrics {metrics} differ from recomputed up to t")

    # CB-R: regra dura antes do LLM de risco, e o LLM nunca a sobrescreve.
    rr = issues["CB-R"]
    risk_calls = sum(r.request.stage == "risk_manager" for r in records)
    portfolio_calls = sum(r.request.stage == "portfolio_manager" for r in records)
    breach = expected_volatility > p["risk_max_volatility"]  # drawdown = 0 e posição 0 na âncora
    if decision["technical_outcome"] == "COMPRA" and breach:
        if decision["risk_source"] != "HARD_RULE" or decision["risk_rule"] != "VOLATILITY" or risk_calls:
            rr.append("COMPRA above the volatility limit not hard-vetoed before the risk LLM")
    if decision["risk_source"] == "HARD_RULE":
        if decision["risk_rule"] == "VOLATILITY" and not breach:
            rr.append("volatility veto without breach")
        if decision["risk_rule"] in ("DRAWDOWN", "CONCENTRATION"):
            rr.append(f"{decision['risk_rule']} veto with zero drawdown/position")
        if risk_calls or portfolio_calls or cause not in RISK_VETO_CAUSES:
            rr.append("hard veto overridden or followed by LLM calls")
    if decision["technical_outcome"] in ("VENDA", "MANTER") and decision["risk_source"] not in ("AUTO_APPROVE", None):
        rr.append("VENDA/MANTER not auto-approved")
    return issues


def cal_b_status(automatic_pass: bool, reviews: Sequence[Mapping[str, Any]], anchors: Sequence[str]) -> str:
    """Regra congelada: gates automáticos, depois os dois autores, sem atalho."""
    if not automatic_pass:
        return CAL_B_FAIL
    fields = ("material_hallucination", "rationale_action_coherence")
    if len(reviews) != 2 or any(
        review["anchors"].get(a, {}).get(f) not in ("PASS", "FAIL") for review in reviews for a in anchors for f in fields
    ):
        return CAL_B_AWAITING_HUMAN_REVIEW
    verdicts = [[review["anchors"][a][f] for a in anchors for f in fields] for review in reviews]
    if verdicts[0] != verdicts[1]:
        return CAL_B_REVIEW_DISAGREEMENT
    return CAL_B_PASS if all(v == "PASS" for v in verdicts[0]) else CAL_B_FAIL


# ── Resultado da CAL-B (registrado) ──────────────────────────────

#: CB-D falhou (9/10 HOLD, total_hold_rate 0.90 >= 0.90): pela regra congelada,
#: FAIL com o holdout consumido. Sem rerodar, sem relaxar gate, sem tuning.
CAL_B_FREEZE_COMMIT = "02ab735"
CAL_B_EVIDENCE = "docs/evidence/cal_b/run_20261005T021523Z"
CAL_B_GATE_RESULTS: Mapping[str, bool] = MappingProxyType(
    {"CB-A": True, "CB-S": True, "CB-C": True, "CB-R": True, "CB-D": False}
)
CAL_B_FINAL_STATUS = CAL_B_FAIL
SYSTEM_CALIBRATION_COMPLETE = False


# ── CAL-B2 (Amendment 9, CAL_B2_PROTOCOL_FREEZE_V1) ──────────────

CAL_B2_PROTOCOL_FREEZE = "CAL_B2_PROTOCOL_FREEZE_V1"
#: Configuração final v2: seleções da CAL-A v2 (21 / 0.40, PROTOCOL_TIE_FALLBACK)
#: e do Sequential Development v2 (drawdown 0.15, EMPIRICAL_S2) + prompt v2.
CAL_B2_FROZEN_PARAMS: Mapping[str, Any] = MappingProxyType(stress_v2_params())
#: Checker semântico de development v2, congelado por blob git antes do batch.
CAL_B2_CHECKER_BLOBS: Mapping[str, str] = MappingProxyType({
    "src/agents/feature_semantics.py": "7a086701afda203a415cf1f9b67912d4788b3e56",
    "scripts/run_h2_v2_defect.py": "2ec09c494732148680b3543ed4ed7ceae58018c2",
})
CAL_B2_PASS = "CAL_B2_PASS — SANITY CHECK ONLY"
CAL_B2_FAIL = "CAL_B2_FAIL — HOLDOUT CONSUMED"
CAL_B2_INVALID = "CAL_B2_INVALID — PARTIAL HOLDOUT CONSUMED"
CAL_B2_REVIEW_DISAGREEMENT = "CAL_B2_REVIEW_DISAGREEMENT"
CAL_B2_AWAITING_HUMAN_REVIEW = "CAL_B2_AWAITING_HUMAN_REVIEW"


def cal_b2_status(automatic_pass: bool, reviews: Sequence[Mapping[str, Any]], anchors: Sequence[str]) -> str:
    """A mesma regra congelada da CAL-B1, com os rótulos da CAL-B2."""
    # ponytail: só troca o prefixo; a regra é uma só para B1 e B2.
    return cal_b_status(automatic_pass, reviews, anchors).replace("CAL_B_", "CAL_B2_", 1)
