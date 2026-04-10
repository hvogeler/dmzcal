from __future__ import annotations

from datetime import date, timedelta
from typing import Final

# Fixed NRW holidays: (month, day) -> German name
_FIXED_HOLIDAYS: Final[dict[tuple[int, int], str]] = {
    (1, 1): "Neujahr",
    (5, 1): "Tag der Arbeit",
    (10, 3): "Tag der Deutschen Einheit",
    (11, 1): "Allerheiligen",
    (12, 25): "1. Weihnachtstag",
    (12, 26): "2. Weihnachtstag",
}

# Easter-relative NRW holidays: offset in days from Easter Sunday -> German name
_EASTER_RELATIVE_HOLIDAYS: Final[dict[int, str]] = {
    -2: "Karfreitag",
    1: "Ostermontag",
    39: "Christi Himmelfahrt",
    50: "Pfingstmontag",
    60: "Fronleichnam",
}


def easter_sunday(year: int) -> date:
    """Return the date of Easter Sunday for the given year.

    Uses the Anonymous Gregorian algorithm (Meeus/Jones/Butcher).
    """
    a: int = year % 19
    b: int = year // 100
    c: int = year % 100
    d: int = b // 4
    e: int = b % 4
    f: int = (b + 8) // 25
    g: int = (b - f + 1) // 3
    h: int = (19 * a + b - d - g + 15) % 30
    i: int = c // 4
    k: int = c % 4
    l: int = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m: int = (a + 11 * h + 22 * l) // 451
    month: int = (h + l - 7 * m + 114) // 31
    day: int = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_nrw_holidays(year: int) -> dict[date, str]:
    """Return all NRW (Nordrhein-Westfalen) public holidays for the given year.

    Returns a dict mapping each holiday date to its German name.
    """
    holidays: dict[date, str] = {}

    # Fixed holidays
    for (month, day), name in _FIXED_HOLIDAYS.items():
        holidays[date(year, month, day)] = name

    # Easter-relative movable holidays
    easter: date = easter_sunday(year)
    for offset, name in _EASTER_RELATIVE_HOLIDAYS.items():
        holidays[easter + timedelta(days=offset)] = name

    return holidays


def get_holiday_for_date(d: date) -> str | None:
    """Return the German holiday name if the given date is an NRW public holiday, else None."""
    holidays: dict[date, str] = get_nrw_holidays(d.year)
    return holidays.get(d)
