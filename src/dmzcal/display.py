import logging
import subprocess

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
