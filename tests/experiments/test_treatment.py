"""Amendment 8: versão do tratamento e regra determinística da CAL-B2."""

import hashlib

import pytest

from src.experiments import treatment
from src.experiments.anchors import CAL_B_COMMITMENT_SHA256, CAL_B_STRATA


def test_versao_e_parametros_v2() -> None:
    assert treatment.H2_TREATMENT_VERSION == 2 and treatment.SCIENTIFIC_TECHNICAL_PROMPT_VERSION == 2
    assert treatment.v2_params({"a": 1}) == {"a": 1, "technical_prompt_version": 2}
    with pytest.raises(ValueError):
        treatment.v2_params({"technical_prompt_version": 1})


def test_seed_publico_e_digest() -> None:
    seed = hashlib.sha256(("HEDGE-FUND-LAB|CAL-B2|" + CAL_B_COMMITMENT_SHA256).encode()).hexdigest()
    assert treatment.CAL_B2_SELECTION_SEED == seed
    assert treatment.session_digest(3, "2018-07-20") == hashlib.sha256(f"{seed}|3|2018-07-20".encode()).hexdigest()


def test_selecao_menor_digest_sem_excluidas() -> None:
    domain = [f"2020-01-{d:02d}" for d in range(1, 31)] * 5  # 150 "sessões", 5 por estrato
    domain = [f"{day}#{i}" for i, day in enumerate(domain)]
    rows = treatment.select_cal_b2(domain, excluded=set())
    blocks = treatment.stratum_sessions(domain)
    assert [r["stratum_id"] for r in rows] == list(CAL_B_STRATA)
    for row in rows:
        best = min(blocks[row["stratum_id"]], key=lambda d: treatment.session_digest(row["stratum_id"], d))
        assert row["winner"] == best and row["candidates"] == 5
    excluded = {rows[0]["winner"]}
    again = treatment.select_cal_b2(domain, excluded=excluded)
    assert again[0]["winner"] != rows[0]["winner"] and again[0]["candidates"] == 4
    assert again[1:] == rows[1:]  # excluir num estrato não mexe nos outros


def test_cal_b2_comprometida_bate_com_a_regra_e_a_evidencia() -> None:
    import json
    from pathlib import Path

    from src.experiments import anchors

    root = Path(__file__).resolve().parents[2]
    sel = json.loads((root / anchors.CAL_B2_SELECTION_EVIDENCE).read_text(encoding="utf-8"))
    assert tuple(sel["cal_b2_anchors"]) == anchors.CAL_B2_ANCHORS
    assert anchors.digest(anchors.CAL_B2_ANCHORS) == anchors.CAL_B2_COMMITMENT_SHA256 == sel["cal_b2_commitment_sha256"]
    assert sel["seed"] == treatment.CAL_B2_SELECTION_SEED
    assert not set(anchors.CAL_B2_ANCHORS) & set(anchors.CAL_B_ANCHORS)
    for row in sel["strata"]:  # vencedor = menor digest, fora das exclusões
        assert row["winner_digest"] == treatment.session_digest(row["stratum_id"], row["winner"])
        assert row["winner"] not in row["excluded_sessions"]
        s = next(x for x in anchors.STRATA if x.stratum_id == row["stratum_id"])
        assert s.subset == "CAL-B" and s.first <= row["winner"] <= s.last
    assert anchors.CAL_B2_STATUS == "SEALED"


def test_runner_recusa_janela_com_ancora_cal_b2() -> None:
    from src.experiments import anchors

    for day in anchors.CAL_B2_ANCHORS:
        with pytest.raises(ValueError, match="CAL-B"):
            anchors.require_cal_b_locked(day, day)


def test_hardening_dirigido_registrado_bate_com_a_evidencia() -> None:
    import json
    from pathlib import Path

    from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2_SHA256

    m = json.loads((Path(__file__).resolve().parents[2] / treatment.H2_V2_DEFECT_EVIDENCE).read_text(encoding="utf-8"))
    assert m["status"] == treatment.H2_V2_DEFECT_STATUS == treatment.H2_V2_DEFECT_FIX_PASSED
    assert all(g["pass"] for g in m["gates"].values())
    assert m["technical_prompt_sha256"] == TECHNICAL_SYSTEM_PROMPT_V2_SHA256
    assert m["participant_params"] == dict(treatment.H2_V2_DEFECT_PARAMS)
    assert m["semantic_audit"]["technical_votes"] == 150


def test_selecao_cal_a_v2_bate_com_a_evidencia() -> None:
    import json
    from pathlib import Path

    sel = treatment.CAL_A_V2_SELECTED_CONFIG
    s = json.loads((Path(__file__).resolve().parents[2] / sel["evidence"]).read_text(encoding="utf-8"))
    assert s["complete"] and s["treatment_version"] == 2
    assert s["paired_technical_audit"]["same_five_technical_responses_in_all_configs"]
    assert s["cal_b_audit"]["cal_b_sessions_touched"] == []
    s1 = {int(k): v for k, v in s["S1"].items()}
    ranking = sorted(s1, key=lambda c: (-s1[c], c))
    assert sel["config_id"] == ranking[0] == s["selected_config_id"] and tuple(ranking) == sel["ranking"]
    assert sel["discrimination"] == ("NONE" if len(set(s1.values())) == 1 else "YES")
    assert sel["selection_basis"] == ("PROTOCOL_TIE_FALLBACK" if sel["discrimination"] == "NONE" else "EMPIRICAL_S1")
    grid = next(c for c in s["grid"] if c["config_id"] == sel["config_id"])
    assert (grid["volatility_window"], grid["risk_max_volatility"]) == (sel["volatility_window"], sel["risk_max_volatility"])
