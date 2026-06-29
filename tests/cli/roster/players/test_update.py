# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster players update command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import players_group


def test_roster_players_update_valueerror_handling() -> None:
    """Ensure roster players update command handles ValueError from action."""
    from typing import Any

    runner = CliRunner()

    def raise_value_error(*_args: Any, **_kwargs: Any) -> None:
        msg = "Test validation error"
        raise ValueError(msg)

    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._update_player_action",
            side_effect=raise_value_error,
        ),
    ):
        result = runner.invoke(
            players_group,
            [
                "update",
                "--player-id",
                "8043169",
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 1
        assert "error:" in result.output.lower()
        assert "test validation error" in result.output.lower()
