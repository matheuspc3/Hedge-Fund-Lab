"""Contrato semântico das features, prompt técnico v2 e checker (Amendment 8)."""

import hashlib

import pytest

from src.agents import feature_semantics as fs
from src.agents.feature_semantics import audit_rationale, contradictions, transitions
from src.agents.features import FEATURE_KEYS, LLM_FEATURE_SCHEMA_VERSION, dimensionless_features
from src.agents.participant import LLMParticipant
from src.agents.technical_analyst import CAUSAL_SYSTEM_PROMPT, system_prompt_for
from src.experiments import treatment
from src.experiments.spec import ParticipantSpec
from src.experiments.stress import STRESS_FROZEN_PARAMS

BASE = {"sma50_gap": 0.03, "sma200_gap": 0.10, "bb_upper_gap": -0.02, "bb_lower_gap": 0.03, "bb_width": 0.08,
        "rsi": 55.0, "macd_ratio": 0.010, "macd_signal_ratio": 0.006}


def claims(text: str, **overrides: float) -> dict[str, bool]:
    return {a["claim"]: a["holds"] for a in audit_rationale(text, {**BASE, **overrides})}


def test_features_e_formulas_identicas_a_v1() -> None:
    assert FEATURE_KEYS == ("bb_lower_gap", "bb_upper_gap", "bb_width", "macd_ratio", "macd_signal_ratio",
                            "rsi", "sma200_gap", "sma50_gap")
    assert LLM_FEATURE_SCHEMA_VERSION == 2
    levels = {"sma_50": 100.0, "sma_200": 80.0, "bb_upper": 110.0, "bb_lower": 90.0, "bb_middle": 100.0,
              "rsi": 55.0, "macd": 2.0, "macd_sinal": 1.0}
    assert dimensionless_features(105.0, levels) == {
        "sma50_gap": 0.05, "sma200_gap": 0.3125, "bb_upper_gap": -0.045455, "bb_lower_gap": 0.166667,
        "bb_width": 0.2, "rsi": 55.0, "macd_ratio": 0.019048, "macd_signal_ratio": 0.009524}


def test_prompt_v2_gerado_do_contrato_e_v1_intacto() -> None:
    prompt = fs.TECHNICAL_SYSTEM_PROMPT_V2
    assert hashlib.sha256(prompt.encode()).hexdigest() == fs.TECHNICAL_SYSTEM_PROMPT_V2_SHA256
    assert hashlib.sha256(CAUSAL_SYSTEM_PROMPT.encode()).hexdigest() == (
        "8659143336bdb7ca20200d0b38701140facd52e9b3ff08dfb65a2109466bf426")  # v1 nunca muda
    for key in FEATURE_KEYS:
        assert f"- {key} = {fs.FEATURE_SEMANTICS[key]}" in prompt
    assert "close / BollingerUpper - 1" in prompt and "close / BollingerLower - 1" in prompt
    assert "State, not transition" in prompt
    # papel, proibições e schema exatamente como na v1
    v1_role, v1_schema = CAUSAL_SYSTEM_PROMPT.rsplit("\n", 1)
    assert prompt.startswith(v1_role) and prompt.endswith(v1_schema)
    # nenhuma instrução para operar mais / evitar MANTER / favorecer direção
    for banned in ("avoid MANTER", "prefer COMPRA", "prefer VENDA", "when in doubt", "take more risk", "trade more"):
        assert banned.lower() not in prompt.lower()
    state = {"features": BASE}
    assert system_prompt_for(state) == CAUSAL_SYSTEM_PROMPT
    assert system_prompt_for(state, 2) == prompt


def test_versao_muda_a_identidade_do_tratamento() -> None:
    from src.agents.llm_client import MockLLMClient
    from src.artifacts import canonical_json

    v1 = dict(STRESS_FROZEN_PARAMS)
    v2 = treatment.v2_params(v1)
    assert set(v2) - set(v1) == {"technical_prompt_version"}  # única diferença de spec
    assert canonical_json(ParticipantSpec("llm_agent", v1).to_dict()) != canonical_json(
        ParticipantSpec("llm_agent", v2).to_dict())
    built = LLMParticipant(llm_client=MockLLMClient(), **{**v2, "provider": "mock"})
    assert built.ensemble_config.prompt_version == 2
    assert LLMParticipant("PETR4.SA", llm_client=MockLLMClient()).ensemble_config.prompt_version == 1
    with pytest.raises(ValueError):
        LLMParticipant("PETR4.SA", llm_client=MockLLMClient(), technical_prompt_version=5)


def test_bollinger_dentro_acima_e_abaixo() -> None:
    inside = {"bb_upper_gap": -0.02, "bb_lower_gap": 0.03}
    assert claims("o preço está dentro das bandas de Bollinger", **inside) == {"INSIDE_BANDS": True}
    assert claims("o preço está acima da banda superior", **inside) == {"ABOVE_UPPER_BAND": False}
    assert claims("o preço está abaixo da banda superior", **inside) == {"BELOW_UPPER_BAND": True}
    assert claims("o fechamento está acima da banda superior", bb_upper_gap=0.01) == {"ABOVE_UPPER_BAND": True}
    assert claims("o fechamento está abaixo da banda inferior", bb_lower_gap=-0.01) == {"BELOW_LOWER_BAND": True}
    assert claims("o preço está abaixo da banda inferior", **inside) == {"BELOW_LOWER_BAND": False}
    assert claims("o preço está acima da banda inferior", **inside) == {"ABOVE_LOWER_BAND": True}
    assert claims("não está acima da banda superior", **inside) == {}  # negação não é afirmação


def test_sma_e_macd() -> None:
    assert claims("acima da SMA50 e abaixo da SMA200", sma200_gap=-0.01) == {"ABOVE_SMA50": True,
                                                                              "BELOW_SMA200": True}
    assert claims("abaixo das médias de 50 e 200") == {"BELOW_SMA50": False, "BELOW_SMA200": False}
    assert claims("o MACD está acima da linha de sinal") == {"MACD_ABOVE_SIGNAL": True}
    assert claims("o MACD está abaixo da linha de sinal") == {"MACD_BELOW_SIGNAL": False}
    # números negativos: -0.0015 > -0.0062, então o MACD está ACIMA do sinal
    assert claims("o MACD está abaixo do sinal", macd_ratio=-0.0015, macd_signal_ratio=-0.0062) == {
        "MACD_BELOW_SIGNAL": False}
    assert claims("sma50_gap positivo e bb_upper_gap negativo") == {"SMA50_GAP_POSITIVE": True,
                                                                    "BB_UPPER_GAP_NEGATIVE": True}


def test_snapshot_nao_prova_transicao() -> None:
    for text in ("o MACD cruzou acima da linha de sinal", "houve crossover no MACD",
                 "o preço rompeu a banda superior", "o preço acabou de entrar nas bandas",
                 "o MACD está cruzando para cima", "a tendência reverteu"):
        assert transitions(audit_rationale(text, BASE)), text
    for text in ("o MACD está acima da linha de sinal", "sem cruzamento claro", "possível rompimento futuro",
                 "aguardar confirmação de rompimento", "oportunidade de reversão à média",
                 "risco de reversão", "reversão iminente"):
        assert not transitions(audit_rationale(text, BASE)), text


def test_checker_reproduz_o_defeito_v1() -> None:
    v1 = ("O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando "
          "possível sobrecompra, apesar das médias móveis positivas.")
    audit = audit_rationale(v1, {**BASE, "bb_upper_gap": -0.02})
    assert {a["claim"] for a in contradictions(audit)} == {"ABOVE_UPPER_BAND"}
    assert transitions(audit)
