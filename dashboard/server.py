"""
Hedge-fund-lab · Servidor HTTP para o Dashboard

Uso:
    python dashboard/server.py [porta]

Acessar: http://localhost:8080 (ou porta especificada)

Endpoints:
    /           — Dashboard principal (Chart.js)
    /logs       — Visualizador de logs em tempo real (SSE)
    /api/logs   — SSE stream do arquivo de logs
"""

import http.server
import json
import logging
import socketserver
import sys
import time
from pathlib import Path

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
        if self.path in ("/logs", "/logs.html"):
            return self._serve_static("logs.html")
        return super().do_GET()

    def _serve_static(self, filename: str) -> None:
        """Serve um arquivo HTML estático do diretório dashboard."""
        path = DIR / filename
        if not path.exists():
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        with open(path, "rb") as f:
            self.wfile.write(f.read())

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
                            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                                last_size = current_size
                            if new_lines:
                                payload = json.dumps({"lines": [l.rstrip("\n\r") for l in new_lines]})
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
                except (OSError, IOError):
                    # Race condition: arquivo deletado entre stat() e open()
                    last_size = 0

                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Cliente desconectou — normal


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    # Configura logger mínimo para o dashboard (standalone)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    with ReusableTCPServer(("", PORT), Handler) as httpd:
        logger.info("Servidor iniciado em http://localhost:%d", PORT)
        logger.info("  Dashboard : http://localhost:%d/", PORT)
        logger.info("  Logs      : http://localhost:%d/logs", PORT)
        logger.info("  Ctrl+C para parar")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor encerrado pelo usuário.")


if __name__ == "__main__":
    main()
