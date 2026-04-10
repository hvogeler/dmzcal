"""Tests for the dmzcal.holidays module."""

from __future__ import annotations

from datetime import date

from dmzcal.holidays import easter_sunday, get_holiday_for_date, get_nrw_holidays


def test_easter_sunday_2025() -> None:
    assert easter_sunday(2025) == date(2025, 4, 20)


def test_easter_sunday_2026() -> None:
    assert easter_sunday(2026) == date(2026, 4, 5)


def test_easter_sunday_2024() -> None:
    assert easter_sunday(2024) == date(2024, 3, 31)


def test_get_nrw_holidays_count() -> None:
    for year in (2024, 2025, 2026):
        holidays = get_nrw_holidays(year)
        assert len(holidays) == 11, f"Expected 11 holidays for {year}, got {len(holidays)}"


def test_fixed_holidays_2025() -> None:
    holidays = get_nrw_holidays(2025)
    expected: dict[date, str] = {
        date(2025, 1, 1): "Neujahr",
        date(2025, 5, 1): "Tag der Arbeit",
        date(2025, 10, 3): "Tag der Deutschen Einheit",
        date(2025, 11, 1): "Allerheiligen",
        date(2025, 12, 25): "1. Weihnachtstag",
        date(2025, 12, 26): "2. Weihnachtstag",
    }
    for d, name in expected.items():
        assert d in holidays, f"{name} ({d}) not found in holidays"
        assert holidays[d] == name


def test_movable_holidays_2025() -> None:
    holidays = get_nrw_holidays(2025)
    expected: dict[date, str] = {
        date(2025, 4, 18): "Karfreitag",
        date(2025, 4, 21): "Ostermontag",
        date(2025, 5, 29): "Christi Himmelfahrt",
        date(2025, 6, 9): "Pfingstmontag",
        date(2025, 6, 19): "Fronleichnam",
    }
    for d, name in expected.items():
        assert d in holidays, f"{name} ({d}) not found in holidays"
        assert holidays[d] == name


def test_get_holiday_for_date_hit() -> None:
    result = get_holiday_for_date(date(2025, 12, 25))
    assert result == "1. Weihnachtstag"


def test_get_holiday_for_date_miss() -> None:
    result = get_holiday_for_date(date(2025, 7, 15))
    assert result is None


def test_movable_holidays_2026() -> None:
    holidays = get_nrw_holidays(2026)
    expected: dict[date, str] = {
        date(2026, 4, 3): "Karfreitag",
        date(2026, 4, 6): "Ostermontag",
        date(2026, 5, 14): "Christi Himmelfahrt",
        date(2026, 5, 25): "Pfingstmontag",
        date(2026, 6, 4): "Fronleichnam",
    }
    for d, name in expected.items():
        assert d in holidays, f"{name} ({d}) not found in holidays"
        assert holidays[d] == name
