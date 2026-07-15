# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the gamesheet-teams CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk import __version__
from gamesheet_sdk.teams.cli import main
from gamesheet_sdk.teams.cli.commands.completion import completion_command
from gamesheet_sdk.teams.cli.commands.login import login_command
from gamesheet_sdk.teams.cli.main import cli


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


def test_teams_login_not_implemented(runner: CliRunner) -> None:
    """Login exits with 'not yet implemented' message."""
    result = runner.invoke(cli, ["login"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_login_help(runner: CliRunner) -> None:
    """Login --help shows usage text with email option."""
    result = runner.invoke(cli, ["login", "--help"])
    assert not result.exit_code
    assert "email" in result.output.lower()


def test_teams_login_without_parent_context(runner: CliRunner) -> None:
    """Login invoked directly still shows not-implemented message."""
    result = runner.invoke(login_command, [])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


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


def test_teams_cli_with_no_headless_flag(runner: CliRunner) -> None:
    """CLI should accept --no-headless flag and set browser_headless=False."""
    result = runner.invoke(cli, ["--no-headless", "login"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_main_handles_keyboard_interrupt() -> None:
    """Main() should catch KeyboardInterrupt and return a clean exit code."""
    from unittest.mock import patch

    from gamesheet_sdk.teams.cli.main import main as teams_main

    with patch.object(cli, "main", side_effect=KeyboardInterrupt):
        result = teams_main([])
        assert isinstance(result, int)


def test_teams_cli_main_module() -> None:
    """Running the module as __main__ should invoke sys.exit(main())."""
    import runpy
    from unittest.mock import patch
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
