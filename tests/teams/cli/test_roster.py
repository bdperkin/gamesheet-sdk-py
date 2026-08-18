# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster CLI command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.teams.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_roster_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams roster --help` shows usage and options."""
    result = runner.invoke(cli, ["roster", "--help"])
    assert result.exit_code == 0
    assert "roster" in result.output.lower()
    assert "import" in result.output
    assert "coaches" in result.output
    assert "players" in result.output


def test_roster_import_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams roster import` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["roster", "import"])
    assert result.exit_code == 1
    assert "roster import is not yet implemented" in result.output


def test_roster_coaches_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams roster coaches` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["roster", "coaches"])
    assert result.exit_code == 1
    assert "roster coaches is not yet implemented" in result.output


def test_roster_players_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams roster players` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["roster", "players"])
    assert result.exit_code == 1
    assert "roster players is not yet implemented" in result.output
