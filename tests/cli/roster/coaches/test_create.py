# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster coaches create command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import coaches_group
from tests.helpers import (
    COACH_FIRST_NAME,
    COACH_ID_PRIMARY,
    COACH_LAST_NAME,
    SEASON_ID,
)


def test_roster_coaches_create_coverage() -> None:
    """Ensure coaches create command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_PRIMARY
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._create_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.cli.commands.roster.render_get_command"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "create",
                "--first-name",
                COACH_FIRST_NAME,
                "--last-name",
                COACH_LAST_NAME,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "created successfully" in result.output.lower()


def test_roster_coaches_create_error_handling() -> None:
    """Ensure coaches create command error path is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._create_coach_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "create",
                "--first-name",
                COACH_FIRST_NAME,
                "--last-name",
                COACH_LAST_NAME,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error creating coach" in result.output.lower()
