# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for gamesheet-teams teams lifecycle CLI commands (archive, restore, delete)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.teams import TeamDetail

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


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


def test_teams_archive_columns_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive --columns` limits displayed columns."""
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
                "--columns",
                "teamName,isArchived",
            ],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_archive_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams archive` errors when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "archive"])
    assert result.exit_code != 0
    assert "team-id" in result.output.lower() or "missing" in result.output.lower()


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


def test_teams_restore_columns_option(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore --columns` limits displayed columns."""
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
                "--columns",
                "teamName,isArchived",
            ],
        )

    assert result.exit_code == 0
    assert "Peterborough Petes 2" in result.output


def test_teams_restore_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams restore` errors when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "restore"])
    assert result.exit_code != 0
    assert "team-id" in result.output.lower() or "missing" in result.output.lower()


def test_teams_delete_with_force(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete -t <id> --force` deletes team."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719", "--force"],
        )

    assert result.exit_code == 0
    assert "Team eb20a094-5c3c-47bc-918f-c8f69cfe0719 deleted successfully." in result.output
    mock_run.assert_called_once()


def test_teams_delete_short_force(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete -t <id> -f` deletes team."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719", "-f"],
        )

    assert result.exit_code == 0
    assert "Team eb20a094-5c3c-47bc-918f-c8f69cfe0719 deleted successfully." in result.output
    mock_run.assert_called_once()


def test_teams_delete_alias_rm(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams rm -t <id> -f` via rm alias."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "rm", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719", "-f"],
        )

    assert result.exit_code == 0
    assert "deleted successfully" in result.output
    mock_run.assert_called_once()


def test_teams_delete_alias_remove(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams remove -t <id> -f` via remove alias."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "remove", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719", "-f"],
        )

    assert result.exit_code == 0
    assert "deleted successfully" in result.output
    mock_run.assert_called_once()


def test_teams_delete_confirmed_prompt(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete` prompts for confirmation and succeeds on 'y'."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719"],
            input="y\n",
        )

    assert result.exit_code == 0
    assert "Delete team?" in result.output
    assert "deleted successfully" in result.output
    mock_run.assert_called_once()


def test_teams_delete_aborted_prompt(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete` aborts when user enters 'n'."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "-t", "eb20a094-5c3c-47bc-918f-c8f69cfe0719"],
            input="n\n",
        )

    assert result.exit_code == 1
    assert "Delete team?" in result.output
    assert "Aborted." in result.output
    mock_run.assert_not_called()


def test_teams_delete_envvar(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete` reads GAMESHEET_TEAM_ID envvar."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.teams.run_action_or_exit",
            return_value=None,
        ) as mock_run,
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "-f"],
            env={"GAMESHEET_TEAM_ID": "eb20a094-5c3c-47bc-918f-c8f69cfe0719"},
        )

    assert result.exit_code == 0
    assert "Team eb20a094-5c3c-47bc-918f-c8f69cfe0719 deleted successfully." in result.output
    mock_run.assert_called_once()


def test_teams_delete_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams delete` fails when --team-id is omitted."""
    result = runner.invoke(cli, ["teams", "delete", "-f"])
    assert result.exit_code != 0
    assert "team-id" in result.output.lower() or "missing" in result.output.lower()
