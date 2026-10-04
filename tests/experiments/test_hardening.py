"""Infraestrutura do Diagnostic Hardening e o preflight no runner.

Nada aqui roda probe científico: o provedor é sempre mock, os estados são
sintéticos e as métricas são calculadas sobre registros montados à mão.
"""

import hashlib
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pandas as pd
import pytest

from src.agents.features import (
    FEATURE_KEYS,
    dimensionless_features,
)
from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.participant import (
    ACTION_BUY,
    BUY_AT_TARGET_NOOP,
    INVALID_RESPONSE,
    PORTFOLIO_HOLD,
    PROVIDER_FAILURE,
    RISK_VETO_DRAWDOWN,
    RISK_VETO_VOLATILITY,
    TECH_EXPLICIT_HOLD,
    TECH_NO_MAJORITY,
    LLMDecisionError,
    LLMDecisionRecord,
    LLMParticipant,
)
from src.agents.state import (
    PortfolioAction,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
)
from src.agents.technical_analyst import INDICATOR_KEYS
from src.artifacts import RunArtifact
from src.experiments import runner as runner_module
from src.experiments.context import RunContext
from src.experiments.hardening import (
    H2_FREEZE_STATUS,
    H2_FREEZE_V1_GATES,
    H2_SC_PROVISIONAL_PARAMS,
    H2_SC_PROVISIONAL_STATUS,
    H2_THINKING_LADDER,
    H_REAL_ELIGIBLE_COUNT,
    H_REAL_ELIGIBLE_SHA256,
    H_REAL_INDICES,
    H_REAL_PAYLOAD_DIGESTS,
    H_REAL_QUANTILES,
    H_REAL_RESERVED_AT_FREEZE,
    H_REAL_SESSIONS,
    H_REAL_SNAPSHOT_ID,
    H_REAL_SNAPSHOT_IDENTITY_DIGEST,
    H_REAL_STATUS,
    H_REAL_TICKER,
    H_REAL_WINDOW,
    H_SYN_ARCHETYPES,
    H_SYN_PAYLOAD_DIGESTS,
    H_SYN_SESSIONS,
    H_SYN_VERSION,
    PENDING_ADVISOR_RATIFICATION,
    PROPOSED_GATES,
    HardeningAbortedError,
    HardeningOutcome,
    HardeningState,
    diagnostic_metrics,
    frozen_observation,
    gate_flags,
    h2_freeze_v1_params,
    h_real_states,
    real_state,
    require_disjoint,
    run_hardening,
    scientific_payload_digest,
    synthetic_frame,
    synthetic_states,
)
from src.experiments.participants import preflight_participant
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import (
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import (
    DatasetSnapshot,
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)
from src.pipeline.transform import DataTransformer, validate_ohlcv

# ── H_syn ────────────────────────────────────────────────────────


def features_of(frame: pd.DataFrame) -> tuple[dict[str, float], float]:
    """Mesmo pipeline do participante: indicadores, razões e volatilidade."""
    row = DataTransformer().calculate_indicators(frame).iloc[-1]
    levels = {key: float(row[key]) for key in INDICATOR_KEYS if pd.notna(row[key])}
    close = frame["fechamento"]
    volatility = close.pct_change().dropna().tail(21).std(ddof=1) * math.sqrt(252)
    return dimensionless_features(float(close.iloc[-1]), levels), float(volatility)


def test_geradores_sao_deterministicos_validos_e_com_warmup() -> None:
    assert len(H_SYN_ARCHETYPES) == 8
    for archetype in H_SYN_ARCHETYPES:
        frame = synthetic_frame(archetype)
        validate_ohlcv(frame)
        assert len(frame) == H_SYN_SESSIONS >= 504
        pd.testing.assert_frame_equal(frame, synthetic_frame(archetype))
        features, _ = features_of(frame)
        assert set(features) == set(FEATURE_KEYS)


CONTRACT = {
    "steady_uptrend": lambda f, v: f["sma50_gap"] > 0
    and f["sma200_gap"] > 0
    and 50 < f["rsi"] < 70,
    "steady_downtrend": lambda f, v: f["sma50_gap"] < 0
    and f["sma200_gap"] < 0
    and 30 < f["rsi"] < 50,
    "range_low_vol": lambda f, v: abs(f["sma200_gap"]) < 0.01 and v < 0.10,
    "range_high_vol": lambda f, v: 0.25 < v < 0.50,
    "extended_rally": lambda f, v: f["rsi"] > 70 and f["bb_upper_gap"] > 0,
    "extended_selloff": lambda f, v: f["rsi"] < 30 and f["bb_lower_gap"] < 0,
    "mixed_signals": lambda f, v: f["sma50_gap"] > 0 and f["sma200_gap"] < 0,
    "volatility_breach": lambda f, v: v > 0.50,
}


@pytest.mark.parametrize("archetype", H_SYN_ARCHETYPES, ids=lambda item: item.name)
def test_cada_arquetipo_cobre_o_estado_de_contrato_declarado(archetype) -> None:
    features, volatility = features_of(synthetic_frame(archetype))
    assert CONTRACT[archetype.name](features, volatility)


# ── Congelamento de H_syn (H_SYN_VERSION = 1) ────────────────────


def digest(history: pd.DataFrame) -> str:
    """Digest do payload canônico pelo mesmo caminho que o harness usa."""
    return scientific_payload_digest(HardeningState("probe", "SYN", history))


def test_h_syn_v1_esta_congelado_no_payload_publicado() -> None:
    """Mudança material nas features enviadas ao provedor falha aqui.

    Gerador novo, fórmula nova ou biblioteca que mude o payload canônico exige
    ``H_SYN_VERSION`` novo e digests novos — nunca ajuste silencioso.
    """
    assert H_SYN_VERSION == 1
    assert set(H_SYN_PAYLOAD_DIGESTS) == {item.name for item in H_SYN_ARCHETYPES}
    for archetype in H_SYN_ARCHETYPES:
        assert digest(synthetic_frame(archetype)) == H_SYN_PAYLOAD_DIGESTS[archetype.name], (
            archetype.name
        )


def test_ruido_abaixo_da_quantizacao_nao_muda_o_digest_e_mudanca_material_muda() -> None:
    frame = synthetic_frame(H_SYN_ARCHETYPES[0])
    expected = H_SYN_PAYLOAD_DIGESTS[H_SYN_ARCHETYPES[0].name]
    # Diferença de plataforma típica: último bit dos floats internos.
    jitter = frame * (1 + 1e-13)
    assert digest(jitter) == expected
    material = frame.copy()
    material.iloc[-1] = material.iloc[-1] * 1.01
    assert digest(material) != expected


# ── H_real: só infraestrutura ────────────────────────────────────


def test_h_real_reservado_pela_regra_mecanica_de_quantis() -> None:
    """As quatro datas são exatamente ``E[floor(q·(len(E)-1))]``."""
    assert H_REAL_TICKER == "PETR4.SA"
    assert H_REAL_STATUS == H2_FREEZE_STATUS
    assert len(H_REAL_SESSIONS) == len(H_REAL_QUANTILES) == 4
    assert list(H_REAL_SESSIONS) == sorted(H_REAL_SESSIONS)
    assert H_REAL_INDICES == tuple(
        math.floor(q * (H_REAL_ELIGIBLE_COUNT - 1)) for q in H_REAL_QUANTILES
    )
    assert set(H_REAL_PAYLOAD_DIGESTS) == set(H_REAL_SESSIONS)
    low, high = H_REAL_WINDOW
    assert all(low <= session <= high for session in H_REAL_SESSIONS)


SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots" / H_REAL_SNAPSHOT_ID


@pytest.mark.skipif(not SNAPSHOT_DIR.exists(), reason="H_real snapshot is local (git-ignored)")
def test_h_real_e_reproduzivel_a_partir_do_snapshot_congelado() -> None:
    """Refaz ``E``, a seleção e os payloads a partir do snapshot imutável."""
    snapshot = load_dataset_snapshot(SNAPSHOT_DIR)
    verify_snapshot_integrity(snapshot)
    assert snapshot.identity_digest == H_REAL_SNAPSHOT_IDENTITY_DIGEST
    frame = load_snapshot_frames(snapshot, (H_REAL_TICKER,))[H_REAL_TICKER]
    position = {session: i for i, session in enumerate(frame.index)}
    low, high = (pd.Timestamp(day) for day in H_REAL_WINDOW)
    eligible = [
        session
        for session in frame.index
        if low <= session <= high and position[session] + 1 >= 504
    ]
    assert len(eligible) == H_REAL_ELIGIBLE_COUNT
    listing = "\n".join(str(session.date()) for session in eligible)
    assert hashlib.sha256(listing.encode()).hexdigest() == H_REAL_ELIGIBLE_SHA256
    selected = tuple(str(eligible[i].date()) for i in H_REAL_INDICES)
    assert selected == H_REAL_SESSIONS
    # h_real_states confere cada payload contra o digest congelado.
    states = h_real_states(frame, H_REAL_RESERVED_AT_FREEZE)
    assert [state.history.index[-1] for state in states] == [
        pd.Timestamp(day) for day in H_REAL_SESSIONS
    ]


def test_spec_congelada_v1_passa_o_preflight_cientifico_so_com_low() -> None:
    """``low`` está qualificado; ``medium``/``high`` exigem DEV_SMOKE antes."""
    report = LLMParticipant.preflight(h2_freeze_v1_params("low"), scientific=True)
    assert report.status == "QUALIFIED"
    for level in H2_THINKING_LADDER[1:]:
        with pytest.raises(ValueError, match="DECLARED_UNQUALIFIED"):
            LLMParticipant.preflight(h2_freeze_v1_params(level), scientific=True)
    assert H2_THINKING_LADDER == ("low", "medium", "high")
    # seed nunca é transmitida: não existe como parâmetro do freeze.
    assert "seed" not in h2_freeze_v1_params("low")
    assert H2_FREEZE_V1_GATES.max_total_hold_rate == 0.90
    assert H2_FREEZE_V1_GATES.max_same_state_flip_rate == 0.10


RESERVED = MappingProxyType({"CAL-A": ["2001-01-02"], "VALIDATION": []})


def test_estado_real_e_truncado_em_t_e_single_asset() -> None:
    frame = synthetic_frame(H_SYN_ARCHETYPES[0])
    session = frame.index[550]
    state = real_state(frame, session, reserved=RESERVED)
    assert state.history.index[-1] == session
    assert len(state.history) == 551
    with pytest.raises(ValueError, match="single-asset"):
        real_state(frame, session, reserved=RESERVED, ticker="VALE3.SA")
    with pytest.raises(ValueError, match="not a bar"):
        real_state(frame, "1999-01-01", reserved=RESERVED)


def test_estado_real_recusa_sessao_reservada_a_outro_conjunto() -> None:
    frame = synthetic_frame(H_SYN_ARCHETYPES[0])
    session = frame.index[550]
    with pytest.raises(ValueError, match="overlaps CAL-B"):
        real_state(frame, session, reserved={"CAL-B": [session]})
    with pytest.raises(TypeError):
        real_state(frame, session)  # type: ignore[call-arg]


def test_conjunto_h_precisa_ser_disjunto() -> None:
    require_disjoint(["2019-03-01"], {"CAL-A": ["2019-03-04"], "VALIDATION": []})
    with pytest.raises(ValueError, match="overlaps CAL-B: 2019-03-01"):
        require_disjoint(
            ["2019-03-01"], {"CAL-A": [], "CAL-B": [pd.Timestamp("2019-03-01")]}
        )


# ── Harness ──────────────────────────────────────────────────────


def mock_factory(votes: list[str], risk: Any = None):
    def build(ticker: str) -> LLMParticipant:
        client = MockLLMClient(
            {
                TechnicalSignal: [
                    {"signal": kind, "justification": "m", "confidence": 0.5}
                    for kind in votes
                ],
                RiskVerdict: risk
                or {"verdict": "APROVADO", "analysis": "m", "risk_metrics": {}},
                PortfolioAction: {"decision": "COMPRA", "reasoning": "m"},
            }
        )
        return LLMParticipant(ticker, llm_client=client, **H2_SC_PROVISIONAL_PARAMS)

    return build


def test_harness_decide_estados_congelados_sem_liquidar() -> None:
    outcomes = run_hardening(
        synthetic_states(), mock_factory(["COMPRA"] * 5), repetitions=2
    )

    assert len(outcomes) == 16
    assert all(
        outcome.error is None and outcome.record is not None for outcome in outcomes
    )
    assert all(
        not outcome.record.input_violations for outcome in outcomes if outcome.record
    )
    causes = {
        o.state_id.split(":")[1]: o.record.final_cause for o in outcomes if o.record
    }
    assert causes["volatility_breach"] == RISK_VETO_VOLATILITY
    assert causes["steady_uptrend"] == ACTION_BUY
    # Repetições são instâncias novas: cada trace tem só a sua sessão.
    assert all(
        o.trace.summary["call_count"] == 7 or o.state_id.endswith("breach")
        for o in outcomes
    )


class RiskDown(LLMClient):
    """Quorum válido; o gestor de risco cai depois de esgotado o retry."""

    def __init__(self) -> None:
        super().__init__()
        self.inner = MockLLMClient(
            {
                TechnicalSignal: {"signal": "COMPRA", "justification": "m", "confidence": 0.5},
                PortfolioAction: {"decision": "COMPRA", "reasoning": "m"},
            }
        )

    async def generate(self, system_prompt, user_prompt, response_schema=None, options=None, *, metadata=None):
        if response_schema is RiskVerdict:
            raise ConnectionError("risk provider down")
        return await self.inner.generate(
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )


def test_harness_continua_quando_o_provedor_cai_no_risco() -> None:
    def factory(ticker: str) -> LLMParticipant:
        return LLMParticipant(ticker, llm_client=RiskDown(), **H2_SC_PROVISIONAL_PARAMS)

    # Os dois primeiros estados chegam ao risco; nenhum aborta o lote.
    outcomes = run_hardening(synthetic_states()[:2], factory, repetitions=2)
    assert len(outcomes) == 4
    for outcome in outcomes:
        assert outcome.reason == PROVIDER_FAILURE
        assert outcome.record is not None
        assert outcome.record.final_cause == PROVIDER_FAILURE
        assert outcome.record.target_weight is None
        assert outcome.trace.summary["error_count"] == 1
    metrics = diagnostic_metrics(outcomes)
    assert metrics["failure_count"] == 4
    assert metrics["failure_causes"] == {PROVIDER_FAILURE: 4}


def test_bug_fora_do_contrato_aborta_o_lote_sem_perder_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built: list[LLMParticipant] = []

    def factory(ticker: str) -> LLMParticipant:
        participant = mock_factory(["COMPRA"] * 5)(ticker)
        if len(built) == 2:
            monkeypatch.setattr(
                participant, "_agent_state", lambda *a, **k: (_ for _ in ()).throw(KeyError("bug"))
            )
        built.append(participant)
        return participant

    with pytest.raises(HardeningAbortedError) as raised:
        run_hardening(synthetic_states(), factory, repetitions=1)
    preserved = raised.value.outcomes
    assert len(preserved) == 3
    assert all(outcome.error is None for outcome in preserved[:2])
    assert preserved[2].error is not None and "KeyError" in preserved[2].error
    assert isinstance(raised.value.__cause__, KeyError)


def test_harness_preserva_trace_e_causa_quando_a_decisao_falha() -> None:
    outcomes = run_hardening(
        synthetic_states()[:1], mock_factory(["not-a-signal"]), repetitions=1
    )
    (outcome,) = outcomes
    assert outcome.reason == INVALID_RESPONSE
    assert outcome.error and outcome.trace.summary["error_count"] > 0


def test_fixture_unitaria_de_drawdown_fora_de_h_syn() -> None:
    """H_syn parte de carteira zerada; drawdown é coberto à parte, aqui.

    Não é estado oficial de H: só prova que a regra de drawdown chega ao
    ``decisions`` com a causa certa quando o pico ficou para trás.
    """
    history = synthetic_frame(H_SYN_ARCHETYPES[0])
    participant = mock_factory(["COMPRA"] * 5)("SYN")
    for end, equity in ((599, 100_000.0), (600, 70_000.0)):
        state = HardeningState("drawdown", "SYN", history.iloc[:end])
        observation = frozen_observation(state, equity)
        participant.decide(observation)
    record = participant.decisions[-1]
    assert record.final_cause == RISK_VETO_DRAWDOWN
    assert record.target_weight is None


# ── Diagnósticos ─────────────────────────────────────────────────


EMPTY_TRACE = RunArtifact(
    name="llm_calls", filename="llm_calls.jsonl", schema_version=2, content=b""
)


def record(cause: str, outcome: str | None) -> LLMDecisionRecord:
    consensus = None
    if outcome is not None:
        reached = outcome != "NO_MAJORITY"
        consensus = TechnicalConsensus(
            total_analysts=5,
            valid_votes=5,
            threshold=0.6,
            counts={"COMPRA": 0, "VENDA": 0, "MANTER": 0},
            consensus_reached=reached,
            winning_signal=outcome if reached else None,
        )
    return LLMDecisionRecord(
        session=pd.Timestamp("2000-01-03"),
        technical_signal=None,
        consensus=consensus,
        risk_verdict=None,
        portfolio_action=None,
        target_weight=None,
        final_cause=cause,
    )


def outcome(
    state: str, cause: str, technical: str | None, error: str | None = None
) -> HardeningOutcome:
    return HardeningOutcome(state, 0, record(cause, technical), EMPTY_TRACE, error=error)


def test_taxas_de_inatividade_excluem_noop_e_falhas() -> None:
    outcomes = [
        outcome("a", TECH_EXPLICIT_HOLD, "MANTER"),
        outcome("a", TECH_NO_MAJORITY, "NO_MAJORITY"),
        outcome("b", RISK_VETO_VOLATILITY, "COMPRA"),
        outcome("b", BUY_AT_TARGET_NOOP, "COMPRA"),
        outcome("c", PORTFOLIO_HOLD, "VENDA"),
        outcome("c", ACTION_BUY, "COMPRA"),
        outcome("c", INVALID_RESPONSE, None, error="boom"),
    ]
    metrics = diagnostic_metrics(outcomes)
    assert metrics["decision_count"] == 6
    assert metrics["failure_count"] == 1
    assert metrics["failure_causes"] == {INVALID_RESPONSE: 1}
    assert metrics["buy_at_target_noop_count"] == 1
    assert metrics["explicit_hold_rate"] == pytest.approx(1 / 6)
    assert metrics["no_majority_abstention_rate"] == pytest.approx(1 / 6)
    assert metrics["risk_veto_rate"] == pytest.approx(1 / 6)
    assert metrics["portfolio_hold_rate"] == pytest.approx(1 / 6)
    assert metrics["total_hold_rate"] == pytest.approx(4 / 6)


def test_falha_sem_excecao_e_registro_ausente_contam_como_falha() -> None:
    """Inversão com política ``flag`` não levanta, mas continua falha técnica."""
    flagged = outcome("a", INVALID_RESPONSE, "COMPRA")
    missing = HardeningOutcome("b", 0, None, EMPTY_TRACE, error="boom", reason="INVALID_INPUT")
    metrics = diagnostic_metrics([flagged, missing, outcome("c", ACTION_BUY, "COMPRA")])
    assert metrics["decision_count"] == 1
    assert metrics["failure_count"] == 2
    assert metrics["failure_causes"] == {INVALID_RESPONSE: 1, "INVALID_INPUT": 1}


def test_instabilidade_so_compara_repeticoes_do_mesmo_estado() -> None:
    outcomes = [
        outcome("s1", ACTION_BUY, "COMPRA"),
        outcome("s1", ACTION_BUY, "VENDA"),
        outcome("s1", TECH_EXPLICIT_HOLD, "MANTER"),
        # COMPRA em s2 contra VENDA em s1 não é flip: o estado mudou.
        outcome("s2", ACTION_BUY, "COMPRA"),
        outcome("s2", ACTION_BUY, "COMPRA"),
    ]
    metrics = diagnostic_metrics(outcomes)
    # s1: 3 pares, 1 flip (COMPRA/VENDA), 3 discordâncias; s2: 1 par, 0 e 0.
    assert metrics["same_state_flip_rate"] == pytest.approx(1 / 4)
    assert metrics["same_state_disagreement_rate"] == pytest.approx(3 / 4)


def test_gates_propostos_continuam_pendentes_de_ratificacao() -> None:
    assert PROPOSED_GATES.status == PENDING_ADVISOR_RATIFICATION
    assert H2_SC_PROVISIONAL_STATUS == PENDING_ADVISOR_RATIFICATION
    flags = gate_flags(
        {
            "total_hold_rate": 0.95,
            "same_state_flip_rate": 0.05,
            "failure_count": 0,
            "max_tokens_count": 0,
        }
    )
    assert flags == {
        "status": PENDING_ADVISOR_RATIFICATION,
        "contract_failures": False,
        "truncated_outputs": False,
        "degenerate_inactive": True,
        "degenerate_unstable": False,
    }


# ── Preflight no runner ──────────────────────────────────────────


def scientific_spec(snapshot: DatasetSnapshot, params: dict[str, Any]) -> ExperimentSpec:
    sessions = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=ParticipantSpec("llm_agent", {"ticker": "PETR4.SA", **params}),
        initial_capital=100_000.0,
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start=str(sessions[30].date()),
            decision_end=str(sessions[31].date()),
            minimum_history_sessions=3,
        ),
    )


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"provider": "mock"}, "missing: .*strict_inputs"),
        (
            {"provider": "mock", **H2_SC_PROVISIONAL_PARAMS, "strict_inputs": False},
            "strict_inputs=True",
        ),
        (
            {
                "provider": "agent_router",
                "model": "m",
                **H2_SC_PROVISIONAL_PARAMS,
                "thinking_level": "low",
                "max_output_tokens": 1024,
            },
            "does not declare",
        ),
        (
            {
                "provider": "gemini",
                "model": "gemini-model-under-test",
                **H2_SC_PROVISIONAL_PARAMS,
                "thinking_level": "low",
                "max_output_tokens": 1024,
            },
            "DECLARED_UNQUALIFIED",
        ),
    ],
    ids=["mock-incompleto", "sem-strict", "openai-compat", "gemini-sem-live-smoke"],
)
def test_runner_recusa_spec_cientifica_antes_de_construir_o_participante(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    params: dict[str, Any],
    message: str,
) -> None:
    def explode(*args: Any, **kwargs: Any):
        raise AssertionError("participant must not be built after a failed preflight")

    monkeypatch.setattr(runner_module, "build_participant", explode)
    runner = ExperimentRunner(
        scientific_spec(snapshot, params),
        context=RunContext("CALIBRATION", "hardening-preflight-test"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    )
    with pytest.raises(ValueError, match=message):
        runner.run()


def test_run_cientifico_com_historico_curto_falha_fechado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Snapshot de fixture tem ~60 sessões: sem SMA 200, o run não decide."""
    runner = ExperimentRunner(
        scientific_spec(snapshot, {"provider": "mock", **H2_SC_PROVISIONAL_PARAMS}),
        context=RunContext("CALIBRATION", "hardening-preflight-test"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    )
    with pytest.raises(LLMDecisionError) as raised:
        runner.run()
    assert raised.value.reason == "INVALID_INPUT"


def test_participantes_sem_preflight_passam() -> None:
    spec = ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"})
    assert preflight_participant(spec, scientific=True) is None
