from datetime import date

import pytest

from src.backtesting.b3_calendar import B3Calendar


def test_sessions_between_uses_inclusive_eligible_bounds():
    calendar = B3Calendar()

    assert calendar.sessions_between(date(2020, 1, 4), date(2020, 1, 12)) == (
        date(2020, 1, 6),
        date(2020, 1, 7),
        date(2020, 1, 8),
        date(2020, 1, 9),
        date(2020, 1, 10),
    )
    assert calendar.first_session_on_or_after(
        date(2020, 1, 4), date(2020, 1, 12)
    ) == date(2020, 1, 6)
    assert calendar.last_session_on_or_before(
        date(2020, 1, 4), date(2020, 1, 12)
    ) == date(2020, 1, 10)


def test_sessions_between_treats_empty_interval_explicitly():
    calendar = B3Calendar()

    assert calendar.sessions_between(date(2026, 12, 24), date(2026, 12, 25)) == ()
    assert (
        calendar.first_session_on_or_after(date(2026, 12, 24), date(2026, 12, 25)) is None
    )
    assert (
        calendar.last_session_on_or_before(date(2026, 12, 24), date(2026, 12, 25)) is None
    )


def test_sessions_between_rejects_inverted_interval():
    with pytest.raises(ValueError, match="start must be on or before end"):
        B3Calendar().sessions_between(date(2024, 1, 2), date(2024, 1, 1))
