# tests/test_main_cli.py
from unittest.mock import patch

import main


def test_cli_cto_calls_cmd_cto():
    with (
        patch("sys.argv", ["main.py", "cto", "idea", "my saas idea"]),
        patch("main.cmd_cto") as mock,
    ):
        main._cli_mode()
    mock.assert_called_once_with("my saas idea", "avg")


def test_cli_cto_onboard_calls_cmd_onboard():
    with (
        patch("sys.argv", ["main.py", "cto", "onboard"]),
        patch("main.cmd_cto_onboard") as mock,
    ):
        main._cli_mode()
    mock.assert_called_once_with("avg")


def test_cli_status_calls_cmd_status():
    with patch("sys.argv", ["main.py", "status"]), patch("main.cmd_status") as mock:
        main._cli_mode()
    mock.assert_called_once()


def test_cli_mode_respected():
    with (
        patch("sys.argv", ["main.py", "--mode", "best", "cto", "idea", "my idea"]),
        patch("main.cmd_cto") as mock,
    ):
        main._cli_mode()
    mock.assert_called_once_with("my idea", "best")


def test_cli_cto_continue():
    with (
        patch("sys.argv", ["main.py", "cto", "continue", "phase-2"]),
        patch("main.cmd_cto_continue") as mock,
    ):
        main._cli_mode()
    mock.assert_called_once_with("phase-2", "avg")
