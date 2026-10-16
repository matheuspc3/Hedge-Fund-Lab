"""V7.5 consolidation: the package matches the local records and tampering is detected."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]
import verify_consolidation_v75 as v75  # noqa: E402

LOCAL = (ROOT / v75.V2 / "result.json").exists()


@unittest.skipUnless(LOCAL, "local Radar/Global PM records absent (clean copy)")
class ConsolidationV75(unittest.TestCase):
    def test_package_matches_records(self):
        report = v75.check()
        self.assertTrue(report["ok"], report)

    def test_tampering_is_detected(self):
        real_metrics, real_sha = v75.metrics, v75.sha
        target = v75.V2 + "/result.json"

        def metrics():
            out = real_metrics()
            out["gpm_v1.outcome"]["value"]["status"] = "VALID_PROPOSAL"
            return out

        with (
            patch.object(v75, "metrics", metrics),
            patch.object(v75, "sha", lambda p: "0" * 64 if p == target else real_sha(p)),
        ):
            report = v75.check()
        self.assertEqual(report["metric_divergences"], ["gpm_v1.outcome"])
        self.assertEqual(report["violations"], [target])
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
