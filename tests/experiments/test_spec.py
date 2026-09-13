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


def test_registry_cobre_os_cinco_classicos() -> None:
    assert set(PARTICIPANT_REGISTRY) == {
        "bollinger",
        "buy_and_hold",
        "equal_weight",
        "min_variance",
        "sma_cross",
    }


def test_kind_desconhecido_falha_listando_os_suportados() -> None:
    with pytest.raises(ValueError, match="unsupported participant kind"):
        build_participant(ParticipantSpec("llm_agent", {"ticker": "PETR4.SA"}))


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
