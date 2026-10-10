"""Forward dashboard checks: real records are read-only; all execution tests fake."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import forward_api as api  # noqa: E402


def test_real_october_decision_and_cash_are_distinct():
    if not (api.OUTPUT / "state.json").exists():
        pytest.skip("local forward records absent")
    d = api.decision("2026-10-09")
    assert d["status"] == "DECIDED" and d["target_session"] == "2026-10-13"
    assert [a["signal"] for a in d["analysts"]] == ["COMPRA"] * 5
    assert sum(e["count"] for e in d["evidence_summary"]) == sum(
        len(a["evidence"]) for a in d["analysts"]
    )
    assert d["pending"]["target_weight"] == 1 and d["execution"] is None
    w = api.portfolios()["wallets"]
    assert w[0]["equity"] == w[1]["equity"] == 100000
    assert w[0]["composition"][0]["weight"] == 0
    assert w[0]["costs"] == 0 and not w[0]["trades"]
    text = json.dumps(d)
    for forbidden in (
        "system_prompt",
        "user_prompt",
        "raw_response",
        "provider_journal",
        "provider_response",
        "api_key",
    ):
        assert forbidden not in text


@pytest.mark.parametrize(
    "session", ["../state", "2026-99-09", "2026-10-09/..", "2026-10-09%00", ""]
)
def test_session_boundary(session):
    with pytest.raises(ValueError):
        api.session_name(session)


def test_missing_failed_and_executed_records(tmp_path):
    assert api.decision(root=tmp_path) is None
    assert not api.portfolios(tmp_path)["wallets"]
    folder = tmp_path / "sessions/2026-10-09"
    folder.mkdir(parents=True)
    data = {"ticker": "PETR4.SA", "target_session": "2026-10-13", "close_used": 56}
    (folder / "input.json").write_text(json.dumps(data))
    assert api.decision(root=tmp_path)["status"] == "AGUARDANDO"
    (folder / "decision.json").write_text(
        json.dumps(
            {
                "status": "FAILED",
                "failure": "secret raw envelope",
                "system_prompt": "DO NOT SERVE",
            }
        )
    )
    d = api.decision(root=tmp_path)
    assert d["status"] == "FAILED" and d["analysts"] == []
    assert "secret raw envelope" not in json.dumps(
        d
    ) and "DO NOT SERVE" not in json.dumps(d)
    (tmp_path / "state.json").write_text(
        json.dumps(
            {
                "sessions": [
                    {
                        "session": "2026-10-13",
                        "executed_decision": "2026-10-09",
                        "trades": [
                            {
                                "type": "BUY",
                                "price": 55,
                                "quantity": 10,
                                "cost": 1,
                                "raw": "DO NOT SERVE",
                            }
                        ],
                    }
                ]
            }
        )
    )
    d = api.decision(root=tmp_path)
    d = api.decision("2026-10-09", tmp_path)
    assert d["execution"]["session"] == "2026-10-13"
    assert "raw" not in d["execution"]["trades"][0]


def test_missed_session_is_in_history(tmp_path):
    (tmp_path / "state.json").write_text(
        json.dumps({"sessions": [{"session": "2026-10-13", "decision": "MISSED"}]})
    )
    assert api.history(tmp_path)[0]["session"] == "2026-10-13"
    assert api.decision("2026-10-13", tmp_path)["status"] == "MISSED"
