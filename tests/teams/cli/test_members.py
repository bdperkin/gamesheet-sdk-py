# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for members CLI command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.teams.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_members_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams members --help` shows usage and options."""
    result = runner.invoke(cli, ["members", "--help"])
    assert result.exit_code == 0
    assert "members" in result.output.lower()
    assert "invite" in result.output


def test_members_invite_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams members invite --help` shows invite subcommands."""
    result = runner.invoke(cli, ["members", "invite", "--help"])
    assert result.exit_code == 0
    assert "invite" in result.output.lower()
    assert "staff" in result.output
    assert "follower" in result.output


def test_members_invite_staff_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams members invite staff` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["members", "invite", "staff"])
    assert result.exit_code == 1
    assert "members invite staff is not yet implemented" in result.output


def test_members_invite_follower_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams members invite follower` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["members", "invite", "follower"])
    assert result.exit_code == 1
    assert "members invite follower is not yet implemented" in result.output
