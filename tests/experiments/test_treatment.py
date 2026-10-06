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
