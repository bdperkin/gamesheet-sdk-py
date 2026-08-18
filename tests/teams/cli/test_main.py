# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the gamesheet-teams CLI entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk import __version__
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.teams.cli import main
from gamesheet_sdk.teams.cli.commands.completion import completion_command
from gamesheet_sdk.teams.cli.commands.login import login_command
from gamesheet_sdk.teams.cli.commands.lookups import lookups_group
from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.lookups import LookupValue
from tests.helpers import TEST_EMAIL_GENERIC

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_teams_cli_help(runner: CliRunner) -> None:
    """--help shows usage text and exits cleanly."""
    result = runner.invoke(cli, ["--help"])
    assert not result.exit_code
    assert "gamesheet-teams" in result.output.lower() or "teams" in result.output.lower()


def test_teams_cli_version(runner: CliRunner) -> None:
    """--version prints the package version."""
    result = runner.invoke(cli, ["--version"])
    assert not result.exit_code
    assert __version__ in result.output


def test_teams_cli_exits_zero_on_no_args() -> None:
    """Main([]) returns 0 (shows help)."""
    assert not main([])


def test_teams_login_success(runner: CliRunner) -> None:
    """Login succeeds and prints success message."""
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.return_value = {
            "access": "a",
            "refresh": "r",
        }
        result = runner.invoke(
            cli,
            ["login", "--email", TEST_EMAIL_GENERIC, "--password", "secret"],
        )

    assert not result.exit_code
    assert "Login successful" in result.output
    assert "Tokens saved" in result.output


def test_teams_login_failure(runner: CliRunner) -> None:
    """Login failure prints error and exits 1."""
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.side_effect = Exception(
            "Invalid credentials",
        )
        result = runner.invoke(
            cli,
            ["login", "--email", TEST_EMAIL_GENERIC, "--password", "wrong"],
        )

    assert result.exit_code == 1
    assert "Login failed" in result.output
    assert "Invalid credentials" in result.output


def test_teams_login_passes_credentials(runner: CliRunner) -> None:
    """Login passes email, password, and timeout to TeamsLoginFlow."""
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.return_value = {
            "access": "a",
            "refresh": "r",
        }
        result = runner.invoke(
            cli,
            [
                "login",
                "--email",
                TEST_EMAIL_GENERIC,
                "--password",
                "secret",
                "--timeout",
                "30.0",
            ],
        )

    assert not result.exit_code
    mock_flow_cls.return_value.authenticate.assert_called_once_with(
        email=TEST_EMAIL_GENERIC,
        password="secret",  # pragma: allowlist secret
        timeout=30.0,
    )


def test_teams_login_no_credentials(runner: CliRunner) -> None:
    """Login with no args passes None for email and password."""
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.return_value = {
            "access": "a",
            "refresh": "r",
        }
        result = runner.invoke(cli, ["login"])

    assert not result.exit_code
    call_kwargs = mock_flow_cls.return_value.authenticate.call_args.kwargs
    assert call_kwargs["email"] is None
    assert call_kwargs["password"] is None


def test_teams_login_help(runner: CliRunner) -> None:
    """Login --help shows usage text with email option."""
    result = runner.invoke(cli, ["login", "--help"])
    assert not result.exit_code
    assert "email" in result.output.lower()


def test_teams_login_without_parent_context(runner: CliRunner) -> None:
    """Login invoked directly with obj works."""
    mock_config = MagicMock()
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.return_value = {
            "access": "a",
            "refresh": "r",
        }
        result = runner.invoke(login_command, [], obj=mock_config)

    assert not result.exit_code
    assert "Login successful" in result.output


def test_teams_completion_bash(runner: CliRunner) -> None:
    """Completion bash emits a completion script."""
    result = runner.invoke(cli, ["completion", "bash"])
    assert not result.exit_code
    assert "complete" in result.output or "_GAMESHEET_TEAMS_COMPLETE" in result.output


def test_teams_completion_zsh(runner: CliRunner) -> None:
    """Completion zsh emits a completion script."""
    result = runner.invoke(cli, ["completion", "zsh"])
    assert not result.exit_code
    assert "compdef" in result.output or "_GAMESHEET_TEAMS_COMPLETE" in result.output


def test_teams_completion_fish(runner: CliRunner) -> None:
    """Completion fish emits a completion script."""
    result = runner.invoke(cli, ["completion", "fish"])
    assert not result.exit_code
    assert "complete" in result.output or "_GAMESHEET_TEAMS_COMPLETE" in result.output


def test_teams_completion_without_parent_context(runner: CliRunner) -> None:
    """Completion invoked directly (no parent) exits cleanly with no output."""
    result = runner.invoke(completion_command, ["bash"])
    assert not result.exit_code
    assert not result.output


def test_teams_default_base_url(runner: CliRunner) -> None:
    """Default base URL for teams is https://teams.gamesheet.app."""
    from gamesheet_sdk.teams.cli.main import _TEAMS_DEFAULT_BASE_URL

    assert _TEAMS_DEFAULT_BASE_URL == "https://teams.gamesheet.app"

    result = runner.invoke(cli, ["--help"])
    assert not result.exit_code
    assert "teams.gamesheet.app" in result.output


def test_teams_rich_click_configuration_applied() -> None:
    """Rich-click configuration settings are applied for the teams CLI."""
    import rich_click as click

    assert click.rich_click.TEXT_MARKUP == "rich"
    assert click.rich_click.SHOW_ARGUMENTS is True
    assert click.rich_click.GROUP_ARGUMENTS_OPTIONS
    assert click.rich_click.MAX_WIDTH == 100


def test_teams_option_groups_configured() -> None:
    """Option groups are configured for the teams CLI."""
    import rich_click as click

    assert "gamesheet-teams" in click.rich_click.OPTION_GROUPS
    option_groups = click.rich_click.OPTION_GROUPS["gamesheet-teams"]
    assert any(g.get("name") == "Configuration Options" for g in option_groups)
    assert any(g.get("name") == "General Options" for g in option_groups)


def test_teams_command_groups_configured() -> None:
    """Command groups are configured for the teams CLI."""
    import rich_click as click

    assert "gamesheet-teams" in click.rich_click.COMMAND_GROUPS
    command_groups = click.rich_click.COMMAND_GROUPS["gamesheet-teams"]
    assert any(g.get("name") == "Authentication" for g in command_groups)
    assert any(g.get("name") == "Utilities" for g in command_groups)
    resources = next(g for g in command_groups if g.get("name") == "Resources")
    assert "lookups" in resources["commands"]
    assert "members" in resources["commands"]
    assert "messages" in resources["commands"]
    assert "roster" in resources["commands"]
    assert "schedule" in resources["commands"]
    assert "seasons" in resources["commands"]
    assert "teams" in resources["commands"]


def test_teams_cli_with_no_headless_flag(runner: CliRunner) -> None:
    """CLI should accept --no-headless flag and still run login."""
    with patch(
        "gamesheet_sdk.teams.cli.commands.login.TeamsLoginFlow",
    ) as mock_flow_cls:
        mock_flow_cls.return_value.authenticate.return_value = {
            "access": "a",
            "refresh": "r",
        }
        result = runner.invoke(cli, ["--no-headless", "login"])

    assert not result.exit_code
    assert "Login successful" in result.output


def test_teams_main_handles_keyboard_interrupt() -> None:
    """Main() should catch KeyboardInterrupt and return a clean exit code."""
    from gamesheet_sdk.teams.cli.main import main as teams_main

    with patch.object(cli, "main", side_effect=KeyboardInterrupt):
        result = teams_main([])
        assert isinstance(result, int)


def test_teams_cli_main_module() -> None:
    """Running the module as __main__ should invoke sys.exit(main())."""
    import runpy
    import warnings

    import pytest

    with (
        patch("sys.argv", ["gamesheet-teams", "--version"]),
        warnings.catch_warnings(),
    ):
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(SystemExit, match="0"):
            runpy.run_module(
                "gamesheet_sdk.teams.cli.main",
                run_name="__main__",
            )


# ---------- lookups command ------------------------------------------------

_MOCK_LOOKUPS = {
    "sports": [
        LookupValue(key="hockey", title="Hockey"),
        LookupValue(key="soccer", title="Soccer"),
    ],
    "game_types": [
        LookupValue(key="league", title="League"),
    ],
}

_LOOKUPS_PATCH = "gamesheet_sdk.teams.cli.commands.lookups.list_lookups"


def test_teams_lookups_help(runner: CliRunner) -> None:
    """Lookups --help shows usage text."""
    result = runner.invoke(cli, ["lookups", "--help"])
    assert not result.exit_code
    assert "lookup" in result.output.lower()


def test_teams_lookups_list_summary(runner: CliRunner) -> None:
    """Default lookups list shows summary with category names and counts."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups"])

    assert not result.exit_code
    assert "sports" in result.output
    assert "game_types" in result.output


def test_teams_lookups_list_category(runner: CliRunner) -> None:
    """Lookups list --category shows values for that category."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "list", "--category", "sports"])

    assert not result.exit_code
    assert "hockey" in result.output
    assert "Hockey" in result.output
    assert "soccer" in result.output


def test_teams_lookups_list_unknown_category(runner: CliRunner) -> None:
    """Unknown --category exits 1 with available categories."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "list", "--category", "bogus"])

    assert result.exit_code == 1
    assert "Unknown category" in result.output
    assert "sports" in result.output


def test_teams_lookups_list_json(runner: CliRunner) -> None:
    """Lookups list --format json outputs valid JSON."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "list", "--format", "json"])

    assert not result.exit_code
    assert "sports" in result.output
    assert "hockey" in result.output


def test_teams_lookups_list_category_json(runner: CliRunner) -> None:
    """Lookups list --category sports --format json outputs values as JSON."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(
            cli,
            ["lookups", "list", "--category", "sports", "--format", "json"],
        )

    assert not result.exit_code
    assert "hockey" in result.output


def test_teams_lookups_error(runner: CliRunner) -> None:
    """HTTP error shows error message and exits 1."""
    with patch(
        _LOOKUPS_PATCH,
        side_effect=GameSheetError("GET /api/lookups returned HTTP 500: boom"),
    ):
        result = runner.invoke(cli, ["lookups"])

    assert result.exit_code == 1
    assert "HTTP 500" in result.output


def test_teams_lookups_alias_ls(runner: CliRunner) -> None:
    """The 'ls' alias works for the list subcommand."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "ls"])

    assert not result.exit_code
    assert "sports" in result.output


def test_teams_lookups_without_parent_context(runner: CliRunner) -> None:
    """Lookups group invoked directly with obj works."""
    mock_config = MagicMock()
    mock_config.timeout = 1.0
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(lookups_group, [], obj=mock_config)

    assert not result.exit_code
    assert "sports" in result.output


# ---------- lookups get command ---------------------------------------------


def test_teams_lookups_get_category(runner: CliRunner) -> None:
    """Lookups get --category shows values for that category."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "get", "--category", "sports"])

    assert not result.exit_code
    assert "hockey" in result.output
    assert "Hockey" in result.output
    assert "soccer" in result.output


def test_teams_lookups_get_unknown_category(runner: CliRunner) -> None:
    """Unknown --category exits 1 with available categories."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "get", "--category", "bogus"])

    assert result.exit_code == 1
    assert "Unknown category" in result.output
    assert "sports" in result.output


def test_teams_lookups_get_json(runner: CliRunner) -> None:
    """Lookups get --category --format json outputs values as JSON."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(
            cli,
            ["lookups", "get", "--category", "sports", "--format", "json"],
        )

    assert not result.exit_code
    assert "hockey" in result.output


def test_teams_lookups_get_error(runner: CliRunner) -> None:
    """HTTP error on get shows error message and exits 1."""
    with patch(
        _LOOKUPS_PATCH,
        side_effect=GameSheetError("GET /api/lookups returned HTTP 500: boom"),
    ):
        result = runner.invoke(cli, ["lookups", "get", "--category", "sports"])

    assert result.exit_code == 1
    assert "HTTP 500" in result.output


def test_teams_lookups_get_alias_show(runner: CliRunner) -> None:
    """The 'show' alias works for the get subcommand."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "show", "--category", "sports"])

    assert not result.exit_code
    assert "hockey" in result.output


def test_teams_lookups_get_alias_view(runner: CliRunner) -> None:
    """The 'view' alias works for the get subcommand."""
    with patch(_LOOKUPS_PATCH, return_value=_MOCK_LOOKUPS):
        result = runner.invoke(cli, ["lookups", "view", "--category", "sports"])

    assert not result.exit_code
    assert "hockey" in result.output


def test_teams_lookups_get_missing_category(runner: CliRunner) -> None:
    """Lookups get without --category exits non-zero (required option)."""
    result = runner.invoke(cli, ["lookups", "get"])
    assert result.exit_code
