# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster coaches create command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster_coaches import teams_roster_coaches_group
from tests.fixtures.constants import TEST_ERROR_GENERIC
from tests.helpers import (
    COACH_FIRST_NAME,
    COACH_ID_PRIMARY,
    COACH_LAST_NAME,
    SEASON_ID,
    TEAM_ID,
)


def test_teams_roster_coaches_create_coverage() -> None:
    """Ensure teams roster coaches create command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_PRIMARY
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_coaches._create_team_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.cli.commands.teams_roster_coaches.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "create",
                "--first-name",
                COACH_FIRST_NAME,
                "--last-name",
                COACH_LAST_NAME,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert not result.exit_code
        assert "added to team" in result.output.lower()


def test_teams_roster_coaches_create_error_handling() -> None:
    """Ensure teams roster coaches create command error path is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_coaches._create_team_coach_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "create",
                "--first-name",
                COACH_FIRST_NAME,
                "--last-name",
                COACH_LAST_NAME,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert result.exit_code == 1
        assert "error creating coach" in result.output.lower()
