"""Flows Prefect para orquestração do pipeline ETL.

Fornece:
- ``pipeline_etl`` — flow principal que coordena extract -> transform -> load
"""

import logging
from dataclasses import dataclass
from typing import cast

import pandas as pd
from prefect import flow, task

from src.config import settings
from src.db.connection import engine, get_session
from src.logger import LogLevel, setup_logger
from src.pipeline.extract import DataExtractor
from src.pipeline.load import DataLoader
from src.pipeline.transform import DataTransformer

# Configura o logger raiz (console + arquivo) antes de qualquer log
setup_logger(level=cast(LogLevel, settings.log_level), log_file=settings.log_file)

logger = logging.getLogger(__name__)
logger.info(
    "Config carregada | db=%s tickers=%s periodo=%s→%s batch=%d cache=%s log=%s",
    settings.database_url,
    settings.default_tickers,
    settings.start_date,
    settings.end_date,
    settings.batch_size,
    settings.cache_dir,
    settings.log_file,
)


@dataclass(frozen=True)
class PipelineResult:
    """Resumo consumível de sucesso e falha por ticker."""

    success_tickers: tuple[str, ...]
    failed_tickers: tuple[str, ...]
    errors: dict[str, str]

    @property
    def complete(self) -> bool:
        return not self.failed_tickers


def init_db() -> None:
    """Cria as tabelas no banco se não existirem."""
    from src.db.models import Base

    Base.metadata.create_all(engine)
    logger.debug("Tabelas verificadas/criadas no banco.")


@task(retries=2, retry_delay_seconds=10)
def extract_task(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Task Prefect: extrai dados via yfinance."""
    logger.info("Extract task: %s %s->%s", ticker, start, end)
    extractor = DataExtractor()
    df = extractor.download(ticker, start, end)
    logger.info("Extract OK: %s -> %d registros", ticker, len(df))
    return df


@task
def transform_task(df: pd.DataFrame) -> pd.DataFrame:
    """Task Prefect: limpa e calcula indicadores."""
    logger.info("Transform task: %d registros", len(df))
    transformer = DataTransformer()
    df_clean = transformer.clean(df)
    df_result = transformer.calculate_indicators(df_clean)
    logger.info("Transform OK: %d registros com %d indicadores", len(df_result), 8)
    return df_result


@task
def load_task(
    ticker: str,
    cotacoes_df: pd.DataFrame,
    indicadores_df: pd.DataFrame,
) -> None:
    """Task Prefect: carrega dados no PostgreSQL."""
    loader = DataLoader(get_session)
    logger.info("Load task: %s — upsert cotações + indicadores", ticker)

    cotacoes_cols = ["data", "abertura", "maxima", "minima", "fechamento", "volume"]
    indicadores_cols = [
        "data",
        "sma_50",
        "sma_200",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "rsi",
        "macd",
        "macd_sinal",
    ]

    cotacoes_to_insert = cast(
        pd.DataFrame,
        cotacoes_df[[c for c in cotacoes_cols if c in cotacoes_df.columns]],
    )
    indicadores_to_insert = cast(
        pd.DataFrame,
        indicadores_df[[c for c in indicadores_cols if c in indicadores_df.columns]],
    )

    loader.upsert_cotacoes(ticker, cotacoes_to_insert)
    loader.upsert_indicators(ticker, indicadores_to_insert)
    logger.info("Load OK: %s", ticker)


@flow(
    name="pipeline-etl",
    log_prints=True,
    description="Pipeline ETL: yfinance -> indicadores -> PostgreSQL",
)
def pipeline_etl(
    tickers: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> PipelineResult:
    """Flow Prefect principal do pipeline de dados.

    Args:
        tickers: Lista de tickers (ex: ["PETR4.SA"]). Default de settings.
        start: Data de início (YYYY-MM-DD). Default de settings.
        end: Data de fim (YYYY-MM-DD). Default de settings.
    """
    tickers = tickers if tickers is not None else settings.default_tickers
    start = start if start is not None else settings.start_date
    end = end if end is not None else settings.end_date

    logger.info("=" * 50)
    logger.info("Pipeline ETL iniciado: %d ticker(s), %s -> %s", len(tickers), start, end)
    logger.info("=" * 50)

    init_db()

    n_ok = 0
    n_fail = 0
    success_tickers: list[str] = []
    failed_tickers: list[str] = []
    errors: dict[str, str] = {}
    for i, ticker in enumerate(tickers, 1):
        logger.info("[%d/%d] Processando %s...", i, len(tickers), ticker)
        try:
            df = extract_task(ticker, start, end)
            df = transform_task(df)
            load_task(ticker, df, df)
            logger.info(
                "[%d/%d] %s concluído — %d registros", i, len(tickers), ticker, len(df)
            )
            n_ok += 1
            success_tickers.append(ticker)
        except Exception as exc:
            logger.exception("[%d/%d] %s FALHOU", i, len(tickers), ticker)
            n_fail += 1
            failed_tickers.append(ticker)
            errors[ticker] = f"{type(exc).__name__}: {exc}"

    logger.info("=" * 50)
    if n_fail:
        logger.warning(
            "Pipeline ETL finalizado com falhas. OK=%d  FALHA=%d", n_ok, n_fail
        )
    else:
        logger.info(
            "Pipeline ETL finalizado com sucesso. %d ticker(s) processados.", n_ok
        )
    logger.info("=" * 50)
    return PipelineResult(
        success_tickers=tuple(success_tickers),
        failed_tickers=tuple(failed_tickers),
        errors=errors,
    )


if __name__ == "__main__":
    pipeline_etl()
