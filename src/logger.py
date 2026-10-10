"""Configuração centralizada de logging para o Hedge-fund-lab.

Uso::

    from src.logger import setup_logger

    # No início da aplicação
    setup_logger(level="INFO", log_file="data/logs/hedgefund.log")

    # No topo de cada módulo
    import logging
    logger = logging.getLogger(__name__)

    # Logs em qualquer lugar
    logger.info("mensagem")
    logger.warning("cuidado")
    logger.error("falhou")
"""

import logging
import sys
from pathlib import Path
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    level: LogLevel = "INFO",
    log_file: str | None = None,
    name: str = "hedgefund",
) -> logging.Logger:
    """Configura o logger raiz e retorna um logger nomeado.

    Adiciona um handler de console (stdout) e opcionalmente um handler
    de arquivo. Todos os ``logging.getLogger(__name__)`` da aplicação
    herdam automaticamente estes handlers.

    Args:
        level: Nível mínimo de log (padrão INFO).
        log_file: Caminho para arquivo de log. Se None, só console.
        name: Nome do logger a retornar.

    Returns:
        Logger configurado.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level))

    # Windows pode expor stdout como cp1252 mesmo em terminais UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ── Console handler ───────────────────────────────────────────
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root.handlers
    ):
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(getattr(logging, level))
        console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(console)

    # ── File handler ──────────────────────────────────────────────
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
            fh = logging.FileHandler(str(log_path), encoding="utf-8")
            fh.setLevel(getattr(logging, level))
            fh.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
            root.addHandler(fh)
            root.info("Logging em arquivo: %s (nível=%s)", log_path.resolve(), level)

    return logging.getLogger(name)
