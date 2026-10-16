"""Shared shell update uses the existing Radar preparation boundary."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_shared_update_scope_lifecycle_and_no_inference():
    result = subprocess.run(
        [
            "node",
            str(ROOT / "tests/market_update_ui_check.js"),
            str(ROOT / "dashboard/shell.js"),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_update_dialog_is_in_shared_shell():
    shell = (ROOT / "dashboard/shell.html").read_text(encoding="utf-8")
    assert (
        'id="hfl-market-open"' in shell and 'aria-controls="hfl-market-dialog"' in shell
    )
    assert 'id="hfl-market-status" role="status"' in shell
