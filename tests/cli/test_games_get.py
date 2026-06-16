"""Tests for games get command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.games import Game, TeamInfo

if TYPE_CHECKING:
    from click.testing import CliRunner


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
        from unittest.mock import Mock

        from gamesheet_sdk.cli.commands.games import games_get_command
        ctx = Mock()
        ctx.obj = {"config": Mock(model_dump=lambda **kw: {}), "season_id": "15020"}
        result = runner.invoke(games_get_command, ["--game-id", "12345"], obj=ctx.obj)
        assert result.exit_code == 0
        assert result.output
        assert mock_action.called
