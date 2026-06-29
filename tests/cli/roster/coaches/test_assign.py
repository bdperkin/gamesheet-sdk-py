# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster coaches assign/unassign commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import coaches_group


def test_roster_coaches_assign_coverage() -> None:
    """Ensure coaches assign command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = "1868550"
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._assign_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.cli.shared.render_get_command"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "assign",
                "--coach-id",
                "1868550",
                # pylint: disable=duplicate-code
                "--team-id",
                "12345",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
        assert "assigned to team" in result.output.lower()


def test_roster_coaches_assign_error_handling() -> None:
    """Ensure coaches assign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            # pylint: enable=duplicate-code
            "gamesheet_sdk.cli.commands.roster._assign_coach_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "assign",
                "--coach-id",
                "1868550",
                "--team-id",
                "12345",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 1
        assert "error assigning coach" in result.output.lower()


def test_roster_coaches_unassign_coverage() -> None:
    """Ensure coaches unassign command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.roster._unassign_coach_action"),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "unassign",
                "--coach-id",
                "1868550",
                "--team-id",
                "12345",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
        assert "unassigned from team" in result.output.lower()


def test_roster_coaches_unassign_error_handling() -> None:
    """Ensure coaches unassign command error handling is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster._unassign_coach_action",
            side_effect=Exception("Test error"),
        ),
    ):
        result = runner.invoke(
            coaches_group,
            [
                "unassign",
                "--coach-id",
                "1868550",
                "--team-id",
                "12345",
            ],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 1
        assert "error unassigning coach" in result.output.lower()
