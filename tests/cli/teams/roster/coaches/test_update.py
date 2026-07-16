# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster coaches update command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.teams_roster_coaches import (
    teams_roster_coaches_group,
)
from tests.fixtures.constants import TEST_ERROR_GENERIC
from tests.helpers import COACH_ID_SECONDARY, SEASON_ID, TEAM_ID


def test_teams_roster_coaches_update_coverage() -> None:
    """Ensure teams roster coaches update command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_SECONDARY
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches._update_team_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.admin.cli.commands.teams_roster_coaches.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "update",
                "--coach-id",
                COACH_ID_SECONDARY,
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert not result.exit_code
        assert "coach 1879938 updated successfully" in result.output.lower()


def test_teams_roster_coaches_update_error_handling() -> None:
    """Ensure teams roster coaches update command error path is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches._update_team_coach_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "update",
                "--coach-id",
                COACH_ID_SECONDARY,
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert result.exit_code == 1
        assert "error updating coach" in result.output.lower()
