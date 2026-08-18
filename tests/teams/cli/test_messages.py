# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for messages CLI command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.teams.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_messages_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams messages --help` shows usage and options."""
    result = runner.invoke(cli, ["messages", "--help"])
    assert result.exit_code == 0
    assert "messages" in result.output.lower()


def test_messages_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams messages` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["messages"])
    assert result.exit_code == 1
    assert "messages is not yet implemented" in result.output
