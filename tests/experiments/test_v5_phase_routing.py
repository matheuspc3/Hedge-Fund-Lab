"""V5 uses the existing scientific specs and refuses full development before PASS."""

import sys

import pytest

from scripts import run_cal_a, run_h2_hardening, run_sequential_dev, run_stress
from src.experiments import anchors, treatment


def test_v5_specs_preserve_grid_execution_and_costs(monkeypatch):
    monkeypatch.setattr(run_cal_a, "TREATMENT_EXTRA", {"technical_prompt_version": 4, "risk_prompt_version": 2})
    monkeypatch.setattr(run_sequential_dev, "TREATMENT_EXTRA", {"technical_prompt_version": 4, "risk_prompt_version": 2})
    for config in anchors.CAL_A_GRID:
        spec = run_cal_a.spec_for(anchors.CAL_A_ANCHORS[0], config)
        assert spec.participant.params["technical_prompt_version"] == 4
        assert spec.participant.params["risk_prompt_version"] == 2
        assert spec.participant.params["volatility_window"] == config["volatility_window"]
        assert spec.participant.params["risk_max_volatility"] == config["risk_max_volatility"]
        assert spec.costs.to_dict() == run_stress.spec_for(run_stress.committed_windows()[0]).costs.to_dict()
    assert dict(treatment.H2_V5_HARDENING_PARAMS) == {**treatment.H2_V4_HARDENING_PARAMS, "technical_prompt_version": 4}
    assert run_cal_a.KINDS[5] == "CAL_A_V5"


@pytest.mark.parametrize("module,args", (
    (run_h2_hardening, ["--treatment", "5", "--mode", "hardening", "--thinking-level", "low"]),
    (run_h2_hardening, ["--treatment", "5", "--mode", "b0", "--thinking-level", "low"]),
    (run_cal_a, ["--treatment", "5"]),
    (run_sequential_dev, ["--treatment", "5"]),
))
def test_v5_phase_routes_through_pass_guard(monkeypatch, module, args):
    import h2_v5

    seen = []

    def stop(*, full_development=False):
        seen.append(full_development)
        raise ValueError("offline stop at full development guard")

    monkeypatch.setattr(h2_v5, "require_pre_live_freeze", stop)
    monkeypatch.setattr(module, "git", lambda *args: "")
    if hasattr(module, "load_key"):
        monkeypatch.setattr(module, "load_key", lambda: None)
    monkeypatch.setattr(sys, "argv", [module.__file__, *args])
    with pytest.raises(ValueError, match="offline stop"):
        module.main()
    assert seen == [True]
