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
import forward_api

logger = logging.getLogger("hedgefund.dashboard")

PORT = 8081
DIR = Path(__file__).parent
PROJECT_ROOT = DIR.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "hedgefund.log"


class Handler(http.server.SimpleHTTPRequestHandler):
    """Handler com rotas especiais para API de logs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    # ── API ───────────────────────────────────────────────────────

    def do_GET(self):
        if not self._local_request():
            return self._send_json({"error": "local_origin_required"}, 403)
        if self.path.startswith("/api/forward/"):
            return self._handle_forward()
        if self.path == "/api/logs":
            return self._handle_logs_sse()
        if self.path.startswith("/api/h2/"):
            return self._handle_h2()
        if self.path in ("/logs", "/logs.html"):
            return self._serve_static("logs.html")
        if self.path in ("/h2", "/h2/"):
            return self._serve_static("h2.html")
        if self.path in ("/paper", "/paper/"):
            return self._serve_static("paper.html")
        if self._static_allowed():
            return super().do_GET()
        return self._send_json(None, 404)

    def _local_request(self, post=False):
        port = self.server.server_address[1]
        hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        if port == 80:
            hosts.update(("localhost", "127.0.0.1"))
        values = self.headers.get_all("Host", [])
        if len(values) != 1 or values[0] not in hosts:
            return False
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1 or (post and len(origins) != 1):
            return False
        if origins and origins[0] != f"http://{values[0]}":
            return False
        return self.headers.get("Sec-Fetch-Site") not in ("cross-site", "same-site")

    def _static_allowed(self):
        path = urlsplit(self.path).path
        allowed = {
            "/",
            "/index.html",
            "/h2.html",
            "/paper.html",
            "/logs.html",
            "/style.css",
            "/app.js",
            "/h2.js",
            "/paper.js",
            "/paper.css",
            "/data.json",
            "/vendor/chart.umd.js",
        }
        return (
            path in allowed
            and self.translate_path(path)
            and Path(self.translate_path(path)).resolve().is_relative_to(DIR.resolve())
        )

    def do_HEAD(self):
        if not self._local_request():
            return self.send_error(403)
        if not self._static_allowed():
            return self.send_error(404)
        return super().do_HEAD()

    def _handle_forward(self):
        url = urlsplit(self.path)
        q = parse_qs(url.query, keep_blank_values=True)
        if set(q) - {"session"} or any(len(v) != 1 for v in q.values()):
            return self._send_json({"error": "invalid_query"}, 400)
        try:
            if url.path == "/api/forward/history" and not q:
                return self._send_json(forward_api.history())
            if url.path == "/api/forward/decision":
                return self._send_json(forward_api.decision(q.get("session", [None])[0]))
            if url.path == "/api/forward/portfolios" and not q:
                return self._send_json(forward_api.portfolios())
        except (ValueError, KeyError, OSError):
            return self._send_json({"error": "invalid_or_incomplete_record"}, 400)
        return self._send_json(None, 404)

    def _handle_h2(self) -> None:
        """Read-only H2 v6 API; every parameter is checked against a fixed set."""
        url = urlsplit(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        source, slot, session = (
            q.get("source", "provisional"),
            q.get("run"),
            q.get("session"),
        )
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
        body = json.dumps(
            value, ensure_ascii=False, allow_nan=False, default=str
        ).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
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
    # On Windows SO_REUSEADDR lets a second server bind a port already in use; an
    # old server kept answering the API while a new one started silently.
    allow_reuse_address = sys.platform != "win32"
    # The default listen backlog (5) refuses connections when rapid source/run
    # switches fire parallel requests; refused fetches looked like "API down".
    request_queue_size = 64

    def handle_error(self, request, client_address):
        """Ignora erros de socket inofensivos (como navegador cancelando requisição)."""
        import sys

        err = sys.exc_info()[1]
        if isinstance(
            err, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)
        ):
            return
        super().handle_error(request, client_address)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    # Configura logger mínimo para o dashboard (standalone)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    with ReusableTCPServer(("127.0.0.1", port), Handler) as httpd:
        logger.info("Servidor iniciado em http://localhost:%d", port)
        logger.info("  H2 v6     : http://localhost:%d/h2", port)
        logger.info("  Paper     : http://localhost:%d/paper", port)
        logger.info("  Legado    : http://localhost:%d/", port)
        logger.info("  Logs      : http://localhost:%d/logs", port)
        logger.info("  Ctrl+C para parar")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor encerrado pelo usuário.")


if __name__ == "__main__":
    main()
