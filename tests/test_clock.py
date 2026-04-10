"""Tests for the dmzcal.clock module."""

from __future__ import annotations

from datetime import date, datetime

from dmzcal.clock import (
    WEEKDAY_NAMES_DE,
    format_date,
    format_special_line,
    format_time,
)


def test_weekday_names_length() -> None:
    assert len(WEEKDAY_NAMES_DE) == 7


def test_weekday_names_monday_first() -> None:
    assert WEEKDAY_NAMES_DE[0] == "Montag"
    assert WEEKDAY_NAMES_DE[6] == "Sonntag"


def test_weekday_names_mapping() -> None:
    d = date(2025, 7, 14)  # a Monday
    assert WEEKDAY_NAMES_DE[d.weekday()] == "Montag"


def test_format_date_no_leading_zeros() -> None:
    assert format_date(date(2026, 4, 7)) == "7.4.2026"


def test_format_date_double_digits() -> None:
    assert format_date(date(2026, 11, 25)) == "25.11.2026"


def test_format_date_single_day_and_month() -> None:
    assert format_date(date(2026, 3, 2)) == "2.3.2026"


def test_format_time_afternoon() -> None:
    assert format_time(datetime(2025, 1, 1, 14, 5)) == "14:05"


def test_format_time_morning() -> None:
    assert format_time(datetime(2025, 1, 1, 9, 30)) == "09:30"


def test_format_time_midnight() -> None:
    assert format_time(datetime(2025, 1, 1, 0, 0)) == "00:00"


def test_format_special_line_empty() -> None:
    assert format_special_line(None, []) == ""


def test_format_special_line_holiday_only() -> None:
    assert format_special_line("Karfreitag", []) == "Karfreitag"


def test_format_special_line_birthday_only() -> None:
    assert format_special_line(None, ["Oma"]) == "Geburtstag: Oma"


def test_format_special_line_multiple_birthdays() -> None:
    assert format_special_line(None, ["Oma", "Opa"]) == "Geburtstag: Oma, Opa"


def test_format_special_line_holiday_and_birthday() -> None:
    assert format_special_line("Karfreitag", ["Oma"]) == "Karfreitag - Geburtstag: Oma"


def test_format_special_line_holiday_and_multiple_birthdays() -> None:
    assert format_special_line("Neujahr", ["Oma", "Opa"]) == "Neujahr - Geburtstag: Oma, Opa"
