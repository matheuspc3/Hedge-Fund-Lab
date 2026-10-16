"""Portfolio and paper browser journeys against the keyless local server."""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import test_ui_v762 as foundation


def test_monitoring_get_contract():
    foundation.Server.setUpClass()
    try:
        base = foundation.Server.base
        with urllib.request.urlopen(base + "/api/portfolio/monitoring") as response:
            d = json.load(response)
        assert (
            d["read_only"]
            and len([w for w in d["wallets"] if w["id"].startswith("h2:")]) == 5
        )
        for suffix in (
            "?wallet=../../x",
            "?wallet=h2:ai&wallet=h2:buy_and_hold",
            "?execute=1",
        ):
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(base + "/api/portfolio/monitoring" + suffix)
            assert exc.value.code == 400
        for asset in ("/monitoring.js", "/monitoring.css"):
            assert urllib.request.urlopen(base + asset).status == 200
    finally:
        foundation.Server.tearDownClass()


@pytest.mark.skipif(
    not shutil.which("node")
    or not foundation.CHROME
    or os.environ.get("HFL_SKIP_BROWSER"),
    reason="Node/Chrome unavailable or browser checks disabled",
)
def test_portfolio_paper_browser_journeys():
    foundation.Server.setUpClass()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "ui_checks.json"
            done = subprocess.run(
                [
                    "node",
                    str(foundation.ROOT / "scripts/ui_check_v764.mjs"),
                    foundation.Server.base,
                    str(report),
                ],
                cwd=foundation.ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=900,
            )
            d = json.loads(report.read_text(encoding="utf-8"))
            assert done.returncode == 0, done.stdout + done.stderr
            assert d["failed"] == 0 and d["passed"] >= 30
            assert d["blocked"] == d["exceptions"] == []
    finally:
        foundation.Server.tearDownClass()
