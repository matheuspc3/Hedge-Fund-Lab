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


#: Preenchidos SÓ pelo commit de compromisso da CAL-B2, antes de qualquer
#: chamada live v2. Vazio = CAL-B2 ainda não comprometida.
CAL_B2_ANCHORS: tuple[str, ...] = ()
CAL_B2_COMMITMENT_SHA256: str | None = None
CAL_B2_STATUS: Mapping[str, Any] = MappingProxyType({"executed": False, "authorized": False})
