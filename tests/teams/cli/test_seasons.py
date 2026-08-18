# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the gamesheet-teams seasons CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.cli.commands.seasons import seasons_group
from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.seasons import (
    PenaltyCode,
    SeasonDetail,
    SeasonSummary,
    SeasonTeam,
)

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner

_MOCK_SUMMARIES = [
    SeasonSummary(
        id="101",
        title="2024-2025 Regular Season",
        stats_year="2024-2025",
        leagueId="201",
        league_id="201",
        league_title="Great Lakes League",
        association_id="301",
        association_title="USA Hockey",
    ),
    SeasonSummary(
        id="102",
        title="2023-2024 Season",
        stats_year="2023-2024",
        leagueId="202",
        league_id="202",
        league_title="Midwest League",
        association_id="",
        association_title="",
    ),
]

_MOCK_DETAIL = SeasonDetail(
    id="101",
    title="2024-2025 Regular Season",
    stats_year="2024-2025",
    leagueId="201",
    sport="hockey",
    start_date="2024-09-01",
    end_date="2025-04-30",
)

_MOCK_PENALTY_CODES = [
    PenaltyCode(code="TRIP", name="Tripping", severity="minor"),
    PenaltyCode(code="SLASH", name="Slashing", severity="minor"),
]

_MOCK_TEAMS = [
    SeasonTeam(id="1001", title="Hawks", division="Varsity"),
    SeasonTeam(id="1002", title="Eagles", division="Varsity"),
]

_LIST_PATCH = "gamesheet_sdk.teams.cli.commands.seasons._list_seasons_action"
_GET_PATCH = "gamesheet_sdk.teams.cli.commands.seasons._get_season_action"
_PENALTY_CODES_PATCH = "gamesheet_sdk.teams.cli.commands.seasons._get_season_penalty_codes_action"
_TEAMS_PATCH = "gamesheet_sdk.teams.cli.commands.seasons._get_season_teams_action"
_SESSION_PATCH = "gamesheet_sdk.teams.cli.commands.seasons.build_authenticated_session"


def test_seasons_help(runner: CliRunner) -> None:
    """Seasons --help shows usage text."""
    result = runner.invoke(cli, ["seasons", "--help"])
    assert not result.exit_code
    assert "seasons" in result.output.lower()
    assert "penalty-codes" in result.output


def test_seasons_list_default(runner: CliRunner) -> None:
    """Default seasons invocation runs list."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(cli, ["seasons"])

    assert not result.exit_code
    assert "101" in result.output
    assert "2024-2025 Regular Season" in result.output
    assert "USA Hockey" in result.output


def test_seasons_list_subcommand(runner: CliRunner) -> None:
    """Seasons list subcommand runs explicitly."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(cli, ["seasons", "list"])

    assert not result.exit_code
    assert "101" in result.output
    assert "Great Lakes League" in result.output


def test_seasons_list_alias_ls(runner: CliRunner) -> None:
    """The 'ls' alias works for seasons list."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(cli, ["seasons", "ls"])

    assert not result.exit_code
    assert "101" in result.output


def test_seasons_list_format_json(runner: CliRunner) -> None:
    """Seasons list --format json outputs JSON array."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(cli, ["seasons", "list", "--format", "json"])

    assert not result.exit_code
    assert '"id": "101"' in result.output
    assert '"title": "2024-2025 Regular Season"' in result.output


def test_seasons_list_columns_filter(runner: CliRunner) -> None:
    """Seasons list --columns filters output columns."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(
            cli,
            ["seasons", "list", "--format", "csv", "--columns", "id,title"],
        )

    assert not result.exit_code
    assert "id,title" in result.output
    assert "stats_year" not in result.output


def test_seasons_list_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Seasons list --output writes to file."""
    output_file = tmp_path / "seasons.json"
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(
            cli,
            ["seasons", "list", "--format", "json", "-o", str(output_file)],
        )

    assert not result.exit_code
    assert output_file.exists()
    assert '"id": "101"' in output_file.read_text()


def test_seasons_get(runner: CliRunner) -> None:
    """Seasons get --season-id retrieves season details."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "101"])

    assert not result.exit_code
    assert "101" in result.output
    assert "2024-2025 Regular Season" in result.output
    assert "hockey" in result.output


def test_seasons_get_alias_show(runner: CliRunner) -> None:
    """The 'show' alias works for seasons get."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(cli, ["seasons", "show", "--season-id", "101"])

    assert not result.exit_code
    assert "101" in result.output


def test_seasons_get_alias_view(runner: CliRunner) -> None:
    """The 'view' alias works for seasons get."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(cli, ["seasons", "view", "--season-id", "101"])

    assert not result.exit_code
    assert "101" in result.output


def test_seasons_get_envvar(runner: CliRunner) -> None:
    """GAMESHEET_SEASON_ID environment variable supplies season ID."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(
            cli,
            ["seasons", "get"],
            env={"GAMESHEET_SEASON_ID": "101"},
        )

    assert not result.exit_code
    assert "101" in result.output


def test_seasons_get_missing_season_id(runner: CliRunner) -> None:
    """Seasons get without --season-id exits non-zero."""
    result = runner.invoke(cli, ["seasons", "get"])
    assert result.exit_code


def test_seasons_get_format_json(runner: CliRunner) -> None:
    """Seasons get --format json outputs JSON."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(
            cli,
            ["seasons", "get", "--season-id", "101", "--format", "json"],
        )

    assert not result.exit_code
    assert '"id": "101"' in result.output
    assert '"sport": "hockey"' in result.output


def test_seasons_get_fields_filter(runner: CliRunner) -> None:
    """Seasons get --fields filters included fields."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_GET_PATCH, return_value=_MOCK_DETAIL),
    ):
        result = runner.invoke(
            cli,
            ["seasons", "get", "--season-id", "101", "--format", "json", "--fields", "id,title"],
        )

    assert not result.exit_code
    assert '"id": "101"' in result.output
    assert '"title": "2024-2025 Regular Season"' in result.output
    assert "sport" not in result.output


def test_seasons_penalty_codes(runner: CliRunner) -> None:
    """Seasons penalty-codes retrieves penalty codes."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_PENALTY_CODES_PATCH, return_value=_MOCK_PENALTY_CODES),
    ):
        result = runner.invoke(cli, ["seasons", "penalty-codes", "--season-id", "101"])

    assert not result.exit_code
    assert "TRIP" in result.output
    assert "Tripping" in result.output
    assert "SLASH" in result.output


def test_seasons_penalty_codes_alias_penalties(runner: CliRunner) -> None:
    """The 'penalties' alias works for penalty-codes."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_PENALTY_CODES_PATCH, return_value=_MOCK_PENALTY_CODES),
    ):
        result = runner.invoke(cli, ["seasons", "penalties", "--season-id", "101"])

    assert not result.exit_code
    assert "TRIP" in result.output


def test_seasons_penalty_codes_missing_id(runner: CliRunner) -> None:
    """Penalty-codes without --season-id exits non-zero."""
    result = runner.invoke(cli, ["seasons", "penalty-codes"])
    assert result.exit_code


def test_seasons_teams(runner: CliRunner) -> None:
    """Seasons teams retrieves teams for a season."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_TEAMS_PATCH, return_value=_MOCK_TEAMS),
    ):
        result = runner.invoke(cli, ["seasons", "teams", "--season-id", "101"])

    assert not result.exit_code
    assert "1001" in result.output
    assert "Hawks" in result.output
    assert "1002" in result.output
    assert "Eagles" in result.output


def test_seasons_teams_missing_id(runner: CliRunner) -> None:
    """Teams without --season-id exits non-zero."""
    result = runner.invoke(cli, ["seasons", "teams"])
    assert result.exit_code


def test_seasons_no_saved_session(runner: CliRunner) -> None:
    """Running seasons when no tokens are saved prompts login and exits 1."""
    with (
        patch("gamesheet_sdk.teams.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.teams.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["seasons", "list"])

    assert result.exit_code == 1
    assert "No saved session found" in result.output
    assert "gamesheet-teams login" in result.output


def test_seasons_auth_error(runner: CliRunner) -> None:
    """AuthenticationError exits 1 with red error message."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, side_effect=AuthenticationError("Token expired")),
    ):
        result = runner.invoke(cli, ["seasons", "list"])

    assert result.exit_code == 1
    assert "Authentication required" in result.output


def test_seasons_gamesheet_error(runner: CliRunner) -> None:
    """GameSheetError exits 1 with error message."""
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, side_effect=GameSheetError("Season '999' not found")),
    ):
        result = runner.invoke(cli, ["seasons", "list"])

    assert result.exit_code == 1
    assert "GameSheet error" in result.output


def test_seasons_without_parent_context(runner: CliRunner) -> None:
    """Seasons group invoked directly with obj works."""
    mock_config = MagicMock()
    mock_config.timeout = 1.0
    mock_session = MagicMock()
    with (
        patch(_SESSION_PATCH, return_value=mock_session),
        patch(_LIST_PATCH, return_value=_MOCK_SUMMARIES),
    ):
        result = runner.invoke(seasons_group, [], obj=mock_config)

    assert not result.exit_code
    assert "101" in result.output
