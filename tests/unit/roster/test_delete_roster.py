# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for delete_coach and delete_player functions."""

from __future__ import annotations

from unittest.mock import MagicMock

from gamesheet_sdk.roster import (
    delete_coach,
    delete_player,
    delete_team_coach,
    delete_team_player,
)


def test_delete_coach_success(mock_session: MagicMock) -> None:
    """Test successful coach deletion."""
    delete_coach(mock_session, "15020", "1879938")
    mock_session.delete.assert_called_once()
    call_args = mock_session.delete.call_args
    assert "/api/seasons/15020/coaches/1879938" in call_args[0][0]


def test_delete_player_success(mock_session: MagicMock) -> None:
    """Test successful player deletion."""
    delete_player(mock_session, "15020", "8116303")
    mock_session.delete.assert_called_once()
    call_args = mock_session.delete.call_args
    assert "/api/seasons/15020/players/8116303" in call_args[0][0]


def test_delete_team_coach_success(mock_session: MagicMock) -> None:
    """Test successful team coach deletion (unassign + delete)."""
    from unittest.mock import patch

    with (
        patch("gamesheet_sdk.roster.coaches.unassign_coach") as mock_unassign,
        patch("gamesheet_sdk.roster.coaches.delete_coach") as mock_delete,
    ):
        delete_team_coach(mock_session, "15020", "523675", "1879939")
        mock_unassign.assert_called_once_with(
            mock_session,
            "15020",
            "1879939",
            "523675",
        )
        mock_delete.assert_called_once_with(mock_session, "15020", "1879939")


def test_delete_team_coach_not_on_roster(mock_session: MagicMock) -> None:
    """Test team coach deletion when coach is not on team roster."""
    from unittest.mock import patch

    from gamesheet_sdk.exceptions import GameSheetError

    with (
        patch(
            "gamesheet_sdk.roster.coaches.unassign_coach",
            side_effect=GameSheetError("Coach not found on team"),
        ),
        patch("gamesheet_sdk.roster.coaches.delete_coach") as mock_delete,
    ):
        # Should still delete even if unassign fails
        delete_team_coach(mock_session, "15020", "523675", "1879939")
        mock_delete.assert_called_once_with(mock_session, "15020", "1879939")


def test_delete_team_player_success(mock_session: MagicMock) -> None:
    """Test successful team player deletion (unassign + delete)."""
    from unittest.mock import patch

    with (
        patch("gamesheet_sdk.roster.players.unassign_player") as mock_unassign,
        patch("gamesheet_sdk.roster.players.delete_player") as mock_delete,
    ):
        delete_team_player(mock_session, "15020", "523675", "8116321")
        mock_unassign.assert_called_once_with(
            mock_session,
            "15020",
            "8116321",
            "523675",
        )
        mock_delete.assert_called_once_with(mock_session, "15020", "8116321")


def test_delete_team_player_not_on_roster(mock_session: MagicMock) -> None:
    """Test team player deletion when player is not on team roster."""
    from unittest.mock import patch

    from gamesheet_sdk.exceptions import GameSheetError

    with (
        patch(
            "gamesheet_sdk.roster.players.unassign_player",
            side_effect=GameSheetError("Player not found on team"),
        ),
        patch("gamesheet_sdk.roster.players.delete_player") as mock_delete,
    ):
        # Should still delete even if unassign fails
        delete_team_player(mock_session, "15020", "523675", "8116321")
        mock_delete.assert_called_once_with(mock_session, "15020", "8116321")
