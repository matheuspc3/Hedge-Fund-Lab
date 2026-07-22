"""Testes para o módulo de carga (src/pipeline/load.py)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.db.models import Ativo
from src.pipeline.load import DataLoader


class TestDataLoader:
    def test_batch_insert_cotacoes(self, mock_session_factory, sample_cotacoes_df):
        """batch_insert adiciona objetos ao session.add_all."""
        mock_session = mock_session_factory()

        # Mock _get_or_create_ativo para retornar ID conhecido
        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            count = loader.batch_insert("PETR4.SA", sample_cotacoes_df, batch_size=10)

        assert count == 10
        assert mock_session.bulk_insert_mappings.called
        assert mock_session.commit.called

    def test_batch_insert_batch_size(self, mock_session_factory):
        """DataFrame com 25 registros, batch_size=10 → 3 chamadas."""
        mock_session = mock_session_factory()
        dates = pd.date_range("2024-01-01", periods=25, freq="D")
        df = pd.DataFrame(
            {
                "data": [d.date() for d in dates],
                "abertura": [100.0] * 25,
                "maxima": [101.0] * 25,
                "minima": [99.0] * 25,
                "fechamento": [100.5] * 25,
                "volume": [1_000_000] * 25,
            }
        )

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            count = loader.batch_insert("PETR4.SA", df, batch_size=10)

        assert count == 25
        assert mock_session.bulk_insert_mappings.call_count == 3
        assert mock_session.commit.called

    def test_empty_dataframe(self, mock_session_factory):
        """DataFrame vazio → sem chamadas a add_all."""
        mock_session = mock_session_factory()
        df = pd.DataFrame(
            columns=["data", "abertura", "maxima", "minima", "fechamento", "volume"]
        )

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            count = loader.batch_insert("PETR4.SA", df)

        assert count == 0
        assert mock_session.bulk_insert_mappings.call_count == 0

    def test_rollback_on_failure(self, mock_session_factory, sample_cotacoes_df):
        """Falha no insert → rollback chamado."""
        mock_session = mock_session_factory()
        mock_session.commit.side_effect = Exception("erro no commit")

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            with pytest.raises(Exception, match="erro no commit"):
                loader.batch_insert("PETR4.SA", sample_cotacoes_df)

        assert mock_session.rollback.called
        assert mock_session.close.called

    def test_upsert_cotacoes(self, mock_session_factory, sample_cotacoes_df):
        """upsert_cotacoes chama execute com stmt de upsert."""
        mock_session = mock_session_factory()

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            count = loader.upsert_cotacoes("PETR4.SA", sample_cotacoes_df, batch_size=10)

        assert count == 10
        assert mock_session.execute.called
        assert mock_session.commit.called

    def test_batch_insert_indicators(self, mock_session_factory, sample_indicadores_df):
        """batch_insert_indicators adiciona objetos."""
        mock_session = mock_session_factory()

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            count = loader.batch_insert_indicators(
                "PETR4.SA", sample_indicadores_df, batch_size=10
            )

        assert count == 10
        assert mock_session.bulk_insert_mappings.called
        assert mock_session.commit.called

    def test_get_or_create_ativo_exists(self, mock_session_factory):
        """Se Ativo já existe, retorna seu ID."""
        mock_session = mock_session_factory()
        existing = MagicMock(spec=Ativo)
        existing.id = 42
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            existing
        )

        loader = DataLoader(mock_session_factory)
        ativo_id = loader._get_or_create_ativo(mock_session, "PETR4.SA")

        assert ativo_id == 42
        mock_session.add.assert_not_called()

    def test_get_or_create_ativo_creates(self, mock_session_factory):
        """Se Ativo não existe, cria e retorna ID."""
        mock_session = mock_session_factory()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Simula o flush atribuindo um ID
        def fake_flush():
            mock_session.add.call_args[0][0].id = 99

        mock_session.flush.side_effect = fake_flush

        loader = DataLoader(mock_session_factory)
        ativo_id = loader._get_or_create_ativo(mock_session, "NOVO4.SA")

        assert ativo_id == 99
        mock_session.add.assert_called_once()

    def test_upsert_rollback_on_failure(self, mock_session_factory, sample_cotacoes_df):
        """Falha no upsert → rollback chamado."""
        mock_session = mock_session_factory()
        mock_session.execute.side_effect = Exception("erro no execute")

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            with pytest.raises(Exception, match="erro no execute"):
                loader.upsert_cotacoes("PETR4.SA", sample_cotacoes_df)

        assert mock_session.rollback.called
        assert mock_session.close.called

    def test_batch_insert_indicators_rollback(
        self, mock_session_factory, sample_indicadores_df
    ):
        """Falha no insert de indicadores → rollback chamado."""
        mock_session = mock_session_factory()
        mock_session.commit.side_effect = Exception("erro no commit")

        with patch.object(DataLoader, "_get_or_create_ativo", return_value=1):
            loader = DataLoader(mock_session_factory)
            with pytest.raises(Exception, match="erro no commit"):
                loader.batch_insert_indicators("PETR4.SA", sample_indicadores_df)

        assert mock_session.rollback.called
        assert mock_session.close.called

    def test_df_to_cotacao_rows_with_index(self):
        """DataFrame com data como índice é convertido corretamente."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "abertura": [100.0, 101.0, 102.0],
                "maxima": [101.0, 102.0, 103.0],
                "minima": [99.0, 100.0, 101.0],
                "fechamento": [100.5, 101.5, 102.5],
                "volume": [1_000_000] * 3,
            },
            index=dates,
        )
        df.index.name = "data"

        loader = DataLoader(lambda: None)
        rows = loader._df_to_cotacao_rows(df, ativo_id=1)

        assert len(rows) == 3
        assert rows[0]["ativo_id"] == 1
        assert "data" in rows[0]

    def test_df_to_indicador_rows_nan_inf(self):
        """NaN/Inf em indicadores → None na saída."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        df = pd.DataFrame(
            {
                "data": [d.date() for d in dates],
                "sma_50": [100.0, float("nan")],
                "sma_200": [float("inf"), None],
                "bb_upper": [102.0, 103.0],
                "bb_middle": [100.0, 101.0],
                "bb_lower": [98.0, 99.0],
                "rsi": [55.0, 56.0],
                "macd": [0.5, 0.6],
                "macd_sinal": [0.3, 0.4],
            }
        )

        loader = DataLoader(lambda: None)
        rows = loader._df_to_indicador_rows(df, ativo_id=1)

        assert rows[0]["sma_50"] == 100.0
        assert rows[1]["sma_50"] is None  # NaN → None
        assert rows[0]["sma_200"] is None  # inf → None
        assert rows[1]["sma_200"] is None  # None stays None
