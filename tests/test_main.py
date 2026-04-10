from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dmzcal.main import df, hello, read_file, setup_logging


def test_hello_returns_greeting() -> None:
    assert hello("World") == "Hello World"


def test_hello_includes_name() -> None:
    assert "Alice" in hello("Alice")


def test_hello_empty_string() -> None:
    assert hello("") == "Hello "


def test_setup_logging_does_not_raise() -> None:
    setup_logging(level=logging.DEBUG)
    setup_logging(level=logging.WARNING)


def test_df_logs_stdout(caplog: pytest.LogCaptureFixture) -> None:
    mock_result = MagicMock()
    mock_result.stdout = "Filesystem  Size  Used\n/dev/disk1  100G  50G\n"
    with (
        patch("subprocess.run", return_value=mock_result) as mock_run,
        caplog.at_level(logging.INFO, logger="dmzcal.main"),
    ):
        df()
    mock_run.assert_called_once_with(["df", "-h"], capture_output=True, text=True, check=True)
    assert "Filesystem" in caplog.text


def test_df_logs_error_on_failure(caplog: pytest.LogCaptureFixture) -> None:
    with (
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "df")),
        caplog.at_level(logging.ERROR, logger="dmzcal.main"),
    ):
        df()
    assert "Failed to run df command" in caplog.text


def test_read_file_logs_content(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    fake_hosts = tmp_path / "hosts"
    fake_hosts.write_text("127.0.0.1 localhost\n", encoding="iso8859-1")

    with (
        patch("dmzcal.main.Path", return_value=fake_hosts),
        caplog.at_level(logging.INFO, logger="dmzcal.main"),
    ):
        read_file()

    assert "localhost" in caplog.text
