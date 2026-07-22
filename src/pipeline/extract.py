"""Módulo de extração de dados financeiros.

Fornece:
- ``RetryPolicy`` — configuração de retentativas com backoff exponencial
- ``DataExtractor`` — download de dados via yfinance com cache CSV
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Configuração de retentativas para download de dados.

    Attributes:
        max_retries: Número máximo de tentativas.
        delay_seconds: Atraso inicial entre tentativas (segundos).
        backoff_factor: Fator multiplicativo do atraso a cada tentativa.
    """

    max_retries: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0


class DataExtractor:
    """Extrator de dados financeiros com cache local.

    Faz download de cotações históricas via yfinance e mantém
    um cache em CSV para evitar downloads repetidos.

    Usage::

        extractor = DataExtractor()
        df = extractor.download("PETR4.SA", "2023-01-01", "2023-12-31")
    """

    COLUMN_MAP = {
        "open": "abertura",
        "high": "maxima",
        "low": "minima",
        "close": "fechamento",
        "adj_close": "fechamento_ajustado",
        "volume": "volume",
    }

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        cache_dir: str = "data/raw",
    ):
        self.retry_policy = retry_policy or RetryPolicy()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── API pública ──────────────────────────────────────────────

    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Faz download dos dados históricos de *ticker* entre *start* e *end*.

        1. Verifica se existe cache local com cobertura suficiente.
        2. Se não, baixa via yfinance com política de retry.
        3. Normaliza os nomes das colunas.
        4. Salva em cache e retorna o DataFrame.

        Raises:
            ValueError: Se o download retornar dados vazios ou ticker inválido.
            RuntimeError: Se esgotar as tentativas de retry.
        """
        logger.info("download(ticker=%s, start=%s, end=%s)", ticker, start, end)
        cached = self._load_from_cache(ticker)
        if cached is not None:
            return cached

        df = self._download_with_retry(ticker, start, end)
        df = self._normalize_columns(df)
        self._save_to_cache(df, ticker)
        logger.info("Download concluído: %s → %d registros", ticker, len(df))
        return df

    # ── Cache ────────────────────────────────────────────────────

    def _cache_path(self, ticker: str) -> Path:
        return self.cache_dir / f"{ticker}.csv"

    def _load_from_cache(self, ticker: str) -> pd.DataFrame | None:
        path = self._cache_path(ticker)
        if not path.exists():
            logger.debug("Cache MISS: %s", path)
            return None
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if df.empty:
                logger.warning("Cache vazio: %s — ignorando", path)
                return None
            logger.info("Cache HIT: %s → %d registros", path, len(df))
            return df
        except Exception as exc:
            logger.warning("Cache corrompido: %s — %s", path, exc)
            return None

    def _save_to_cache(self, df: pd.DataFrame, ticker: str) -> None:
        path = self._cache_path(ticker)
        df.to_csv(path)
        logger.debug("Cache salvo: %s (%d registros)", path, len(df))

    # ── Download com retry ───────────────────────────────────────

    def _download_with_retry(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        last_exc: Exception | None = None
        delay = self.retry_policy.delay_seconds
        max_retries = self.retry_policy.max_retries

        for attempt in range(1, max_retries + 1):
            logger.info(
                "Download %s — tentativa %d/%d", ticker, attempt, max_retries
            )
            try:
                df = yf.download(ticker, start=start, end=end, progress=False)
                if df is None or df.empty:
                    raise ValueError(f"yfinance retornou dados vazios para {ticker}")
                logger.debug("Download %s OK (tentativa %d)", ticker, attempt)
                return df
            except Exception as e:
                last_exc = e
                logger.warning(
                    "Erro no download %s (tentativa %d/%d): %s",
                    ticker, attempt, max_retries, e,
                )
                if attempt < max_retries:
                    logger.debug("Aguardando %.1fs antes de retentar...", delay)
                    time.sleep(delay)
                    delay *= self.retry_policy.backoff_factor

        logger.error(
            "Download de %s falhou após %d tentativas. Último erro: %s",
            ticker, max_retries, last_exc,
        )
        raise RuntimeError(
            f"Download de {ticker} falhou após {max_retries} tentativas. "
            f"Último erro: {last_exc}"
        )

    # ── Normalização de colunas ──────────────────────────────────

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Renomeia colunas do yfinance (multi-index) para nomes padronizados."""
        before = list(df.columns)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        df = df.rename(columns=DataExtractor.COLUMN_MAP)

        # Garante que apenas as colunas mapeadas estejam presentes
        expected = set(DataExtractor.COLUMN_MAP.values())
        available = {c for c in df.columns if c in expected}
        result = df[sorted(available, key=list(DataExtractor.COLUMN_MAP.values()).index)]
        logger.debug("Colunas normalizadas: %s → %s", before, list(result.columns))
        return result
