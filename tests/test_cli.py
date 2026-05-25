"""Tests for :mod:`gamesheet_sdk.cli`."""

# pylint: disable=redefined-outer-name,protected-access
# - redefined-outer-name: pytest fixtures share names with the params they bind
# - protected-access: tests legitimately inspect internals

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gamesheet_sdk import __version__
from gamesheet_sdk.auth import LOGIN_PATH
from gamesheet_sdk.cli import _configure_logging, cli, main
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError


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


# ---------- list-associations subcommand --------------------------------


def _stub_associations(*ids_and_titles: tuple[str, str]) -> list[object]:
    """Build fake Association objects without needing pydantic instantiation."""
    out = []
    for aid, title in ids_and_titles:
        a = MagicMock()
        a.id = aid
        a.title = title
        a.model_dump.return_value = {"id": aid, "title": title}
        out.append(a)
    return out


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_default_table_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(
        ("11", "Hockey Time Productions"),
        ("40", "SuperSeries AAA"),
    )
    result = runner.invoke(cli, ["list-associations"])
    assert result.exit_code == 0, result.output
    assert "11\tHockey Time Productions" in result.output
    assert "40\tSuperSeries AAA" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_json_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["list-associations", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == [{"id": "11", "title": "Hockey Time"}]


@patch("gamesheet_sdk.cli.load_refresh_token", return_value=None)
@patch("gamesheet_sdk.cli.load_access_token", return_value=None)
def test_list_associations_missing_token_exits_one(
    _mock_load_access: MagicMock, _mock_load_refresh: MagicMock, runner: CliRunner
) -> None:
    result = runner.invoke(cli, ["list-associations"])
    assert result.exit_code == 1
    assert "No saved session" in result.output
    assert "Run `gamesheet-sdk-py login`" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_authentication_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = AuthenticationError("HTTP 401")
    result = runner.invoke(cli, ["list-associations"])
    assert result.exit_code == 1
    assert "Authentication required" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_other_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = GameSheetError("HTTP 500")
    result = runner.invoke(cli, ["list-associations"])
    assert result.exit_code == 1
    assert "GameSheet error" in result.output
