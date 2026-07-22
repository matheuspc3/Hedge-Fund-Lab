"""Testes para os modelos ORM (src/db/models.py)."""

from datetime import date

import pytest
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Ativo, Base, CotacaoDiaria, IndicadorTecnico


@pytest.fixture(scope="module")
def engine():
    """Cria engine SQLite in-memory para testes dos modelos."""
    e = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def session(engine):
    """Sessão limpa para cada teste."""
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()
    yield sess
    sess.rollback()
    sess.close()


class TestAtivo:
    def test_create_ativo(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        assert ativo.id is not None
        assert ativo.ticker == "PETR4"
        assert ativo.setor == "Petróleo"
        assert ativo.created_at is not None

    def test_ticker_unique(self, session: Session):
        session.add(Ativo(ticker="WEGE3", setor="Máquinas"))
        session.flush()

        with pytest.raises(Exception):
            session.add(Ativo(ticker="WEGE3", setor="Duplicado"))
            session.flush()

    def test_ticker_indexed(self):
        col: Column = Ativo.__table__.columns["ticker"]
        assert col.unique
        assert not col.nullable
        assert any(i.unique for i in Ativo.__table__.indexes if "ticker" in i.columns)

    def test_created_at_default(self, session: Session):
        ativo = Ativo(ticker="TEST4", setor="Teste")
        session.add(ativo)
        session.flush()
        assert ativo.created_at is not None

    def test_repr(self):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        assert "PETR4" in repr(ativo)
        assert "Petróleo" in repr(ativo)


class TestCotacaoDiaria:
    def test_create_cotacao(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        cotacao = CotacaoDiaria(
            ativo_id=ativo.id,
            data=date(2024, 1, 2),
            abertura=100.0,
            maxima=101.0,
            minima=99.0,
            fechamento=100.5,
            volume=1_000_000,
        )
        session.add(cotacao)
        session.flush()

        assert cotacao.id is not None
        assert cotacao.abertura == 100.0
        assert cotacao.fechamento == 100.5

    def test_foreign_key(self):
        col: Column = CotacaoDiaria.__table__.columns["ativo_id"]
        assert col.foreign_keys

    def test_data_is_date_type(self):
        col: Column = CotacaoDiaria.__table__.columns["data"]
        assert isinstance(col.type, Date)

    def test_price_not_null(self):
        col: Column = CotacaoDiaria.__table__.columns["abertura"]
        assert not col.nullable

    def test_negative_price_raises(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        with pytest.raises(ValueError, match="must be >= 0"):
            CotacaoDiaria(
                ativo_id=ativo.id,
                data=date(2024, 1, 2),
                abertura=-100.0,
                maxima=101.0,
                minima=99.0,
                fechamento=100.5,
                volume=1_000_000,
            )

    def test_negative_volume_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            CotacaoDiaria(
                ativo_id=1,
                data=date(2024, 1, 2),
                abertura=100.0,
                maxima=101.0,
                minima=99.0,
                fechamento=100.5,
                volume=-1,
            )


class TestIndicadorTecnico:
    def test_create_indicador(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        ind = IndicadorTecnico(
            ativo_id=ativo.id,
            data=date(2024, 1, 2),
            sma_50=101.0,
            sma_200=100.0,
            bb_upper=105.0,
            bb_middle=101.0,
            bb_lower=97.0,
            rsi=55.0,
            macd=0.5,
            macd_sinal=0.3,
        )
        session.add(ind)
        session.flush()

        assert ind.id is not None
        assert ind.sma_50 == 101.0
        assert ind.rsi == 55.0

    def test_nullable_indicators(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        ind = IndicadorTecnico(ativo_id=ativo.id, data=date(2024, 1, 2))
        session.add(ind)
        session.flush()

        assert ind.sma_50 is None
        assert ind.sma_200 is None
        assert ind.rsi is None

    def test_data_is_date_type(self):
        col: Column = IndicadorTecnico.__table__.columns["data"]
        assert isinstance(col.type, Date)

    def test_foreign_key(self):
        col: Column = IndicadorTecnico.__table__.columns["ativo_id"]
        assert col.foreign_keys

    def test_repr(self):
        ind = IndicadorTecnico(ativo_id=1, data=date(2024, 1, 2))
        assert "IndicadorTecnico" in repr(ind)
        assert "2024-01-02" in repr(ind)


class TestRelationships:
    def test_ativo_cotacoes_relationship(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        for i in range(1, 4):
            session.add(
                CotacaoDiaria(
                    ativo_id=ativo.id,
                    data=date(2024, 1, i),
                    abertura=100.0,
                    maxima=101.0,
                    minima=99.0,
                    fechamento=100.5,
                    volume=1_000_000,
                )
            )
        session.flush()

        assert len(ativo.cotacoes) == 3

    def test_ativo_indicadores_relationship(self, session: Session):
        ativo = Ativo(ticker="PETR4", setor="Petróleo")
        session.add(ativo)
        session.flush()

        session.add(IndicadorTecnico(ativo_id=ativo.id, data=date(2024, 1, 2)))
        session.flush()

        assert len(ativo.indicadores) == 1
