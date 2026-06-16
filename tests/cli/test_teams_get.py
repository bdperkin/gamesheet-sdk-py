"""Tests for teams get command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.teams import Team

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_teams_get(runner: CliRunner) -> None:
    """The teams get command should retrieve a single team."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id="15020",
            title="Test Team",
            roster={"players": [], "coaches": []},
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["teams", "get", "--season-id", "15020", "--team-id", "401"])
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_teams_get_with_fields(runner: CliRunner) -> None:
    """The teams get command should support --fields and JSON format."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id="15020",
            title="Test Team",
            roster={"players": [], "coaches": []},
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "teams",
                "get",
                "--season-id",
                "15020",
                "--team-id",
                "401",
                "--fields",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_teams_get_empty_fields(runner: CliRunner) -> None:
    """The teams get command should handle empty fields spec."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id="15020",
            title="Test Team",
            roster={"players": [], "coaches": []},
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            ["teams", "get", "--season-id", "15020", "--team-id", "401", "--fields", ","],
        )
        assert not result.exit_code
        assert result.output
