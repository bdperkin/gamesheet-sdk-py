"""Tests for referees command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_referees_group_has_help_option(runner: CliRunner) -> None:
    """The referees group should accept -h and --help."""
    result_short = runner.invoke(cli, ["referees", "-h"])
    assert result_short.exit_code == 0
    assert "referees" in result_short.output.lower()
    result_long = runner.invoke(cli, ["referees", "--help"])
    assert result_long.exit_code == 0
    assert "referees" in result_short.output.lower()


def test_referees_missing_season_id_shows_error(runner: CliRunner) -> None:
    """Calling 'referees list' without a season ID should show an error."""
    result = runner.invoke(cli, ["referees", "list"])
    assert result.exit_code == 2  # Usage error
    assert "season-id" in result.output.lower() or "missing option" in result.output.lower()
