# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams roster players penalty-report command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster_players import teams_roster_players_group
from tests.helpers import PLAYER_ID_SECONDARY, SEASON_ID, TEAM_ID_SECONDARY


def test_teams_roster_players_penalty_report_coverage(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Ensure teams roster players penalty-report command body is covered."""
    runner = CliRunner()
    mock_report = {
        "player_games": [],
        "player_penalties": [],
        "rostered_players": [{"status": "playing", "team_id": 523675}],
    }
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_players.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
            return_value=mock_report,
        ) as mock_get_report,
    ):
        result = runner.invoke(
            teams_roster_players_group,
            ["penalty-report", "--player-id", PLAYER_ID_SECONDARY],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "player_games" in result.output
        mock_get_report.assert_called_once_with(
            mock_session,
            SEASON_ID,
            PLAYER_ID_SECONDARY,
        )


def test_teams_roster_players_penalty_report_requires_player_id(
    mock_config: MagicMock,
) -> None:
    """Test that penalty-report requires --player-id."""
    result = CliRunner().invoke(
        teams_roster_players_group,
        ["penalty-report"],
        obj={
            "config": mock_config,
            "season_id": SEASON_ID,
            "team_id": TEAM_ID_SECONDARY,
        },
    )
    assert result.exit_code
    assert "--player-id" in result.output or "player-id" in result.output.lower()


def test_teams_roster_players_penalty_report_json_format(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test penalty report with JSON output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"player_games": [], "player_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_players.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            ["penalty-report", "--player-id", PLAYER_ID_SECONDARY, "--format", "json"],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "player_games" in result.output


def test_teams_roster_players_penalty_report_yaml_format(
    mock_session: MagicMock,
    mock_config: MagicMock,
) -> None:
    """Test penalty report with YAML output format."""
    runner = CliRunner()
    mock_report: dict[str, Any] = {"player_games": [], "player_penalties": []}
    with (
        patch(
            "gamesheet_sdk.cli.commands.teams_roster_players.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.roster.get_player_penalty_report",
            return_value=mock_report,
        ),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            ["penalty-report", "--player-id", PLAYER_ID_SECONDARY, "--format", "yaml"],
            obj={
                "config": mock_config,
                "season_id": SEASON_ID,
                "team_id": TEAM_ID_SECONDARY,
            },
        )
        assert not result.exit_code
        assert "player_games" in result.output
