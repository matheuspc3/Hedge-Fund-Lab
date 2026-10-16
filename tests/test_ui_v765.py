"""HTTP read-only contract, server restart and Chrome journeys for ledger V1."""

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


def test_ledger_http_get_no_write_routes_and_server_restart():
    snapshots = []
    for _ in range(2):
        foundation.Server.setUpClass()
        try:
            base = foundation.Server.base + "/api/portfolio/ledger"
            with urllib.request.urlopen(base) as response:
                assert json.load(response)["wallets"] == []
            with urllib.request.urlopen(
                base + "?demo=1&wallet=synthetic-v765"
            ) as response:
                d = json.load(response)
                snapshots.append((d["summary"], d["curve"], d["trades"]))
                assert d["read_only"] and d["classification"] == "SYNTHETIC_TEST"
            for suffix in (
                "?wallet=synthetic-v765",
                "?demo=1&wallet=../../x",
                "?demo=1&demo=0",
                "?demo=1&wallet=synthetic-v765&limit=0",
            ):
                with pytest.raises(urllib.error.HTTPError) as exc:
                    urllib.request.urlopen(base + suffix)
                assert exc.value.code == 400
            request = urllib.request.Request(
                base,
                method="POST",
                data=b"{}",
                headers={"Content-Type": "application/json"},
            )
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(request)
            assert exc.value.code in (403, 404, 405)
        finally:
            foundation.Server.tearDownClass()
    assert snapshots[0] == snapshots[1]


@pytest.mark.skipif(
    not shutil.which("node")
    or not foundation.CHROME
    or os.environ.get("HFL_SKIP_BROWSER"),
    reason="Node/Chrome unavailable or browser checks disabled",
)
def test_paper_ledger_chrome_journeys():
    foundation.Server.setUpClass()
    try:
        with tempfile.TemporaryDirectory(prefix="hfl-paper-ui-") as tmp:
            report = Path(tmp) / "ui.json"
            result = subprocess.run(
                [
                    "node",
                    str(foundation.ROOT / "scripts/ui_check_v765.mjs"),
                    foundation.Server.base,
                    str(report),
                ],
                cwd=foundation.ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=600,
            )
            data = json.loads(report.read_text(encoding="utf-8"))
            assert result.returncode == 0, result.stdout + result.stderr
            assert data["failed"] == 0 and data["passed"] >= 30
            assert data["blocked"] == data["exceptions"] == []
    finally:
        foundation.Server.tearDownClass()
