# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster coaches assign/unassign commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.roster_coaches import coaches_group
from tests.fixtures.constants import TEST_ERROR_GENERIC
from tests.helpers import COACH_ID_PRIMARY, SEASON_ID, TEAM_ID


def test_roster_coaches_assign_coverage() -> None:
    """Ensure coaches assign command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = COACH_ID_PRIMARY
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._assign_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.admin.cli.shared.render_get_command"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "assign",
                "--coach-id",
                COACH_ID_PRIMARY,
                "--team-id",
                TEAM_ID,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "assigned to team" in result.output.lower()


def test_roster_coaches_assign_error_handling() -> None:
    """Ensure coaches assign command error handling is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._assign_coach_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "assign",
                "--coach-id",
                COACH_ID_PRIMARY,
                "--team-id",
                TEAM_ID,
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error assigning coach" in result.output.lower()


def test_roster_coaches_unassign_coverage() -> None:
    """Ensure coaches unassign command body is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session",
        ),
        patch("gamesheet_sdk.admin.cli.commands.roster_coaches._unassign_coach_action"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "unassign",
                "--coach-id",
                COACH_ID_PRIMARY,
                "--team-id",
                TEAM_ID,
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
        assert "unassigned from team" in result.output.lower()


def test_roster_coaches_unassign_error_handling() -> None:
    """Ensure coaches unassign command error handling is covered."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._unassign_coach_action",
            side_effect=Exception(TEST_ERROR_GENERIC),
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "unassign",
                "--coach-id",
                COACH_ID_PRIMARY,
                "--team-id",
                TEAM_ID,
            ],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert result.exit_code == 1
        assert "error unassigning coach" in result.output.lower()
