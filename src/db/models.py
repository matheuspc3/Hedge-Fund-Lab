"""Modelos ORM para o Hedge-fund-lab.

TrÃªs tabelas principais:
- ``Ativo`` â€” ativos financeiros (PETR4, WEGE3, etc.)
Três tabelas principais:
- ``Ativo`` — ativos financeiros (PETR4, WEGE3, etc.)
- ``CotacaoDiaria`` — cotações OHLCV diárias
- ``IndicadorTecnico`` — indicadores técnicos calculados
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship, validates


class Base(DeclarativeBase):
    """Classe base declarativa no estilo SQLAlchemy 2.0."""


class Ativo(Base):
    """Ativo financeiro negociado em bolsa."""

    __tablename__ = "ativos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    setor = Column(String(100), nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    cotacoes = relationship(
        "CotacaoDiaria", back_populates="ativo", cascade="all, delete-orphan"
    )
    indicadores = relationship(
        "IndicadorTecnico", back_populates="ativo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ativo(ticker='{self.ticker}', setor='{self.setor}')>"


class CotacaoDiaria(Base):
    """Cotação diária OHLCV de um ativo."""

    __tablename__ = "cotacoes_diarias"
    __table_args__ = (UniqueConstraint("ativo_id", "data", name="uq_cotacao_ativo_data"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ativo_id = Column(
        Integer, ForeignKey("ativos.id", ondelete="CASCADE"), nullable=False
    )
    data = Column(Date, nullable=False, index=True)
    abertura = Column(Float, nullable=False)
    maxima = Column(Float, nullable=False)
    minima = Column(Float, nullable=False)
    fechamento = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    ativo = relationship("Ativo", back_populates="cotacoes")

    @validates("abertura", "maxima", "minima", "fechamento", "volume")
    def _validate_positive(self, key: str, value: float) -> float:
        if value is not None and value < 0:
            raise ValueError(f"{key} must be >= 0, got {value}")
        return value

    def __repr__(self) -> str:
        return f"<CotacaoDiaria(ativo_id={self.ativo_id}, data={self.data}, fechamento={self.fechamento})>"


class IndicadorTecnico(Base):
    """Indicadores tÃ©cnicos calculados para um ativo em uma data."""

    __tablename__ = "indicadores_tecnicos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ativo_id = Column(
        Integer, ForeignKey("ativos.id", ondelete="CASCADE"), nullable=False
    )
    data = Column(Date, nullable=False, index=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_sinal = Column(Float, nullable=True)

    ativo = relationship("Ativo", back_populates="indicadores")

    def __repr__(self) -> str:
        return f"<IndicadorTecnico(ativo_id={self.ativo_id}, data={self.data})>"
