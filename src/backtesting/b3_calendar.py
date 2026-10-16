"""Calendário histórico de sessões do mercado à vista da B3."""

import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta


def _easter_sunday(year: int) -> date:
    """Calcula a Páscoa gregoriana sem dependência externa."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    correction = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * correction) // 451
    month = (h + correction - 7 * m + 114) // 31
    day = (h + correction - 7 * m + 114) % 31 + 1
    return date(year, month, day)


#: Versão das regras históricas. Muda sempre que uma regra ou exceção muda.
#: v2: auditoria contra as sessões oficiais do COTAHIST da B3, 2016-2026
#: (``docs/evidence/calendar/``).
B3_CALENDAR_VERSION = 2

#: Até 2021 a B3 fechava nos feriados de São Paulo: aniversário da cidade
#: (25/jan, municipal), Revolução Constitucionalista (9/jul, estadual) e
#: Consciência Negra (20/nov, municipal). A partir de 2022 passou a operar
#: neles e a fechar só em feriado nacional.
LAST_YEAR_CLOSED_ON_SAO_PAULO_HOLIDAYS = 2021

#: 20/nov vira feriado nacional (Lei 14.759/2023; B3 OC 207/2023-PRE).
FIRST_YEAR_NOVEMBER_20_NATIONAL = 2024

#: Exceções históricas documentadas, com motivo. Em 2020 São Paulo antecipou
#: os feriados de 9/jul e 20/nov para maio (contenção da COVID-19); a B3
#: operou nas datas originais, que deixaram de ser feriado naquele ano.
HISTORICAL_OPENINGS: dict[date, str] = {
    date(2020, 7, 9): "SP anticipated the 9 Jul holiday to 25 May 2020 (COVID-19)",
    date(2020, 11, 20): "SP anticipated the 20 Nov holiday to 21 May 2020 (COVID-19)",
}


def _last_weekday_of_year(year: int) -> date:
    """Último dia útil de segunda a sexta do ano; a B3 não tem pregão nele."""
    day = date(year, 12, 31)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


@dataclass(frozen=True)
class B3Calendar:
    """Sessões do mercado à vista da B3, com a história das regras.

    Regras por ano, não uma lista fixa: feriados nacionais, os feriados de São
    Paulo enquanto a B3 fechava neles (até 2021), 20/nov nacional desde 2024,
    véspera de Natal, último dia útil do ano e as exceções documentadas em
    :data:`HISTORICAL_OPENINGS`. A equivalência com as sessões oficiais do
    COTAHIST de 2016-01-04 a 2026-08-31 é verificada por teste.
    """

    extra_closures: frozenset[date] = field(default_factory=frozenset)
    extra_openings: frozenset[date] = field(default_factory=frozenset)

    def holidays(self, year: int) -> frozenset[date]:
        easter = _easter_sunday(year)
        fixed = {
            date(year, 1, 1),
            date(year, 4, 21),
            date(year, 5, 1),
            date(year, 9, 7),
            date(year, 10, 12),
            date(year, 11, 2),
            date(year, 11, 15),
            date(year, 12, 24),
            date(year, 12, 25),
            _last_weekday_of_year(year),
        }
        if year <= LAST_YEAR_CLOSED_ON_SAO_PAULO_HOLIDAYS:
            fixed |= {date(year, 1, 25), date(year, 7, 9), date(year, 11, 20)}
        if year >= FIRST_YEAR_NOVEMBER_20_NATIONAL:
            fixed.add(date(year, 11, 20))
        movable = {
            easter - timedelta(days=48),  # segunda de Carnaval
            easter - timedelta(days=47),  # terça de Carnaval
            easter - timedelta(days=2),  # Sexta-feira Santa
            easter + timedelta(days=60),  # Corpus Christi
        }
        openings = set(self.extra_openings) | set(HISTORICAL_OPENINGS)
        return frozenset((fixed | movable | set(self.extra_closures)) - openings)

    def is_session(self, value: date) -> bool:
        if value in self.extra_openings:
            return True
        return value.weekday() < 5 and value not in self.holidays(value.year)

    def sessions_digest(self, start: date, end: date) -> str:
        """SHA-256 das sessões do intervalo (datas ISO unidas por ``\\n``)."""
        listing = "\n".join(day.isoformat() for day in self.sessions_between(start, end))
        return hashlib.sha256(listing.encode("utf-8")).hexdigest()

    def next_session(self, value: date) -> date:
        candidate = value + timedelta(days=1)
        # ponytail: regras + exceções cobrem o uso diário; um feed oficial deve
        # substituir este laço se a B3 passar a publicar calendário por API.
        for _ in range(31):
            if self.is_session(candidate):
                return candidate
            candidate += timedelta(days=1)
        raise RuntimeError(f"no B3 session found after {value}")

    def sessions_between(self, start: date, end: date) -> tuple[date, ...]:
        """Lista sessões locais esperadas no intervalo inclusivo.

        Regras históricas v2, equivalentes às sessões oficiais do COTAHIST de
        2016-01-04 a 2026-08-31 (teste de equivalência). Fora desse intervalo
        valem as mesmas regras, sem verificação oficial. ``extra_closures`` e
        ``extra_openings`` fixam exceções adicionais.
        """
        if start > end:
            raise ValueError("start must be on or before end")
        return tuple(
            start + timedelta(days=offset)
            for offset in range((end - start).days + 1)
            if self.is_session(start + timedelta(days=offset))
        )

    def first_session_on_or_after(self, start: date, end: date) -> date | None:
        """Retorna a primeira sessão no intervalo, ou ``None`` se não houver."""
        sessions = self.sessions_between(start, end)
        return sessions[0] if sessions else None

    def last_session_on_or_before(self, start: date, end: date) -> date | None:
        """Retorna a última sessão no intervalo, ou ``None`` se não houver."""
        sessions = self.sessions_between(start, end)
        return sessions[-1] if sessions else None
