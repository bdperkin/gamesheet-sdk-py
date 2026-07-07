# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster players assign/unassign commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster_players import players_group
from tests.fixtures.constants import TEST_ERROR_GENERIC
from tests.helpers import PLAYER_ID, SEASON_ID, TEAM_ID


def test_roster_players_assign_coverage() -> None:
    """Ensure players assign command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = PLAYER_ID
    with (
        patch("gamesheet_sdk.cli.commands.roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster_players._assign_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.cli.shared.render_get_command"),
    ):
        result = runner.invoke(
            players_group,
            [
                "assign",
                "--player-id",
                PLAYER_ID,
                "--team-id",
                TEAM_ID,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "assigned to team" in result.output.lower()


def test_roster_players_assign_error_handling() -> None:
    """Ensure players assign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster_players._assign_player_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            players_group,
            [
                "assign",
                "--player-id",
                PLAYER_ID,
                "--team-id",
                TEAM_ID,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error assigning player" in result.output.lower()


def test_roster_players_unassign_coverage() -> None:
    """Ensure players unassign command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster_players.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.roster_players._unassign_player_action"),
    ):
        result = runner.invoke(
            players_group,
            [
                "unassign",
                "--player-id",
                PLAYER_ID,
                "--team-id",
                TEAM_ID,
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "unassigned from team" in result.output.lower()


def test_roster_players_unassign_error_handling() -> None:
    """Ensure players unassign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster_players._unassign_player_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            players_group,
            [
                "unassign",
                "--player-id",
                PLAYER_ID,
                "--team-id",
                TEAM_ID,
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error unassigning player" in result.output.lower()
