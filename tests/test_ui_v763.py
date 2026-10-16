"""Mercado/Radar browser journeys, using the existing keyless test server."""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import pytest
import test_ui_v762 as foundation

ROOT = foundation.ROOT


@pytest.mark.skipif(
    not shutil.which("node")
    or not foundation.CHROME
    or os.environ.get("HFL_SKIP_BROWSER"),
    reason="Node/Chrome unavailable or browser checks disabled",
)
def test_market_radar_interactions():
    foundation.Server.setUpClass()
    try:
        for route in (
            "/market",
            "/market/",
            "/market.html",
            "/market.js",
            "/market-ui.js",
            "/market.css",
        ):
            with urllib.request.urlopen(
                foundation.Server.base + route, timeout=30
            ) as response:
                assert response.status == 200
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui_checks.json"
            done = subprocess.run(
                [
                    "node",
                    str(ROOT / "scripts/ui_check_v763.mjs"),
                    foundation.Server.base,
                    str(out),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=900,
            )
            report = json.loads(out.read_text(encoding="utf-8"))
            assert done.returncode == 0, (
                done.stdout
                + done.stderr
                + str([r for r in report["results"] if not r["ok"]])
            )
            assert report["failed"] == 0 and report["passed"] >= 40
            assert report["blocked"] == [] and report["exceptions"] == []
    finally:
        foundation.Server.tearDownClass()
