# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster coaches penalty-report command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.main import cli
from tests.helpers import COACH_ID_TERTIARY, SEASON_ID


def test_coaches_penalty_report_requires_coach_id() -> None:
    """Test that penalty-report command requires --coach-id."""
    result = CliRunner().invoke(
        cli,
        [
            "--base-url",
            "https://test.example.com",
            "roster",
            "--season-id",
            SEASON_ID,
            "coaches",
            "penalty-report",
        ],
    )
    assert result.exit_code
    assert "--coach-id" in result.output or "coach-id" in result.output.lower()


def test_coaches_penalty_report_success(mock_session: MagicMock) -> None:
    """Test successful penalty report retrieval."""
    runner = CliRunner()
    mock_report = {
        "coach_games": [],
        "coach_penalties": [],
        "rostered_coaches": [{"status": "coaching", "team_id": 523675}],
        "season_coaches": [
            {"first_name": "SCOTTY", "id": 1879742, "last_name": "BOWMAN"},
        ],
    }
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_coach_penalty_report",
            return_value=mock_report,
        ) as mock_get_report,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "penalty-report",
                "--coach-id",
                COACH_ID_TERTIARY,
            ],
        )
        assert not result.exit_code
        assert "coach_games" in result.output
        mock_get_report.assert_called_once_with(
            mock_session,
            SEASON_ID,
            COACH_ID_TERTIARY,
        )


def test_coaches_penalty_report_uses_env_var(mock_session: MagicMock) -> None:
    """Test that penalty-report uses GAMESHEET_COACH_ID environment variable."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"coach_games": [], "coach_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_coach_penalty_report",
            return_value=mock_report,
        ) as mock_get_report,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "penalty-report",
            ],
            env={"GAMESHEET_COACH_ID": COACH_ID_TERTIARY},
        )
        assert not result.exit_code
        mock_get_report.assert_called_once_with(
            mock_session,
            SEASON_ID,
            COACH_ID_TERTIARY,
        )


def test_coaches_penalty_report_json_format(mock_session: MagicMock) -> None:
    """Test penalty report with JSON output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"coach_games": [], "coach_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_coach_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "penalty-report",
                "--coach-id",
                COACH_ID_TERTIARY,
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert "coach_games" in result.output


def test_coaches_penalty_report_yaml_format(mock_session: MagicMock) -> None:
    """Test penalty report with YAML output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"coach_games": [], "coach_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_coach_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "penalty-report",
                "--coach-id",
                COACH_ID_TERTIARY,
                "--format",
                "yaml",
            ],
        )
        assert not result.exit_code
        assert "coach_games" in result.output
