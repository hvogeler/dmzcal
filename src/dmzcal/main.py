"""Entry point."""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with RichHandler at the given log level."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


logger = logging.getLogger(__name__)


def hello(name: str) -> str:
    """Return a greeting string for the given name."""
    return f"Hello {name}"


def df() -> None:
    """Run the system `df -h` command and log its output."""
    try:
        result = subprocess.run(
            ["df", "-h"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("%s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to run df command: %s", e)


def read_file() -> None:
    """Read /etc/hosts and log its contents."""
    p = Path("/etc/hosts")
    logger.info("Reading '%s' file", p.name)
    content = p.read_text(encoding="iso8859-1")
    logger.info("%s file content: %s", p.name, content)


def main() -> None:
    """Parse CLI arguments and run the main workflow."""
    setup_logging(level=logging.INFO)
    parser = argparse.ArgumentParser(description="gen-db-load-psets")

    parser.add_argument(
        "-n", "--name", required=True, type=str, default="No-Name", help="Name to hello"
    )

    args = parser.parse_args()
    name: str = args.name

    logger.info("Name is '%s'", name)
    logger.info("%s", hello(name=name))

    df()
    read_file()

