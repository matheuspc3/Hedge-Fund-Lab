"""CAL_B_PROTOCOL_FREEZE_V1: autorização limitada, gates automáticos e regra de status."""

from types import SimpleNamespace

import pytest

from src.agents.technical_analyst import build_prompt, system_prompt_for
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


def test_cal_b_consumida_nao_reabre() -> None:
    assert anchors.CAL_B_STATUS == "CONSUMED"
    with pytest.raises(ValueError, match="CONSUMED"):
        authorize_cal_b("CAL-B", CAL_B_COMMITMENT_SHA256, DATES, 1)


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
                                response_schema=schema, user_prompt=user_prompt, analyst_id=i,
                                system_prompt=kw.get("system", system_prompt_for({"features": FEATURES}))))


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


def test_status_registrado_bate_com_a_evidencia() -> None:
    import json
    from pathlib import Path

    run = Path(__file__).resolve().parents[2] / cal_b.CAL_B_EVIDENCE
    report = json.loads((run / "automatic_gates.json").read_text(encoding="utf-8"))
    assert {g: v["pass"] for g, v in report["gates"].items()} == dict(cal_b.CAL_B_GATE_RESULTS)
    assert report["hold_rates"]["total_holds"] == 9 and report["hold_rates"]["decisions"] == 10
    assert report["batch_commit"].startswith(cal_b.CAL_B_FREEZE_COMMIT)
    assert json.loads((run / "status.json").read_text(encoding="utf-8"))["status"] == cal_b.CAL_B_FINAL_STATUS
    assert cal_b.cal_b_status(report["automatic_pass"], [], DATES) == cal_b.CAL_B_FINAL_STATUS == cal_b.CAL_B_FAIL
    assert not cal_b.SYSTEM_CALIBRATION_COMPLETE


# ── CAL-B2 (Amendment 9) ─────────────────────────────────────────

B2 = ("2018-08-16", "2019-04-05", "2019-10-07", "2020-07-01", "2021-01-21",
      "2021-09-22", "2022-04-07", "2022-11-01", "2023-06-26", "2023-12-18")
B2_COMMITMENT = "518dd9ddc132244726fc40b2939684876c6f69bf6bad67ea1f91a78fc4e9b167"


def test_cal_b2_config_final_e_spec_hash() -> None:
    import hashlib

    from src.artifacts import canonical_json
    from src.experiments.spec import ParticipantSpec

    p = cal_b.CAL_B2_FROZEN_PARAMS
    assert (p["technical_prompt_version"], p["volatility_window"], p["risk_max_volatility"],
            p["risk_max_drawdown"], p["risk_max_concentration"]) == (2, 21, 0.40, 0.15, 1.0)
    assert {k: v for k, v in p.items() if k not in ("technical_prompt_version", "risk_max_drawdown")} == {
        k: v for k, v in cal_b.CAL_B_FROZEN_PARAMS.items() if k != "risk_max_drawdown"}
    spec = canonical_json(ParticipantSpec("llm_agent", dict(p)).to_dict())
    assert hashlib.sha256(spec.encode()).hexdigest() == anchors.CAL_B2_SPEC_SHA256


def test_cal_b2_autorizacao_limitada_recusa_qualquer_desvio(monkeypatch: pytest.MonkeyPatch) -> None:
    assert anchors.CAL_B2_ANCHORS == B2 and anchors.CAL_B2_COMMITMENT_SHA256 == B2_COMMITMENT == digest(B2)
    ok = ("CAL-B2", B2_COMMITMENT, B2, 1, 2, 2, anchors.CAL_B2_SPEC_SHA256)
    monkeypatch.setattr(anchors, "CAL_B2_STATUS", "SEALED")
    auth = anchors.authorize_cal_b2(*ok)
    assert auth.require_anchor("2020-07-01") == "2020-07-01"
    with pytest.raises(ValueError, match="not a committed"):
        auth.require_anchor("2020-06-01")  # âncora CAL-B1
    for i, bad in ((0, "CAL-B"), (1, CAL_B_COMMITMENT_SHA256), (2, B2[:9]), (2, B2[::-1]), (2, DATES), (3, 2),
                   (3, True), (4, 1), (5, 1), (6, "0" * 64)):
        with pytest.raises(ValueError):
            anchors.authorize_cal_b2(*ok[:i], bad, *ok[i + 1:])
    monkeypatch.setattr(anchors, "CAL_B2_STATUS", "CONSUMED")
    with pytest.raises(ValueError, match="CONSUMED"):
        anchors.authorize_cal_b2(*ok)


def test_cal_b2_guards_de_versao_e_identidade() -> None:
    from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2

    v2 = cal_b.CAL_B2_FROZEN_PARAMS
    decision, _ = buy_case(0.5)
    tech = [record("technical_analyst", i, {"signal": "COMPRA", "justification": "x", "confidence": 0.6},
                   build_prompt({"features": FEATURES}), system=TECHNICAL_SYSTEM_PROMPT_V2) for i in range(1, 6)]
    assert not any(cal_b.anchor_issues("2020-06-01", decision, tech, FEATURES, 0.5, "2020-06-01", v2).values())
    old = [record("technical_analyst", i, {"signal": "COMPRA", "justification": "x", "confidence": 0.6},
                  build_prompt({"features": FEATURES})) for i in range(1, 6)]  # prompt v1 sob spec v2
    assert cal_b.anchor_issues("2020-06-01", decision, old, FEATURES, 0.5, "2020-06-01", v2)["CB-S"]
    leak = [record("technical_analyst", i, {"signal": "COMPRA", "justification": "x", "confidence": 0.6},
                   "PETR4 2020-06-01 " + build_prompt({"features": FEATURES}),
                   system=TECHNICAL_SYSTEM_PROMPT_V2) for i in range(1, 6)]
    assert cal_b.anchor_issues("2020-06-01", decision, leak, FEATURES, 0.5, "2020-06-01", v2)["CB-C"]


def test_cal_b2_rotulos_de_status_e_checker_congelado() -> None:
    import subprocess

    def review(value: str) -> dict:
        return {"anchors": {d: {"material_hallucination": value, "rationale_action_coherence": value} for d in B2}}

    assert cal_b.cal_b2_status(False, [], B2) == cal_b.CAL_B2_FAIL == "CAL_B2_FAIL — HOLDOUT CONSUMED"
    assert cal_b.cal_b2_status(True, [], B2) == cal_b.CAL_B2_AWAITING_HUMAN_REVIEW
    assert cal_b.cal_b2_status(True, [review("PASS")] * 2, B2) == cal_b.CAL_B2_PASS
    assert cal_b.cal_b2_status(True, [review("PASS"), review("FAIL")], B2) == cal_b.CAL_B2_REVIEW_DISAGREEMENT
    for path, blob in cal_b.CAL_B2_CHECKER_BLOBS.items():
        assert subprocess.run(["git", "hash-object", path], capture_output=True, text=True,
                              check=True).stdout.strip() == blob


def test_cal_b2_gates_registrados_batem_com_a_evidencia() -> None:
    import json
    from pathlib import Path

    run = Path(__file__).resolve().parents[2] / cal_b.CAL_B2_EVIDENCE
    report = json.loads((run / "automatic_gates.json").read_text(encoding="utf-8"))
    assert {g: v["pass"] for g, v in report["gates"].items()} == dict(cal_b.CAL_B2_GATE_RESULTS)
    assert report["hold_rates"]["total_holds"] == 7 and report["hold_rates"]["decisions"] == 10
    assert report["batch_commit"].startswith(cal_b.CAL_B2_BATCH_COMMIT)
    assert report["financial_outcome"].startswith("NOT COMPUTED")
    assert anchors.CAL_B2_STATUS == "CONSUMED"
    with pytest.raises(ValueError, match="CONSUMED"):
        anchors.authorize_cal_b2("CAL-B2", B2_COMMITMENT, B2, 1, 2, 2, anchors.CAL_B2_SPEC_SHA256)


# ── CAL-B3 (Amendment 11) ────────────────────────────────────────

B3 = ("2018-08-03", "2019-03-19", "2019-10-18", "2020-05-13", "2021-01-06",
      "2021-08-17", "2022-03-11", "2022-11-29", "2023-05-12", "2024-01-11")
B3_COMMITMENT = "a5cadecd361de5059370bf4bfa97b1417b82eb8951950cf92b0aebc7edecdbaf"
B3_OK = ("CAL-B3", B3_COMMITMENT, B3, 1, 3, 2, 2, "1d63ad4cc93f9ef49368ba6772a22403354b36f3cc7d9d57d3b0627b85b9becc")


def test_cal_b3_config_final_e_spec_hash() -> None:
    import hashlib

    from src.artifacts import canonical_json
    from src.experiments.spec import ParticipantSpec

    p = cal_b.CAL_B3_FROZEN_PARAMS
    assert (p["technical_prompt_version"], p["risk_prompt_version"], p["volatility_window"], p["risk_max_volatility"],
            p["risk_max_drawdown"], p["risk_max_concentration"]) == (2, 2, 21, 0.50, 0.25, 1.0)
    assert (p["provider"], p["model"], p["thinking_level"], p["temperature"], p["max_output_tokens"]) == (
        "gemini", "gemini-3.8-flash", "low", 1.0, 8192)
    assert (p["analyst_count"], p["consensus_threshold"], p["require_all_votes"], p["decision_frequency"],
            p["strict_inputs"], p["portfolio_inversion_policy"], p["long_target_weight"]) == (
        5, 0.6, True, 1, True, "fail", 1.0)
    assert "seed" not in p
    spec = canonical_json(ParticipantSpec("llm_agent", dict(p)).to_dict())
    assert hashlib.sha256(spec.encode()).hexdigest() == anchors.CAL_B3_SPEC_SHA256 == B3_OK[-1]


def test_cal_b3_autorizacao_limitada_recusa_qualquer_desvio(monkeypatch: pytest.MonkeyPatch) -> None:
    assert anchors.CAL_B3_ANCHORS == B3 and anchors.CAL_B3_COMMITMENT_SHA256 == B3_COMMITMENT == digest(B3)
    assert anchors.CAL_B_AUTHORIZED is False and anchors.CAL_B3_REPETITIONS == 1
    monkeypatch.setattr(anchors, "CAL_B3_STATUS", "SEALED")
    auth = anchors.authorize_cal_b3(*B3_OK)
    assert auth.require_anchor("2020-05-13") == "2020-05-13"
    with pytest.raises(ValueError, match="not a committed"):
        auth.require_anchor("2020-07-01")  # âncora CAL-B2
    for i, bad in ((0, "CAL-B2"), (1, B2_COMMITMENT), (2, B3[:9]), (2, B3[::-1]), (2, B2), (3, 2), (3, True),
                   (4, 2), (5, 1), (6, 1), (7, anchors.CAL_B2_SPEC_SHA256)):
        with pytest.raises(ValueError):
            anchors.authorize_cal_b3(*B3_OK[:i], bad, *B3_OK[i + 1:])
    monkeypatch.setattr(anchors, "CAL_B3_STATUS", "CONSUMED")
    with pytest.raises(ValueError, match="CONSUMED"):
        anchors.authorize_cal_b3(*B3_OK)


def test_cal_b3_guards_de_versao_dos_tres_prompts() -> None:
    from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2
    from src.agents.portfolio_manager import QUALITATIVE_SYSTEM_PROMPT
    from src.agents.risk_contract import RISK_SYSTEM_PROMPT_V2
    from src.agents.risk_manager import SYSTEM_PROMPT

    v3 = cal_b.CAL_B3_FROZEN_PARAMS
    decision, _ = buy_case(0.5)
    decision = {**decision, "final_cause": "ACTION_BUY", "risk_source": "LLM", "risk_rule": None,
                "portfolio_rule": None}
    tech = [record("technical_analyst", i, {"signal": "COMPRA", "justification": "x", "confidence": 0.6},
                   build_prompt({"features": FEATURES}), system=TECHNICAL_SYSTEM_PROMPT_V2) for i in range(1, 6)]
    risk_prompt = '{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.4}}'

    def downstream(risk_system: str, portfolio_system: str) -> list:
        return [record("risk_manager", 0, {"verdict": "APROVADO", "analysis": "ok", "risk_metrics": {}}, risk_prompt,
                       system=risk_system),
                record("portfolio_manager", 0, {"decision": "COMPRA", "reasoning": "ok"}, "{}",
                       system=portfolio_system)]

    clean = cal_b.anchor_issues("2020-06-01", decision, tech + downstream(RISK_SYSTEM_PROMPT_V2,
                                QUALITATIVE_SYSTEM_PROMPT), FEATURES, 0.4, "2020-06-01", v3)
    assert not any(clean.values()), clean
    for risk_system, portfolio_system in ((SYSTEM_PROMPT, QUALITATIVE_SYSTEM_PROMPT),
                                          (RISK_SYSTEM_PROMPT_V2, SYSTEM_PROMPT)):
        issues = cal_b.anchor_issues("2020-06-01", decision, tech + downstream(risk_system, portfolio_system),
                                     FEATURES, 0.4, "2020-06-01", v3)
        assert issues["CB-S"] and "system prompt differs" in issues["CB-S"][0]
    # regra dura v3 (0.50): COMPRA a 0.51 tem de ser vetada antes do LLM de risco
    assert cal_b.anchor_issues("2020-06-01", decision, tech + downstream(RISK_SYSTEM_PROMPT_V2,
                               QUALITATIVE_SYSTEM_PROMPT), FEATURES, 0.51, "2020-06-01", v3)["CB-R"]


def test_cal_b3_regra_de_status_com_um_autor() -> None:
    def sheet(value: str | None, override: dict | None = None) -> dict:
        rows = {d: {"material_unsupported_claim": value, "rationale_action_coherence": value} for d in B3}
        rows.update(override or {})
        return {"anchors": rows}

    assert cal_b.cal_b3_status(False, sheet("PASS"), B3) == cal_b.CAL_B3_FAIL == "CAL_B3_FAIL — HOLDOUT CONSUMED"
    assert cal_b.cal_b3_status(True, None, B3) == cal_b.CAL_B3_AWAITING_PRIMARY_AUTHOR_REVIEW
    assert cal_b.cal_b3_status(True, sheet(None), B3) == cal_b.CAL_B3_AWAITING_PRIMARY_AUTHOR_REVIEW
    assert cal_b.cal_b3_status(True, sheet("PASS"), B3) == cal_b.CAL_B3_PASS == "CAL_B3_PASS — SANITY CHECK ONLY"
    one_fail = {B3[4]: {"material_unsupported_claim": "PASS", "rationale_action_coherence": "FAIL"}}
    assert cal_b.cal_b3_status(True, sheet("PASS", one_fail), B3) == cal_b.CAL_B3_FAIL
    assert cal_b.PRIMARY_HUMAN_REVIEWERS_REQUIRED == 1
    assert cal_b.SECOND_INDEPENDENT_REVIEW == ("NOT REQUIRED FOR PROGRESSION", "RECOMMENDED AS LATER AUDIT")


def test_cal_b3_veto_do_risk_so_descritivo() -> None:
    assert cal_b.RISK_LLM_VETO_RATE_HAS_NO_MINIMUM_GATE is True
    assert "CB3-HR" in cal_b.CAL_B3_GATES and not any("VETO" in g for g in cal_b.CAL_B3_GATES)
    assert cal_b.risk_activity([])["RISK_LLM_DISCRETIONARY_VETO"] == "NOT_EXERCISED"
    approved = cal_b.risk_activity(["APROVADO"] * 4)
    assert approved["RISK_LLM_DISCRETIONARY_VETO"] == "NOT_OBSERVED" and approved["approval_rate"] == 1.0
    assert cal_b.risk_activity(["APROVADO", "VETADO"])["RISK_LLM_DISCRETIONARY_VETO"] == "OBSERVED"
    assert cal_b.CAL_B_MAX_TOTAL_HOLD_RATE == 0.90  # CB3-D: o mesmo limiar, literal


def test_cal_b3_checkers_congelados_por_blob() -> None:
    import subprocess

    from src.agents.risk_contract import RISK_RATIONALE_CHECKER_VERSION

    assert RISK_RATIONALE_CHECKER_VERSION == cal_b.CAL_B3_RISK_CHECKER_VERSION == 2
    assert set(cal_b.CAL_B3_CHECKER_BLOBS) == {"src/agents/feature_semantics.py", "scripts/run_h2_v2_defect.py",
                                               "src/agents/risk_contract.py"}
    for path, blob in cal_b.CAL_B3_CHECKER_BLOBS.items():
        assert subprocess.run(["git", "hash-object", path], capture_output=True, text=True,
                              check=True).stdout.strip() == blob
