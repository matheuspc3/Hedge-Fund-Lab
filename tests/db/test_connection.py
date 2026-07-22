"""Testes para o módulo de conexão (src/db/connection.py)."""

from unittest.mock import MagicMock, patch

import pytest

from src.db.connection import get_session, session_scope


class TestGetSession:
    def test_get_session_returns_session(self):
        """get_session retorna uma sessão."""
        with patch("src.db.connection.SessionLocal") as mock_factory:
            mock_session = MagicMock()
            mock_factory.return_value = mock_session
            session = get_session()
            assert session == mock_session
            mock_factory.assert_called_once()


class TestSessionScope:
    def test_session_scope_commit_on_success(self):
        """Context manager faz commit."""
        with patch("src.db.connection.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            with session_scope() as session:
                session.add("test")

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_session_scope_rollback_on_error(self):
        """Context manager faz rollback em caso de erro."""
        with patch("src.db.connection.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(ValueError, match="test error"):
                with session_scope() as session:
                    session.add("test")
                    raise ValueError("test error")

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    def test_session_scope_rollback_on_base_exception(self):
        """BaseException também causa rollback."""
        with patch("src.db.connection.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(SystemExit):
                with session_scope() as session:
                    session.add("test")
                    raise SystemExit(1)

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
