"""Tests for leagues command group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.leagues import League

if TYPE_CHECKING:

    from click.testing import CliRunner


def test_leagues_group_has_help_option(runner: CliRunner) -> None:
    """The leagues group should accept -h and --help."""
    result_short = runner.invoke(cli, ["leagues", "-h"])
    assert not result_short.exit_code
    assert "leagues" in result_short.output.lower()
    result_long = runner.invoke(cli, ["leagues", "--help"])
    assert not result_long.exit_code
    assert "leagues" in result_long.output.lower()


def test_leagues_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["leagues", "ls", "--association-id", "38"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_leagues_missing_association_id_shows_error(runner: CliRunner) -> None:
    """Calling 'leagues list' without an association ID should show an error."""
    result = runner.invoke(cli, ["leagues", "list"])
    assert result.exit_code == 2  # Usage error
    assert "association-id" in result.output.lower() or "missing option" in result.output.lower()


def test_leagues_list_json_output(runner: CliRunner) -> None:
    """The leagues list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--format", "json"])
        assert not result.exit_code
        assert '"id": "100"' in result.output
        assert '"title": "Test League"' in result.output


def test_leagues_list_yaml_output(runner: CliRunner) -> None:
    """The leagues list command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--format", "yaml"])
        assert not result.exit_code
        assert "id:" in result.output or "id :" in result.output
        assert "Test League" in result.output


def test_leagues_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for leagues."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--columns", "id,title"])
        assert not result.exit_code
        assert "100" in result.output
        assert "Test League" in result.output


def test_leagues_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for leagues."""
    output_file = tmp_path / "leagues.json"
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["leagues", "list", "--association-id", "38", "--format", "json", "--output", str(output_file)],
        )
        assert not result.exit_code
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "100"' in content


def test_leagues_list_csv_output(runner: CliRunner) -> None:
    """The leagues list command should support CSV output."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--format", "csv"])
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_leagues_bare_invocation_runs_list(runner: CliRunner) -> None:
    """Bare 'leagues ASSOC_ID' with no args shows help mentioning list as default."""
    result = runner.invoke(cli, ["leagues", "--help"])
    assert not result.exit_code
    # Help should mention that list is the default or show list command
    assert "list" in result.output.lower() or "ls" in result.output.lower()


def test_leagues_list_grid_format(runner: CliRunner) -> None:
    """The leagues list command should support grid format."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--format", "grid"])
        assert not result.exit_code
        # Grid format should have borders
        assert "+" in result.output or "|" in result.output


def test_leagues_list_simple_format(runner: CliRunner) -> None:
    """The leagues list command should support simple format."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38", "--format", "simple"])
        assert not result.exit_code
        assert "100" in result.output


def test_leagues_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Leagues list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["leagues", "list", "--association-id", "38"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_leagues_list_with_env_var(runner: CliRunner) -> None:
    """The association ID can be provided via GAMESHEET_ASSOCIATION_ID environment variable."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["leagues", "list"], env={"GAMESHEET_ASSOCIATION_ID": "38"})
        assert not result.exit_code
        mock_list.assert_called_once()
