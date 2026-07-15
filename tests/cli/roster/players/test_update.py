# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster players update command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.roster_players import players_group
from tests.fixtures.constants import TEST_ERROR_VALIDATION
from tests.helpers import PLAYER_ID, SEASON_ID


def test_roster_players_update_coverage() -> None:
    """Ensure roster players update command body is covered."""
    runner = CliRunner()
    mock_player = MagicMock()
    mock_player.id = PLAYER_ID
    with (
        patch("gamesheet_sdk.admin.cli.commands.roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_players._update_player_action",
            return_value=mock_player,
        ),
        patch("gamesheet_sdk.admin.cli.commands.roster_players.render_get_command"),
    ):
        result = runner.invoke(
            players_group,
            [
                "update",
                "--player-id",
                PLAYER_ID,
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert f"player {PLAYER_ID} updated successfully" in result.output.lower()


def test_roster_players_update_valueerror_handling() -> None:
    """Ensure roster players update command handles ValueError from action."""
    from typing import Any

    runner = CliRunner()

    def raise_value_error(*_args: Any, **_kwargs: Any) -> None:
        raise ValueError(TEST_ERROR_VALIDATION)

    with (
        patch("gamesheet_sdk.admin.cli.commands.roster_players.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_players._update_player_action",
            side_effect=raise_value_error,
        ),
    ):
        result = runner.invoke(
            players_group,
            [
                "update",
                "--player-id",
                PLAYER_ID,
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error:" in result.output.lower()
        assert "test validation error" in result.output.lower()
