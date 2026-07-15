# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams command group."""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli


def test_teams_group_has_help_option(runner: CliRunner) -> None:
    """The teams group should accept -h and --help."""
    result_short = runner.invoke(cli, ["teams", "-h"])
    assert not result_short.exit_code
    assert "teams" in result_short.output.lower()
    result_long = runner.invoke(cli, ["teams", "--help"])
    assert not result_long.exit_code
    assert "teams" in result_short.output.lower()


def test_teams_missing_season_id_shows_error(runner: CliRunner) -> None:
    """Calling 'teams list' without a season ID should show an error."""
    result = runner.invoke(cli, ["teams", "list"])
    assert result.exit_code == 2  # Usage error
    assert "season-id" in result.output.lower() or "missing option" in result.output.lower()
