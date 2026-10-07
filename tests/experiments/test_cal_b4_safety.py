"""Pre-live commitment reproduction and guards; no CAL-B4 inference or features."""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from scripts.run_cal_a import BankedGeminiClient
from src.experiments import anchors, treatment

ROOT = Path(__file__).resolve().parents[2]


def test_cal_b4_commitment_selection_and_ranking():
    sel = json.loads((ROOT / anchors.CAL_B4_SELECTION_EVIDENCE).read_text(encoding="utf-8"))
    seed = hashlib.sha256(("HEDGE-FUND-LAB|CAL-B4|" + anchors.CAL_B3_COMMITMENT_SHA256).encode()).hexdigest()
    assert sel["seed"] == treatment.CAL_B4_SELECTION_SEED == seed
    assert tuple(sel["cal_b4_anchors"]) == anchors.CAL_B4_ANCHORS
    assert anchors.digest(anchors.CAL_B4_ANCHORS) == anchors.CAL_B4_COMMITMENT_SHA256 == sel["cal_b4_commitment_sha256"]
    assert not set(anchors.CAL_B4_ANCHORS) & set(sel["excluded_sessions"])
    # Reproduce calendar-only candidate order, winner and ranking hash for every stratum.
    calendar = (ROOT / "docs/evidence/calendar/b3_official_sessions_2016-01-04_2026-08-31.txt").read_text().splitlines()
    for row in sel["strata"]:
        block = next(s for s in anchors.STRATA if s.stratum_id == row["stratum_id"])
        candidates = [d for d in calendar if block.first <= d <= block.last
                      and d not in sel["excluded_sessions"]]
        ranked = sorted(candidates, key=lambda d: (treatment.session_digest(block.stratum_id, d, seed), d))
        assert len(ranked) == row["candidates"]
        assert ranked[0] == row["winner"]
        ranking = "\n".join(f"{d}|{treatment.session_digest(block.stratum_id, d, seed)}" for d in ranked)
        assert hashlib.sha256(ranking.encode()).hexdigest() == row["ranking_sha256"]
    assert anchors.CAL_B4_STATUS == "SEALED" and anchors.CAL_B_AUTHORIZED is False


@pytest.mark.parametrize("day", anchors.CAL_B4_ANCHORS)
def test_runner_guard_and_call_bank_block_cal_b4(day):
    with pytest.raises(ValueError, match="CAL-B"):
        anchors.require_cal_b_locked(day, day)
    client = BankedGeminiClient(api_key="test-key", model="gemini-3.8-flash")
    client.begin_session(day)
    with pytest.raises(RuntimeError, match="must never reach the call bank"):
        asyncio.run(client.generate("unused", "unused"))


def test_call_bank_blocks_validation_before_network():
    client = BankedGeminiClient(api_key="test-key", model="gemini-3.8-flash")
    client.begin_session("2024-09-02")
    with pytest.raises(RuntimeError, match="after 2024-08-30"):
        asyncio.run(client.generate("unused", "unused"))
