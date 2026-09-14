"""Módulo de carga de dados no PostgreSQL.

Fornece:
- ``DataLoader`` — inserção em batch de cotações e indicadores
"""

import logging
from collections.abc import Callable

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.config import settings
from src.db.models import Ativo, CotacaoDiaria, IndicadorTecnico

logger = logging.getLogger(__name__)


class DataLoader:
    """Carregador de dados financeiros no banco PostgreSQL.

    Faz inserção em batch com suporte a upsert e rollback automático.

    Usage::

        loader = DataLoader(get_session)
        loader.batch_insert("PETR4.SA", cotacoes_df)
        loader.batch_insert_indicators("PETR4.SA", indicadores_df)
    """

    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    # ── Cotações ─────────────────────────────────────────────────────────

    def batch_insert(self, ticker: str, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Insere cotações diárias em batches.

        Args:
            ticker: Ticker do ativo (ex: PETR4.SA).
            df: DataFrame com colunas data, abertura, maxima, minima, fechamento, volume.
            batch_size: Número de registros por batch.

        Returns:
            Número total de registros inseridos.
        """
        logger.info(
            "batch_insert: %s — %d registros (batch_size=%d)", ticker, len(df), batch_size
        )
        session = self.session_factory()
        try:
            ativo_id = self._get_or_create_ativo(session, ticker)
            rows = self._df_to_cotacao_rows(df, ativo_id)
            total = self._insert_batches(session, rows, CotacaoDiaria, batch_size)
            session.commit()
            logger.info("batch_insert OK: %s → %d cotações inseridas", ticker, total)
            return total
        except BaseException:
            session.rollback()
            logger.exception("batch_insert ROLLBACK: %s", ticker)
            raise
        finally:
            session.close()
            logger.debug("batch_insert: sessão encerrada — %s", ticker)

    def upsert_cotacoes(
        self, ticker: str, df: pd.DataFrame, batch_size: int = 1000
    ) -> int:
        """Insere cotações com upsert (evita duplicatas por (ativo_id, data)).

        Registros existentes são atualizados pela chave ``(ativo_id, data)``.
        """
        is_sqlite = settings.database_url.startswith("sqlite")

        logger.info(
            "upsert_cotacoes: %s — %d registros (batch_size=%d)",
            ticker,
            len(df),
            batch_size,
        )
        session = self.session_factory()
        try:
            ativo_id = self._get_or_create_ativo(session, ticker)
            rows = self._df_to_cotacao_rows(df, ativo_id)
            total = self._upsert_batches(
                session,
                rows,
                CotacaoDiaria,
                ["abertura", "maxima", "minima", "fechamento", "volume"],
                batch_size,
                is_sqlite,
            )

            session.commit()
            logger.info("upsert_cotacoes OK: %s → %d cotações", ticker, total)
            return total
        except BaseException:
            session.rollback()
            logger.exception("upsert_cotacoes ROLLBACK: %s", ticker)
            raise
        finally:
            session.close()
            logger.debug("upsert_cotacoes: sessão encerrada — %s", ticker)

    # ── Indicadores ──────────────────────────────────────────────────────

    def upsert_indicators(
        self, ticker: str, df: pd.DataFrame, batch_size: int = 1000
    ) -> int:
        """Insere ou atualiza indicadores por ``(ativo_id, data)``.

        Args:
            ticker: Ticker do ativo.
            df: DataFrame com colunas: data, sma_50, sma_200, bb_upper,
                bb_middle, bb_lower, rsi, macd, macd_sinal.
            batch_size: Número de registros por batch.

        Returns:
            Número total de registros inseridos.
        """
        is_sqlite = settings.database_url.startswith("sqlite")
        logger.info("upsert_indicators: %s — %d registros", ticker, len(df))
        session = self.session_factory()
        try:
            ativo_id = self._get_or_create_ativo(session, ticker)
            rows = self._df_to_indicador_rows(df, ativo_id)
            total = self._upsert_batches(
                session,
                rows,
                IndicadorTecnico,
                [
                    "sma_50",
                    "sma_200",
                    "bb_upper",
                    "bb_middle",
                    "bb_lower",
                    "rsi",
                    "macd",
                    "macd_sinal",
                ],
                batch_size,
                is_sqlite,
            )
            session.commit()
            logger.info("upsert_indicators OK: %s → %d indicadores", ticker, total)
            return total
        except BaseException:
            session.rollback()
            logger.exception("upsert_indicators ROLLBACK: %s", ticker)
            raise
        finally:
            session.close()
            logger.debug("upsert_indicators: sessão encerrada — %s", ticker)

    def upsert_indicadores(
        self, ticker: str, df: pd.DataFrame, batch_size: int = 1000
    ) -> int:
        """Insere indicadores técnicos com upsert (ON CONFLICT DO NOTHING)."""
        is_sqlite = settings.database_url.startswith("sqlite")
        logger.info(
            "upsert_indicadores: %s — %d registros (batch_size=%d)",
            ticker,
            len(df),
            batch_size,
        )
        session = self.session_factory()
        try:
            ativo_id = self._get_or_create_ativo(session, ticker)
            rows = self._df_to_indicador_rows(df, ativo_id)
            total = 0

            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                if is_sqlite:
                    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                    stmt = sqlite_insert(IndicadorTecnico).values(batch)
                    stmt = stmt.on_conflict_do_nothing()
                else:
                    from sqlalchemy.dialects.postgresql import insert as pg_insert

                    stmt = pg_insert(IndicadorTecnico).values(batch)
                    stmt = stmt.on_conflict_do_nothing()
                session.execute(stmt)
                total += len(batch)

            session.commit()
            logger.info("upsert_indicadores OK: %s → %d indicadores", ticker, total)
            return total
        except BaseException:
            session.rollback()
            logger.exception("upsert_indicadores ROLLBACK: %s", ticker)
            raise
        finally:
            session.close()
            logger.debug("upsert_indicadores: sessão encerrada — %s", ticker)

    # ── Métodos auxiliares ───────────────────────────────────────────────

    @staticmethod
    def _get_or_create_ativo(session: Session, ticker: str) -> int:
        """Busca ou cria um Ativo. Retorna o id."""
        ativo = session.query(Ativo).filter_by(ticker=ticker).first()
        if ativo is None:
            ativo = Ativo(ticker=ticker, setor="N/A")
            session.add(ativo)
            session.flush()
            logger.info("Ativo criado: %s (id=%d)", ticker, ativo.id)
        else:
            logger.debug("Ativo encontrado: %s (id=%d)", ticker, ativo.id)
        return ativo.id  # type: ignore[return-value]

    @staticmethod
    def _df_to_cotacao_rows(df: pd.DataFrame, ativo_id: int) -> list[dict]:
        """Converte DataFrame de cotações para lista de dicts."""
        df = df.copy()
        if "data" not in df.columns:
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: "data"})

        rows: list[dict] = []
        for _, row in df.iterrows():
            data_val = row["data"]
            if isinstance(data_val, pd.Timestamp):
                data_val = data_val.date()
            rows.append(
                {
                    "ativo_id": ativo_id,
                    "data": data_val,
                    "abertura": float(row["abertura"]),
                    "maxima": float(row["maxima"]),
                    "minima": float(row["minima"]),
                    "fechamento": float(row["fechamento"]),
                    "volume": float(row["volume"]),
                }
            )
        return rows

    @staticmethod
    def _df_to_indicador_rows(df: pd.DataFrame, ativo_id: int) -> list[dict]:
        """Converte DataFrame de indicadores para lista de dicts, tratando NaN."""
        df = df.copy()
        if "data" not in df.columns:
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: "data"})

        indicator_cols = [
            "sma_50",
            "sma_200",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "rsi",
            "macd",
            "macd_sinal",
        ]

        rows: list[dict] = []
        for _, row in df.iterrows():
            data_val = row["data"]
            if isinstance(data_val, pd.Timestamp):
                data_val = data_val.date()

            record: dict = {"ativo_id": ativo_id, "data": data_val}
            for col in indicator_cols:
                val = row.get(col)
                if val is not None and (
                    isinstance(val, float) and (np.isnan(val) or np.isinf(val))
                ):
                    record[col] = None
                else:
                    record[col] = None if val is None else float(val)

            rows.append(record)
        return rows

    @staticmethod
    def _insert_batches(
        session: Session,
        rows: list[dict],
        model_class: type,
        batch_size: int,
    ) -> int:
        """Insere linhas em batches e retorna o total."""
        total = 0
        n_batches = (len(rows) - 1) // batch_size + 1 if rows else 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            session.bulk_insert_mappings(model_class, batch)
            total += len(batch)
            logger.debug(
                "Insert batch %d/%d: %d registros em %s",
                i // batch_size + 1,
                n_batches,
                len(batch),
                model_class.__name__,
            )
        return total

    @staticmethod
    def _upsert_batches(
        session: Session,
        rows: list[dict],
        model_class: type,
        update_columns: list[str],
        batch_size: int,
        is_sqlite: bool,
    ) -> int:
        """Executa upsert portável entre SQLite e PostgreSQL."""
        if is_sqlite:
            from sqlalchemy.dialects.sqlite import insert
        else:
            from sqlalchemy.dialects.postgresql import insert

        total = 0
        for i in range(0, len(rows), batch_size):
            stmt = insert(model_class).values(rows[i : i + batch_size])
            stmt = stmt.on_conflict_do_update(
                index_elements=["ativo_id", "data"],
                set_={
                    column: getattr(stmt.excluded, column) for column in update_columns
                },
            )
            session.execute(stmt)
            total += len(rows[i : i + batch_size])
        return total
