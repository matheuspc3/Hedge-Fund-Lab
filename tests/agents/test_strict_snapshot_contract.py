"""V5 language contract; the v3 checker remains the same ruler."""

import hashlib

import pytest

from src.agents import feature_semantics as fs
from src.agents.features import LLM_FEATURE_SCHEMA_VERSION
from src.agents.technical_analyst import AnalystEnsembleConfig, system_prompt_for
from src.agents.technical_prompt_v4 import (
    STRICT_SNAPSHOT_LANGUAGE,
    TECHNICAL_SYSTEM_PROMPT_V4,
    TECHNICAL_SYSTEM_PROMPT_V4_SHA256,
)
from src.artifacts import canonical_json
from src.experiments import treatment
from src.experiments.spec import ParticipantSpec

PAIRS = (
    ("o preço está abaixo da SMA200", "o preço permanece abaixo da SMA200"),
    ("o RSI está neutro", "o RSI permanece neutro"),
    ("o MACD está acima da signal", "o MACD continua acima da signal"),
    ("o momentum atual é fraco", "o momentum enfraqueceu"),
    ("a configuração atual é mista", "o mercado entrou em consolidação"),
)


@pytest.mark.parametrize("allowed,forbidden", PAIRS)
def test_explicit_prompt_contrast_and_frozen_checker(allowed, forbidden):
    assert f'ALLOWED: "{allowed}"' in STRICT_SNAPSHOT_LANGUAGE
    assert f'NOT ALLOWED: "{forbidden}"' in STRICT_SNAPSHOT_LANGUAGE
    assert not fs.temporal_state_claims(allowed)
    assert fs.temporal_state_claims(forbidden) or fs.transitions(fs.audit_rationale(forbidden, {}))


def test_only_temporal_section_changes_and_scientific_identity():
    assert TECHNICAL_SYSTEM_PROMPT_V4.removesuffix(STRICT_SNAPSHOT_LANGUAGE) == (
        fs.TECHNICAL_SYSTEM_PROMPT_V3.removesuffix(fs.SNAPSHOT_ONLY_LANGUAGE)
    )
    assert TECHNICAL_SYSTEM_PROMPT_V4.startswith(fs.TECHNICAL_SYSTEM_PROMPT_V2 + "\n\n")
    assert hashlib.sha256(TECHNICAL_SYSTEM_PROMPT_V4.encode()).hexdigest() == TECHNICAL_SYSTEM_PROMPT_V4_SHA256
    assert TECHNICAL_SYSTEM_PROMPT_V4_SHA256 != fs.TECHNICAL_SYSTEM_PROMPT_V3_SHA256
    assert system_prompt_for({"features": {"rsi": 50}}, 4) == TECHNICAL_SYSTEM_PROMPT_V4
    assert AnalystEnsembleConfig(prompt_version=4).prompt_version == 4
    old, new = dict(treatment.H2_V4_DEFECT_PARAMS), dict(treatment.H2_V5_DEFECT_PARAMS)
    assert {k for k in old if old[k] != new[k]} == {"technical_prompt_version"}
    assert canonical_json(ParticipantSpec("llm_agent", old).to_dict()) != canonical_json(ParticipantSpec("llm_agent", new).to_dict())
    assert (new["technical_prompt_version"], new["risk_prompt_version"]) == (4, 2)
    assert (new["volatility_window"], new["risk_max_volatility"], new["risk_max_drawdown"], new["risk_max_concentration"]) == (21, .50, .25, 1.0)
    assert LLM_FEATURE_SCHEMA_VERSION == 2 and fs.TECHNICAL_RATIONALE_CHECKER_VERSION == 3
    assert treatment.CAL_B4_CARRIED_FORWARD_TO_H2_V5
    assert treatment.CAL_B4_HOLDOUT_INTEGRITY == "PRESERVED"


@pytest.mark.parametrize("text", (
    "o estado atual é compatível com tendência de alta",
    "momentum positivo", "momentum negativo", "momentum fraco", "momentum forte",
    "configuração de momentum mista",
    "RSI alto indica predominância relativa de ganhos na janela do indicador",
))
def test_current_trend_momentum_and_rsi_lookback_allowed(text):
    assert not fs.temporal_state_claims(text)
