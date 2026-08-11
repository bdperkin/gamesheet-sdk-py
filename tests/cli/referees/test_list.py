# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for referees list command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.referees import Referee
from tests.helpers import (
    CLI_TEST_SEASON_ID,
    DEFAULT_PLAYER_LAST_NAME,
    TEST_EMAIL_GENERIC,
    TIMESTAMP_2024_01_01,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_referees_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            ["referees", "ls", "--season-id", CLI_TEST_SEASON_ID],
        )
        assert not result.exit_code
        mock_list.assert_called_once()


def test_referees_list_json_output(runner: CliRunner) -> None:
    """The referees list command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="John",
                last_name=DEFAULT_PLAYER_LAST_NAME,
                email="john@example.com",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["referees", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "json"],
        )
        assert not result.exit_code
        assert '"id": "ref-1"' in result.output
        assert '"first_name": "John"' in result.output


def test_referees_list_yaml_output(runner: CliRunner) -> None:
    """The referees list command should support YAML output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="John",
                last_name=DEFAULT_PLAYER_LAST_NAME,
                email="john@example.com",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["referees", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "yaml"],
        )
        assert not result.exit_code
        assert "id:" in result.output or "id :" in result.output
        assert "John" in result.output


def test_referees_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for referees."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="John",
                last_name=DEFAULT_PLAYER_LAST_NAME,
                email="john@example.com",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "referees",
                "list",
                "--season-id",
                CLI_TEST_SEASON_ID,
                "--columns",
                "id,first_name",
            ],
        )
        assert not result.exit_code
        assert "ref-1" in result.output
        assert "John" in result.output


def test_referees_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for referees."""
    output_file = tmp_path / "referees.json"
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="Test",
                last_name="User",
                email=TEST_EMAIL_GENERIC,
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "referees",
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
        assert '"id": "ref-1"' in content


def test_referees_list_csv_output(runner: CliRunner) -> None:
    """The referees list command should support CSV output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="John",
                last_name=DEFAULT_PLAYER_LAST_NAME,
                email="john@example.com",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["referees", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "csv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_referees_list_tsv_output(runner: CliRunner) -> None:
    """The referees list command should support TSV output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            Referee(
                id="ref-1",
                season_id=CLI_TEST_SEASON_ID,
                first_name="John",
                last_name=DEFAULT_PLAYER_LAST_NAME,
                email="john@example.com",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["referees", "list", "--season-id", CLI_TEST_SEASON_ID, "--format", "tsv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        # TSV uses tabs
        assert "\t" in result.output


def test_referees_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Referees list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(
            cli,
            ["referees", "list", "--season-id", CLI_TEST_SEASON_ID],
        )
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_referees_list_with_env_var(runner: CliRunner) -> None:
    """The season ID can be provided via GAMESHEET_SEASON_ID environment variable."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._list_referees_action",
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
            ["referees", "list"],
            env={"GAMESHEET_SEASON_ID": CLI_TEST_SEASON_ID},
        )
        assert not result.exit_code
        mock_list.assert_called_once()
