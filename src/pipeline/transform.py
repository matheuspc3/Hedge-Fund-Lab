"""Módulo de transformação e cálculo de indicadores técnicos.

Fornece:
- ``DataTransformer`` — limpeza de dados e cálculo de indicadores

A partir da Fase 2, os cálculos de indicadores delegam para as funções
puras em ``src/indicators/``.
"""

import logging
import math

import pandas as pd

from src.indicators.sma import sma as _sma
from src.indicators.bollinger import bollinger_bands as _bollinger
from src.indicators.rsi import rsi as _rsi
from src.indicators.macd import macd as _macd

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transformador de dados financeiros.

    Usage::

        transformer = DataTransformer()
        df_clean = transformer.clean(df_raw)
        df_with_indicators = transformer.calculate_indicators(df_clean)
    """

    # ── Limpeza ──────────────────────────────────────────────────

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """Limpeza básica: forward-fill NaN, remover linhas totalmente NaN, ordenar.

        Args:
            df: DataFrame bruto com DatetimeIndex.

        Returns:
            DataFrame limpo e ordenado por data.
        """
        if df.empty:
            logger.debug("clean: DataFrame vazio — retornando vazio")
            return df
        before = len(df)
        df = df.ffill().dropna(how="all")
        df = df.sort_index()
        dropped = before - len(df)
        if dropped:
            logger.debug("clean: %d → %d linhas (%d totalmente NaN removidas)", before, len(df), dropped)
        else:
            logger.debug("clean: %d linhas (sem alterações)", before)
        return df

    # ── Indicadores ──────────────────────────────────────────────
    #
    # Os cálculos delegam para as funções puras em src/indicators/.
    # Mantemos os métodos privados como atalhos para evitar import
    # direto no código cliente.

    @staticmethod
    def _calc_sma(series: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average (delega para src.indicators.sma)."""
        return _sma(series, window)

    @staticmethod
    def _calc_bollinger(
        series: pd.Series, window: int = 20, k: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands (delega para src.indicators.bollinger)."""
        return _bollinger(series, window, k)

    @staticmethod
    def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index (delega para src.indicators.rsi)."""
        return _rsi(series, period)

    @staticmethod
    def _calc_macd(
        series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (delega para src.indicators.macd)."""
        return _macd(series, fast, slow, signal)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula todos os indicadores técnicos e adiciona como colunas.

        Requer coluna ``fechamento``.

        Adiciona:
            sma_50, sma_200, bb_upper, bb_middle, bb_lower, rsi, macd, macd_sinal

        Args:
            df: DataFrame limpo (após clean()) com coluna 'fechamento'.

        Returns:
            DataFrame com colunas originais + indicadores.
        """
        if "fechamento" not in df.columns:
            logger.error(
                "calculate_indicators: coluna 'fechamento' ausente. Colunas: %s",
                list(df.columns),
            )
            raise KeyError("DataFrame must contain 'fechamento' column")

        logger.info("Calculando indicadores para %d registros", len(df))
        close = df["fechamento"]

        df = df.copy()
        df["sma_50"] = self._calc_sma(close, 50)
        df["sma_200"] = self._calc_sma(close, 200)
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = self._calc_bollinger(close)
        df["rsi"] = self._calc_rsi(close)
        macd_line, signal_line, _ = self._calc_macd(close)
        df["macd"] = macd_line
        df["macd_sinal"] = signal_line

        # Estatísticas resumidas
        sma_200_nan = df["sma_200"].isna().sum()
        if sma_200_nan > 0:
            pct = sma_200_nan / len(df) * 100
            logger.debug(
                "SMA_200: %.1f%% NaN (%d/%d) — dados insuficientes para janela de 200",
                pct, sma_200_nan, len(df),
            )
        if "rsi" in df.columns and df["rsi"].notna().any():
            logger.debug(
                "RSI range: [%.1f, %.1f]",
                df["rsi"].min(), df["rsi"].max(),
            )

        return df

    # ── Serialização ─────────────────────────────────────────────

    @staticmethod
    def sanitize_for_json(records: list[dict]) -> list[dict]:
        """Substitui NaN e Inf por None para serialização JSON segura.

        Uso::

            records = df.to_dict(orient="records")
            records = DataTransformer.sanitize_for_json(records)
            json.dump(records, f)  # safe
        """
        result: list[dict] = []
        n_sanitized = 0
        for record in records:
            sanitized = {}
            for k, v in record.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    sanitized[k] = None
                    n_sanitized += 1
                else:
                    sanitized[k] = v
            result.append(sanitized)
        if n_sanitized:
            logger.debug("Sanitize: %d valores NaN/Inf convertidos para None", n_sanitized)
        return result
