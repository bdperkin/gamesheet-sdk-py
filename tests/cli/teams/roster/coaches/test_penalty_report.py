# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams roster coaches penalty-report command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.teams_roster_coaches import (
    teams_roster_coaches_group,
)
from tests.helpers import COACH_ID_TERTIARY, SEASON_ID, TEAM_ID_SECONDARY


def test_teams_roster_coaches_penalty_report_coverage(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster coaches penalty-report command body is covered."""
    runner = CliRunner()
    mock_report = {
        "coach_games": [],
        "coach_penalties": [],
        "rostered_coaches": [{"status": "coaching", "team_id": 523675}],
    }
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.admin.roster.get_coach_penalty_report",
            return_value=mock_report,
        ) as mock_get_report,
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            ["penalty-report", "--coach-id", COACH_ID_TERTIARY],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "coach_games" in result.output
        mock_get_report.assert_called_once_with(
            mock_session,
            SEASON_ID,
            COACH_ID_TERTIARY,
        )


def test_teams_roster_coaches_penalty_report_requires_coach_id(
    mock_config: MagicMock,
) -> None:
    """Test that penalty-report requires --coach-id."""
    result = CliRunner().invoke(
        teams_roster_coaches_group,
        ["penalty-report"],
        obj={
            "config": mock_config,
            "season_id": SEASON_ID,
            "team_id": TEAM_ID_SECONDARY,
        },
    )
    assert result.exit_code
    assert "--coach-id" in result.output or "coach-id" in result.output.lower()


def test_teams_roster_coaches_penalty_report_json_format(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test penalty report with JSON output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"coach_games": [], "coach_penalties": []}
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.admin.roster.get_coach_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            ["penalty-report", "--coach-id", COACH_ID_TERTIARY, "--format", "json"],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "coach_games" in result.output


def test_teams_roster_coaches_penalty_report_yaml_format(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test penalty report with YAML output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"coach_games": [], "coach_penalties": []}
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.teams_roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.admin.roster.get_coach_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            ["penalty-report", "--coach-id", COACH_ID_TERTIARY, "--format", "yaml"],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "coach_games" in result.output
