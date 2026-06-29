# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for games list commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.games import (
    brackets_group,
    completed_group,
    scheduled_group,
)


def test_games_scheduled_list_coverage() -> None:
    """Ensure scheduled list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render_list_command"),
    ):
        result = runner.invoke(
            scheduled_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code


def test_games_completed_list_coverage() -> None:
    """Ensure completed list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render_list_command"),
    ):
        result = runner.invoke(
            completed_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code


def test_games_brackets_list_coverage() -> None:
    """Ensure brackets list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render_list_command"),
    ):
        result = runner.invoke(
            brackets_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
