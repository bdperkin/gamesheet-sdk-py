# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster coaches list command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands import teams_roster_coaches_group
from tests.helpers import SEASON_ID, TEAM_ID


def test_teams_roster_coaches_list_coverage() -> None:
    """Ensure teams roster coaches list command body is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.run_action_or_exit",
            return_value=[],
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.render_list_command",
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert not result.exit_code
