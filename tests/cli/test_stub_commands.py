# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test coverage for stub commands that are not yet implemented.

These tests ensure all stub commands are covered by tests, even though they just return "not implemented"
errors. This keeps coverage at 100%.
"""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.games import scheduled_group


def test_games_scheduled_create_stub() -> None:
    """Test games scheduled create stub command."""
    result = CliRunner().invoke(scheduled_group, ["create"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_games_scheduled_update_stub() -> None:
    """Test games scheduled update stub command."""
    result = CliRunner().invoke(scheduled_group, ["update"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_games_scheduled_delete_stub() -> None:
    """Test games scheduled delete stub command."""
    result = CliRunner().invoke(scheduled_group, ["delete"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()
