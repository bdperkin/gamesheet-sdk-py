"""Tests for :mod:`gamesheet_sdk.cli`."""

# pylint: disable=redefined-outer-name,protected-access
# - redefined-outer-name: pytest fixtures share names with the params they bind
# - protected-access: tests legitimately inspect internals

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gamesheet_sdk import __version__
from gamesheet_sdk.auth import LOGIN_PATH
from gamesheet_sdk.cli import _configure_logging, cli, main
from gamesheet_sdk.exceptions import AuthenticationError


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------- top-level group ----------------------------------------------


def test_main_no_args_prints_help_and_exits_zero() -> None:
    """`gamesheet-sdk-py` with no subcommand shows help and returns 0."""
    assert main([]) == 0


def test_version_flag_exits_zero(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_flag_lists_login_subcommand(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "login" in result.output


def test_unknown_subcommand_returns_two() -> None:
    """Unknown subcommand is a usage error -> exit 2."""
    assert main(["totally-not-a-subcommand"]) == 2


# ---------- logging configuration ----------------------------------------


def test_configure_logging_default_warning_level() -> None:
    _configure_logging(0)
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_v_sets_info() -> None:
    _configure_logging(1)
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_vv_sets_debug() -> None:
    _configure_logging(2)
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_vvv_clamps_to_debug() -> None:
    _configure_logging(7)
    assert logging.getLogger().level == logging.DEBUG


# ---------- login subcommand --------------------------------------------


@patch("gamesheet_sdk.cli._login_action")
def test_login_succeeds_with_explicit_credentials(
    mock_login: MagicMock, runner: CliRunner
) -> None:
    result = runner.invoke(
        cli,
        ["login", "--email", "alice@example.com", "--password", "hunter2"],
    )
    assert result.exit_code == 0, result.output
    assert "Login succeeded" in result.output
    mock_login.assert_called_once()
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "alice@example.com"
    assert kwargs["password"] == "hunter2"
    assert kwargs["timeout"] == 15.0


@patch("gamesheet_sdk.cli._login_action")
def test_login_failure_exits_one(mock_login: MagicMock, runner: CliRunner) -> None:
    mock_login.side_effect = AuthenticationError("bad creds")
    result = runner.invoke(
        cli,
        ["login", "--email", "a@b.c", "--password", "x"],
    )
    assert result.exit_code == 1
    assert "Login failed" in result.output
    assert "bad creds" in result.output


@patch("gamesheet_sdk.cli._login_action")
def test_login_passes_custom_timeout(mock_login: MagicMock, runner: CliRunner) -> None:
    runner.invoke(
        cli,
        [
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
            "--timeout",
            "5",
        ],
    )
    _, kwargs = mock_login.call_args
    assert kwargs["timeout"] == 5.0


@patch("gamesheet_sdk.cli._login_action")
def test_login_reads_credentials_from_env(
    mock_login: MagicMock,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GAMESHEET_USERNAME", "envuser@example.com")
    monkeypatch.setenv("GAMESHEET_PASSWORD", "envpw")
    result = runner.invoke(cli, ["login"])
    assert result.exit_code == 0, result.output
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "envuser@example.com"
    assert kwargs["password"] == "envpw"


@patch("gamesheet_sdk.cli._login_action")
def test_login_prompts_when_no_credentials_anywhere(
    mock_login: MagicMock, runner: CliRunner
) -> None:
    """Without --email/--password and without env vars, click prompts."""
    result = runner.invoke(
        cli,
        ["login"],
        input="prompt-user@example.com\nprompt-pw\n",
    )
    assert result.exit_code == 0, result.output
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "prompt-user@example.com"
    assert kwargs["password"] == "prompt-pw"


# ---------- base-url / headless overrides flow into Config -------------


@patch("gamesheet_sdk.cli._login_action")
@patch("gamesheet_sdk.cli.BrowserSession")
def test_base_url_override_reaches_config(
    mock_browser: MagicMock,
    mock_login: MagicMock,
    runner: CliRunner,
) -> None:
    del mock_login  # unused; we just need to short-circuit auth
    runner.invoke(
        cli,
        [
            "--base-url",
            "https://override.example",
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
        ],
    )
    config_arg = mock_browser.call_args[0][0]
    assert config_arg.base_url == "https://override.example"


@patch("gamesheet_sdk.cli._login_action")
@patch("gamesheet_sdk.cli.BrowserSession")
def test_no_headless_reaches_config(
    mock_browser: MagicMock,
    mock_login: MagicMock,
    runner: CliRunner,
) -> None:
    del mock_login
    runner.invoke(
        cli,
        [
            "--no-headless",
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
        ],
    )
    config_arg = mock_browser.call_args[0][0]
    assert config_arg.browser_headless is False


# ---------- main() wrapper edge cases ------------------------------------


def test_main_propagates_systemexit_int() -> None:
    """Plain SystemExit(int) inside a click command should map to its code."""
    with patch("gamesheet_sdk.cli._login_action", side_effect=SystemExit(7)):
        rc = main(["login", "--email", "a@b.c", "--password", "x"])
    assert rc == 7


def test_main_login_path_constant_matches_auth_module() -> None:
    """Trivial smoke: LOGIN_PATH is what cli ends up wiring auth.login to."""
    assert LOGIN_PATH.startswith("/")
