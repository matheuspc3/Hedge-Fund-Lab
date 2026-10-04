"""Identidade determinística da especificação experimental."""

import json
from dataclasses import fields

import pytest

from src.backtesting.costs import CostModel
from src.experiments.participants import (
    PARTICIPANT_REGISTRY,
    build_participant,
    required_tickers,
)
from src.experiments.spec import (
    CostSpec,
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
    canonical_json,
)


def base_spec(**overrides) -> ExperimentSpec:
    payload = {
        "snapshot_id": "20200102T000000000000Z-abc123456789",
        "participant": ParticipantSpec(
            "sma_cross",
            {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15},
        ),
        "initial_capital": 100_000.0,
        "costs": CostSpec(brokerage_fixed=1.0, spread_bps=10.0, tax_rate=0.001),
        "metrics": MetricSpec(),
    }
    payload.update(overrides)
    return ExperimentSpec(**payload)  # type: ignore[arg-type]


# ── spec_hash ────────────────────────────────────────────────────


def test_spec_hash_ignora_a_ordem_dos_dicionarios() -> None:
    ordered = base_spec(
        participant=ParticipantSpec(
            "sma_cross",
            {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15},
        )
    )
    shuffled = base_spec(
        participant=ParticipantSpec(
            "sma_cross",
            {"slow_window": 15, "ticker": "PETR4.SA", "fast_window": 5},
        )
    )

    assert list(ordered.participant.params) != list(shuffled.participant.params)
    assert ordered.spec_hash == shuffled.spec_hash
    assert canonical_json(ordered.to_dict()) == canonical_json(shuffled.to_dict())


def test_spec_hash_e_estavel_entre_instancias_equivalentes() -> None:
    assert base_spec().spec_hash == base_spec().spec_hash
    assert len(base_spec().spec_hash) == 64


@pytest.mark.parametrize(
    "override",
    [
        {"initial_capital": 100_001.0},
        {"snapshot_id": "20200102T000000000000Z-999999999999"},
        {"costs": CostSpec(brokerage_fixed=2.0, spread_bps=10.0, tax_rate=0.001)},
        {"metrics": MetricSpec(periods_per_year=12)},
        {
            "participant": ParticipantSpec(
                "sma_cross",
                {"ticker": "PETR4.SA", "fast_window": 6, "slow_window": 15},
            )
        },
        {"participant": ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"})},
    ],
    ids=["capital", "snapshot", "custo", "metrica", "sma-window", "participante"],
)
def test_parametro_material_muda_o_spec_hash(override) -> None:
    assert base_spec(**override).spec_hash != base_spec().spec_hash


def test_spec_hash_nao_depende_de_horario_nem_de_caminho_local() -> None:
    payload = base_spec().to_dict()
    serialized = canonical_json(payload)

    assert "run_id" not in serialized
    assert "created_at" not in serialized
    assert "path" not in serialized
    assert set(payload) == {
        "schema_version",
        "snapshot_id",
        "participant",
        "initial_capital",
        "costs",
        "metrics",
        "execution",
        "evaluation",
    }


def test_spec_serializa_para_json_puro() -> None:
    # Nenhum objeto Python arbitrário atravessa a serialização.
    assert json.loads(canonical_json(base_spec().to_dict())) == base_spec().to_dict()


# ── Validação ────────────────────────────────────────────────────


def test_spec_nao_aceita_instancia_de_participante() -> None:
    """O contrato é descritivo: não existe campo para um objeto mutável."""
    assert {field.name for field in fields(ExperimentSpec)} == {
        "snapshot_id",
        "participant",
        "initial_capital",
        "costs",
        "metrics",
        "execution",
        "evaluation",
    }
    with pytest.raises(ValueError, match="must be a JSON scalar"):
        ParticipantSpec("sma_cross", {"ticker": object()})


@pytest.mark.parametrize("capital", [0.0, -1.0, float("nan"), float("inf")])
def test_capital_invalido_e_rejeitado(capital: float) -> None:
    with pytest.raises(ValueError, match="initial_capital must be finite"):
        base_spec(initial_capital=capital)


def test_cost_spec_constroi_o_cost_model_real() -> None:
    spec = CostSpec(brokerage_fixed=1.5, spread_bps=20.0, tax_rate=0.002)

    assert spec.build() == CostModel(
        brokerage_fixed=1.5, spread_bps=20.0, tax_rate=0.002
    )


def test_metric_spec_expoe_os_defaults_tecnicos_sem_congelar() -> None:
    assert MetricSpec().to_dict() == {
        "risk_free_rate": 0.0,
        "mar": 0.0,
        "periods_per_year": 252,
    }


# ── Registry ─────────────────────────────────────────────────────


def test_registry_cobre_os_cinco_classicos_e_o_participante_llm() -> None:
    assert set(PARTICIPANT_REGISTRY) == {
        "bollinger",
        "buy_and_hold",
        "equal_weight",
        "indicator_family_control",
        "llm_agent",
        "min_variance",
        "sma_cross",
    }


def test_kind_desconhecido_falha_listando_os_suportados() -> None:
    with pytest.raises(ValueError, match="unsupported participant kind"):
        build_participant(ParticipantSpec("random_walk", {"ticker": "PETR4.SA"}))


def test_parametro_invalido_do_participante_falha_cedo() -> None:
    with pytest.raises(ValueError, match="invalid params for participant"):
        build_participant(ParticipantSpec("sma_cross", {"janela": 5}))


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"}), ("PETR4.SA",)),
        (ParticipantSpec("equal_weight", {"rebalance_freq": 10}), ()),
    ],
    ids=["single-asset", "carteira"],
)
def test_universo_exigido_vem_da_spec(spec: ParticipantSpec, expected) -> None:
    assert required_tickers(spec) == expected


# ── Imutabilidade real do participante ───────────────────────────


def test_params_sao_copiados_na_construcao() -> None:
    """`frozen=True` congela o campo; o dicionário precisa ser copiado."""
    params = {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15}
    participant = ParticipantSpec("sma_cross", params)
    spec = base_spec(participant=participant)
    before = spec.spec_hash

    params["fast_window"] = 999
    params["injetado"] = "nao deveria aparecer"

    assert participant.params["fast_window"] == 5
    assert "injetado" not in participant.params
    assert participant.to_dict()["params"]["fast_window"] == 5
    assert spec.spec_hash == before


def test_params_nao_aceitam_mutacao_direta() -> None:
    participant = ParticipantSpec("sma_cross", {"ticker": "PETR4.SA", "fast_window": 5})

    with pytest.raises(TypeError):
        participant.params["fast_window"] = 999  # type: ignore[index]
    with pytest.raises(TypeError):
        del participant.params["ticker"]  # type: ignore[attr-defined]

    assert participant.params["fast_window"] == 5


def test_to_dict_devolve_dict_novo_e_desacoplado() -> None:
    participant = ParticipantSpec("sma_cross", {"ticker": "PETR4.SA", "fast_window": 5})
    payload = participant.to_dict()

    assert isinstance(payload["params"], dict)
    payload["params"]["fast_window"] = 999

    assert participant.params["fast_window"] == 5
    assert participant.to_dict()["params"]["fast_window"] == 5
    assert json.loads(canonical_json(payload)) == payload


def test_spec_hash_e_estavel_durante_toda_a_vida_da_spec() -> None:
    """Nenhuma referência externa usada na criação pode alterar a identidade."""
    params = {"ticker": "PETR4.SA", "fast_window": 5, "slow_window": 15}
    participant = ParticipantSpec("sma_cross", params)
    costs = CostSpec(brokerage_fixed=1.0, spread_bps=10.0, tax_rate=0.001)
    metrics = MetricSpec()
    spec = ExperimentSpec(
        snapshot_id="20200102T000000000000Z-abc123456789",
        participant=participant,
        initial_capital=100_000.0,
        costs=costs,
        metrics=metrics,
    )
    before = spec.spec_hash

    params.clear()
    params["slow_window"] = -1

    assert spec.spec_hash == before
    assert spec.participant.params == {
        "ticker": "PETR4.SA",
        "fast_window": 5,
        "slow_window": 15,
    }


def test_participante_read_only_continua_construindo_e_comparando() -> None:
    """A estrutura read-only não pode quebrar registry, igualdade nem ordem."""
    spec = ParticipantSpec("sma_cross", {"fast_window": 5, "ticker": "PETR4.SA"})
    shuffled = ParticipantSpec("sma_cross", {"ticker": "PETR4.SA", "fast_window": 5})

    instance = build_participant(spec)

    assert instance is not None
    assert required_tickers(spec) == ("PETR4.SA",)
    assert spec == shuffled
    assert canonical_json(spec.to_dict()) == canonical_json(shuffled.to_dict())


# ── Identidade científica: regressão do spec_hash ────────────────
#
# Os dois hashes abaixo foram calculados com o código do commit 57f4976,
# **anterior** ao hardening pré-B0, e reproduzidos sem mudança depois dele.
# Uma spec histórica que omite os parâmetros novos precisa continuar com
# exatamente a mesma identidade: os novos campos só entram quando declarados.

GOLDEN_CLASSIC_SPEC_HASH = "a6221c4b064524d6207335c77494160724b5fe21b8c4c71b7af68440c77c1f63"
GOLDEN_LEGACY_LLM_SPEC_HASH = (
    "00e5277bb8750f886bcf41e1f26b1cc7fa2eb21ea69d5a665bff0e11e2da7dc7"
)

LEGACY_LLM_PARAMS = {
    "ticker": "PETR4.SA",
    "provider": "agent_router",
    "model": "openai/gpt-4o-mini",
    "analyst_count": 30,
    "consensus_threshold": 5 / 6,
    "decision_frequency": 1,
    "long_target_weight": 0.25,
}


def llm_spec(params: dict) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id="20200102T000000000000Z-abc123456789",
        participant=ParticipantSpec("llm_agent", params),
        initial_capital=100_000.0,
        costs=CostSpec(brokerage_fixed=1.0, spread_bps=10.0, tax_rate=0.001),
        metrics=MetricSpec(),
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start="2024-01-02",
            decision_end="2024-06-28",
            minimum_history_sessions=504,
        ),
    )


def test_spec_historica_preserva_o_hash_de_antes_do_hardening() -> None:
    assert base_spec().spec_hash == GOLDEN_CLASSIC_SPEC_HASH
    assert llm_spec(dict(LEGACY_LLM_PARAMS)).spec_hash == GOLDEN_LEGACY_LLM_SPEC_HASH


#: Spec científica completa: cada campo declarado, como o preflight exige.
SCIENTIFIC_PARAMS = {
    "ticker": "PETR4.SA",
    "provider": "gemini",
    "model": "gemini-model-under-test",
    "temperature": 1.0,
    "thinking_level": "low",
    "max_output_tokens": 4096,
    "analyst_count": 5,
    "consensus_threshold": 0.6,
    "require_all_votes": True,
    "decision_frequency": 1,
    "strict_inputs": True,
    "portfolio_inversion_policy": "fail",
    "long_target_weight": 1.0,
    "risk_max_concentration": 1.0,
    "risk_max_volatility": 0.5,
    "risk_max_drawdown": 0.25,
    "volatility_window": 21,
    "seed_base": 10_000,
}


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("provider", "agent_router"),
        ("model", "outro-modelo"),
        ("temperature", 0.7),
        ("thinking_level", "high"),
        ("max_output_tokens", 2048),
        ("analyst_count", 7),
        ("consensus_threshold", 0.8),
        ("require_all_votes", False),
        ("decision_frequency", 2),
        ("strict_inputs", False),
        ("portfolio_inversion_policy", "flag"),
        ("long_target_weight", 0.5),
        ("risk_max_concentration", 0.9),
        ("risk_max_volatility", 0.4),
        ("risk_max_drawdown", 0.2),
        ("volatility_window", 63),
        ("seed_base", 1),
    ],
)
def test_parametro_cientifico_declarado_muda_o_spec_hash(name: str, value: object) -> None:
    changed = llm_spec({**SCIENTIFIC_PARAMS, name: value})
    assert changed.spec_hash != llm_spec(dict(SCIENTIFIC_PARAMS)).spec_hash


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("temperature", 1.0),
        ("thinking_level", "low"),
        ("max_output_tokens", 4096),
        ("strict_inputs", False),
        ("portfolio_inversion_policy", "flag"),
    ],
)
def test_parametro_novo_so_entra_no_hash_quando_declarado(name: str, value: object) -> None:
    """Declarar o valor default ainda é declarar: a spec diz mais que antes."""
    legacy = llm_spec(dict(LEGACY_LLM_PARAMS))
    assert legacy.spec_hash == GOLDEN_LEGACY_LLM_SPEC_HASH
    assert llm_spec({**LEGACY_LLM_PARAMS, name: value}).spec_hash != legacy.spec_hash


def test_evidencia_observada_nunca_e_configuracao_da_spec() -> None:
    """``resolved_model`` e cia. vivem no trace, nunca na spec."""
    serialized = canonical_json(llm_spec(dict(SCIENTIFIC_PARAMS)).to_dict())
    for observed in ("resolved_model", "provider_response_id", "finish_reason"):
        assert observed not in serialized


def test_int_e_float_de_mesmo_valor_tem_hashes_diferentes() -> None:
    """Comportamento ANTERIOR ao hardening, documentado e não corrigido.

    ``canonical_json`` serializa ``1`` e ``1.0`` de formas diferentes, então
    duas specs com o mesmo comportamento podem ter identidades diferentes.
    Corrigir isso muda identidade de forma ampla e fica fora deste diff; a
    convenção é declarar parâmetros contínuos sempre como ``float``.
    """
    as_int = llm_spec({**SCIENTIFIC_PARAMS, "temperature": 1})
    as_float = llm_spec({**SCIENTIFIC_PARAMS, "temperature": 1.0})
    assert as_int.spec_hash != as_float.spec_hash
