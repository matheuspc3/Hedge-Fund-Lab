"""OA-1 provisional route + dashboard reader, end to end on generated data.

Fake native HTTP transport, synthetic prices, network blocked. Requires a clean
tree (the candidate manifest is verified for real).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "dashboard"))

import h2_api  # noqa: E402
import run_h2_v6_provisional as oa1  # noqa: E402
from qualify_h2_v6_production import NativeFactory  # noqa: E402

from src.experiments.h2_evaluation_manifest import (  # noqa: E402
    CANDIDATE,
    verify_manifest,
)
from src.experiments.h2_evaluation_offline import (  # noqa: E402
    no_network,
    synthetic_fixture,
)
from src.experiments.h2_evaluation_production import JournalIntegrityError  # noqa: E402


class OfflineBatch(oa1.ProvisionalValidationBatch):
    def _require_inputs(self):
        """Generated snapshot and tmp root instead of the reserved ones."""


def test_oa1_validation_seal_and_dashboard(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "OFFLINE_TEST_NOT_A_SECRET")
    sha = oa1.candidate_sha()
    document = verify_manifest(CANDIDATE, sha)
    snapshot = synthetic_fixture(tmp_path / "fixture")
    auth = oa1.write_authorization(
        document,
        sha,
        "OFFLINE TEST FIXTURE (not a human act)",
        path=tmp_path / "auth.json",
    )

    # The real input gate refuses generated data and foreign output roots.
    with pytest.raises(ValueError, match="snapshot"):
        oa1.ProvisionalValidationBatch(snapshot, sha, auth, root=tmp_path / "refused")

    # Any field outside the expected identity voids the authorization.
    forged = json.loads(auth.read_text(encoding="utf-8"))
    forged["final_test_authorized"] = True
    (tmp_path / "forged.json").write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(ValueError, match="final_test_authorized"):
        oa1.check_authorization(document, sha, tmp_path / "forged.json")

    batch = OfflineBatch(snapshot, sha, auth, root=tmp_path / "out")
    factory = NativeFactory()
    batch.transport_factory = factory
    try:
        with no_network():
            summary = oa1.complete(batch)
        assert summary["mode"] == oa1.MODE and summary["academic_ratification"] is False
        assert len(factory.transports) == 3
        assert all(
            p.name.startswith("H2-V6-OA1-VALIDATION-")
            for p in (batch.root / "runs").iterdir()
        )
        checkpoint = oa1.seal(batch, tmp_path / "checkpoint.json")
        sealed = json.loads(checkpoint.read_text(encoding="utf-8"))
        assert sealed["statistics"] == summary["statistics"]
        assert sealed["final_test_authorized"] is False

        # Authorization changed after construction: the per-transport gate fails closed.
        auth.write_text(auth.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with pytest.raises(JournalIntegrityError):
            batch._check_authority()
    finally:
        batch.close()

    monkeypatch.setitem(h2_api.SOURCES, "provisional", batch.root)
    real = h2_api.validation("provisional")
    assert real["synthetic"] is False and real["banner"] is None
    assert real["state"] == "CONCLUÍDA E SELADA"
    assert all(p["metrics"] for p in real["participants"])
    assert real["statistics"]["delta"] == summary["statistics"]["delta"]
    assert len(real["curves"]["dates"]) == 248 and set(real["costs"]) == {
        "0",
        "5",
        "10",
        "20",
    }
    assert {p["sessions_started"] for p in real["progress"].values()} == {247}
    detail = h2_api.run_detail("provisional", "L01")
    session = detail["decisions"][0]["decision_session"]
    assert h2_api.trace("provisional", "L01", session)["calls"]
    assert h2_api.artifact_path("provisional", "L01", "../../.env") is None
    assert h2_api.artifact_path("provisional", "_root", "summary.json").is_file()

    demo = h2_api.validation("demo")
    assert demo["synthetic"] is True and demo["banner"] == h2_api.DEMO_BANNER
    assert (
        demo["costs"]["20"]["statistics"] is None
    )  # one invalid replay → no subset aggregate
