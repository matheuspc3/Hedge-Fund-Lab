"""Calendário B3 v2 contra as sessões oficiais do COTAHIST (2016-2026)."""

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from src.backtesting.b3_calendar import B3_CALENDAR_VERSION, B3Calendar

EVIDENCE = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "calendar"
OFFICIAL = EVIDENCE / "b3_official_sessions_2016-01-04_2026-08-31.txt"


def test_regras_reproduzem_exatamente_as_sessoes_oficiais_da_b3() -> None:
    official = OFFICIAL.read_text(encoding="utf-8").split()
    meta = json.loads((EVIDENCE / "b3_calendar_v2_sources.json").read_text(encoding="utf-8"))
    listing = "\n".join(official)
    assert hashlib.sha256(listing.encode()).hexdigest() == meta["sessions_sha256"]
    assert meta["calendar_version"] == B3_CALENDAR_VERSION == 2

    calendar = B3Calendar()
    rule = [day.isoformat() for day in calendar.sessions_between(date(2016, 1, 4), date(2026, 8, 31))]
    assert rule == official
    assert calendar.sessions_digest(date(2016, 1, 4), date(2026, 8, 31)) == meta["sessions_sha256"]


@pytest.mark.parametrize(
    ("day", "is_session", "why"),
    [
        (date(2019, 1, 25), False, "aniversário de SP fechava até 2021"),
        (date(2021, 7, 9), False, "9 de julho fechava até 2021"),
        (date(2018, 11, 20), False, "20/nov municipal fechava até 2021"),
        (date(2022, 1, 25), True, "a partir de 2022 a B3 opera em feriado de SP"),
        (date(2023, 1, 25), True, "25/01/2023 teve pregão"),
        (date(2024, 7, 9), True, "9 de julho aberto desde 2022"),
        (date(2023, 11, 20), True, "20/11/2023 teve pregão"),
        (date(2024, 11, 20), False, "20/nov nacional desde 2024"),
        (date(2025, 11, 20), False, "20/nov nacional desde 2024"),
        (date(2020, 7, 9), True, "2020: feriado antecipado para maio, B3 abriu"),
        (date(2020, 11, 20), True, "2020: feriado antecipado para maio, B3 abriu"),
        (date(2022, 12, 30), False, "último dia útil do ano"),
        (date(2023, 12, 29), False, "último dia útil do ano"),
        (date(2024, 12, 31), False, "último dia útil do ano"),
        (date(2017, 5, 29), True, "segunda comum; PETR4 negociou no COTAHIST"),
        (date(2023, 7, 9), False, "domingo"),
    ],
)
def test_casos_historicos_nomeados(day: date, is_session: bool, why: str) -> None:
    assert B3Calendar().is_session(day) is is_session, why
