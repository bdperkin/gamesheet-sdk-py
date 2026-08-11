# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the gamesheet-admin CLI entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk import __version__
from gamesheet_sdk.admin.cli import main
from gamesheet_sdk.admin.cli.commands.completion import completion_command
from gamesheet_sdk.admin.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_admin_cli_help(runner: CliRunner) -> None:
    """--help shows usage text and exits cleanly."""
    result = runner.invoke(cli, ["--help"])
    assert not result.exit_code
    assert "gamesheet-admin" in result.output.lower() or "admin" in result.output.lower()


def test_admin_cli_version(runner: CliRunner) -> None:
    """--version prints the package version."""
    result = runner.invoke(cli, ["--version"])
    assert not result.exit_code
    assert __version__ in result.output


def test_admin_cli_exits_zero_on_no_args() -> None:
    """Main([]) returns 0 (shows help)."""
    assert not main([])


def test_admin_login_help(runner: CliRunner) -> None:
    """Login --help shows usage text."""
    result = runner.invoke(cli, ["login", "--help"])
    assert not result.exit_code
    assert "email" in result.output.lower()


def test_admin_completion_bash(runner: CliRunner) -> None:
    """Completion bash emits a completion script."""
    result = runner.invoke(cli, ["completion", "bash"])
    assert not result.exit_code
    assert "complete" in result.output or "_GAMESHEET_ADMIN_COMPLETE" in result.output


def test_admin_completion_zsh(runner: CliRunner) -> None:
    """Completion zsh emits a completion script."""
    result = runner.invoke(cli, ["completion", "zsh"])
    assert not result.exit_code
    assert "compdef" in result.output or "_GAMESHEET_ADMIN_COMPLETE" in result.output


def test_admin_completion_fish(runner: CliRunner) -> None:
    """Completion fish emits a completion script."""
    result = runner.invoke(cli, ["completion", "fish"])
    assert not result.exit_code
    assert "complete" in result.output or "_GAMESHEET_ADMIN_COMPLETE" in result.output


def test_admin_completion_without_parent_context(runner: CliRunner) -> None:
    """Completion invoked directly (no parent) exits cleanly with no output."""
    result = runner.invoke(completion_command, ["bash"])
    assert not result.exit_code
    assert not result.output


def test_admin_cli_main_module() -> None:
    """Running the module as __main__ should invoke sys.exit(main())."""
    import runpy
    import warnings
    from unittest.mock import patch

    import pytest

    with (
        patch("sys.argv", ["gamesheet-admin", "--version"]),
        warnings.catch_warnings(),
    ):
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(SystemExit, match="0"):
            runpy.run_module(
                "gamesheet_sdk.admin.cli.main",
                run_name="__main__",
            )
