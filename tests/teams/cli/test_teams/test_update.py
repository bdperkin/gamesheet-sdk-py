# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for gamesheet-teams teams update CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.teams import TeamDetail

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


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
    assert "img-123" in result.output


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
    assert "team-id" in result.output.lower() or "missing" in result.output.lower()


def test_teams_update_no_fields_error(runner: CliRunner) -> None:
    """Test `gamesheet-teams teams update` exits with error when no update fields are passed."""
    result = runner.invoke(cli, ["teams", "update", "--team-id", "t-201"])
    assert result.exit_code == 1
    assert "Error: At least one field must be provided for update" in result.output
