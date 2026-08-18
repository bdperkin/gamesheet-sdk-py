# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the gamesheet-teams teams CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.cli.commands.teams import teams_group
from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.teams import (
    TeamDetail,
    TeamSummary,
)

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner

_MOCK_SUMMARIES = [
    TeamSummary(
        memberId="m-101",
        teamId="t-201",
        relationship="coach",
        status="active",
        onboardingCompletedAt="2024-09-01T00:00:00Z",
        teamName="Hawks 12U",
        ageCategory="12U",
        clubId="c-301",
        joinedAt="2024-08-15T00:00:00Z",
        statsYear="2024-2025",
    ),
    TeamSummary(
        memberId="m-102",
        teamId="t-202",
        relationship="manager",
        status="active",
        onboardingCompletedAt="2024-09-02T00:00:00Z",
        teamName="Eagles 14U",
        ageCategory="14U",
        clubId="c-302",
        joinedAt="2024-08-20T00:00:00Z",
        statsYear="2024-2025",
    ),
]

_MOCK_DETAIL = TeamDetail(
    memberId="m-101",
    teamId="t-201",
    relationship="coach",
    status="active",
    onboardingCompletedAt="2024-09-01T00:00:00Z",
    teamName="Hawks 12U",
    ageCategory="12U",
    clubId="c-301",
    joinedAt="2024-08-15T00:00:00Z",
    statsYear="2024-2025",
)


def test_teams_group_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams --help` displays command options and subcommands."""
    result = runner.invoke(cli, ["teams", "--help"])
    assert result.exit_code == 0
    assert "View teams from the teams API." in result.output
    assert "list" in result.output
    assert "get" in result.output


def test_teams_default_invokes_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams` defaults to running `list` subcommand."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(cli, ["teams"])

    assert result.exit_code == 0
    assert "Hawks 12U" in result.output
    assert "Eagles 14U" in result.output


def test_teams_list_json_format(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams list --format json` produces valid JSON output."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(cli, ["teams", "list", "--format", "json"])

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output
    assert '"memberId": "m-101"' in result.output


def test_teams_list_alias_ls(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams ls` runs the list command."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(cli, ["teams", "ls"])

    assert result.exit_code == 0
    assert "Hawks 12U" in result.output


def test_teams_list_custom_columns(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams list --columns teamName,relationship`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(cli, ["teams", "list", "-c", "teamName,relationship", "--format", "json"])

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output
    assert '"relationship": "coach"' in result.output


def test_teams_list_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Test `gamesheet-teams teams list --output <path>` saves output to file."""
    output_file = tmp_path / "teams_list.json"
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "list", "--format", "json", "-o", str(output_file)],
        )

    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "Hawks 12U" in content


def test_teams_get_by_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams get --team-id t-201`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_DETAIL,
        ),
    ):
        result = runner.invoke(cli, ["teams", "get", "--team-id", "t-201", "--format", "json"])

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output
    assert '"memberId": "m-101"' in result.output


def test_teams_get_by_short_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams get -t t-201`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_DETAIL,
        ),
    ):
        result = runner.invoke(cli, ["teams", "get", "-t", "t-201", "--format", "json"])

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output


def test_teams_get_by_envvar(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams get` with GAMESHEET_TEAM_ID env var."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_DETAIL,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "get", "--format", "json"],
            env={"GAMESHEET_TEAM_ID": "t-201"},
        )

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output


def test_teams_get_missing_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams get` fails when --team-id is missing."""
    result = runner.invoke(cli, ["teams", "get"])
    assert result.exit_code != 0
    assert "Missing option '--team-id'" in result.output or "Missing option '-t'" in result.output


def test_teams_get_aliases_show_and_view(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams show` and `view` aliases."""
    for alias in ["show", "view"]:
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
                return_value=_MOCK_DETAIL,
            ),
        ):
            result = runner.invoke(cli, ["teams", alias, "-t", "t-201", "--format", "json"])

        assert result.exit_code == 0
        assert '"teamName": "Hawks 12U"' in result.output


def test_teams_get_fields_filter(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams get -f teamName,relationship`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_DETAIL,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "get", "-t", "t-201", "-f", "teamName,relationship", "--format", "json"],
        )

    assert result.exit_code == 0
    assert '"teamName": "Hawks 12U"' in result.output
    assert '"relationship": "coach"' in result.output


def test_teams_get_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Test `gamesheet-teams teams get -o <path>` saves get result to file."""
    out_file = tmp_path / "team_detail.json"
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_DETAIL,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "get", "-t", "t-201", "--format", "json", "-o", str(out_file)],
        )

    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Hawks 12U" in content


def test_teams_cli_auth_error(runner: CliRunner) -> None:
    """Test CLI error handling when action raises AuthenticationError."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            side_effect=AuthenticationError("Token expired"),
        ),
    ):
        result = runner.invoke(cli, ["teams", "list"])

    assert result.exit_code == 1


def test_teams_cli_gamesheet_error(runner: CliRunner) -> None:
    """Test CLI error handling when action raises GameSheetError."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            side_effect=GameSheetError("Team not found"),
        ),
    ):
        result = runner.invoke(cli, ["teams", "get", "-t", "t-999"])

    assert result.exit_code == 1


def test_teams_group_direct_invocation(runner: CliRunner) -> None:
    """Test direct invocation of teams_group with obj."""
    mock_config = MagicMock()
    mock_config.timeout = 1.0
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=_MOCK_SUMMARIES,
        ),
    ):
        result = runner.invoke(teams_group, [], obj=mock_config)

    assert result.exit_code == 0
    assert "Hawks 12U" in result.output
