"""Build a portable, read-only explorer from the completed, reconciled exports."""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "data/cache/continuous-replay/april-november-2026-flash/qualified-v2"


def build():
    out = ROOT / "exports"
    replay = json.loads((out / "explorer.json").read_text(encoding="utf-8"))
    checks = json.loads((ROOT / "checks.json").read_text(encoding="utf-8"))
    preservation = json.loads((ROOT / "preservation_check.json").read_text(encoding="utf-8"))
    assert replay["completed"] and len(replay["days"]) == 153
    assert checks["status"] == preservation["status"] == "PASS"
    assert checks["daily_wallet_states_reconstructed"] == 918
    assert all(len(d["valuation"]) == 6 for d in replay["days"])
    bundle = json.dumps({"replay": replay, "checks": checks, "preservation": preservation}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    chart = (PROJECT / "dashboard/vendor/chart.umd.js").read_text(encoding="utf-8")
    assert "</script" not in chart.lower()
    template = (PROJECT / "dashboard/replay_explorer.html").read_text(encoding="utf-8")
    html = template.replace("__CHART_JS__", chart, 1).replace("__REPLAY_BUNDLE_JSON__", bundle, 1)
    (out / "index.html").write_text(html, encoding="utf-8")
    calls = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    (out / "calls-data.js").write_text("window.replayCalls=" + json.dumps(calls, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    launcher = """# Interface local de leitura; encerre com Ctrl+C.
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webbrowser

if __name__ == '__main__':
    handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parent))
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print('Explorador local: ' + url, flush=True)
        print('Encerre com Ctrl+C.', flush=True)
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
"""
    (out / "abrir_explorador.py").write_text(launcher, encoding="utf-8")
    (out / "LEIA-ME.txt").write_text("Explorador da campanha contínua de seis carteiras\n\nCom Python instalado, execute:\n  python abrir_explorador.py\n\nO inicializador abre um servidor somente em 127.0.0.1 e o navegador.\nEncerre com Ctrl+C na janela do servidor. Não há escrita em produção ou novas chamadas Gemini.\n\nMantenha index.html, calls-data.js e os CSV/JSON na mesma pasta.\nOs dados centrais e o gráfico estão incorporados ao HTML; as chamadas completas são carregadas localmente sob demanda.\nO preview HTTP foi verificado; a política do navegador de teste bloqueia file://, portanto a abertura direta não foi verificada.\n", encoding="utf-8")
    print(json.dumps({"html": str(out / "index.html"), "html_bytes": len(html.encode()), "calls": len(calls["logical_calls"]), "offline": True}))


if __name__ == "__main__":
    build()
