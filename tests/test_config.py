"""Tests for dmzcal.config module."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from dmzcal.config import (
    DEFAULT_CONFIG_PATH,
    Config,
    get_birthdays_for_date,
    load_config,
)

VALID_YAML = """\
birthdays:
  - name: "Oma"
    month: 3
    day: 15
  - name: "Hans"
    month: 12
    day: 24
"""


def test_load_config_valid(tmp_path: Path) -> None:
    """Write a valid YAML to a tmp file, load it, verify birthdays are parsed correctly."""
    config_file = tmp_path / "birthdays.yaml"
    config_file.write_text(VALID_YAML, encoding="utf-8")

    config = load_config(config_file)

    assert len(config.birthdays) == 2
    assert config.birthdays[0]["name"] == "Oma"
    assert config.birthdays[0]["month"] == 3
    assert config.birthdays[0]["day"] == 15
    assert config.birthdays[1]["name"] == "Hans"
    assert config.birthdays[1]["month"] == 12
    assert config.birthdays[1]["day"] == 24


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Pass a non-existent path, verify it returns empty config (no exception)."""
    missing = tmp_path / "does_not_exist.yaml"

    config = load_config(missing)

    assert config.birthdays == []


def test_load_config_malformed_yaml(tmp_path: Path) -> None:
    """Write invalid YAML to a tmp file, verify it raises an exception."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("birthdays:\n  - name: [unterminated", encoding="utf-8")

    with pytest.raises((ValueError, yaml.YAMLError)):
        load_config(config_file)


def test_load_config_empty_file(tmp_path: Path) -> None:
    """Write an empty file, verify it returns empty config."""
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("", encoding="utf-8")

    config = load_config(config_file)

    assert config.birthdays == []


def test_load_config_no_birthdays_key(tmp_path: Path) -> None:
    """Write YAML without a birthdays key, verify it returns empty config."""
    config_file = tmp_path / "no_key.yaml"
    config_file.write_text("some_other_key:\n  - value: 1\n", encoding="utf-8")

    config = load_config(config_file)

    assert config.birthdays == []


def test_get_birthdays_for_date_match() -> None:
    """Create config with a birthday on March 15, query March 15, verify name returned."""
    config = Config(
        birthdays=[
            {"name": "Oma", "month": 3, "day": 15},
            {"name": "Hans", "month": 12, "day": 24},
        ]
    )

    result = get_birthdays_for_date(date(2025, 3, 15), config)

    assert result == ["Oma"]


def test_get_birthdays_for_date_no_match() -> None:
    """Query a date with no birthdays, verify empty list."""
    config = Config(
        birthdays=[
            {"name": "Oma", "month": 3, "day": 15},
        ]
    )

    result = get_birthdays_for_date(date(2025, 7, 1), config)

    assert result == []


def test_get_birthdays_for_date_multiple() -> None:
    """Create config with two birthdays on same date, verify both names returned."""
    config = Config(
        birthdays=[
            {"name": "Oma", "month": 3, "day": 15},
            {"name": "Opa", "month": 3, "day": 15},
            {"name": "Hans", "month": 12, "day": 24},
        ]
    )

    result = get_birthdays_for_date(date(2025, 3, 15), config)

    assert result == ["Oma", "Opa"]


def test_default_config_path() -> None:
    """Verify DEFAULT_CONFIG_PATH ends with the expected path components."""
    assert DEFAULT_CONFIG_PATH.parts[-3:] == (".config", "dmzcal", "birthdays.yaml")
    expected = Path.home() / ".config" / "dmzcal" / "birthdays.yaml"
    assert expected == DEFAULT_CONFIG_PATH


def test_load_config_top_level_not_mapping(tmp_path: Path) -> None:
    """Top-level YAML that is not a mapping should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a YAML mapping"):
        load_config(config_file)


def test_load_config_birthdays_not_list(tmp_path: Path) -> None:
    """birthdays key that is not a list should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("birthdays: 42\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected 'birthdays' to be a list"):
        load_config(config_file)


def test_load_config_entry_not_mapping(tmp_path: Path) -> None:
    """A birthday entry that is not a mapping should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("birthdays:\n  - just a string\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not a mapping"):
        load_config(config_file)


def test_load_config_entry_missing_keys(tmp_path: Path) -> None:
    """A birthday entry missing required keys should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("birthdays:\n  - name: Oma\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required keys"):
        load_config(config_file)


def test_load_config_entry_name_not_string(tmp_path: Path) -> None:
    """A birthday entry with a non-string name should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        "birthdays:\n  - name: 123\n    month: 3\n    day: 15\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="'name' must be a string"):
        load_config(config_file)


def test_load_config_entry_month_not_int(tmp_path: Path) -> None:
    """A birthday entry with a non-int month should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        'birthdays:\n  - name: Oma\n    month: "three"\n    day: 15\n', encoding="utf-8"
    )

    with pytest.raises(ValueError, match="'month' must be an int"):
        load_config(config_file)


def test_load_config_entry_day_not_int(tmp_path: Path) -> None:
    """A birthday entry with a non-int day should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        'birthdays:\n  - name: Oma\n    month: 3\n    day: "fifteen"\n', encoding="utf-8"
    )

    with pytest.raises(ValueError, match="'day' must be an int"):
        load_config(config_file)


def test_load_config_entry_month_out_of_range(tmp_path: Path) -> None:
    """A birthday entry with month outside 1-12 should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        "birthdays:\n  - name: Oma\n    month: 13\n    day: 15\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="month must be 1"):
        load_config(config_file)


def test_load_config_entry_day_out_of_range(tmp_path: Path) -> None:
    """A birthday entry with day outside 1-31 should raise ValueError."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        "birthdays:\n  - name: Oma\n    month: 3\n    day: 0\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="day must be 1"):
        load_config(config_file)


def test_load_config_entry_bool_month_rejected(tmp_path: Path) -> None:
    """A birthday entry with a boolean month should raise ValueError (bool is not int)."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        "birthdays:\n  - name: Oma\n    month: true\n    day: 15\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="'month' must be an int"):
        load_config(config_file)
