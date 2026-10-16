"""Start the dashboard for UI checks without any Gemini key in the process.

The real server loads GEMINI_API_KEY from .env when the variable is absent; here the
variable is removed and the .env loader is replaced, so a paid call
cannot authenticate even if something tried. UI checks only issue GET requests.

Usage: .venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8097
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dashboard"), str(ROOT / "scripts"), str(ROOT)]
os.environ.pop("GEMINI_API_KEY", None)
import server  # noqa: E402

# The default argument of load_gemini_key is bound at import; replace the loader.
server.load_gemini_key = lambda *a, **k: "ausente (verificação de UI)"
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "8097"]
server.main()
