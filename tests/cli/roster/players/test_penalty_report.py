# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster players penalty-report command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.main import cli
from tests.helpers import SEASON_ID


def test_players_penalty_report_requires_player_id() -> None:
    """Test that penalty-report command requires --player-id."""
    result = CliRunner().invoke(
        cli,
        [
            "--base-url",
            "https://test.example.com",
            "roster",
            "--season-id",
            SEASON_ID,
            "players",
            "penalty-report",
        ],
    )
    assert result.exit_code
    assert "--player-id" in result.output or "player-id" in result.output.lower()


def test_players_penalty_report_success(mock_session: MagicMock) -> None:
    """Test successful penalty report retrieval."""
    runner = CliRunner()
    mock_report = {
        "player_games": [],
        "player_penalties": [],
        "rostered_players": [{"status": "playing", "team_id": 523675}],
        "season_players": [
            {"first_name": "WAYNE", "id": 8113805, "last_name": "GRETZKY"},
        ],
    }
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
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
                "players",
                "penalty-report",
                "--player-id",
                "8113805",
            ],
        )
        assert not result.exit_code
        assert "player_games" in result.output
        mock_get_report.assert_called_once_with(mock_session, SEASON_ID, "8113805")


def test_players_penalty_report_uses_env_var(mock_session: MagicMock) -> None:
    """Test that penalty-report uses GAMESHEET_PLAYER_ID environment variable."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"player_games": [], "player_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
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
                "players",
                "penalty-report",
            ],
            env={"GAMESHEET_PLAYER_ID": "8113805"},
        )
        assert not result.exit_code
        mock_get_report.assert_called_once_with(mock_session, SEASON_ID, "8113805")


def test_players_penalty_report_json_format(mock_session: MagicMock) -> None:
    """Test penalty report with JSON output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"player_games": [], "player_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
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
                "players",
                "penalty-report",
                "--player-id",
                "8113805",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert "player_games" in result.output


def test_players_penalty_report_yaml_format(mock_session: MagicMock) -> None:
    """Test penalty report with YAML output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"player_games": [], "player_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
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
                "players",
                "penalty-report",
                "--player-id",
                "8113805",
                "--format",
                "yaml",
            ],
        )
        assert not result.exit_code
        assert "player_games" in result.output
