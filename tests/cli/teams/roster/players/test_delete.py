# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams roster players delete command."""

from __future__ import annotations

from unittest.mock import MagicMock

# pylint: disable=import-error,no-name-in-module
from gamesheet_sdk.cli.commands.teams_roster_players import (  # type: ignore[import-not-found]
    teams_roster_players_group,
)
from tests.cli.teams.roster.conftest import run_roster_delete_test
from tests.helpers import (
    PLAYER_ID_QUATERNARY,
    SEASON_ID,
    TEAM_ID_SECONDARY,
)


def test_teams_roster_players_delete_coverage(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster players delete command body is covered."""
    exit_code, output, mock_delete = run_roster_delete_test(
        group=teams_roster_players_group,
        resource_type="player",
        resource_id=PLAYER_ID_QUATERNARY,
        action_path="gamesheet_sdk.cli.commands.teams_roster_players._delete_team_player_action",
        # pylint: disable=duplicate-code
        season_id=SEASON_ID,
        team_id=TEAM_ID_SECONDARY,
        session=mock_session,
        config=mock_config,
        with_force=True,
    )
    assert not exit_code
    assert "deleted successfully" in output
    mock_delete.assert_called_once_with(
        mock_session,
        SEASON_ID,
        TEAM_ID_SECONDARY,
        # pylint: enable=duplicate-code
        PLAYER_ID_QUATERNARY,
    )


def test_teams_roster_players_delete_error_handling(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster players delete command error path is covered."""
    exit_code, output, _ = run_roster_delete_test(
        group=teams_roster_players_group,
        resource_type="player",
        resource_id=PLAYER_ID_QUATERNARY,
        action_path="gamesheet_sdk.cli.commands.teams_roster_players._delete_team_player_action",
        season_id=SEASON_ID,
        team_id=TEAM_ID_SECONDARY,
        session=mock_session,
        config=mock_config,
        with_force=True,
        should_fail=True,
        error_message="Delete failed",
    )
    assert exit_code == 1
    assert "Error deleting player" in output


def test_teams_roster_players_delete_requires_confirmation(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test that delete requires confirmation without --force."""
    exit_code, _, mock_delete = run_roster_delete_test(
        group=teams_roster_players_group,
        resource_type="player",
        resource_id=PLAYER_ID_QUATERNARY,
        action_path="gamesheet_sdk.cli.commands.teams_roster_players._delete_team_player_action",
        season_id=SEASON_ID,
        team_id=TEAM_ID_SECONDARY,
        session=mock_session,
        config=mock_config,
        with_force=False,
        input_text="n\n",
    )
    assert exit_code == 1
    mock_delete.assert_not_called()
