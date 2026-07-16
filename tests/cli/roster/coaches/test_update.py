# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster coaches update command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.roster_coaches import coaches_group
from tests.fixtures.constants import TEST_ERROR_VALIDATION
from tests.helpers import COACH_ID_SECONDARY, SEASON_ID


def test_roster_coaches_update_coverage() -> None:
    """Ensure roster coaches update command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_SECONDARY
    with (
        patch("gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._update_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.admin.cli.commands.roster_coaches.render_get_command"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "update",
                "--coach-id",
                COACH_ID_SECONDARY,
                "--first-name",
                "UPDATED",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "coach 1879938 updated successfully" in result.output.lower()


def test_roster_coaches_update_valueerror_handling() -> None:
    """Ensure roster coaches update command handles ValueError from action."""
    from typing import Any

    runner = CliRunner()

    def raise_value_error(*_args: Any, **_kwargs: Any) -> None:
        raise ValueError(TEST_ERROR_VALIDATION)

    with (
        patch("gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._update_coach_action",
            side_effect=raise_value_error,
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "update",
                "--coach-id",
                COACH_ID_SECONDARY,
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
