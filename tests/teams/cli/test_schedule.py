# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule CLI command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.teams.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_schedule_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "--help"])
    assert result.exit_code == 0
    assert "schedule" in result.output.lower()
    assert "export" in result.output
    assert "subscribe" in result.output
    assert "practices" in result.output
    assert "events" in result.output
    assert "games" in result.output


def test_schedule_export_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule export` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "export"])
    assert result.exit_code == 1
    assert "schedule export is not yet implemented" in result.output


def test_schedule_subscribe_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "subscribe"])
    assert result.exit_code == 1
    assert "schedule subscribe is not yet implemented" in result.output


def test_schedule_practices_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "practices"])
    assert result.exit_code == 1
    assert "schedule practices is not yet implemented" in result.output


def test_schedule_events_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "events"])
    assert result.exit_code == 1
    assert "schedule events is not yet implemented" in result.output


def test_schedule_games_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "games"])
    assert result.exit_code == 1
    assert "schedule games is not yet implemented" in result.output
