"""Coverage tests for roster players create command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import players_group


def test_roster_players_create_coverage() -> None:
    """Ensure players create command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = "8043169"
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._create_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.cli.commands.roster.render_get_command"),
    ):
        result = runner.invoke(
            players_group,
            [
                "create",
                "--first-name",
                "AUSTIN",
                "--last-name",
                "ADAMSKY",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
        assert "created successfully" in result.output.lower()


def test_roster_players_create_error_handling() -> None:
    """Ensure players create command error path is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._create_player_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            players_group,
            [
                "create",
                "--first-name",
                "AUSTIN",
                "--last-name",
                "ADAMSKY",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 1
        assert "error creating player" in result.output.lower()
