"""Tests for associations command group."""

# pylint: disable=redefined-outer-name,protected-access
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.associations import Association
from gamesheet_sdk.cli import cli

if TYPE_CHECKING:

    from click.testing import CliRunner


def test_associations_group_has_help_option(runner: CliRunner) -> None:
    """The associations group should accept -h and --help."""
    result_short = runner.invoke(cli, ["associations", "-h"])
    assert result_short.exit_code == 0
    assert "associations" in result_short.output.lower()
    result_long = runner.invoke(cli, ["associations", "--help"])
    assert result_long.exit_code == 0
    assert "associations" in result_long.output.lower()


def test_associations_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["associations", "ls"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_associations_bare_invocation_runs_list(runner: CliRunner) -> None:
    """Bare 'associations' should implicitly run 'list'."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["associations"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_associations_list_json_output(runner: CliRunner) -> None:
    """The list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Association(
                id="1",
                title="Test Association",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "json"])
        assert result.exit_code == 0
        assert '"id": "1"' in result.output
        assert '"title": "Test Association"' in result.output


def test_associations_list_yaml_output(runner: CliRunner) -> None:
    """The list command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Association(
                id="1",
                title="Test Association",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "yaml"])
        assert result.exit_code == 0
        assert "id:" in result.output or "id :" in result.output
        assert "Test Association" in result.output


def test_associations_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Association(
                id="1",
                title="Test Association",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--columns", "id,title"])
        assert result.exit_code == 0
        # Should have id and title somewhere
        assert "1" in result.output
        assert "Test Association" in result.output


def test_associations_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file."""
    output_file = tmp_path / "output.json"
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Association(
                id="1",
                title="Test",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(
            cli,
            ["associations", "list", "--format", "json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "1"' in content


def test_associations_list_csv_output(runner: CliRunner) -> None:
    """The list command should support CSV output."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Association(
                id="1",
                title="Test Association",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["associations", "list", "--format", "csv"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        # CSV should have header + data row
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_associations_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Associations list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_associations_list_with_authentication_error(runner: CliRunner) -> None:
    """Associations list should handle AuthenticationError gracefully."""
    from gamesheet_sdk.exceptions import AuthenticationError

    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="refresh"),
        patch(
            "gamesheet_sdk.cli.commands.associations._list_associations_action",
            side_effect=AuthenticationError("Token expired"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "Authentication required" in result.output or "expired" in result.output.lower()


def test_associations_list_with_gamesheet_error(runner: CliRunner) -> None:
    """Associations list should handle GameSheetError gracefully."""
    from gamesheet_sdk.exceptions import GameSheetError

    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="refresh"),
        patch(
            "gamesheet_sdk.cli.commands.associations._list_associations_action",
            side_effect=GameSheetError("API error"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "GameSheet error" in result.output or "error" in result.output.lower()
