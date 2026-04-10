"""Birthday configuration loader.

Reads a YAML file containing birthday entries and provides helpers
for querying birthdays by date.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Final, TypedDict

import yaml

logger: Final = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH: Final[Path] = Path.home() / ".config" / "dmzcal" / "birthdays.yaml"


class BirthdayEntry(TypedDict):
    """A single birthday record."""

    name: str
    month: int
    day: int


@dataclass
class Config:
    """Application configuration holding a list of birthday entries."""

    birthdays: list[BirthdayEntry] = field(default_factory=list)


def load_config(path: Path) -> Config:
    """Load and validate a birthday YAML configuration file.

    If *path* does not exist an empty :class:`Config` is returned and a
    warning is logged.  Malformed YAML (including unexpected types) will
    raise an exception.

    Parameters
    ----------
    path:
        Filesystem path to the YAML configuration file.

    Returns
    -------
    Config
        The parsed configuration.

    Raises
    ------
    yaml.YAMLError
        If the file contains invalid YAML.
    ValueError
        If the parsed structure does not match the expected schema.
    """
    if not path.exists():
        logger.warning("Config file not found: %s — using empty config", path)
        return Config()

    raw_text = path.read_text(encoding="utf-8")
    data: object = yaml.safe_load(raw_text)

    # An empty file yields None from safe_load.
    if data is None:
        return Config()

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping at top level, got {type(data).__name__}")

    raw_birthdays: object = data.get("birthdays")

    if raw_birthdays is None:
        return Config()

    if not isinstance(raw_birthdays, list):
        raise ValueError(f"Expected 'birthdays' to be a list, got {type(raw_birthdays).__name__}")

    birthdays: list[BirthdayEntry] = []
    for idx, entry in enumerate(raw_birthdays):
        if not isinstance(entry, dict):
            raise ValueError(f"Birthday entry {idx} is not a mapping: {entry!r}")

        missing = [k for k in ("name", "month", "day") if k not in entry]
        if missing:
            raise ValueError(f"Birthday entry {idx} is missing required keys: {missing}")

        name: object = entry["name"]
        month: object = entry["month"]
        day: object = entry["day"]

        if not isinstance(name, str):
            raise ValueError(
                f"Birthday entry {idx}: 'name' must be a string, got {type(name).__name__}"
            )
        if not isinstance(month, int) or isinstance(month, bool):
            raise ValueError(
                f"Birthday entry {idx}: 'month' must be an int, got {type(month).__name__}"
            )
        if not isinstance(day, int) or isinstance(day, bool):
            raise ValueError(
                f"Birthday entry {idx}: 'day' must be an int, got {type(day).__name__}"
            )

        if not (1 <= month <= 12):
            raise ValueError(f"Birthday entry {idx}: month must be 1–12, got {month}")
        if not (1 <= day <= 31):
            raise ValueError(f"Birthday entry {idx}: day must be 1–31, got {day}")

        birthdays.append(BirthdayEntry(name=name, month=month, day=day))

    return Config(birthdays=birthdays)


def get_birthdays_for_date(d: date, config: Config) -> list[str]:
    """Return names whose birthday matches the month and day of *d*.

    Parameters
    ----------
    d:
        The date to check against.
    config:
        The loaded birthday configuration.

    Returns
    -------
    list[str]
        Names with a matching birthday (may be empty).
    """
    return [
        entry["name"]
        for entry in config.birthdays
        if entry["month"] == d.month and entry["day"] == d.day
    ]
