"""Módulo de transformação e cálculo de indicadores técnicos.

Fornece:
- ``DataTransformer`` — limpeza de dados e cálculo de indicadores

A partir da Fase 2, os cálculos de indicadores delegam para as funções
puras em ``src/indicators/``.
"""

import logging
import math
from typing import cast

import numpy as np
import pandas as pd

from src.indicators.bollinger import bollinger_bands as _bollinger
from src.indicators.macd import macd as _macd
from src.indicators.rsi import rsi as _rsi
from src.indicators.sma import sma as _sma

logger = logging.getLogger(__name__)

OHLC_COLUMNS = ["abertura", "maxima", "minima", "fechamento"]
OHLCV_COLUMNS = [*OHLC_COLUMNS, "volume"]


class DataQualityError(ValueError):
    """Dados OHLCV não atendem ao contrato mínimo de qualidade."""


def _raise_for_rows(rule: str, invalid: pd.Series) -> None:
    """Falha com contagem e um índice de exemplo quando há linhas inválidas."""
    count = int(invalid.sum())
    if count:
        example = invalid.index[int(np.flatnonzero(invalid.to_numpy())[0])]
        raise DataQualityError(
            f"{rule}: {count} linha(s) afetada(s); exemplo de índice: {example}"
        )


def validate_ohlcv(df: pd.DataFrame) -> None:
    """Valida barras OHLCV normalizadas sem corrigir dados silenciosamente."""
    if not isinstance(df.index, pd.DatetimeIndex):
        raise DataQualityError(
            f"índice temporal inválido: esperado DatetimeIndex, recebido {type(df.index).__name__}"
        )
    if df.index.hasnans:
        raise DataQualityError(
            f"índice contém NaT: {int(df.index.isna().sum())} linha(s) afetada(s)"
        )
    if df.index.has_duplicates:
        duplicated = df.index.duplicated(keep=False)
        example = df.index[duplicated][0]
        raise DataQualityError(
            "índice contém datas duplicadas: "
            f"{int(duplicated.sum())} linha(s) afetada(s); exemplo de índice: {example}"
        )
    if not df.index.is_monotonic_increasing:
        positions = np.flatnonzero(df.index.asi8[1:] < df.index.asi8[:-1]) + 1
        raise DataQualityError(
            "índice fora de ordem crescente: "
            f"{len(positions)} linha(s) afetada(s); exemplo de índice: {df.index[positions[0]]}"
        )

    missing = [column for column in OHLCV_COLUMNS if column not in df.columns]
    if missing:
        raise DataQualityError(f"colunas OHLCV ausentes: {', '.join(missing)}")
    if df.columns.has_duplicates:
        raise DataQualityError("colunas OHLCV duplicadas")

    non_numeric = [
        column
        for column in OHLCV_COLUMNS
        if not pd.api.types.is_numeric_dtype(df[column])
        or pd.api.types.is_bool_dtype(df[column])
    ]
    if non_numeric:
        raise DataQualityError(
            f"colunas OHLCV não numéricas: {', '.join(non_numeric)}"
        )

    values = cast(pd.DataFrame, df[OHLCV_COLUMNS])
    missing_values = values.isna()
    if missing_values.to_numpy().any():
        invalid = pd.Series(
            missing_values.to_numpy().any(axis=1), index=df.index, dtype=bool
        )
        first_column = missing_values.columns[
            int(np.argwhere(missing_values.to_numpy())[0, 1])
        ]
        _raise_for_rows(f"OHLCV contém NaN em {first_column}", invalid)

    array = values.to_numpy(dtype=float)
    finite = pd.Series(
        np.isfinite(array).all(axis=1), index=df.index, dtype=bool
    )
    _raise_for_rows("OHLCV contém valor não finito", ~finite)

    _raise_for_rows(
        "OHLC deve ser estritamente positivo",
        pd.Series((array[:, :4] <= 0).any(axis=1), index=df.index, dtype=bool),
    )
    _raise_for_rows(
        "volume deve ser não negativo",
        pd.Series(array[:, 4] < 0, index=df.index, dtype=bool),
    )
    _raise_for_rows(
        "máxima inconsistente com abertura, fechamento ou mínima",
        pd.Series(
            (array[:, 1, None] < array[:, [0, 3, 2]]).any(axis=1),
            index=df.index,
            dtype=bool,
        ),
    )
    _raise_for_rows(
        "mínima inconsistente com abertura ou fechamento",
        pd.Series(
            (array[:, 2, None] > array[:, [0, 3]]).any(axis=1),
            index=df.index,
            dtype=bool,
        ),
    )


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
        """Valida OHLCV e preenche apenas ausências em colunas auxiliares.

        Args:
            df: DataFrame bruto com DatetimeIndex.

        Returns:
            DataFrame limpo e ordenado por data.
        """
        if df.empty:
            logger.debug("clean: DataFrame vazio — retornando vazio")
            return df
        validate_ohlcv(df)
        df = df.ffill()
        validate_ohlcv(df)
        logger.debug("clean: %d linhas validadas", len(df))
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
        close = cast(pd.Series, df["fechamento"])

        df = df.copy()
        df["sma_50"] = self._calc_sma(close, 50)
        df["sma_200"] = self._calc_sma(close, 200)
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = self._calc_bollinger(close)
        df["rsi"] = self._calc_rsi(close)
        macd_line, signal_line, _ = self._calc_macd(close)
        df["macd"] = macd_line
        df["macd_sinal"] = signal_line

        # Estatísticas resumidas
        sma_200_nan = int(cast(pd.Series, df["sma_200"]).isna().sum())
        if sma_200_nan > 0:
            pct = sma_200_nan / len(df) * 100
            logger.debug(
                "SMA_200: %.1f%% NaN (%d/%d) — dados insuficientes para janela de 200",
                pct,
                sma_200_nan,
                len(df),
            )
        rsi_values = cast(pd.Series, df["rsi"])
        if "rsi" in df.columns and bool(rsi_values.notna().any()):
            logger.debug(
                "RSI range: [%.1f, %.1f]",
                rsi_values.min(),
                rsi_values.max(),
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
            logger.debug(
                "Sanitize: %d valores NaN/Inf convertidos para None", n_sanitized
            )
        return result
