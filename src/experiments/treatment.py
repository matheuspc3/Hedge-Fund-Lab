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
"""

import hashlib
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

import numpy as np

from src.experiments.anchors import CAL_B_COMMITMENT_SHA256, CAL_B_STRATA, STRATA_COUNT
from src.experiments.hardening import H2_FROZEN_THINKING_LEVEL, h2_freeze_v1_params
from src.experiments.stress import STRESS_FROZEN_PARAMS

H2_TREATMENT_VERSION = 2
SCIENTIFIC_TECHNICAL_PROMPT_VERSION = 2
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
SEQUENTIAL_DEV_V2_SELECTED_CONFIG: Mapping[str, Any] | None = None


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


def session_digest(stratum_id: int, day: str) -> str:
    """SHA256(seed + "|" + stratum_id + "|" + ISO_DATE)."""
    return hashlib.sha256(f"{CAL_B2_SELECTION_SEED}|{stratum_id}|{day}".encode("utf-8")).hexdigest()


def stratum_sessions(domain: Sequence[str]) -> dict[int, list[str]]:
    """As sessões de cada um dos 30 estratos (mesmo ``array_split`` do Amendment 2)."""
    blocks = np.array_split(np.array(list(domain)), STRATA_COUNT)
    return {i: [str(day) for day in block] for i, block in enumerate(blocks, 1)}


def select_cal_b2(domain: Sequence[str], excluded: set[str]) -> list[dict[str, Any]]:
    """Menor digest entre as sessões elegíveis de cada estrato CAL-B.

    Nenhum retorno, volatilidade, feature, resposta de LLM ou regime entra: só
    o seed público, o id do estrato e a data.
    """
    blocks = stratum_sessions(domain)
    rows = []
    for stratum_id in CAL_B_STRATA:
        candidates = [day for day in blocks[stratum_id] if day not in excluded]
        ranked = sorted(candidates, key=lambda day: (session_digest(stratum_id, day), day))
        rows.append({
            "stratum_id": stratum_id,
            "candidates": len(candidates),
            "excluded_in_stratum": len(blocks[stratum_id]) - len(candidates),
            "winner": ranked[0],
            "winner_digest": session_digest(stratum_id, ranked[0]),
            "ranking_sha256": hashlib.sha256(
                "\n".join(f"{day}|{session_digest(stratum_id, day)}" for day in ranked).encode("utf-8")
            ).hexdigest(),
        })
    return rows




# ── Resultado do hardening dirigido (registrado) ─────────────────

H2_V2_DEFECT_EVIDENCE = "docs/evidence/h2_v2/defect_hardening_20261006T022111Z/manifest.json"
H2_V2_DEFECT_STATUS = H2_V2_DEFECT_FIX_PASSED
