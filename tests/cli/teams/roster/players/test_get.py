# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for teams roster players get command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

# pylint: disable=import-error,no-name-in-module
from gamesheet_sdk.cli.commands.teams_roster_players import (  # type: ignore[import-not-found]
    teams_roster_players_group,
)
from tests.helpers import PLAYER_ID, SEASON_ID, TEAM_ID


def test_teams_roster_players_get_coverage() -> None:
    """Ensure teams roster players get command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = PLAYER_ID
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_players._get_team_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.cli.commands.teams_roster_players.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            [
                "get",
                "--player-id",
                PLAYER_ID,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID, "team_id": TEAM_ID},
        )
        assert not result.exit_code
