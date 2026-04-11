"""Full-screen calendar / clock UI for the DMZ dementia calendar.

Displays the current weekday (in German), date, time, and optional
holiday / birthday information on a black background.  Designed for a
Raspberry Pi with a 7″ 1280×720 display running Tk 9.0.
"""

from __future__ import annotations

import logging
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Final

from dmzcal.config import Config, get_birthdays_for_date
from dmzcal.display import set_brightness
from dmzcal.holidays import get_holiday_for_date

logger: Final = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FONT_DIR: Final[Path] = Path(__file__).parent / "fonts"

WEEKDAY_NAMES_DE: Final[tuple[str, ...]] = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)

_LONGEST_WEEKDAY: Final[str] = "Donnerstag"

_COLOR_WHITE: Final[str] = "#FFFFFF"
_COLOR_ORANGE: Final[str] = "#FFB347"
_COLOR_BLACK: Final[str] = "#000000"

_TICK_INTERVAL_MS: Final[int] = 5000
_CORNER_SIZE: Final[int] = 80
_EXIT_TAP_TIMEOUT_MS: Final[int] = 5000

# Preferred font families in order of priority.
_PREFERRED_FAMILIES: Final[tuple[str, ...]] = (
    "Inter",
    "Noto Sans",
    "Roboto",
    "DejaVu Sans",
    "Helvetica",
)

_FULLSCREEN_WIDTH: Final[int] = 1280
_FULLSCREEN_HEIGHT: Final[int] = 720
_WINDOWED_WIDTH: Final[int] = 800
_WINDOWED_HEIGHT: Final[int] = 480

_BRIGHTNESS_PERCENT_DAY: int = 60
_BRIGHTNESS_PERCENT_NIGHT: int = 30

_NIGHT_STARTS_AT_HOUR: int = 18
_DAY_STARTS_AT_HOUR: int = 7


# ---------------------------------------------------------------------------
# Exit tap state machine enums
# ---------------------------------------------------------------------------


class ExitTapState(Enum):
    """States for the four-corner exit tap sequence."""

    IDLE = "idle"
    TOP_LEFT_TAPPED = "top_left_tapped"
    TOP_RIGHT_TAPPED = "top_right_tapped"
    BOTTOM_RIGHT_TAPPED = "bottom_right_tapped"


class Corner(Enum):
    """Screen corner classification for tap detection."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    NONE = "none"


# ---------------------------------------------------------------------------
# Public format helpers (pure functions, no Tk dependency)
# ---------------------------------------------------------------------------


def format_date(d: date) -> str:
    """Format a date as ``D.M.YYYY`` with no leading zeros.

    Examples: ``"7.4.2026"``, ``"31.3.2026"``, ``"2.11.2026"``
    """
    return f"{d.day}.{d.month}.{d.year}"


def format_time(dt: datetime) -> str:
    """Format a datetime's time component as ``HH:MM`` in 24-hour format.

    Examples: ``"14:05"``, ``"09:30"``, ``"00:00"``
    """
    return dt.strftime("%H:%M")


def format_special_line(holiday: str | None, birthdays: list[str]) -> str:
    """Combine holiday and birthday information into a single display string.

    Returns
    -------
    str
        - ``""`` when there is neither a holiday nor any birthdays.
        - ``"Karfreitag"`` for a holiday-only day.
        - ``"Geburtstag: Oma"`` for a single birthday.
        - ``"Geburtstag: Oma, Opa"`` for multiple birthdays.
        - ``"Karfreitag - Geburtstag: Oma"`` for a holiday *and* birthday(s).
    """
    parts: list[str] = []

    if holiday is not None:
        parts.append(holiday)

    if birthdays:
        parts.append("Geburtstag: " + ", ".join(birthdays))

    return " - ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers (require a running Tk instance)
# ---------------------------------------------------------------------------


def _register_bundled_fonts(root: tk.Tk) -> None:
    """Add the bundled font directory to Tk 9.0's font search path.

    On Tk < 9.0 this is a no-op (the call is simply skipped).
    """
    if not _FONT_DIR.is_dir():
        logger.warning("Bundled font directory not found: %s", _FONT_DIR)
        return
    try:
        root.tk.call("lappend", "::tk::fontpath", str(_FONT_DIR))
        logger.info("Registered font directory with Tk: %s", _FONT_DIR)
    except tk.TclError:
        logger.debug("Tk fontpath extension not available — bundled fonts may not load")


def _resolve_font_family(root: tk.Tk) -> str:
    """Return the first available family from :data:`_PREFERRED_FAMILIES`.

    Falls back to ``"TkDefaultFont"`` if none of the preferred families are
    found on the system.
    """
    available: set[str] = {f.lower() for f in tkfont.families(root=root)}
    for family in _PREFERRED_FAMILIES:
        if family.lower() in available:
            logger.info("Selected font family: %s", family)
            return family
    logger.warning("No preferred font family found — falling back to TkDefaultFont")
    return "TkDefaultFont"


def _compute_day_font_size(
    root: tk.Tk,
    family: str,
    target_width: int,
) -> int:
    """Binary-search for the largest bold font size where *_LONGEST_WEEKDAY* fits *target_width*."""
    lo: int = 10
    hi: int = 300
    best: int = lo

    while lo <= hi:
        mid: int = (lo + hi) // 2
        test_font = tkfont.Font(root=root, family=family, size=mid, weight="bold")
        measured: int = test_font.measure(_LONGEST_WEEKDAY)
        if measured <= target_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best


def _build_special_text(d: date, config: Config) -> str:
    """Return the combined holiday / birthday string for *d*, or ``""``."""
    holiday: str | None = get_holiday_for_date(d)
    names: list[str] = get_birthdays_for_date(d, config)
    return format_special_line(holiday, names)


# ---------------------------------------------------------------------------
# Main UI class
# ---------------------------------------------------------------------------


class CalendarDisplay:
    """Full-screen (or windowed) calendar / clock display.

    Parameters
    ----------
    root:
        The Tk root window.
    config:
        Loaded birthday / holiday configuration.
    fullscreen:
        If ``True`` the window is set to 1280×720 with no decorations and
        a hidden cursor.  ``False`` opens a regular development window.
    """

    def __init__(
        self,
        root: tk.Tk,
        config: Config,
        fullscreen: bool = True,
    ) -> None:
        self._root: Final[tk.Tk] = root
        self._config: Final[Config] = config
        self._fullscreen: Final[bool] = fullscreen
        self.brightness: int = 0

        # Track the currently displayed date so we only refresh date-dependent
        # labels when the day actually changes.
        self._current_date: date | None = None

        # --- window setup ---------------------------------------------------
        self._root.title("DMZ Kalender")
        self._root.configure(background=_COLOR_BLACK)

        if fullscreen:
            self._root.overrideredirect(True)
            self._root.geometry(f"{_FULLSCREEN_WIDTH}x{_FULLSCREEN_HEIGHT}")
            self._root.config(cursor="none")
            target_width: int = _FULLSCREEN_WIDTH
        else:
            self._root.geometry(f"{_WINDOWED_WIDTH}x{_WINDOWED_HEIGHT}")
            target_width = _WINDOWED_WIDTH

        # --- fonts -----------------------------------------------------------
        _register_bundled_fonts(self._root)
        family: str = _resolve_font_family(self._root)

        # Leave a small horizontal margin (96 % of target) so the text doesn't
        # touch the very edge of the screen.
        usable_width: int = int(target_width * 0.96)
        day_size: int = _compute_day_font_size(self._root, family, usable_width)
        date_size: int = max(day_size // 5, 12)
        time_size: int = max(day_size // 8, 10)
        special_size: int = max(day_size // 5, 10)

        self._day_font: Final[tkfont.Font] = tkfont.Font(
            root=self._root, family=family, size=day_size, weight="bold"
        )
        self._date_font: Final[tkfont.Font] = tkfont.Font(
            root=self._root, family=family, size=date_size, weight="bold"
        )
        self._time_font: Final[tkfont.Font] = tkfont.Font(
            root=self._root, family=family, size=time_size, weight="bold"
        )
        self._special_font: Final[tkfont.Font] = tkfont.Font(
            root=self._root, family=family, size=special_size, weight="normal"
        )

        # --- layout ----------------------------------------------------------
        # A single centred frame holds the main labels (day, date, time).
        self._frame: Final[tk.Frame] = tk.Frame(self._root, background=_COLOR_BLACK)
        self._frame.pack(expand=True)

        self.day_label: Final[tk.Label] = tk.Label(
            self._frame,
            text="",
            font=self._day_font,
            foreground=_COLOR_WHITE,
            background=_COLOR_BLACK,
            anchor="center",
        )
        self.day_label.pack(fill="x", pady=(0, 4))

        self.date_label: Final[tk.Label] = tk.Label(
            self._frame,
            text="",
            font=self._date_font,
            foreground=_COLOR_WHITE,
            background=_COLOR_BLACK,
            anchor="center",
        )
        self.date_label.pack(fill="x", pady=(0, 4))

        self.time_label: Final[tk.Label] = tk.Label(
            self._frame,
            text="",
            font=self._time_font,
            foreground=_COLOR_WHITE,
            background=_COLOR_BLACK,
            anchor="center",
        )
        self.time_label.pack(fill="x")

        # Special label (holiday/birthday) pinned to the bottom-right corner.
        self.special_label: Final[tk.Label] = tk.Label(
            self._root,
            text="",
            font=self._special_font,
            foreground=_COLOR_ORANGE,
            background=_COLOR_BLACK,
            anchor="e",
        )
        self.special_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-6)

        # --- exit mechanism state --------------------------------------------
        self._exit_tap_state: ExitTapState = ExitTapState.IDLE
        self._exit_tap_timer: str | None = None

        self._root.bind("<Button-1>", self._on_tap)
        self._root.bind("<Control-Shift-q>", self._exit_app_event)
        self._root.bind("<Control-Shift-Q>", self._exit_app_event)

        # --- initial draw & start tick loop ----------------------------------
        self._tick()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_date_labels(self, today: date) -> None:
        """Refresh the day-of-week, special, and date labels for *today*."""
        weekday_name: str = WEEKDAY_NAMES_DE[today.weekday()]
        self.day_label.configure(text=weekday_name)

        special_text: str = _build_special_text(today, self._config)
        self.special_label.configure(text=special_text)

        date_text: str = format_date(today)
        self.date_label.configure(text=date_text)

    def _tick(self) -> None:
        """Called every _TICK_INTERVAL_MS to refresh the display."""
        now: datetime = datetime.now()
        today: date = now.date()

        # Always update the time.
        time_text: str = format_time(now)
        self.time_label.configure(text=time_text)

        # Only refresh date-dependent labels when the day rolls over.
        if self._current_date != today:
            self._current_date = today
            self._update_date_labels(today)

        # Set brightness
        logger.info("Hour is %d", now.hour)
        if now.hour >= _NIGHT_STARTS_AT_HOUR or now.hour < _DAY_STARTS_AT_HOUR:  # noqa: SIM102
            if self.brightness != _BRIGHTNESS_PERCENT_NIGHT:
                logger.info("Change brightness to %d %%", _BRIGHTNESS_PERCENT_NIGHT)
                self.brightness = _BRIGHTNESS_PERCENT_NIGHT
                set_brightness(self.brightness)
        if now.hour >= _DAY_STARTS_AT_HOUR and now.hour < _NIGHT_STARTS_AT_HOUR:  # noqa: SIM102
            if self.brightness != _BRIGHTNESS_PERCENT_DAY:
                logger.info("Change brightness to %d %%", _BRIGHTNESS_PERCENT_DAY)
                self.brightness = _BRIGHTNESS_PERCENT_DAY
                set_brightness(self.brightness)

        self._root.after(_TICK_INTERVAL_MS, self._tick)

    # ------------------------------------------------------------------
    # Exit mechanism
    # ------------------------------------------------------------------

    def _classify_corner(self, x: int, y: int) -> Corner:
        """Return which corner zone *(x, y)* falls into, or ``NONE``."""
        width: int = self._root.winfo_width()
        height: int = self._root.winfo_height()

        in_left: bool = x < _CORNER_SIZE
        in_right: bool = x >= width - _CORNER_SIZE
        in_top: bool = y < _CORNER_SIZE
        in_bottom: bool = y >= height - _CORNER_SIZE

        if in_left and in_top:
            return Corner.TOP_LEFT
        if in_right and in_top:
            return Corner.TOP_RIGHT
        if in_right and in_bottom:
            return Corner.BOTTOM_RIGHT
        if in_left and in_bottom:
            return Corner.BOTTOM_LEFT
        return Corner.NONE

    def _on_tap(self, event: tk.Event[tk.Misc]) -> None:
        """Handle a mouse click and feed it to the exit tap state machine."""
        corner: Corner = self._classify_corner(event.x, event.y)
        if corner is Corner.NONE:
            return
        self._advance_exit_state(corner)

    def _reset_exit_sequence(self) -> None:
        """Reset the exit tap state machine to IDLE and cancel any pending timeout."""
        if self._exit_tap_timer is not None:
            self._root.after_cancel(self._exit_tap_timer)
            self._exit_tap_timer = None
        if self._exit_tap_state is not ExitTapState.IDLE:
            logger.debug("Exit tap sequence reset from %s to IDLE", self._exit_tap_state.value)
        self._exit_tap_state = ExitTapState.IDLE

    def _advance_exit_state(self, corner: Corner) -> None:
        """Advance the four-corner exit state machine based on *corner*."""
        state = self._exit_tap_state

        if state is ExitTapState.IDLE:
            if corner is Corner.TOP_LEFT:
                self._reset_exit_sequence()
                self._exit_tap_state = ExitTapState.TOP_LEFT_TAPPED
                self._exit_tap_timer = self._root.after(
                    _EXIT_TAP_TIMEOUT_MS, self._reset_exit_sequence
                )
                logger.debug("Exit tap: TOP_LEFT tapped — waiting for TOP_RIGHT")
            else:
                self._reset_exit_sequence()

        elif state is ExitTapState.TOP_LEFT_TAPPED:
            if corner is Corner.TOP_RIGHT:
                self._reset_exit_sequence()
                self._exit_tap_state = ExitTapState.TOP_RIGHT_TAPPED
                self._exit_tap_timer = self._root.after(
                    _EXIT_TAP_TIMEOUT_MS, self._reset_exit_sequence
                )
                logger.debug("Exit tap: TOP_RIGHT tapped — waiting for BOTTOM_RIGHT")
            else:
                self._reset_exit_sequence()

        elif state is ExitTapState.TOP_RIGHT_TAPPED:
            if corner is Corner.BOTTOM_RIGHT:
                self._reset_exit_sequence()
                self._exit_tap_state = ExitTapState.BOTTOM_RIGHT_TAPPED
                self._exit_tap_timer = self._root.after(
                    _EXIT_TAP_TIMEOUT_MS, self._reset_exit_sequence
                )
                logger.debug("Exit tap: BOTTOM_RIGHT tapped — waiting for BOTTOM_LEFT")
            else:
                self._reset_exit_sequence()

        elif state is ExitTapState.BOTTOM_RIGHT_TAPPED:
            if corner is Corner.BOTTOM_LEFT:
                self._reset_exit_sequence()
                logger.info("Exit tap sequence completed — exiting application")
                self._exit_app()
            else:
                self._reset_exit_sequence()

    def _exit_app(self) -> None:
        """Log and destroy the root window to exit the application."""
        logger.info("Exiting DMZ calendar application")
        self._root.destroy()

    def _exit_app_event(self, event: tk.Event[tk.Misc]) -> None:
        """Handle Ctrl+Shift+Q keyboard shortcut to exit."""
        logger.info("Ctrl+Shift+Q pressed — exiting application")
        self._exit_app()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Enter the Tk main loop (blocks until the window is closed)."""
        self._root.mainloop()
