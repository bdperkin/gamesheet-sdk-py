"""Tests for roster players get command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.roster import Player

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_players_get(runner: CliRunner) -> None:
    """The players get command should retrieve a single player."""
    with (
        patch("gamesheet_sdk.cli.commands.roster._get_player_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id="501",
            season_id="15020",
            first_name="John",
            last_name="Doe",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli, ["roster", "--season-id", "15020", "players", "get", "--player-id", "501"],
        )
        assert result.exit_code == 0
        assert result.output
        assert mock_action.called


def test_players_get_with_fields(runner: CliRunner) -> None:
    """The players get command should support --fields and JSON format."""
    with (
        patch("gamesheet_sdk.cli.commands.roster._get_player_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id="501",
            season_id="15020",
            first_name="John",
            last_name="Doe",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli, ["roster", "--season-id", "15020", "players", "get",
                  "--player-id", "501", "--fields", "id", "--format", "json"],
        )
        assert result.exit_code == 0
        assert result.output


def test_players_get_empty_fields(runner: CliRunner) -> None:
    """The players get command should handle empty fields spec."""
    with (
        patch("gamesheet_sdk.cli.commands.roster._get_player_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id="501",
            season_id="15020",
            first_name="John",
            last_name="Doe",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli, ["roster", "--season-id", "15020", "players", "get", "--player-id", "501", "--fields", ","],
        )
        assert result.exit_code == 0
        assert result.output
