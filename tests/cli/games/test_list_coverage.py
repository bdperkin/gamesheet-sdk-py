# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for games list commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.games_brackets import brackets_group
from gamesheet_sdk.admin.cli.commands.games_completed import completed_group
from gamesheet_sdk.admin.cli.commands.games_scheduled import scheduled_group
from tests.helpers import SEASON_ID


def test_games_scheduled_list_coverage() -> None:
    """Ensure scheduled list command body is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_list_command"),
    ):
        result = runner.invoke(
            scheduled_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code


def test_games_completed_list_coverage() -> None:
    """Ensure completed list command body is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.games_completed.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.games_completed.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.admin.cli.commands.games_completed.render_list_command"),
    ):
        result = runner.invoke(
            completed_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code


def test_games_brackets_list_coverage() -> None:
    """Ensure brackets list command returns not implemented error."""
    result = CliRunner().invoke(
        brackets_group,
        ["list", "-F", "json"],
        obj={"config": MagicMock(), "season_id": SEASON_ID},
    )
    assert result.exit_code == 1  # Not implemented
    assert "not yet implemented" in result.output.lower()
