"""
Hedge-fund-lab · Servidor HTTP para o Dashboard

Uso:
    python dashboard/server.py [porta]

Acessar: http://localhost:8080 (ou porta especificada)

Endpoints (somente leitura; servidor escuta apenas em 127.0.0.1):
    /h2                  — Dashboard H2 v6 (Validation, comparações, auditoria)
    /api/h2/status       — identidade, governança e estado das fases
    /api/h2/validation   — métricas, curvas, progresso e custos (?source=provisional|official|demo)
    /api/h2/run          — decisões e trades de um run (?source&run)
    /api/h2/trace        — chamadas LLM de uma sessão (?source&run&session)
    /api/h2/analysis     — preço x decisões, ciclos, exposição, multiagente (?source)
    /api/h2/decision     — Technical → Risk → Portfolio → execução de uma sessão (?source&run&session)
    /api/h2/artifact     — download de artifact selado (?source&run&name)
    /                    — Dashboard legado (Chart.js)
    /logs                — Visualizador de logs em tempo real (SSE)
    /api/logs            — SSE stream do arquivo de logs
"""

import http.server
import json
import logging
import re
import socketserver
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import h2_api

logger = logging.getLogger("hedgefund.dashboard")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
DIR = Path(__file__).parent
PROJECT_ROOT = DIR.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "hedgefund.log"


class Handler(http.server.SimpleHTTPRequestHandler):
    """Handler com rotas especiais para API de logs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    # ── API ───────────────────────────────────────────────────────

    def do_GET(self):
        if self.path == "/api/logs":
            return self._handle_logs_sse()
        if self.path.startswith("/api/h2/"):
            return self._handle_h2()
        if self.path in ("/logs", "/logs.html"):
            return self._serve_static("logs.html")
        if self.path in ("/h2", "/h2/"):
            return self._serve_static("h2.html")
        return super().do_GET()

    def _handle_h2(self) -> None:
        """Read-only H2 v6 API; every parameter is checked against a fixed set."""
        url = urlsplit(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        source, slot, session = q.get("source", "provisional"), q.get("run"), q.get("session")
        if source not in (*h2_api.SOURCES, "demo") or (
            slot is not None and slot not in (*h2_api.LLM, *h2_api.BENCHMARKS, "_root")
        ):
            return self._send_json(None, 400)
        if url.path == "/api/h2/status":
            return self._send_json(h2_api.status())
        if url.path == "/api/h2/validation":
            return self._send_json(h2_api.validation(source))
        if url.path == "/api/h2/run" and slot:
            return self._send_json(h2_api.run_detail(source, slot))
        if url.path == "/api/h2/analysis":
            return self._send_json(h2_api.analysis(source))
        is_session = re.fullmatch(r"\d{4}-\d{2}-\d{2}", session or "")
        if url.path == "/api/h2/trace" and slot and is_session:
            return self._send_json(h2_api.trace(source, slot, session))
        if url.path == "/api/h2/decision" and slot and is_session:
            return self._send_json(h2_api.decision(source, slot, session))
        if url.path == "/api/h2/artifact" and slot:
            path = h2_api.artifact_path(source, slot, q.get("name", ""))
            if path is None:
                return self._send_json(None, 404)
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return None
        return self._send_json(None, 404)

    def _send_json(self, value, code=200) -> None:
        code = 404 if value is None and code == 200 else code
        body = json.dumps(value, ensure_ascii=False, allow_nan=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, filename: str) -> None:
        """Serve um arquivo HTML estático do diretório dashboard."""
        path = DIR / filename
        if not path.exists():
            self.send_error(404, "Not found")
            return

        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _handle_logs_sse(self) -> None:
        """SSE endpoint: envia linhas do arquivo de log em tempo real."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        last_size = 0
        try:
            while True:
                try:
                    if LOG_FILE.exists():
                        current_size = LOG_FILE.stat().st_size
                        if current_size > last_size:
                            with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                                last_size = current_size
                            if new_lines:
                                payload = json.dumps(
                                    {"lines": [line.rstrip("\n\r") for line in new_lines]}
                                )
                                self.wfile.write(f"data: {payload}\n\n".encode())
                                self.wfile.flush()
                        elif current_size < last_size:
                            # Log foi rotacionado/truncado — reinicia
                            last_size = 0
                            payload = json.dumps({"reset": True})
                            self.wfile.write(f"data: {payload}\n\n".encode())
                            self.wfile.flush()
                    else:
                        # Arquivo ainda não existe
                        payload = json.dumps({"lines": [], "waiting": True})
                        self.wfile.write(f"data: {payload}\n\n".encode())
                        self.wfile.flush()
                except OSError:
                    # Race condition: arquivo deletado entre stat() e open()
                    last_size = 0

                # Ping SSE para detectar se o cliente (navegador) fechou a aba/deu refresh.
                # Como SSE ignora linhas que começam com ":", serve como keep-alive invisível.
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()

                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Cliente desconectou — normal


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """Ignora erros de socket inofensivos (como navegador cancelando requisição)."""
        import sys
        err = sys.exc_info()[1]
        if isinstance(err, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def main():
    # Configura logger mínimo para o dashboard (standalone)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    with ReusableTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        logger.info("Servidor iniciado em http://localhost:%d", PORT)
        logger.info("  H2 v6     : http://localhost:%d/h2", PORT)
        logger.info("  Legado    : http://localhost:%d/", PORT)
        logger.info("  Logs      : http://localhost:%d/logs", PORT)
        logger.info("  Ctrl+C para parar")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor encerrado pelo usuário.")


if __name__ == "__main__":
    main()
