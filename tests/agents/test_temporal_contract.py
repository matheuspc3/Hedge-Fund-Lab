"""Golden PT/EN temporal claims; state adjectives and nonassertions remain allowed."""

import hashlib

import pytest

from src.agents import feature_semantics as fs
from src.agents.technical_analyst import system_prompt_for
from src.experiments import treatment

FAIL = (
    "recuperação de curto prazo", "recuperação recente", "consolidação ou perda de momentum",
    "momentum enfraqueceu", "o preço recuperou", "o ativo está se recuperando",
    "price rebounded", "price recovered", "the trend is recovering",
    "o momentum fortaleceu", "fortalecimento recente do momentum",
    "momentum weakening", "MACD weakened", "strengthening trend", "trend strengthened",
    "o ativo ganhou momentum", "o preço perdeu momentum", "gaining momentum", "losing momentum",
    "o preço acelerou", "a tendência desacelerou", "o RSI melhorou", "o MACD piorou",
    "a tendência deteriorou", "MACD improved", "momentum worsened", "price accelerated",
    "trend decelerated", "trend deteriorated", "o preço está consolidando",
    "price entered consolidation", "price is consolidating", "o preço permanece acima da SMA50",
    "o RSI continua neutro", "o ativo ainda está em alta", "price remains above SMA50",
    "RSI continues neutral", "MACD is still positive", "o preço aumentou", "MACD decreased",
    "o preço reverteu", "price reversed", "price pulled back", "momentum became stronger",
)
PASS = (
    "o estado atual apresenta momentum fraco", "o momentum atual é positivo",
    "o momentum é forte", "o estado atual é misto", "RSI is neutral", "MACD is weak",
    "the current configuration is mixed", "the close is above the SMA50",
    "MACD is below its signal line", "o preço está acima da SMA50",
    "o MACD está acima do sinal", "não houve recuperação", "sem perda de momentum",
    "não é possível afirmar que o momentum enfraqueceu", "MACD has not weakened",
    "no recent recovery is observable", "price did not improve", "without weakening momentum",
    "if price recovered, a comparison would be needed", "aguardar recuperação futura",
    "a definição de recuperação exige comparação temporal", "o termo consolidação não é observado",
    "o RSI resume ganhos e perdas recentes", "a janela de 50 sessões define a SMA50",
    "permanece a decisão de MANTER", "the analysis continues with the current snapshot",
    "recuperação", "consolidação", "a consolidação dos dados terminou",
    "the recovery of the file succeeded", "the report improved",
)


@pytest.mark.parametrize("text", FAIL)
def test_golden_fail(text):
    assert fs.temporal_state_claims(text), text


@pytest.mark.parametrize("text", PASS)
def test_golden_pass(text):
    assert not fs.temporal_state_claims(text), text


def test_v4_only_changes_technical_prompt_and_hash():
    old = treatment.stress_v3_params()
    new = treatment.v4_params(old)
    assert {k for k in old if old[k] != new[k]} == {"technical_prompt_version"}
    assert treatment.H2_TREATMENT_VERSION == 4
    assert (new["technical_prompt_version"], new["risk_prompt_version"]) == (3, 2)
    assert fs.TECHNICAL_SYSTEM_PROMPT_V3.startswith(fs.TECHNICAL_SYSTEM_PROMPT_V2 + "\n\n")
    assert hashlib.sha256(fs.TECHNICAL_SYSTEM_PROMPT_V3.encode()).hexdigest() == fs.TECHNICAL_SYSTEM_PROMPT_V3_SHA256
    assert system_prompt_for({"features": {"rsi": 50}}, 3) == fs.TECHNICAL_SYSTEM_PROMPT_V3


def test_negation_does_not_hide_following_claim():
    assert fs.temporal_state_claims("Não há direção clara, mas o momentum enfraqueceu.")
