"""Entry point for the DMZ dementia calendar application."""

from __future__ import annotations

import argparse
import logging
import tkinter as tk
from pathlib import Path
from typing import Final

from rich.logging import RichHandler

from dmzcal.clock import CalendarDisplay
from dmzcal.config import DEFAULT_CONFIG_PATH, load_config
from dmzcal.display import set_brightness

logger: Final = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with RichHandler at the given log level."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def main() -> None:
    """Parse CLI arguments, load configuration, and launch the calendar UI."""
    parser = argparse.ArgumentParser(
        description="DMZ Dementia Calendar — large-format day-of-week display",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the birthdays YAML config file (default: %(default)s)",
    )
    parser.add_argument(
        "-w",
        "--windowed",
        action="store_true",
        default=False,
        help="Run in windowed mode instead of fullscreen (useful for development)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG) logging",
    )

    args = parser.parse_args()

    log_level: int = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)

    config_path: Path = args.config
    logger.info("Loading config from: %s", config_path)
    config = load_config(config_path)
    logger.info("Loaded %d birthday(s)", len(config.birthdays))

    fullscreen: bool = not args.windowed
    logger.info("Starting calendar display (fullscreen=%s)", fullscreen)

    root = tk.Tk()
    display = CalendarDisplay(root=root, config=config, fullscreen=fullscreen)
    display.run()
