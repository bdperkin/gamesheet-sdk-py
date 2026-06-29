# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster coaches update command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import coaches_group


def test_roster_coaches_update_coverage() -> None:
    """Ensure roster coaches update command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = "1879938"
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._update_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.cli.commands.roster.render_get_command"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "update",
                "--coach-id",
                "1879938",
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
        assert "coach 1879938 updated successfully" in result.output.lower()


def test_roster_coaches_update_valueerror_handling() -> None:
    """Ensure roster coaches update command handles ValueError from action."""
    from typing import Any

    runner = CliRunner()

    def raise_value_error(*_args: Any, **_kwargs: Any) -> None:
        msg = "Test validation error"
        raise ValueError(msg)

    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._update_coach_action",
            side_effect=raise_value_error,
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "update",
                "--coach-id",
                "1879938",
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
