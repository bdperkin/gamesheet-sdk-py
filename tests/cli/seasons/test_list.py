"""Tests for seasons list command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.seasons import Season

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_seasons_group_has_help_option(runner: CliRunner) -> None:
    """The seasons group should accept -h and --help."""
    result_short = runner.invoke(cli, ["seasons", "-h"])
    assert not result_short.exit_code
    assert "seasons" in result_short.output.lower()
    result_long = runner.invoke(cli, ["seasons", "--help"])
    assert not result_long.exit_code
    assert "seasons" in result_short.output.lower()


def test_seasons_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["seasons", "ls", "--league-id", "1148580"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_seasons_missing_league_id_shows_error(runner: CliRunner) -> None:
    """Calling 'seasons list' without a league ID should show an error."""
    result = runner.invoke(cli, ["seasons", "list"])
    assert result.exit_code == 2  # Usage error
    assert "league-id" in result.output.lower() or "missing option" in result.output.lower()


def test_seasons_list_json_output(runner: CliRunner) -> None:
    """The seasons list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "--league-id", "1148580", "--format", "json"],
        )
        assert not result.exit_code
        assert '"id": "501"' in result.output
        assert '"title": "2024-2025"' in result.output


def test_seasons_list_yaml_output(runner: CliRunner) -> None:
    """The seasons list command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "--league-id", "1148580", "--format", "yaml"],
        )
        assert not result.exit_code
        assert "id:" in result.output or "id :" in result.output
        assert "2024-2025" in result.output


def test_seasons_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for seasons."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "--league-id", "1148580", "--columns", "id,title"],
        )
        assert not result.exit_code
        assert "501" in result.output
        assert "2024-2025" in result.output


def test_seasons_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for seasons."""
    output_file = tmp_path / "seasons.json"
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="Test",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "seasons",
                "list",
                "--league-id",
                "1148580",
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )
        assert not result.exit_code
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "501"' in content


def test_seasons_list_csv_output(runner: CliRunner) -> None:
    """The seasons list command should support CSV output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "--league-id", "1148580", "--format", "csv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_seasons_list_tsv_output(runner: CliRunner) -> None:
    """The seasons list command should support TSV output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "--league-id", "1148580", "--format", "tsv"],
        )
        assert not result.exit_code
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        # TSV uses tabs
        assert "\t" in result.output


def test_seasons_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Seasons list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["seasons", "list", "--league-id", "1148580"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_seasons_list_with_env_var(runner: CliRunner) -> None:
    """The league ID can be provided via GAMESHEET_LEAGUE_ID environment variable."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(
            cli,
            ["seasons", "list"],
            env={"GAMESHEET_LEAGUE_ID": "1148580"},
        )
        assert not result.exit_code
        mock_list.assert_called_once()
