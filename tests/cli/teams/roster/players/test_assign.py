# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster players assign/unassign commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster import teams_roster_players_group


def test_teams_roster_players_assign_coverage() -> None:
    """Ensure teams roster players assign command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = "8043169"
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._assign_team_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.cli.shared.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "assign",
                "--player-id",
                "8043169",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert not result.exit_code
        assert "assigned to team" in result.output.lower()


def test_teams_roster_players_assign_error_handling() -> None:
    """Ensure teams roster players assign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._assign_team_player_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "assign",
                "--player-id",
                "8043169",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert result.exit_code == 1
        assert "error assigning player" in result.output.lower()


def test_teams_roster_players_unassign_coverage() -> None:
    """Ensure teams roster players unassign command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.teams_roster._unassign_team_player_action"),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "unassign",
                "--player-id",
                "8043169",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert not result.exit_code
        assert "unassigned from team" in result.output.lower()


def test_teams_roster_players_unassign_error_handling() -> None:
    """Ensure teams roster players unassign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._unassign_team_player_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "unassign",
                "--player-id",
                "8043169",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert result.exit_code == 1
        assert "error unassigning player" in result.output.lower()
