"""Identidade da janela avaliada e do contexto metodológico.

Duas regras opostas, e é a oposição que importa:

- a **janela** muda o que é computado, logo muda o ``spec_hash``;
- **fase** e **case_id** não mudam número algum, logo **não** entram no hash.
"""

import json
from dataclasses import FrozenInstanceError
from datetime import date
from typing import cast

import pytest

from src.experiments.context import SCIENTIFIC_PHASES, RunContext
from src.experiments.spec import (
    EvaluationSpec,
    ExperimentSpec,
    ParticipantSpec,
    canonical_json,
)

SMA = ParticipantSpec("sma_cross", {"ticker": "PETR4.SA"})


def evaluation(**override) -> EvaluationSpec:
    params: dict = {
        "decision_start": "2024-01-02",
        "decision_end": "2024-03-01",
        "minimum_history_sessions": 60,
    }
    params.update(override)
    return EvaluationSpec(**params)


def spec(**override) -> ExperimentSpec:
    params: dict = {
        "snapshot_id": "snap",
        "participant": SMA,
        "initial_capital": 100_000.0,
        "evaluation": evaluation(),
    }
    params.update(override)
    return ExperimentSpec(**params)


# ── A janela é material ──────────────────────────────────────────


def test_mesma_janela_produz_o_mesmo_hash() -> None:
    assert spec().spec_hash == spec().spec_hash


@pytest.mark.parametrize(
    "override",
    [
        {"decision_start": "2024-01-03"},
        {"decision_end": "2024-03-04"},
        {"minimum_history_sessions": 61},
    ],
    ids=["decision_start", "decision_end", "minimum_history_sessions"],
)
def test_parametro_da_janela_muda_o_hash(override) -> None:
    assert spec(evaluation=evaluation(**override)).spec_hash != spec().spec_hash


def test_janela_ausente_difere_de_janela_declarada() -> None:
    """Modo técnico legado e run científico não podem colidir em identidade."""
    assert spec(evaluation=None).spec_hash != spec().spec_hash


def test_janela_entra_na_forma_canonica() -> None:
    payload = spec().to_dict()
    assert payload["evaluation"] == {
        "decision_start": "2024-01-02",
        "decision_end": "2024-03-01",
        "minimum_history_sessions": 60,
    }
    assert json.loads(canonical_json(payload)) == payload


def test_janela_ausente_aparece_como_null_explicito() -> None:
    """Ausência é configuração declarada, não campo que sumiu do JSON."""
    assert spec(evaluation=None).to_dict()["evaluation"] is None


# ── Normalização ─────────────────────────────────────────────────


def test_formatos_equivalentes_de_data_produzem_o_mesmo_hash() -> None:
    """Identidade não pode depender de como o chamador escreveu a data.

    ``EvaluationSpec`` aceita texto ISO, ``date`` e ``Timestamp`` e normaliza
    os três para ``YYYY-MM-DD`` antes de o hash existir.
    """
    import pandas as pd

    texto = spec()
    objeto = spec(
        evaluation=EvaluationSpec(
            decision_start=date(2024, 1, 2),
            decision_end=cast(pd.Timestamp, pd.Timestamp("2024-03-01")),
            minimum_history_sessions=60,
        )
    )
    assert texto.spec_hash == objeto.spec_hash


def test_tres_formas_da_mesma_data_colapsam_na_mesma_forma_canonica() -> None:
    """Texto, ``date`` e ``Timestamp`` produzem o mesmo campo, não só o mesmo hash."""
    import pandas as pd

    formas = [
        "2026-01-10",
        date(2026, 1, 10),
        cast(pd.Timestamp, pd.Timestamp("2026-01-10")),
    ]
    canonicas = {
        evaluation(decision_start=forma, decision_end=forma).to_dict()["decision_start"]
        for forma in formas
    }
    assert canonicas == {"2026-01-10"}
    hashes = {
        spec(evaluation=evaluation(decision_start=forma, decision_end=forma)).spec_hash
        for forma in formas
    }
    assert len(hashes) == 1


@pytest.mark.parametrize(
    "momento",
    ["2026-01-10T00:00:00+00:00", "2026-01-10 12:00", "2026-01-10T09:30:00-03:00"],
    ids=["utc", "com-hora", "offset-b3"],
)
def test_instante_nao_e_sessao(momento: str) -> None:
    """Hora e timezone continuam recusados: a arena decide uma vez por sessão."""
    with pytest.raises(ValueError, match="time-of-day|timezone-naive"):
        evaluation(decision_start=momento)


def test_timestamp_com_timezone_e_recusado() -> None:
    import pandas as pd

    with pytest.raises(ValueError, match="timezone-naive"):
        evaluation(
            decision_start=cast(
                pd.Timestamp, pd.Timestamp("2026-01-10", tz="America/Sao_Paulo")
            )
        )


def test_janela_e_imutavel() -> None:
    window = evaluation()
    with pytest.raises(FrozenInstanceError):
        window.decision_start = "2024-05-05"  # type: ignore[misc]


def test_ancora_unica_e_reconhecida() -> None:
    assert evaluation(decision_end="2024-01-02").single_anchor is True
    assert evaluation().single_anchor is False


# ── Validação ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"decision_start": "2024-04-01"}, "must not be after"),
        ({"minimum_history_sessions": 0}, "must be >= 1"),
        ({"minimum_history_sessions": -3}, "must be >= 1"),
        ({"minimum_history_sessions": True}, "must be an integer"),
        ({"minimum_history_sessions": 2.5}, "must be an integer"),
        ({"decision_start": "2024-01-02 09:30"}, "without time-of-day"),
        ({"decision_start": "nao-e-data"}, "not a valid date"),
        ({"decision_start": 20240102}, "must be a date"),
    ],
    ids=[
        "start-depois-do-end",
        "minimo-zero",
        "minimo-negativo",
        "minimo-bool",
        "minimo-fracionario",
        "com-horario",
        "texto-invalido",
        "inteiro",
    ],
)
def test_configuracao_invalida_nao_vira_hash(override, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        evaluation(**override)


# ── Contexto metodológico fica fora do hash ──────────────────────


def test_phase_nao_altera_o_spec_hash() -> None:
    """Dois runs que só diferem na fase computam exatamente o mesmo."""
    hashes = {spec().spec_hash for _ in SCIENTIFIC_PHASES}
    assert len(hashes) == 1
    assert "phase" not in canonical_json(spec().to_dict())


def test_case_id_nao_altera_o_spec_hash() -> None:
    assert "case_id" not in canonical_json(spec().to_dict())


def test_contexto_nao_e_campo_da_spec() -> None:
    from dataclasses import fields

    names = {field.name for field in fields(ExperimentSpec)}
    assert "phase" not in names
    assert "case_id" not in names


def test_contexto_e_imutavel() -> None:
    context = RunContext("CALIBRATION", "calibration-election-01")
    with pytest.raises(FrozenInstanceError):
        context.phase = "FINAL_TEST"  # type: ignore[misc]


@pytest.mark.parametrize("phase", SCIENTIFIC_PHASES)
def test_fases_do_protocolo_sao_aceitas(phase: str) -> None:
    assert RunContext(phase).to_dict()["phase"] == phase


@pytest.mark.parametrize(
    ("phase", "case_id", "message"),
    [
        ("TRAIN", None, "unsupported phase"),
        ("calibration", None, "unsupported phase"),
        ("", None, "cannot be empty"),
        ("CALIBRATION", "   ", "cannot be blank"),
        ("CALIBRATION", "x" * 200, "at most"),
    ],
    ids=["fase-inexistente", "minuscula", "vazia", "case-em-branco", "case-longo"],
)
def test_contexto_invalido_e_recusado(phase, case_id, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        RunContext(phase, case_id)
