"""V6 reuses frozen phase specs and requires authorization and preceding PASS."""

import runpy
import sys

import pytest

from scripts import run_cal_a, run_h2_hardening, run_sequential_dev, run_stress
from src.experiments import anchors, treatment


def test_specs_preserve_grid_costs_and_historical_versions(monkeypatch):
    extra = {"technical_prompt_version": 5, "risk_prompt_version": 2, "technical_response_schema_version": 2}
    monkeypatch.setattr(run_cal_a, "TREATMENT_EXTRA", extra)
    monkeypatch.setattr(run_sequential_dev, "TREATMENT_EXTRA", extra)
    for row in anchors.CAL_A_GRID:
        spec = run_cal_a.spec_for(anchors.CAL_A_ANCHORS[0], row)
        assert all(spec.participant.params[k] == v for k,v in extra.items())
        assert spec.participant.params["volatility_window"] == row["volatility_window"]
        assert spec.participant.params["risk_max_volatility"] == row["risk_max_volatility"]
        assert spec.costs.to_dict() == run_stress.spec_for(run_stress.committed_windows()[0]).costs.to_dict()
    assert dict(treatment.H2_V6_HARDENING_PARAMS) == {**treatment.H2_V5_HARDENING_PARAMS, **extra}
    assert treatment.CAL_A_V6_SELECTED_CONFIG is None and treatment.SEQUENTIAL_DEV_V6_SELECTED_CONFIG is None
    with pytest.raises(ValueError):
        treatment.stress_v6_params()


@pytest.mark.parametrize("module,args,phase", (
    (run_h2_hardening,["--treatment","6","--mode","hardening","--thinking-level","low"],"hardening"),
    (run_h2_hardening,["--treatment","6","--mode","b0","--thinking-level","low"],"b0"),
    (run_cal_a,["--treatment","6"],"cal_a"),
    (run_sequential_dev,["--treatment","6"],"sequential"),
    (run_stress,["run","--treatment","6"],"stress"),
))
def test_every_phase_stops_at_guard_before_network(monkeypatch,module,args,phase):
    import h2_v6
    seen=[]
    def stop(**kwargs):
        seen.append(kwargs)
        raise ValueError("offline guard stop")
    monkeypatch.setattr(h2_v6,"require_pre_live_freeze",stop)
    monkeypatch.setattr(module,"git",lambda *args: "")
    if hasattr(module,"load_key"):
        monkeypatch.setattr(module,"load_key",lambda: None)
    monkeypatch.setattr(sys,"argv",[module.__file__,*args])
    with pytest.raises(ValueError,match="offline guard stop"):
        if module is run_stress:
            runpy.run_path(module.__file__,run_name="__main__")
        else:
            module.main()
    assert seen == [{"full_development":True,"phase":phase}]


def test_structural_failure_prevents_phase_selection_and_progression():
    from scripts.h2_v6 import apply_structural_gates, committed_phase, require_sessions
    payload = {"complete":True,"technical_audit":{"technical_calls":300,"technical_votes":300,
        "technical_prompt_v5_only":True,"V6-E":0,"V6-S1":0,"V6-S2":0,"V6-S3":1}}
    assert not apply_structural_gates(payload)["v6_phase_pass"]
    assert payload["status"] == treatment.H2_V6_DEFECT_FIX_FAILED
    with pytest.raises(ValueError,match="requires committed defect PASS"):
        committed_phase("defect")
    for day in (*anchors.CAL_B4_ANCHORS,"2024-09-02"):
        with pytest.raises(ValueError):
            require_sessions([day])
