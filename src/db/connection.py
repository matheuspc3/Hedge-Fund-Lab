"""Conexão com o banco de dados PostgreSQL via SQLAlchemy.

Fornece:
- ``engine`` — motor SQLAlchemy compartilhado
- ``SessionLocal`` — fábrica de sessões
- ``get_session()`` — obtém uma nova sessão
- ``session_scope()`` — context manager que commita/rollback automaticamente
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("Engine SQLAlchemy criado: %s", settings.database_url)


def get_session() -> Session:
    """Retorna uma nova sessão SQLAlchemy."""
    session = SessionLocal()
    logger.debug("Nova sessão criada: id=%s", id(session))
    return session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager que fornece uma sessão com commit/rollback automáticos.

    Uso::

        with session_scope() as session:
            session.add(meu_obj)
            # commit automático no final
    """
    session = get_session()
    try:
        logger.debug("session_scope iniciada: id=%s", id(session))
        yield session
        session.commit()
        logger.debug("session_scope commit OK: id=%s", id(session))
    except BaseException:
        session.rollback()
        logger.error("session_scope rollback: id=%s", id(session), exc_info=True)
        raise
    finally:
        session.close()
        logger.debug("session_scope encerrada: id=%s", id(session))
