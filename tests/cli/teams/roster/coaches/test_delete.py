# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams roster coaches delete command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster import teams_roster_coaches_group


def test_teams_roster_coaches_delete_coverage(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster coaches delete command body is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._delete_team_coach_action",
        ) as mock_delete,
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "delete",
                "--coach-id",
                "1879939",
                "--force",
            ],
            obj={"config": mock_config, "season_id": "15020", "team_id": "523675"},
        )
        assert not result.exit_code
        assert "deleted successfully" in result.output
        mock_delete.assert_called_once_with(
            mock_session,
            "15020",
            "523675",
            "1879939",
        )


def test_teams_roster_coaches_delete_error_handling(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster coaches delete command error path is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._delete_team_coach_action",
            side_effect=Exception("Delete failed"),
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "delete",
                "--coach-id",
                "1879939",
                "--force",
            ],
            obj={"config": mock_config, "season_id": "15020", "team_id": "523675"},
        )
        assert result.exit_code == 1
        assert "Error deleting coach" in result.output


def test_teams_roster_coaches_delete_requires_confirmation(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test that delete requires confirmation without --force."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._delete_team_coach_action",
        ) as mock_delete,
    ):
        # Answer 'n' to confirmation
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "delete",
                "--coach-id",
                "1879939",
            ],
            obj={"config": mock_config, "season_id": "15020", "team_id": "523675"},
            input="n\n",
        )
        assert result.exit_code == 1
        mock_delete.assert_not_called()
