"""Coverage tests for teams roster players create command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster import teams_roster_players_group


def test_teams_roster_players_create_coverage() -> None:
    """Ensure teams roster players create command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = "8043169"
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._create_team_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.cli.commands.teams_roster.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "create",
                "--first-name",
                "AUSTIN",
                "--last-name",
                "ADAMSKY",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert not result.exit_code
        assert "added to team" in result.output.lower()


def test_teams_roster_players_create_error_handling() -> None:
    """Ensure teams roster players create command error path is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._create_team_player_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "create",
                "--first-name",
                "AUSTIN",
                "--last-name",
                "ADAMSKY",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert result.exit_code == 1
        assert "error creating player" in result.output.lower()
