# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster coaches get command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.teams_roster_coaches import (
    teams_roster_coaches_group,
)
from tests.helpers import COACH_ID_PRIMARY, SEASON_ID, TEAM_ID


def test_teams_roster_coaches_get_coverage() -> None:
    """Ensure teams roster coaches get command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_PRIMARY
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches._get_team_coach_action",
            return_value=mock_coach,
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.render_get_command",
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "get",
                "--coach-id",
                COACH_ID_PRIMARY,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert not result.exit_code
