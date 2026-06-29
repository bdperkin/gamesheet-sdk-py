# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for games get command."""

from __future__ import annotations

from unittest.mock import Mock, patch

from click.testing import CliRunner

from gamesheet_sdk.config import Config
from gamesheet_sdk.games import Game, TeamInfo


def test_games_get(runner: CliRunner) -> None:
    """The games get command should retrieve a single game."""
    with (
        patch("gamesheet_sdk.cli.commands.games._get_game_action") as mock_action,
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
        # Invoke via the CLI to exercise the full games_group -> games_get_command path
        # but can't use "games get" due to ResourceGroup alias conflict, so invoke function directly
        from gamesheet_sdk.cli.commands.games import games_get_command

        # Use a real Config object to avoid Mock serialization issues
        config = Config(base_url="https://test.example")
        ctx = Mock()
        ctx.obj = {"config": config, "season_id": "15020"}
        result = runner.invoke(games_get_command, ["--game-id", "12345"], obj=ctx.obj)
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_games_get_with_fields(runner: CliRunner) -> None:
    """The games get command should support --fields and JSON format."""
    with (
        patch("gamesheet_sdk.cli.commands.games._get_game_action") as mock_action,
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
        from gamesheet_sdk.cli.commands.games import games_get_command

        config = Config(base_url="https://test.example")
        ctx = Mock()
        ctx.obj = {"config": config, "season_id": "15020"}
        result = runner.invoke(
            games_get_command,
            [
                "--game-id",
                "12345",
                "--fields",
                "id",
                "--format",
                "json",
            ],
            obj=ctx.obj,
        )
        assert not result.exit_code
        assert result.output


def test_games_get_empty_fields(runner: CliRunner) -> None:
    """The games get command should handle empty fields spec."""
    with (
        patch("gamesheet_sdk.cli.commands.games._get_game_action") as mock_action,
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
        from gamesheet_sdk.cli.commands.games import games_get_command

        config = Config(base_url="https://test.example")
        ctx = Mock()
        ctx.obj = {"config": config, "season_id": "15020"}
        result = runner.invoke(
            games_get_command,
            ["--game-id", "12345", "--fields", ","],
            obj=ctx.obj,
        )
        assert not result.exit_code
        assert result.output


def test_games_scheduled_get_coverage() -> None:
    """Ensure games scheduled get command body is covered."""
    from unittest.mock import MagicMock

    from gamesheet_sdk.cli.commands.games import games_group

    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=MagicMock(
                model_dump=lambda **__kw: {
                    "id": 123,
                    "status": "scheduled",
                    "date": "2024-01-01",
                },
            ),
        ),
        patch("gamesheet_sdk.cli.commands.games.render_get_command"),
    ):
        result = runner.invoke(
            games_group,
            [
                "--season-id",
                "100",
                "scheduled",
                "get",
                "--game-id",
                "123",
                "-F",
                "json",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
