"""Versões do tratamento H2 (Amendment 8).

v1 falhou o sanity check da CAL-B1 (degeneração, holdout consumido). O
post-mortem (``docs/evidence/cal_b_v1/postmortem/``) achou um defeito objetivo:
o prompt técnico entregava as 8 razões sem definição nem convenção de sinal, e
o modelo lia ``bb_upper_gap < 0`` como rompimento da banda superior. A v2 muda
SÓ o system prompt técnico (glossário semântico + regra estado-não-transição);
features, fórmulas, schema, N, quorum, geração, risco, custos, Risk prompt e
Portfolio prompt ficam idênticos. A identidade muda pelo parâmetro
``technical_prompt_version`` (entra no ``spec_hash``) e pelo hash do prompt
(entra na identidade de cada chamada no trace).

v3 (Amendment 10): a CAL-B2 mostrou o Risk vetando por um "limiar de 50%" de
confidence que não existe. A v3 muda SÓ o system prompt do Risk
(``risk_prompt_version = 2``); o Technical v2 é byte-idêntico e suas respostas
observadas são reaproveitadas por identidade exata (FROZEN_COMPONENT_REPLAY).
"""

import hashlib
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

import numpy as np

from src.experiments import anchors
from src.experiments.anchors import CAL_B_COMMITMENT_SHA256, CAL_B_STRATA, STRATA_COUNT
from src.experiments.hardening import H2_FROZEN_THINKING_LEVEL, h2_freeze_v1_params
from src.experiments.stress import STRESS_FROZEN_PARAMS

H2_TREATMENT_VERSION = 3
SCIENTIFIC_TECHNICAL_PROMPT_VERSION = 2
SCIENTIFIC_RISK_PROMPT_VERSION = 2
H2_V1_STATUS = "H2 V1 FAILED CAL-B1 — CONSUMED"
CAL_B1_STATUS = "CONSUMED — DEVELOPMENT EVIDENCE"

#: Hardening dirigido ao defeito: as 10 âncoras CAL-B1 (consumidas) x R=3, N=5.
H2_V2_DEFECT_REPETITIONS = 3

H2_V2_SEMANTIC_FIX_FAILED = "H2_V2_SEMANTIC_FIX FAILED"
H2_V2_DEGENERACY_PERSISTS = "H2_V2 SEMANTICS FIXED — DEGENERACY PERSISTS"
H2_V2_DEFECT_FIX_PASSED = "H2_V2 MINIMAL DEFECT FIX PASSED"


def v2_params(base: Mapping[str, Any]) -> dict[str, Any]:
    """A spec v1 dada com o prompt técnico v2 e nada mais."""
    if "technical_prompt_version" in base:
        raise ValueError("base params already declare a technical prompt version")
    return {**base, "technical_prompt_version": SCIENTIFIC_TECHNICAL_PROMPT_VERSION}


#: Hardening dirigido: a configuração final de desenvolvimento v1 + prompt v2.
H2_V2_DEFECT_PARAMS: Mapping[str, Any] = MappingProxyType(v2_params(STRESS_FROZEN_PARAMS))
#: Diagnostic Hardening / B0 v2: a mesma spec ex ante da v1 (freeze v1, LOW) + prompt v2.
H2_V2_HARDENING_PARAMS: Mapping[str, Any] = MappingProxyType(v2_params(h2_freeze_v1_params(H2_FROZEN_THINKING_LEVEL)))

#: Seleções v2, preenchidas só pelos commits de resultado de cada fase.
#: CAL-A v2: S1 idêntico nas seis configurações -> DISCRIMINATION NONE ->
#: config 1 pelo desempate do protocolo, não por desempenho superior.
CAL_A_V2_SELECTED_CONFIG: Mapping[str, Any] | None = MappingProxyType({
    "config_id": 1, "volatility_window": 21, "risk_max_volatility": 0.40,
    "S1": 0.0007185651086917932, "ranking": (1, 2, 3, 4, 5, 6),
    "discrimination": "NONE", "selection_basis": "PROTOCOL_TIE_FALLBACK",
    "evidence": "docs/evidence/cal_a_v2/run_20261006T022946Z/summary.json",
})
#: Sequential Development v2: S2 discriminou (D02 > D01 = D03) -> D02
#: (risk_max_drawdown 0.15), basis EMPIRICAL_S2 pela regra congelada do
#: Amendment 5. R = 3; a diferença vem de duas repetições em que o drawdown
#: passou de 0.15 — evidência de development, não afirmação de superioridade.
SEQUENTIAL_DEV_V2_SELECTED_CONFIG: Mapping[str, Any] | None = MappingProxyType({
    "config_id": 2, "name": "D02", "risk_max_drawdown": 0.15,
    "S2": 0.001153585309757399, "ranking": (2, 1, 3),
    "discrimination": "YES", "selection_basis": "EMPIRICAL_S2",
    "evidence": "docs/evidence/sequential_dev_v2/run_20261006T023608Z/summary.json",
})


def stress_v2_params() -> dict[str, Any]:
    """Config congelada v2 para o Stress: seleções da CAL-A v2 e do Sequential Dev v2."""
    if CAL_A_V2_SELECTED_CONFIG is None or SEQUENTIAL_DEV_V2_SELECTED_CONFIG is None:
        raise ValueError("Stress v2 needs the CAL-A v2 and Sequential Development v2 selections")
    return v2_params({
        **{k: v for k, v in STRESS_FROZEN_PARAMS.items()},
        "volatility_window": CAL_A_V2_SELECTED_CONFIG["volatility_window"],
        "risk_max_volatility": CAL_A_V2_SELECTED_CONFIG["risk_max_volatility"],
        "risk_max_drawdown": SEQUENTIAL_DEV_V2_SELECTED_CONFIG["risk_max_drawdown"],
    })



def v2_calibration_provenance() -> dict[str, str]:
    """Discriminação e base de seleção das calibrações v2 (nenhuma superioridade afirmada)."""
    if CAL_A_V2_SELECTED_CONFIG is None or SEQUENTIAL_DEV_V2_SELECTED_CONFIG is None:
        raise ValueError("v2 provenance needs the CAL-A v2 and Sequential Development v2 selections")
    return {
        "CAL_A_V2_DISCRIMINATION": CAL_A_V2_SELECTED_CONFIG["discrimination"],
        "CAL_A_V2_SELECTION_BASIS": CAL_A_V2_SELECTED_CONFIG["selection_basis"],
        "SEQUENTIAL_DEV_V2_DISCRIMINATION": SEQUENTIAL_DEV_V2_SELECTED_CONFIG["discrimination"],
        "SEQUENTIAL_DEV_V2_SELECTION_BASIS": SEQUENTIAL_DEV_V2_SELECTED_CONFIG["selection_basis"],
    }

# ── CAL-B2: novo holdout por seleção determinística (só identidade/data) ──

CAL_B2_SELECTION_SEED = hashlib.sha256(
    ("HEDGE-FUND-LAB|CAL-B2|" + CAL_B_COMMITMENT_SHA256).encode("utf-8")
).hexdigest()


def session_digest(stratum_id: int, day: str, seed: str = CAL_B2_SELECTION_SEED) -> str:
    """SHA256(seed + "|" + stratum_id + "|" + ISO_DATE)."""
    return hashlib.sha256(f"{seed}|{stratum_id}|{day}".encode("utf-8")).hexdigest()


def stratum_sessions(domain: Sequence[str]) -> dict[int, list[str]]:
    """As sessões de cada um dos 30 estratos (mesmo ``array_split`` do Amendment 2)."""
    blocks = np.array_split(np.array(list(domain)), STRATA_COUNT)
    return {i: [str(day) for day in block] for i, block in enumerate(blocks, 1)}


def select_cal_b2(domain: Sequence[str], excluded: set[str], seed: str = CAL_B2_SELECTION_SEED) -> list[dict[str, Any]]:
    """Menor digest entre as sessões elegíveis de cada estrato CAL-B.

    Nenhum retorno, volatilidade, feature, resposta de LLM ou regime entra: só
    o seed público, o id do estrato e a data.
    """
    blocks = stratum_sessions(domain)
    rows = []
    for stratum_id in CAL_B_STRATA:
        candidates = [day for day in blocks[stratum_id] if day not in excluded]
        ranked = sorted(candidates, key=lambda day: (session_digest(stratum_id, day, seed), day))
        rows.append({
            "stratum_id": stratum_id,
            "candidates": len(candidates),
            "excluded_in_stratum": len(blocks[stratum_id]) - len(candidates),
            "winner": ranked[0],
            "winner_digest": session_digest(stratum_id, ranked[0], seed),
            "ranking_sha256": hashlib.sha256(
                "\n".join(f"{day}|{session_digest(stratum_id, day, seed)}" for day in ranked).encode("utf-8")
            ).hexdigest(),
        })
    return rows




# ── Resultado do hardening dirigido (registrado) ─────────────────

H2_V2_DEFECT_EVIDENCE = "docs/evidence/h2_v2/defect_hardening_20261006T022111Z/manifest.json"
H2_V2_DEFECT_STATUS = H2_V2_DEFECT_FIX_PASSED


# ── Resultado do Stress v2 (registrado) ──────────────────────────

STRESS_V2_EVIDENCE = "docs/evidence/stress_v2/run_20261006T030655Z/summary.json"
STRESS_V2_STATUS = "STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL"


# ── Status de development v2 ─────────────────────────────────────

H2_V2_DEVELOPMENT_SUMMARY = "docs/evidence/h2_v2/development_summary.json"
H2_V2_DEVELOPMENT_STATUS = "H2_V2 DEVELOPMENT COMPLETE — READY FOR CAL-B2 PROTOCOL"


# ── Governança da v2 (Amendment 10) ──────────────────────────────

#: Status histórico da CAL-B2, preservado: fichas humanas em branco, segunda
#: revisão não aguardada. Não é reescrito como PASS nem FAIL.
CAL_B2_HISTORICAL_STATUS = "CAL_B2_AWAITING_HUMAN_REVIEW"
CAL_B2_ROLE = "CONSUMED — DEVELOPMENT EVIDENCE"
#: O conteúdo da CAL-B2 corrige o sistema (v3): a v2 não pode mais ir a System
#: Freeze, qualquer que seja uma revisão humana futura.
H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True
H2_V2_SYSTEM_FREEZE_INELIGIBILITY_REASON = "CAL_B2 CONSUMED AND USED AS DEVELOPMENT EVIDENCE"


# ── H2 v3 (Amendment 10) ─────────────────────────────────────────

FROZEN_COMPONENT_REPLAY = "TECHNICAL_V2"
#: Evidência v2 de onde vêm as respostas do componente congelado, por fase.
FROZEN_V2_EVIDENCE: Mapping[str, str] = MappingProxyType({
    "defect": "docs/evidence/cal_b2/run_20261006T125636Z",
    "hardening": "docs/evidence/h2_v2/hardening_low_20261006T022444Z",
    "b0": "docs/evidence/h2_v2/b0_low_20261006T022838Z",
    "cal_a": "docs/evidence/cal_a_v2/run_20261006T022946Z/summary.json",
    "sequential_dev": "docs/evidence/sequential_dev_v2/run_20261006T023608Z/summary.json",
    "stress": STRESS_V2_EVIDENCE,
})


def v3_params(base: Mapping[str, Any]) -> dict[str, Any]:
    """Uma spec v2 (prompt técnico v2) com o Risk prompt v2 e nada mais."""
    if base.get("technical_prompt_version") != SCIENTIFIC_TECHNICAL_PROMPT_VERSION or "risk_prompt_version" in base:
        raise ValueError("v3 starts from a v2 spec (technical prompt v2, no risk prompt version)")
    return {**base, "risk_prompt_version": SCIENTIFIC_RISK_PROMPT_VERSION}


#: Hardening dirigido: configuração final v2 (21 / 0.40 / 0.15) + Risk prompt v2.
H2_V3_DEFECT_PARAMS: Mapping[str, Any] = MappingProxyType(v3_params(stress_v2_params()))
#: Diagnostic Hardening / B0 v3: a mesma spec ex ante da v2 + Risk prompt v2.
H2_V3_HARDENING_PARAMS: Mapping[str, Any] = MappingProxyType(v3_params(H2_V2_HARDENING_PARAMS))
H2_V3_DEFECT_REPETITIONS = 3

H2_V3_TECHNICAL_FAILURE = "H2_V3_DEFECT_HARDENING TECHNICAL FAILURE"
H2_V3_RISK_FIX_FAILED = "H2_V3_RISK_CONTRACT_FIX FAILED"
H2_V3_DEGENERACY_PERSISTS = "H2_V3 RISK CONTRACT FIXED — DEGENERACY PERSISTS"
H2_V3_DEFECT_FIX_PASSED = "H2_V3 MINIMAL DEFECT FIX PASSED"

#: Seleções v3, preenchidas só pelos commits de resultado de cada fase.
#: CAL-A v3: S1 discriminou só pela âncora 2023-01-18 (0.40 e 63/0.50 vetam por
#: regra dura; 21/0.50, 21/0.60 e 63/0.60 deixam o Risk v3 aprovar). Empate exato
#: no topo entre 2, 3 e 6 -> menor config_id. R = 3, uma âncora: development
#: evidence, sem afirmação de superioridade robusta.
CAL_A_V3_SELECTED_CONFIG: Mapping[str, Any] | None = MappingProxyType({
    "config_id": 2, "volatility_window": 21, "risk_max_volatility": 0.50,
    "S1": 0.0012577896112663505, "ranking": (2, 3, 6, 1, 4, 5),
    "discrimination": "YES", "selection_basis": "EMPIRICAL_S1",
    "tie": "TOP_TIE_2_3_6_FALLBACK_LOWEST_CONFIG_ID",
    "evidence": "docs/evidence/cal_a_v3/run_20261006T151945Z/summary.json",
})
#: Sequential Development v3 (base 21 / 0.50 da CAL-A v3): S2 D01 = D03 > D02
#: (o limite 0.15 vetou entradas por regra dura em r2/r3; com 0.25/0.35 o Risk v3
#: aprova). Empate exato no topo (1, 3) -> menor config_id -> D01. R = 3:
#: development evidence, sem afirmação de superioridade robusta.
SEQUENTIAL_DEV_V3_SELECTED_CONFIG: Mapping[str, Any] | None = MappingProxyType({
    "config_id": 1, "name": "D01", "risk_max_drawdown": 0.25,
    "S2": 0.2614222625465128, "ranking": (1, 3, 2),
    "discrimination": "YES", "selection_basis": "EMPIRICAL_S2",
    "tie": "TOP_TIE_1_3_FALLBACK_LOWEST_CONFIG_ID",
    "evidence": "docs/evidence/sequential_dev_v3/run_20261006T152426Z/summary.json",
})


def stress_v3_params() -> dict[str, Any]:
    """Config congelada v3 para o Stress: seleções da CAL-A v3 e do Sequential Dev v3."""
    if CAL_A_V3_SELECTED_CONFIG is None or SEQUENTIAL_DEV_V3_SELECTED_CONFIG is None:
        raise ValueError("Stress v3 needs the CAL-A v3 and Sequential Development v3 selections")
    return v3_params({
        **stress_v2_params(),
        "volatility_window": CAL_A_V3_SELECTED_CONFIG["volatility_window"],
        "risk_max_volatility": CAL_A_V3_SELECTED_CONFIG["risk_max_volatility"],
        "risk_max_drawdown": SEQUENTIAL_DEV_V3_SELECTED_CONFIG["risk_max_drawdown"],
    })


def v3_calibration_provenance() -> dict[str, str]:
    """Discriminação e base de seleção das calibrações v3 (nenhuma superioridade afirmada)."""
    if CAL_A_V3_SELECTED_CONFIG is None or SEQUENTIAL_DEV_V3_SELECTED_CONFIG is None:
        raise ValueError("v3 provenance needs the CAL-A v3 and Sequential Development v3 selections")
    return {
        "CAL_A_V3_DISCRIMINATION": CAL_A_V3_SELECTED_CONFIG["discrimination"],
        "CAL_A_V3_SELECTION_BASIS": CAL_A_V3_SELECTED_CONFIG["selection_basis"],
        "SEQUENTIAL_DEV_V3_DISCRIMINATION": SEQUENTIAL_DEV_V3_SELECTED_CONFIG["discrimination"],
        "SEQUENTIAL_DEV_V3_SELECTION_BASIS": SEQUENTIAL_DEV_V3_SELECTED_CONFIG["selection_basis"],
    }


# ── CAL-B3: novo holdout da v3 (só identidade/data) ──────────────

CAL_B3_SELECTION_SEED = hashlib.sha256(
    ("HEDGE-FUND-LAB|CAL-B3|" + str(anchors.CAL_B2_COMMITMENT_SHA256)).encode("utf-8")
).hexdigest()


def require_cal_b3_committed() -> None:
    """Nenhuma chamada live v3 antes do compromisso da CAL-B3 (Amendment 10)."""
    if not anchors.CAL_B3_ANCHORS or anchors.digest(anchors.CAL_B3_ANCHORS) != anchors.CAL_B3_COMMITMENT_SHA256:
        raise ValueError("CAL-B3 must be committed before any H2 v3 live call")
    if anchors.CAL_B3_STATUS != "SEALED":
        raise ValueError(f"CAL-B3 is {anchors.CAL_B3_STATUS}; v3 development needs it sealed")


# ── Resultado do hardening dirigido v3 (registrado) ──────────────

H2_V3_DEFECT_EVIDENCE = "docs/evidence/h2_v3/defect_hardening_20261006T151527Z/manifest.json"
H2_V3_DEFECT_STATUS = H2_V3_DEFECT_FIX_PASSED


# ── Resultado do Stress v3 (registrado) ──────────────────────────

STRESS_V3_EVIDENCE = "docs/evidence/stress_v3/run_20261006T152701Z/summary.json"
STRESS_V3_STATUS = "STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL"
