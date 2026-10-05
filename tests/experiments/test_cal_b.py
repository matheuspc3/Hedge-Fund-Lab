"""CAL_B_PROTOCOL_FREEZE_V1: autorização limitada, gates automáticos e regra de status."""

from types import SimpleNamespace

import pytest

from src.agents.technical_analyst import build_prompt
from src.experiments import anchors, cal_b
from src.experiments.anchors import (
    CAL_A_ANCHORS,
    CAL_B_ANCHORS,
    CAL_B_COMMITMENT_SHA256,
    authorize_cal_b,
    digest,
)

DATES = ("2018-07-19", "2019-03-07", "2019-10-15", "2020-06-01", "2021-01-13",
         "2021-08-20", "2022-03-31", "2022-11-04", "2023-06-15", "2024-01-22")


def test_ancoras_e_hash_integral() -> None:
    assert CAL_B_ANCHORS == DATES
    assert CAL_B_COMMITMENT_SHA256 == "51d73b2285d4e0e103bfb3fc4f5cd26892a6b96fe7dbe8d43cd1e429937f38c0"
    assert digest(CAL_B_ANCHORS) == CAL_B_COMMITMENT_SHA256
    assert anchors.CAL_B_AUTHORIZED is False  # nenhum unlock global
    assert anchors.CAL_B_REPETITIONS == 1


def test_autorizacao_limitada_recusa_qualquer_desvio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anchors, "CAL_B_STATUS", "SEALED")
    auth = authorize_cal_b("CAL-B", CAL_B_COMMITMENT_SHA256, DATES, 1)
    assert auth.require_anchor("2020-06-01") == "2020-06-01"
    with pytest.raises(ValueError, match="not a committed"):
        auth.require_anchor(CAL_A_ANCHORS[0])
    for bad in (("CAL-A", CAL_B_COMMITMENT_SHA256, DATES, 1), ("CAL-B", "0" * 64, DATES, 1),
                ("CAL-B", CAL_B_COMMITMENT_SHA256, DATES[:9], 1),
                ("CAL-B", CAL_B_COMMITMENT_SHA256, DATES[::-1], 1),
                ("CAL-B", CAL_B_COMMITMENT_SHA256, DATES, 3), ("CAL-B", CAL_B_COMMITMENT_SHA256, DATES, True)):
        with pytest.raises(ValueError):
            authorize_cal_b(*bad)
    monkeypatch.setattr(anchors, "CAL_B_STATUS", "CONSUMED")
    with pytest.raises(ValueError, match="CONSUMED"):
        authorize_cal_b("CAL-B", CAL_B_COMMITMENT_SHA256, DATES, 1)


def test_configuracao_final_congelada() -> None:
    p = cal_b.CAL_B_FROZEN_PARAMS
    assert (p["provider"], p["model"], p["thinking_level"], p["temperature"], p["max_output_tokens"]) == (
        "gemini", "gemini-3.8-flash", "low", 1.0, 8192)
    assert (p["analyst_count"], p["consensus_threshold"], p["require_all_votes"]) == (5, 0.6, True)
    assert (p["decision_frequency"], p["strict_inputs"], p["portfolio_inversion_policy"]) == (1, True, "fail")
    assert (p["long_target_weight"], p["volatility_window"], p["risk_max_volatility"],
            p["risk_max_drawdown"], p["risk_max_concentration"]) == (1.0, 21, 0.40, 0.25, 1.0)
    assert "seed" not in p
    assert cal_b.CAL_B_MAX_TOTAL_HOLD_RATE == 0.90


def test_degeneracao_reusa_codigos_do_hardening() -> None:
    nine = ["TECH_EXPLICIT_HOLD"] * 5 + ["TECH_NO_MAJORITY", "RISK_VETO_VOLATILITY", "RISK_VETO_LLM",
                                         "PORTFOLIO_HOLD", "ACTION_BUY"]
    assert cal_b.hold_rates(nine)["total_holds"] == 9 and cal_b.hold_rates(nine)["degenerate_inactive"]
    eight = nine[:8] + ["BUY_AT_TARGET_NOOP", "ACTION_SELL"]  # NOOP não é HOLD
    rates = cal_b.hold_rates(eight)
    assert rates["total_holds"] == 8 and not rates["degenerate_inactive"]
    assert rates["explicit_hold_rate"] == 0.5 and rates["risk_veto_rate"] == 0.2


def test_prefiltro_lexico_aponta_fato_externo() -> None:
    cats = {h["category"] for h in cal_b.prescreen("A Petrobras subiu em 2020 com o petróleo, volume alto, R$ 30")}
    assert cats == {"asset_identity", "calendar", "external_information", "volume", "absolute_price"}
    assert cal_b.prescreen("RSI em 44.6 e MACD abaixo do sinal; preço acima da SMA200.") == []


FEATURES = {"bb_lower_gap": 0.05, "bb_upper_gap": -0.02, "bb_width": 0.1, "macd_ratio": 0.01,
            "macd_signal_ratio": 0.005, "rsi": 55.0, "sma200_gap": 0.1, "sma50_gap": 0.03}


def record(stage: str, i: int, response: dict, user_prompt: str, **kw) -> SimpleNamespace:
    schema = {"technical_analyst": "TechnicalSignal", "risk_manager": "RiskVerdict",
              "portfolio_manager": "PortfolioAction"}[stage]
    return SimpleNamespace(
        call_id=f"{stage}-{i}", status=kw.get("status", "ok"), finish_reason=kw.get("finish", "STOP"),
        resolved_model="gemini-3.8-flash", validated_response=response,
        transport_options={"max_output_tokens": 8192, "temperature": 1.0, "thinking_level": "low"},
        request=SimpleNamespace(stage=stage, decision_session=kw.get("session", "2020-06-01"),
                                response_schema=schema, user_prompt=user_prompt, analyst_id=i))


def buy_case(volatility: float, **kw):
    tech = [record("technical_analyst", i, {"signal": "COMPRA", "justification": "x", "confidence": 0.6},
                   build_prompt({"features": FEATURES}), **(kw if i == 1 else {})) for i in range(1, 6)]
    decision = {"decision_session": "2020-06-01", "final_cause": "RISK_VETO_VOLATILITY", "valid_votes": 5,
                "analyst_count": 5, "consensus_threshold": 0.6, "technical_outcome": "COMPRA",
                "risk_source": "HARD_RULE", "risk_rule": "VOLATILITY", "portfolio_rule": "VETOED_UPSTREAM",
                "input_violations": [], "errors": [], "failures": []}
    return decision, tech


def test_gates_limpos_e_violacoes_detectadas() -> None:
    decision, tech = buy_case(0.5)
    clean = cal_b.anchor_issues("2020-06-01", decision, tech, FEATURES, 0.5, "2020-06-01")
    assert not any(clean.values()), clean
    # volatilidade abaixo do limite: veto duro sem violação
    assert cal_b.anchor_issues("2020-06-01", decision, tech, FEATURES, 0.3, "2020-06-01")["CB-R"]
    # LLM de risco chamado depois do veto duro
    risk = record("risk_manager", 0, {"verdict": "APROVADO", "analysis": "ok", "risk_metrics": {}}, "{}")
    assert cal_b.anchor_issues("2020-06-01", decision, tech + [risk], FEATURES, 0.5, "2020-06-01")["CB-R"]
    # truncamento, payload posterior a t e quorum incompleto
    decision, tech = buy_case(0.5, finish="MAX_TOKENS")
    assert cal_b.anchor_issues("2020-06-01", decision, tech, FEATURES, 0.5, "2020-06-01")["CB-S"]
    assert cal_b.anchor_issues("2020-06-01", decision, tech, {**FEATURES, "rsi": 56.0}, 0.5, "2020-06-01")["CB-C"]
    assert cal_b.anchor_issues("2020-06-01", decision, tech, FEATURES, 0.5, "2020-06-02")["CB-C"]
    assert cal_b.anchor_issues("2020-06-01", decision, tech[:4], FEATURES, 0.5, "2020-06-01")["CB-S"]
    assert cal_b.anchor_issues("2020-06-01", None, [], FEATURES, 0.5, "2020-06-01")["CB-A"]


def test_regra_de_status_sem_atalho() -> None:
    def review(value: str, override: dict | None = None) -> dict:
        a = {d: {"material_hallucination": value, "rationale_action_coherence": value} for d in DATES}
        a.update(override or {})
        return {"anchors": a}

    assert cal_b.cal_b_status(False, [review("PASS")] * 2, DATES) == cal_b.CAL_B_FAIL
    assert cal_b.cal_b_status(True, [review("PASS")], DATES) == cal_b.CAL_B_AWAITING_HUMAN_REVIEW
    assert cal_b.cal_b_status(True, [review("PASS"), review(None)], DATES) == cal_b.CAL_B_AWAITING_HUMAN_REVIEW
    assert cal_b.cal_b_status(True, [review("PASS")] * 2, DATES) == cal_b.CAL_B_PASS
    one_fail = {DATES[3]: {"material_hallucination": "FAIL", "rationale_action_coherence": "PASS"}}
    assert cal_b.cal_b_status(True, [review("PASS"), review("PASS", one_fail)], DATES) == cal_b.CAL_B_REVIEW_DISAGREEMENT
    assert cal_b.cal_b_status(True, [review("PASS", one_fail)] * 2, DATES) == cal_b.CAL_B_FAIL
