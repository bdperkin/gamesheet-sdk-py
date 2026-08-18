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
    assert "View and update teams from the teams API." in result.output
    assert "list" in result.output
    assert "get" in result.output
    assert "update" in result.output


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


def test_teams_update_success(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update` modifies team fields and renders result."""
    updated_mock = TeamDetail(
        teamId="t-201",
        teamName="Updated Hawks",
        skill="rec",
        ageCategory="12U",
        province="VA",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=updated_mock,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--team-id",
                "t-201",
                "--name",
                "Updated Hawks",
                "--skill",
                "rec",
                "--age-category",
                "12U",
                "--province",
                "VA",
            ],
        )

    assert result.exit_code == 0
    assert "Updated Hawks" in result.output
    assert "rec" in result.output
    mock_action.assert_called_once()


def test_teams_update_aliases(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams set` and `gamesheet-teams teams edit` work as aliases for update."""
    updated_mock = TeamDetail(
        teamId="t-201",
        teamName="Updated Hawks",
    )
    for alias in ("set", "edit"):
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
                return_value=updated_mock,
            ),
        ):
            result = runner.invoke(
                cli,
                ["teams", alias, "--team-id", "t-201", "--team-name", "Updated Hawks"],
            )

        assert result.exit_code == 0
        assert "Updated Hawks" in result.output


def test_teams_update_with_logo(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update` accepts --team-logo and --logo options."""
    updated_mock = TeamDetail(
        teamId="t-201",
        teamLogo="https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=updated_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "update", "-t", "t-201", "--logo", "logo.png"],
        )

    assert result.exit_code == 0
    assert "https://imagedelivery.net" in result.output


def test_teams_update_format_json(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update --format json` produces valid JSON output."""
    updated_mock = TeamDetail(
        teamId="t-201",
        teamName="Updated Hawks",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=updated_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--team-id",
                "t-201",
                "--name",
                "Updated Hawks",
                "--format",
                "json",
            ],
        )

    assert result.exit_code == 0
    assert '"teamName": "Updated Hawks"' in result.output


def test_teams_update_fields_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update --fields` filters displayed fields."""
    updated_mock = TeamDetail(
        teamId="t-201",
        teamName="Updated Hawks",
        skill="rec",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=updated_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "-t",
                "t-201",
                "--name",
                "Updated Hawks",
                "--fields",
                "teamName",
            ],
        )

    assert result.exit_code == 0
    assert "Updated Hawks" in result.output


def test_teams_update_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Test `gamesheet-teams teams update -o <file>` writes output to file."""
    out_file = tmp_path / "update_out.txt"
    updated_mock = TeamDetail(
        teamId="t-201",
        teamName="Updated Hawks",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=updated_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "-t",
                "t-201",
                "--name",
                "Updated Hawks",
                "-o",
                str(out_file),
            ],
        )

    assert result.exit_code == 0
    content = out_file.read_text(encoding="utf-8")
    assert "Updated Hawks" in content


def test_teams_update_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update` errors when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "update", "--name", "New Name"])
    assert result.exit_code != 0
    assert "Missing option '--team-id'" in result.output or "Missing option '-t'" in result.output


def test_teams_update_no_fields_error(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update` exits with error when no update fields are passed."""
    result = runner.invoke(cli, ["teams", "update", "--team-id", "t-201"])
    assert result.exit_code == 1
    assert "Error: At least one field must be provided for update" in result.output


def test_teams_archive_success(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive -t <id>` archives team successfully."""
    archived_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=True,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=archived_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "archive", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719"],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_archive_envvar(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive` picks up GAMESHEET_TEAM_ID envvar."""
    archived_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=True,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=archived_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "archive"],
            env={"GAMESHEET_TEAM_ID": "eb20a094-5c3c-47bc-918f-c8f69cfe0719"},
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_archive_format_json(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive --format json` outputs valid JSON."""
    archived_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=True,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=archived_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "archive",
                "--team-id",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "--format",
                "json",
            ],
        )

    assert result.exit_code == 0
    assert '"teamId": "eb20a094-5c3c-47bc-918f-c8f69cfe0719"' in result.output
    assert '"isArchived": true' in result.output


def test_teams_archive_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Test `gamesheet-teams teams archive -o <file>` writes output to file."""
    out_file = tmp_path / "archive_out.txt"
    archived_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=True,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=archived_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "archive",
                "-t",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "-o",
                str(out_file),
            ],
        )

    assert result.exit_code == 0
    content = out_file.read_text(encoding="utf-8")
    assert "Peterborough Petes 2" in content


def test_teams_archive_fields_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive --fields` limits displayed fields."""
    archived_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=True,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=archived_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "archive",
                "-t",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "--fields",
                "teamName,isArchived",
            ],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_archive_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive` errors when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "archive"])
    assert result.exit_code != 0
    assert "Missing option '--team-id'" in result.output or "Missing option '-t'" in result.output


def test_teams_restore_success(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore -t <id>` restores team successfully."""
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "restore", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719"],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_restore_alias_unarchive(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams unarchive -t <id>` functions via alias."""
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "unarchive", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719"],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_restore_envvar(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore` picks up GAMESHEET_TEAM_ID envvar."""
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            ["teams", "restore"],
            env={"GAMESHEET_TEAM_ID": "eb20a094-5c3c-47bc-918f-c8f69cfe0719"},
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_restore_format_json(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore --format json` outputs valid JSON."""
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "restore",
                "--team-id",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "--format",
                "json",
            ],
        )

    assert result.exit_code == 0
    assert '"teamId": "eb20a094-5c3c-47bc-918f-c8f69cfe0719"' in result.output
    assert '"isArchived": false' in result.output


def test_teams_restore_output_file(runner: CliRunner, tmp_path: Path) -> None:
    """Test `gamesheet-teams teams restore -o <file>` writes output to file."""
    out_file = tmp_path / "restore_out.txt"
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "restore",
                "-t",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "-o",
                str(out_file),
            ],
        )

    assert result.exit_code == 0
    content = out_file.read_text(encoding="utf-8")
    assert "Peterborough Petes 2" in content


def test_teams_restore_fields_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore --fields` limits displayed fields."""
    restored_mock = TeamDetail(
        teamId="eb20a094-5c3c-47bc-918f-c8f69cfe0719",
        teamName="Peterborough Petes 2",
        isArchived=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=restored_mock,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "restore",
                "-t",
                "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
                "--fields",
                "teamName,isArchived",
            ],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_restore_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore` errors when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "restore"])
    assert result.exit_code != 0
    assert "Missing option '--team-id'" in result.output or "Missing option '-t'" in result.output
