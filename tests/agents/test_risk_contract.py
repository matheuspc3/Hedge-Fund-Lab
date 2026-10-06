"""Risk prompt v2, semântica da confidence e checker de regras numéricas (Amendment 10)."""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

import pytest

from src.agents import risk_contract as rc
from src.agents.feature_semantics import (
    TECHNICAL_SYSTEM_PROMPT_V2,
    TECHNICAL_SYSTEM_PROMPT_V2_SHA256,
)
from src.agents.llm_client import LLMCallMetadata, MockLLMClient
from src.agents.participant import LLMParticipant
from src.agents.portfolio_manager import QUALITATIVE_SYSTEM_PROMPT
from src.agents.risk_manager import SYSTEM_PROMPT, RiskConfig, RiskManager
from src.agents.state import RiskVerdict, TechnicalSignal
from src.agents.technical_analyst import system_prompt_for
from src.artifacts import canonical_json
from src.experiments import treatment
from src.experiments.spec import ParticipantSpec

ROOT = Path(__file__).resolve().parents[2]
#: Payload lógico do Risk na âncora CAL-B2 2023-06-26 (o caso do defeito).
PAYLOAD = {"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.364617},
           "technical_signal": {"confidence": 0.462, "justification": "Consenso coletivo: 3/5 votos em COMPRA",
                                "signal": "COMPRA"}}


def codes(text: str, verdict: str = "VETADO", payload: dict = PAYLOAD) -> set[str]:
    return {a["code"] for a in rc.audit_risk_rationale(text, verdict, payload)}


def risk_state(volatility: float = 0.30, drawdown: float = 0.0) -> dict:
    return {"ticker": "PETR4.SA", "cash": 100_000.0, "position": 0.0, "current_price": 30.0, "equity": 100_000.0,
            "recent_volatility": volatility, "current_drawdown": drawdown, "errors": [],
            "technical_signal": TechnicalSignal(signal="COMPRA", justification="Consenso coletivo: 3/5 votos em "
                                                "COMPRA", confidence=0.462)}


# 1-5: o checker sobre o rationale visível


def test_1_confidence_0462_nao_autoriza_abaixo_de_50() -> None:
    original = ("O sinal técnico apresenta uma confiança baixa de 0.462 (abaixo do limiar de 50%), com consenso "
                "fraco (3/5 votos). Somado à volatilidade recente elevada de 36.46%, a relação risco/retorno é "
                "desfavorável para a preservação de capital.")
    assert codes(original) == {rc.UNSUPPORTED_CONFIDENCE_THRESHOLD}
    assert rc.UNSUPPORTED_CONFIDENCE_THRESHOLD in codes("A confiança (0.462) está abaixo de 50%, e a volatilidade "
                                                        "recente de 36.46% é elevada.")


@pytest.mark.parametrize("text", [
    "Confiança de 0.462 inferior ao limiar de 0.50; volatilidade recente de 36.46% elevada.",
    "O limiar de confiança de 0.5 não foi atingido e a volatilidade de 36.46% é alta.",
    "Confiança menor que o mínimo exigido diante da volatilidade recente de 36.46%.",
    "A confiança insuficiente porque é menor que 0.6, com volatilidade de 36.46%.",
    "Sinais sem convicção mínima não devem ser executados; volatilidade de 36.46%.",
    "A confiança não atinge a margem mínima de segurança; volatilidade recente de 36,46%.",
    "Confidence of 0.462 is below the 50% threshold and volatility of 36.46% is high.",
    "Confidence does not reach the minimum required level given volatility at 36.46%.",
])
def test_2_threshold_inventado_falha(text: str) -> None:
    assert rc.UNSUPPORTED_CONFIDENCE_THRESHOLD in codes(text)


def test_3_confidence_moderada_sem_regra_numerica_permitida() -> None:
    assert codes("Sinal de COMPRA com confiança moderada (0.462) e consenso de 3/5. Concentração e drawdown "
                 "zerados; a volatilidade recente de 36.46% é elevada, mas a carteira está em caixa.",
                 "APROVADO") == set()
    assert codes("Não existe limiar de confiança configurado; a confiança de 0.462 é considerada só "
                 "qualitativamente junto da volatilidade recente de 36.46%.", "APROVADO") == set()


def test_4_veto_so_por_confidence_viola_o_contrato() -> None:
    found = codes("Sinal vetado devido à baixa confiança de 46,2%, insuficiente para justificar exposição, "
                  "apesar do drawdown nulo e da volatilidade recente de 36.46%.")
    assert found == {rc.CONFIDENCE_ONLY_DECISION}
    assert rc.gate_counts(rc.audit_risk_rationale("Vetado: confiança fraca (0.462) e consenso de 3/5.", "VETADO",
                                                  PAYLOAD)) == {"V3-R1": False, "V3-R2": False, "V3-R3": True}


def test_5_veto_qualitativo_em_metricas_fornecidas_permitido() -> None:
    assert codes("Consenso dividido (3/5) e confiança moderada de 0.462 combinados a uma volatilidade recente "
                 "elevada de 36.46%: com drawdown e concentração zerados, a relação risco/retorno ainda é "
                 "desfavorável. Operação vetada para preservar capital.") == set()


def test_regra_numerica_inventada_sobre_metrica() -> None:
    assert codes("A volatilidade atual é 0.37, elevada.", payload={**PAYLOAD, "risk_metrics": {
        **PAYLOAD["risk_metrics"], "recent_volatility": 0.37}}) == set()
    assert rc.UNSUPPORTED_NUMERIC_RULE in codes("A volatilidade de 0.37 excede o limite de 0.30.")
    assert rc.UNSUPPORTED_NUMERIC_RULE in codes("O drawdown de 22% ultrapassa os limites prudenciais; "
                                                "volatilidade de 36.46%.")
    assert rc.UNSUPPORTED_NUMERIC_RULE in codes("Volatility of 36.46% is above the 30% limit.")
    assert codes("Sem violar os limites de risco: drawdown e concentração zerados, volatilidade de 36.46%.",
                 "APROVADO") == set()


def test_contradicao_textual_de_veredito() -> None:
    assert rc.VERDICT_TEXT_CONTRADICTION in codes("Operação aprovada: volatilidade de 36.46% aceitável.")
    assert rc.VERDICT_TEXT_CONTRADICTION in codes("A entrada é vetada; volatilidade de 36.46%.", "APROVADO")
    assert codes("Não há motivo para veto: volatilidade de 36.46% e drawdown nulo.", "APROVADO") == set()


def test_calibracao_no_corpus_de_development_reproduz_o_caso() -> None:
    """O Risk v1 da CAL-B2 (consumida, development) é marcado; o checker não lê a CAL-B3."""
    path = ROOT / treatment.FROZEN_V2_EVIDENCE["defect"] / "anchors" / "2023-06-26" / "llm_calls.jsonl"
    risk = next(json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if '"risk_manager"' in x)
    v = risk["validated_response"]
    assert json.loads(risk["user_prompt"]) == PAYLOAD
    assert rc.gate_counts(rc.audit_risk_rationale(v["analysis"], v["verdict"], PAYLOAD))["V3-R1"]


# 6-10: contrato, identidade e componentes inalterados


def test_6_veto_duro_continua_antes_do_llm() -> None:
    llm = MockLLMClient({RiskVerdict: {"verdict": "APROVADO", "analysis": "ok", "risk_metrics": {}}})
    manager = RiskManager(llm, RiskConfig(max_volatility=0.40, max_drawdown=0.15, max_concentration=1.0,
                                          prompt_version=2))
    for volatility, drawdown, rule in ((0.41, 0.0, "VOLATILITY"), (0.30, 0.16, "DRAWDOWN")):
        result = asyncio.run(manager.evaluate(risk_state(volatility, drawdown)))  # type: ignore[arg-type]
        assert (result["risk_verdict"].verdict, result["risk_source"], result["risk_rule"]) == ("VETADO", "HARD_RULE",
                                                                                                rule)
    assert not llm.calls
    asyncio.run(manager.evaluate(risk_state()))  # type: ignore[arg-type]
    assert [c.system_prompt for c in llm.calls] == [rc.RISK_SYSTEM_PROMPT_V2]


def test_7_risk_prompt_v1_reproduzivel() -> None:
    assert hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest() == rc.RISK_SYSTEM_PROMPT_V1_SHA256
    llm = MockLLMClient({RiskVerdict: {"verdict": "APROVADO", "analysis": "ok", "risk_metrics": {}}})
    asyncio.run(RiskManager(llm, RiskConfig(max_concentration=1.0)).evaluate(risk_state()))  # type: ignore[arg-type]
    assert [c.system_prompt for c in llm.calls] == [SYSTEM_PROMPT]


def test_8_risk_prompt_v2_muda_a_identidade() -> None:
    prompt = rc.RISK_SYSTEM_PROMPT_V2
    assert hashlib.sha256(prompt.encode()).hexdigest() == rc.RISK_SYSTEM_PROMPT_V2_SHA256
    for must in ("Não existe um limiar numérico de confidence", "não vetaram a operação",
                 "Não invente, suponha nem aplique novos thresholds", "retorne APROVADO ou VETADO"):
        assert must in prompt
    for banned in ("aprove mais", "evite VETADO", "prefira APROVADO", "mais trades"):
        assert banned.lower() not in prompt.lower()
    v2 = treatment.stress_v2_params()
    v3 = treatment.v3_params(v2)
    assert set(v3) - set(v2) == {"risk_prompt_version"} and v3["risk_prompt_version"] == 2
    assert canonical_json(ParticipantSpec("llm_agent", v2).to_dict()) != canonical_json(
        ParticipantSpec("llm_agent", v3).to_dict())
    with pytest.raises(ValueError):
        treatment.v3_params(v3)
    built = LLMParticipant(llm_client=MockLLMClient(), **{**v3, "provider": "mock"})
    assert built.risk_config.prompt_version == 2
    assert LLMParticipant("PETR4.SA", llm_client=MockLLMClient()).risk_config.prompt_version == 1
    with pytest.raises(ValueError):
        LLMParticipant("PETR4.SA", llm_client=MockLLMClient(), risk_prompt_version=3)
    assert treatment.H2_V3_DEFECT_PARAMS == {**treatment.stress_v2_params(), "risk_prompt_version": 2}
    assert (treatment.H2_V3_DEFECT_PARAMS["volatility_window"], treatment.H2_V3_DEFECT_PARAMS["risk_max_volatility"],
            treatment.H2_V3_DEFECT_PARAMS["risk_max_drawdown"],
            treatment.H2_V3_DEFECT_PARAMS["risk_max_concentration"]) == (21, 0.40, 0.15, 1.0)


def test_9_technical_prompt_v2_byte_identico() -> None:
    assert hashlib.sha256(TECHNICAL_SYSTEM_PROMPT_V2.encode()).hexdigest() == TECHNICAL_SYSTEM_PROMPT_V2_SHA256 == (
        "a3dec11f4c8911397c0f04ec5c0b7eb6265c420b3b6f7e3f494dd79ca43782e1")
    built = LLMParticipant(llm_client=MockLLMClient(), **{**treatment.H2_V3_DEFECT_PARAMS, "provider": "mock"})
    assert built.ensemble_config.prompt_version == 2
    assert system_prompt_for({"features": {"rsi": 50.0}}, built.ensemble_config.prompt_version) == (
        TECHNICAL_SYSTEM_PROMPT_V2)


def test_10_portfolio_inalterado() -> None:
    v2_hash = "497b56e89f1f2fc193f999e6bc23c88cccb7a2c6da96de5c11f09417482ae68a"  # gravado nos traces v2
    assert hashlib.sha256(QUALITATIVE_SYSTEM_PROMPT.encode()).hexdigest() == v2_hash
    v2 = LLMParticipant(llm_client=MockLLMClient(), **{**treatment.stress_v2_params(), "provider": "mock"})
    v3 = LLMParticipant(llm_client=MockLLMClient(), **{**treatment.H2_V3_DEFECT_PARAMS, "provider": "mock"})
    assert v2.portfolio_config == v3.portfolio_config and v2.sizing.__dict__ == v3.sizing.__dict__


def test_semantica_da_confidence_documentada() -> None:
    s = rc.TECHNICAL_CONFIDENCE_SEMANTICS_V1
    assert s["range"] == (0.0, 1.0) and s["decision_threshold"] is None
    assert not any(s[k] for k in ("calibrated_probability", "probability_of_positive_return",
                                  "controls_position_sizing", "creates_hard_rule", "sole_basis_for_risk_verdict"))


# Replay do componente congelado


def test_replay_congelado_so_por_identidade_exata() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from h2_v3 import FrozenReplayClient, frozen_index, replay_audit

    path = ROOT / treatment.FROZEN_V2_EVIDENCE["defect"] / "anchors" / "2023-06-26" / "llm_calls.jsonl"
    index = frozen_index([path])
    v2 = next(r for r in index.values() if r.request.analyst_id == 1)
    live = MockLLMClient({TechnicalSignal: {"signal": "VENDA", "justification": "novo", "confidence": 0.9}})
    uses: list = []
    client = FrozenReplayClient(live, index, provider="gemini", model="gemini-3.8-flash", uses=uses,
                                context={"anchor": "2023-06-26"}, required=frozenset({"technical_analyst"}))
    client.begin_session("2023-06-26")
    req = v2.request
    meta = LLMCallMetadata(stage=req.stage, analyst_id=req.analyst_id)
    out = asyncio.run(client.generate(req.system_prompt, req.user_prompt, TechnicalSignal,
                                      dict(req.requested_options), metadata=meta))
    assert out.model_dump() == v2.validated_response and not live.calls
    with pytest.raises(RuntimeError, match="live call refused"):  # payload diferente: nunca vira chamada nova
        asyncio.run(client.generate(req.system_prompt, req.user_prompt + " ", TechnicalSignal,
                                    dict(req.requested_options), metadata=meta))
    assert [u["source"] for u in uses] == ["frozen_v2"]
    audit = replay_audit([(v2, index)])
    assert audit["replayed"] == {"technical_analyst": 1} and audit["technical_prompt_v2_byte_identical"]
