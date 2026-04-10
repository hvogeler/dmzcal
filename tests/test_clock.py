"""Tests for the dmzcal.clock module."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime

import pytest

from dmzcal.clock import (
    _CORNER_SIZE,
    _EXIT_TAP_TIMEOUT_MS,
    WEEKDAY_NAMES_DE,
    CalendarDisplay,
    Corner,
    ExitTapState,
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


# ---------------------------------------------------------------------------
# Exit tap state machine tests
# ---------------------------------------------------------------------------


def _get_state(display: CalendarDisplay) -> ExitTapState:
    """Read the exit tap state without mypy narrowing the result to a Literal."""
    state: ExitTapState = display._exit_tap_state
    return state


# We test the state machine logic by calling _classify_corner and
# _advance_exit_state directly on a CalendarDisplay instance.  To avoid
# needing a real Tk mainloop we use a minimal Tk root that is destroyed
# at the end of each test.

_SCREEN_W: int = 800
_SCREEN_H: int = 480


@pytest.fixture()
def display() -> Iterator[CalendarDisplay]:
    """Create a CalendarDisplay in windowed mode for testing."""
    import tkinter as tk

    from dmzcal.config import Config

    root = tk.Tk()
    config = Config(birthdays=[])
    d = CalendarDisplay(root=root, config=config, fullscreen=False)
    # Force the window to a known size so winfo_width/height return correct
    # values inside _classify_corner.  We must call update() (not just
    # update_idletasks) so the geometry manager actually resizes the window.
    root.geometry(f"{_SCREEN_W}x{_SCREEN_H}")
    root.update()
    yield d
    try:
        root.destroy()
    except Exception:
        pass


# -- Corner classification --------------------------------------------------


class TestClassifyCorner:
    """Tests for CalendarDisplay._classify_corner."""

    def test_top_left(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(0, 0) == Corner.TOP_LEFT
        assert display._classify_corner(_CORNER_SIZE - 1, _CORNER_SIZE - 1) == Corner.TOP_LEFT

    def test_top_right(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(_SCREEN_W - 1, 0) == Corner.TOP_RIGHT
        assert (
            display._classify_corner(_SCREEN_W - _CORNER_SIZE, _CORNER_SIZE - 1) == Corner.TOP_RIGHT
        )

    def test_bottom_right(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(_SCREEN_W - 1, _SCREEN_H - 1) == Corner.BOTTOM_RIGHT
        assert (
            display._classify_corner(_SCREEN_W - _CORNER_SIZE, _SCREEN_H - _CORNER_SIZE)
            == Corner.BOTTOM_RIGHT
        )

    def test_bottom_left(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(0, _SCREEN_H - 1) == Corner.BOTTOM_LEFT
        assert (
            display._classify_corner(_CORNER_SIZE - 1, _SCREEN_H - _CORNER_SIZE)
            == Corner.BOTTOM_LEFT
        )

    def test_center_is_none(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(_SCREEN_W // 2, _SCREEN_H // 2) == Corner.NONE

    def test_top_edge_center_is_none(self, display: CalendarDisplay) -> None:
        assert display._classify_corner(_SCREEN_W // 2, 0) == Corner.NONE

    def test_just_outside_corner_is_none(self, display: CalendarDisplay) -> None:
        # One pixel outside the top-left zone horizontally
        assert display._classify_corner(_CORNER_SIZE, 0) == Corner.NONE
        # One pixel outside the top-left zone vertically
        assert display._classify_corner(0, _CORNER_SIZE) == Corner.NONE


# -- State machine transitions ----------------------------------------------


class TestExitTapStateMachine:
    """Tests for the four-corner exit tap state machine."""

    def test_initial_state_is_idle(self, display: CalendarDisplay) -> None:
        assert _get_state(display) == ExitTapState.IDLE

    def test_top_left_advances_to_top_left_tapped(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        assert _get_state(display) == ExitTapState.TOP_LEFT_TAPPED

    def test_wrong_first_corner_stays_idle(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_RIGHT)
        assert _get_state(display) == ExitTapState.IDLE

    def test_full_sequence_exits(self, display: CalendarDisplay) -> None:
        """The complete TL → TR → BR → BL sequence should destroy the root."""
        display._advance_exit_state(Corner.TOP_LEFT)
        assert _get_state(display) == ExitTapState.TOP_LEFT_TAPPED

        display._advance_exit_state(Corner.TOP_RIGHT)
        assert _get_state(display) == ExitTapState.TOP_RIGHT_TAPPED

        display._advance_exit_state(Corner.BOTTOM_RIGHT)
        assert _get_state(display) == ExitTapState.BOTTOM_RIGHT_TAPPED

        display._advance_exit_state(Corner.BOTTOM_LEFT)
        # After the final tap the root is destroyed; state resets to IDLE.
        assert _get_state(display) == ExitTapState.IDLE

    def test_wrong_second_corner_resets(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        assert _get_state(display) == ExitTapState.TOP_LEFT_TAPPED

        display._advance_exit_state(Corner.BOTTOM_LEFT)  # wrong
        assert _get_state(display) == ExitTapState.IDLE

    def test_wrong_third_corner_resets(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        display._advance_exit_state(Corner.TOP_RIGHT)
        assert _get_state(display) == ExitTapState.TOP_RIGHT_TAPPED

        display._advance_exit_state(Corner.TOP_LEFT)  # wrong
        assert _get_state(display) == ExitTapState.IDLE

    def test_wrong_fourth_corner_resets(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        display._advance_exit_state(Corner.TOP_RIGHT)
        display._advance_exit_state(Corner.BOTTOM_RIGHT)
        assert _get_state(display) == ExitTapState.BOTTOM_RIGHT_TAPPED

        display._advance_exit_state(Corner.TOP_RIGHT)  # wrong
        assert _get_state(display) == ExitTapState.IDLE

    def test_timeout_resets_to_idle(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        assert _get_state(display) == ExitTapState.TOP_LEFT_TAPPED
        assert display._exit_tap_timer is not None

        # Simulate the timeout callback firing.
        display._reset_exit_sequence()
        assert _get_state(display) == ExitTapState.IDLE
        assert display._exit_tap_timer is None

    def test_reset_cancels_pending_timer(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        timer_id = display._exit_tap_timer
        assert timer_id is not None

        display._reset_exit_sequence()
        assert display._exit_tap_timer is None

    def test_sequence_can_restart_after_reset(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        display._advance_exit_state(Corner.BOTTOM_RIGHT)  # wrong → reset
        assert _get_state(display) == ExitTapState.IDLE

        # Start again — should work fine.
        display._advance_exit_state(Corner.TOP_LEFT)
        assert _get_state(display) == ExitTapState.TOP_LEFT_TAPPED

    def test_timer_set_at_each_intermediate_state(self, display: CalendarDisplay) -> None:
        display._advance_exit_state(Corner.TOP_LEFT)
        assert display._exit_tap_timer is not None

        display._advance_exit_state(Corner.TOP_RIGHT)
        assert display._exit_tap_timer is not None

        display._advance_exit_state(Corner.BOTTOM_RIGHT)
        assert display._exit_tap_timer is not None


# -- Enum sanity checks -----------------------------------------------------


class TestEnums:
    """Basic sanity checks for the exit-related enums."""

    def test_exit_tap_state_has_four_members(self) -> None:
        assert len(ExitTapState) == 4

    def test_corner_has_five_members(self) -> None:
        assert len(Corner) == 5

    def test_corner_none_is_distinct(self) -> None:
        real_corners = {Corner.TOP_LEFT, Corner.TOP_RIGHT, Corner.BOTTOM_RIGHT, Corner.BOTTOM_LEFT}
        assert Corner.NONE not in real_corners
