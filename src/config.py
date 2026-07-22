"""Configuração centralizada do Hedge-fund-lab.

Carrega variáveis de ambiente do arquivo .env (se existir)
e disponibiliza um singleton ``settings`` para todo o projeto.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente / .env."""

    database_url: str = "sqlite:///hedgefundlab.db"
    default_tickers: list[str] = [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
        "ABEV3.SA", "WEGE3.SA", "CMIG4.SA", "RENT3.SA", "SUZB3.SA",
    ]
    start_date: str = "2016-01-01"
    end_date: str = "2025-12-31"
    batch_size: int = 1000
    cache_dir: str = "data/raw"
    log_level: str = "INFO"
    log_file: str = "data/logs/hedgefund.log"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# ── Metadados dos tickers ──────────────────────────────────────────
TICKER_INFO: dict[str, dict[str, str]] = {
    "PETR4.SA": {"nome": "Petrobras", "setor": "Petróleo & Gás"},
    "VALE3.SA": {"nome": "Vale", "setor": "Mineração"},
    "ITUB4.SA": {"nome": "Itaú Unibanco", "setor": "Bancos"},
    "BBDC4.SA": {"nome": "Bradesco", "setor": "Bancos"},
    "BBAS3.SA": {"nome": "Banco do Brasil", "setor": "Bancos"},
    "ABEV3.SA": {"nome": "Ambev", "setor": "Bebidas"},
    "WEGE3.SA": {"nome": "WEG", "setor": "Indústria"},
    "CMIG4.SA": {"nome": "Cemig", "setor": "Energia"},
    "RENT3.SA": {"nome": "Localiza", "setor": "Locação de Veículos"},
    "SUZB3.SA": {"nome": "Suzano", "setor": "Papel & Celulose"},
}

settings = Settings()
