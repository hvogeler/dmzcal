import logging
import subprocess

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with RichHandler at the given log level."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


logger = logging.getLogger(__name__)


def get_max_brightness() -> int:
    """Get maximum brightness"""
    result = subprocess.run(
        ["cat", "/sys/class/backlight/11-0045/max_brightness"],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout)


def set_brightness(percent: int):
    """Set display brightness in percent"""
    try:
        max_brightness = get_max_brightness()
        new_brightness = int((float(percent) / 100.0) * max_brightness)
        logger.info("Maximum Brightness = %d", max_brightness)
        logger.info("New Brightness = %d", new_brightness)

        subprocess.run(
            ["sudo", "tee", "/sys/class/backlight/11-0045/brightness"],
            input=str(new_brightness),
            capture_output=True,
            text=True,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        logger.error("Failed to run df command: %s", e)


def main() -> None:
    """Set brightnes in percent of maximum brightness"""
    setup_logging()
    set_brightness(10)


if __name__ == "__main__":
    main()
