# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for completed games get CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.config import Config
from gamesheet_sdk.games import Game, TeamInfo
from tests.helpers import SEASON_ID, TEAM_ID


def test_games_get(runner: CliRunner) -> None:
    """The games completed get command should retrieve a single game."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.games._get_completed_game_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Game(
            id=12345,
            status="completed",
            date="2024-06-15",
            time="19:00",
            location="Arena A",
            visitor=TeamInfo(id=101, title="Team A"),
            home=TeamInfo(id=102, title="Team B"),
            visitor_score=3,
            home_score=2,
        )
        from gamesheet_sdk.cli.commands.games import completed_get_command

        # Use a real Config object to avoid Mock serialization issues
        config = Config(base_url="https://test.example")
        # completed_get_command expects ctx.obj to be {"config": config, "season_id": season_id}
        ctx_obj = {"config": config, "season_id": SEASON_ID}
        result = runner.invoke(
            completed_get_command,
            ["--game-id", TEAM_ID],
            obj=ctx_obj,
        )
        assert not result.exit_code
        assert result.output
        assert mock_action.called



def test_games_get_with_fields(runner: CliRunner) -> None:
    """The games completed get command should support --fields and JSON format."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.games._get_completed_game_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Game(
            id=12345,
            status="completed",
            date="2024-06-15",
            time="19:00",
            location="Arena A",
            visitor=TeamInfo(id=101, title="Team A"),
            home=TeamInfo(id=102, title="Team B"),
            visitor_score=3,
            home_score=2,
        )
        from gamesheet_sdk.cli.commands.games import completed_get_command

        config = Config(base_url="https://test.example")
        ctx_obj = {"config": config, "season_id": SEASON_ID}
        result = runner.invoke(
            completed_get_command,
            [
                "--game-id",
                TEAM_ID,
                "--fields",
                "id",
                "--format",
                "json",
            ],
            obj=ctx_obj,
        )
        assert not result.exit_code
        assert result.output



def test_games_get_empty_fields(runner: CliRunner) -> None:
    """The games completed get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.games._get_completed_game_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Game(
            id=12345,
            status="completed",
            date="2024-06-15",
            time="19:00",
            location="Arena A",
            visitor=TeamInfo(id=101, title="Team A"),
            home=TeamInfo(id=102, title="Team B"),
            visitor_score=3,
            home_score=2,
        )
        from gamesheet_sdk.cli.commands.games import completed_get_command

        config = Config(base_url="https://test.example")
        ctx_obj = {"config": config, "season_id": SEASON_ID}
        result = runner.invoke(
            completed_get_command,
            ["--game-id", TEAM_ID, "--fields", ","],
            obj=ctx_obj,
        )
        assert not result.exit_code
        assert result.output
