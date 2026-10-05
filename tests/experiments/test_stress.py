"""STRESS_PROBING_FREEZE_V1: universo, seleção mecânica, fronteira e contrato de risco."""

from pathlib import Path

import pandas as pd
import pytest

from src.experiments import runner as runner_module
from src.experiments import stress
from src.experiments.anchors import CAL_B_STRATA, STRATA
from src.experiments.context import RunContext
from src.experiments.hardening import H_REAL_SESSIONS
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import EvaluationSpec, ExecutionSpec, ExperimentSpec, ParticipantSpec
from src.pipeline.snapshot import DatasetSnapshot, load_snapshot_frames


def test_configuracao_h2_congelada_sem_mudanca() -> None:
    p = stress.STRESS_FROZEN_PARAMS
    assert (p["provider"], p["model"], p["thinking_level"]) == ("gemini", "gemini-3.8-flash", "low")
    assert (p["temperature"], p["max_output_tokens"]) == (1.0, 8192)
    assert "seed" not in p
    assert (p["analyst_count"], p["consensus_threshold"], p["require_all_votes"]) == (5, 0.6, True)
    assert (p["decision_frequency"], p["strict_inputs"], p["portfolio_inversion_policy"]) == (1, True, "fail")
    assert p["long_target_weight"] == 1.0
    assert (p["volatility_window"], p["risk_max_volatility"]) == (21, 0.40)
    assert (p["risk_max_drawdown"], p["risk_max_concentration"]) == (0.25, 1.0)
    assert (p["retry_attempts"], p["retry_base_delay"]) == (6, 2.0)
    assert dict(stress.CALIBRATION_PROVENANCE) == {
        "CAL_A_DISCRIMINATION": "NONE",
        "CAL_A_SELECTION_BASIS": "PROTOCOL_TIE_FALLBACK",
        "SEQUENTIAL_DEV_DISCRIMINATION": "NONE",
        "SEQUENTIAL_DEV_SELECTION_BASIS": "PROTOCOL_TIE_FALLBACK",
    }
    assert stress.STRESS_REPETITIONS == 3 and stress.STRESS_WINDOW_COUNT == 4


def test_universo_sao_os_20_estratos_nao_cal_b() -> None:
    eligible = stress.STRESS_ELIGIBLE_STRATA
    assert len(eligible) == 20
    assert {s.stratum_id for s in eligible} == set(range(1, 31)) - set(CAL_B_STRATA)
    assert all(s.subset == "CAL-A" for s in eligible)  # fronteiras exatas do Amendment 2
    assert stress.STRESS_DOMAIN == ("2018-01-12", "2024-02-28")
    for day in H_REAL_SESSIONS:  # H_real cai só em estratos CAL-B
        assert not any(s.first <= day <= s.last for s in eligible)


def test_metricas_de_mercado_so_dentro_da_janela() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="B")
    window = pd.DataFrame(
        {"abertura": [10.0, 11.5, 9.0, 8.0, 9.9], "fechamento": [10.0, 11.0, 8.8, 9.0, 9.9]}, index=idx
    )
    m = stress.market_stress_metrics(window)
    assert m["market_max_drawdown"] == pytest.approx(1 - 8.8 / 11.0)
    returns = pd.Series([0.1, 8.8 / 11 - 1, 9 / 8.8 - 1, 9.9 / 9 - 1])
    assert m["realized_volatility"] == pytest.approx(returns.std(ddof=1) * 252**0.5)
    assert m["worst_daily_return"] == pytest.approx(8.8 / 11 - 1)
    # gaps só a partir da segunda sessão: 11.5/10, 9/11, 8/8.8, 9.9/9
    assert m["max_abs_overnight_gap"] == pytest.approx(abs(9.0 / 11.0 - 1))


def test_selecao_mecanica_ordem_desempate_e_sem_repeticao() -> None:
    metrics = {
        1: {"market_max_drawdown": 0.5, "realized_volatility": 0.9, "worst_daily_return": -0.2, "max_abs_overnight_gap": 0.1},
        2: {"market_max_drawdown": 0.5, "realized_volatility": 0.9, "worst_daily_return": -0.2, "max_abs_overnight_gap": 0.1},
        4: {"market_max_drawdown": 0.1, "realized_volatility": 0.2, "worst_daily_return": -0.3, "max_abs_overnight_gap": 0.1},
        5: {"market_max_drawdown": 0.2, "realized_volatility": 0.3, "worst_daily_return": -0.1, "max_abs_overnight_gap": 0.0},
    }
    ranked = stress.rankings(metrics)
    assert ranked["MAX_DRAWDOWN"] == [1, 2, 5, 4]  # empate 1/2 -> menor id
    assert ranked["WORST_DAILY_RETURN"] == [4, 1, 2, 5]  # mais negativo primeiro
    assert ranked["MAX_ABS_OVERNIGHT_GAP"] == [1, 2, 4, 5]
    assert stress.select_stress_windows(ranked) == [
        ("MAX_DRAWDOWN", 1),
        ("MAX_REALIZED_VOLATILITY", 2),  # 1 já escolhido -> próximo
        ("WORST_DAILY_RETURN", 4),
        ("MAX_ABS_OVERNIGHT_GAP", 5),  # 1, 2 e 4 usados
    ]
    assert stress.ranking_digest([1, 2], metrics, "market_max_drawdown") != stress.ranking_digest(
        [2, 1], metrics, "market_max_drawdown"
    )


def test_cal_b_nunca_e_janela_nem_metrica() -> None:
    cal_b = next(s for s in STRATA if s.stratum_id in CAL_B_STRATA)
    frame = pd.DataFrame({"abertura": [1.0], "fechamento": [1.0]}, index=[pd.Timestamp(cal_b.first)])
    with pytest.raises(ValueError, match="CAL-B"):
        stress.stratum_frame(frame, cal_b)
    with pytest.raises(ValueError, match="CAL-B"):
        stress.stress_boundary("S1", cal_b)
    eligible = stress.STRESS_ELIGIBLE_STRATA[0]
    with pytest.raises(ValueError, match="differ"):  # sessão faltando/sobrando
        stress.stratum_frame(frame, eligible)


def test_probes_de_risco_deterministicos() -> None:
    rows = {row["case"]: row for row in stress.risk_contract_probes()}
    assert all(row["pass"] for row in rows.values()), [r for r in rows.values() if not r["pass"]]
    assert rows["dd_0.250000"]["risk_source"] == "LLM"  # regra é ">": 0.25 não veta
    assert rows["dd_0.250001"]["risk_rule"] == "DRAWDOWN" and rows["dd_0.250001"]["llm_risk_calls"] == 0
    assert rows["dd_raw_0.2500004_canon_0.250000"]["canonical_drawdown"] == 0.25
    assert rows["dd_raw_0.2500006_canon_0.250001"]["canonical_drawdown"] == 0.250001
    assert rows["vol_0.400000"]["risk_source"] == "LLM"
    assert rows["vol_0.400001"]["risk_rule"] == "VOLATILITY" and rows["vol_0.400001"]["llm_risk_calls"] == 0
    assert rows["vol_raw_0.4000004_canon_0.400000"]["canonical_volatility"] == 0.4
    for name in ("sell_both_breached", "hold_both_breached"):  # saída/inação nunca bloqueada
        assert rows[name]["risk_source"] == "AUTO_APPROVE" and rows[name]["verdict"] == "APROVADO"


def test_runner_recusa_ordem_que_atravessa_a_janela_de_stress(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """no_order_execution_may_cross_stress_window_boundary, aplicada pelo runner."""
    sessions = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index
    first, last = (str(sessions[i].date()) for i in (20, 30))
    boundary = stress.PhaseWindow("STRESS_TEST", first, last)

    def runner(end: str) -> ExperimentRunner:
        spec = ExperimentSpec(
            snapshot_id=snapshot.snapshot_id,
            participant=ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"}),
            initial_capital=100_000.0,
            execution=ExecutionSpec(quantity_mode="fractional_notional"),
            evaluation=EvaluationSpec(decision_start=first, decision_end=end, minimum_history_sessions=3),
        )
        return ExperimentRunner(
            spec, context=RunContext("CALIBRATION", "stress-boundary-test"), snapshot_dir=snapshot_dir,
            runs_dir=runs_dir, repository_dir=tmp_path, allow_dirty=True, boundaries=(boundary,),
        )

    built: list[object] = []
    real_build = runner_module.build_participant
    monkeypatch.setattr(runner_module, "build_participant", lambda s: built.append(s) or real_build(s))
    with pytest.raises(ValueError, match="no_order_execution_may_cross_phase_boundary.*STRESS_TEST"):
        runner(last).run()  # decidir na última sessão executaria fora da janela
    with pytest.raises(ValueError, match="crosses"):
        runner(str(sessions[35].date())).run()
    assert built == []  # recusado antes de construir o participante

    result = runner(str(sessions[29].date())).run()  # penúltima = última decisão
    assert result.evaluation.settlement_session == sessions[30]
    assert result.evaluation.data_end == sessions[30]  # nada depois da janela chega ao motor
    assert result.equity_curve.index[-1] == sessions[30]
    assert all(pd.Timestamp(t.date) <= sessions[30] for t in result.trades)
