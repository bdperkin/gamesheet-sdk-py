# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for divisions list command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.divisions import Division
from tests.helpers import CLI_TEST_SEASON_ID, TIMESTAMP_2024_01_01

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


def test_divisions_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = []
        result = runner.invoke(
            cli,
            ["divisions", "ls", "--season-id", CLI_TEST_SEASON_ID],
        )
        assert not result.exit_code
        mock_list.assert_called_once()


def test_divisions_missing_season_id_shows_error(runner: CliRunner) -> None:
    """Calling 'divisions list' without a season ID should show an error."""
    result = runner.invoke(cli, ["divisions", "list"])
    assert result.exit_code == 2  # Usage error
    assert "season-id" in result.output.lower() or "missing option" in result.output.lower()


def test_divisions_list_json_output(runner: CliRunner) -> None:
    """The divisions list command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="U13 AAA",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "divisions",
                "list",
                "--season-id",
                CLI_TEST_SEASON_ID,
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert '"id": "101"' in result.output
        assert '"title": "U13 AAA"' in result.output


def test_divisions_list_yaml_output(runner: CliRunner) -> None:
    """The divisions list command should support YAML output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="U13 AAA",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "divisions",
                "list",
                "--season-id",
                CLI_TEST_SEASON_ID,
                "--format",
                "yaml",
            ],
        )
        assert not result.exit_code
        assert "id:" in result.output or "id :" in result.output
        assert "U13 AAA" in result.output


def test_divisions_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for divisions."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="U13 AAA",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "divisions",
                "list",
                "--season-id",
                CLI_TEST_SEASON_ID,
                "--columns",
                "id,title",
            ],
        )
        assert not result.exit_code
        assert "101" in result.output
        assert "U13 AAA" in result.output


def test_divisions_list_output_to_file(runner: CliRunner, tmp_path: Path) -> None:
    """The --output option should write to a file for divisions."""
    output_file = tmp_path / "divisions.json"
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="Test",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "divisions",
                "list",
                "--season-id",
                CLI_TEST_SEASON_ID,
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )
        assert not result.exit_code
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "101"' in content


def test_divisions_list_csv_output(runner: CliRunner) -> None:
    """The divisions list command should support CSV output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="U13 AAA",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["divisions", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "csv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_divisions_list_tsv_output(runner: CliRunner) -> None:
    """The divisions list command should support TSV output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = [
            Division(
                id="101",
                season_id=CLI_TEST_SEASON_ID,
                title="U13 AAA",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["divisions", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "tsv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        # TSV uses tabs
        assert "\t" in result.output


def test_divisions_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Divisions list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(
            cli,
            ["divisions", "list", "--season-id", CLI_TEST_SEASON_ID],
        )
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_divisions_list_with_env_var(runner: CliRunner) -> None:
    """The season ID can be provided via GAMESHEET_SEASON_ID environment variable."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions._list_divisions_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_list.return_value = []
        result = runner.invoke(
            cli,
            ["divisions", "list"],
            env={"GAMESHEET_SEASON_ID": CLI_TEST_SEASON_ID},
        )
        assert not result.exit_code
        mock_list.assert_called_once()
