"""Calendário mínimo de sessões do mercado à vista da B3."""

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


@dataclass(frozen=True)
class B3Calendar:
    """Resolve sessões de ações com regras recorrentes e exceções explícitas."""

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
            date(year, 11, 20),
            date(year, 12, 24),
            date(year, 12, 25),
            date(year, 12, 31),
        }
        movable = {
            easter - timedelta(days=48),  # segunda de Carnaval
            easter - timedelta(days=47),  # terça de Carnaval
            easter - timedelta(days=2),  # Sexta-feira Santa
            easter + timedelta(days=60),  # Corpus Christi
        }
        return frozenset(
            (fixed | movable | set(self.extra_closures)) - set(self.extra_openings)
        )

    def is_session(self, value: date) -> bool:
        if value in self.extra_openings:
            return True
        return value.weekday() < 5 and value not in self.holidays(value.year)

    def next_session(self, value: date) -> date:
        candidate = value + timedelta(days=1)
        # ponytail: regras + exceções cobrem o uso diário; um feed oficial deve
        # substituir este laço se a B3 passar a publicar calendário por API.
        for _ in range(31):
            if self.is_session(candidate):
                return candidate
            candidate += timedelta(days=1)
        raise RuntimeError(f"no B3 session found after {value}")
