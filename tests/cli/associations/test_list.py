# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for associations list command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.admin.associations import Association
from gamesheet_sdk.admin.cli.main import cli
from tests.helpers import (
    DEFAULT_ASSOCIATION_NAME,
    TIMESTAMP_2024_01_01,
    assert_no_session_error,
    assert_output_contains_id,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_associations_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
        result = runner.invoke(cli, ["associations", "ls"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_associations_bare_invocation_runs_list(runner: CliRunner) -> None:
    """Bare 'associations' should implicitly run 'list'."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
        result = runner.invoke(cli, ["associations"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_associations_list_json_output(runner: CliRunner) -> None:
    """The list command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
            Association(
                id="1",
                title=DEFAULT_ASSOCIATION_NAME,
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "json"])
        assert not result.exit_code
        assert '"id": "1"' in result.output
        assert '"title": "' + DEFAULT_ASSOCIATION_NAME + '"' in result.output


def test_associations_list_yaml_output(runner: CliRunner) -> None:
    """The list command should support YAML output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
            Association(
                id="1",
                title=DEFAULT_ASSOCIATION_NAME,
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "yaml"])
        assert not result.exit_code
        assert_output_contains_id(result)
        assert DEFAULT_ASSOCIATION_NAME in result.output


def test_associations_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
            Association(
                id="1",
                title=DEFAULT_ASSOCIATION_NAME,
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--columns", "id,title"])
        assert not result.exit_code
        # Should have id and title somewhere
        assert "1" in result.output
        assert DEFAULT_ASSOCIATION_NAME in result.output


def test_associations_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file."""
    output_file = tmp_path / "output.json"
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
            Association(
                id="1",
                title="Test",
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(
            cli,
            ["associations", "list", "--format", "json", "--output", str(output_file)],
        )
        assert not result.exit_code
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "1"' in content


def test_associations_list_csv_output(runner: CliRunner) -> None:
    """The list command should support CSV output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
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
            Association(
                id="1",
                title=DEFAULT_ASSOCIATION_NAME,
                created_at=TIMESTAMP_2024_01_01,
                updated_at=TIMESTAMP_2024_01_01,
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "csv"])
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        # CSV should have header + data row
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_associations_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Associations list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert_no_session_error(result)


def test_associations_list_with_authentication_error(runner: CliRunner) -> None:
    """Associations list should handle AuthenticationError gracefully."""
    from gamesheet_sdk.common.exceptions import AuthenticationError

    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
            side_effect=AuthenticationError("Token expired"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "Authentication required" in result.output or "expired" in result.output.lower()


def test_associations_list_with_gamesheet_error(runner: CliRunner) -> None:
    """Associations list should handle GameSheetError gracefully."""
    from gamesheet_sdk.common.exceptions import GameSheetError

    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
            side_effect=GameSheetError("API error"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "GameSheet error" in result.output or "error" in result.output.lower()
