"""Tests for seasons get command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.seasons import SeasonDetail

if TYPE_CHECKING:

    from click.testing import CliRunner


def test_seasons_get_alias_show_works(runner: CliRunner) -> None:
    """The 'show' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "show", "--season-id", "15020"])
        assert result.exit_code == 0
        mock_get.assert_called_once()


def test_seasons_get_alias_view_works(runner: CliRunner) -> None:
    """The 'view' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "view", "--season-id", "15020"])
        assert result.exit_code == 0
        mock_get.assert_called_once()


def test_seasons_get_missing_season_id_shows_error(runner: CliRunner) -> None:
    """Calling 'seasons get' without a season ID should show an error."""
    result = runner.invoke(cli, ["seasons", "get"])
    assert result.exit_code == 2  # Usage error
    assert "season-id" in result.output.lower() or "missing option" in result.output.lower()


def test_seasons_get_json_output(runner: CliRunner) -> None:
    """The seasons get command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season 2026",
            external_id="test-uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020", "--format", "json"])
        assert result.exit_code == 0
        assert '"id": "15020"' in result.output
        assert '"title": "Test Season 2026"' in result.output
        assert '"sport": "hockey"' in result.output


def test_seasons_get_yaml_output(runner: CliRunner) -> None:
    """The seasons get command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020", "--format", "yaml"])
        assert result.exit_code == 0
        assert "id:" in result.output or "id :" in result.output
        assert "Test Season" in result.output


def test_seasons_get_fields_filter(runner: CliRunner) -> None:
    """The --fields option should filter output fields for seasons get."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020", "--fields", "id,title,sport"])
        assert result.exit_code == 0
        assert "15020" in result.output
        assert "Test Season" in result.output


def test_seasons_get_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for seasons get."""
    output_file = tmp_path / "season.json"
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(
            cli,
            ["seasons", "get", "--season-id", "15020", "--format", "json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "15020"' in content


def test_seasons_get_table_format(runner: CliRunner) -> None:
    """The seasons get command should support table formats with key-value pairs."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020", "--format", "simple"])
        assert result.exit_code == 0
        # Should have field and value columns
        assert "field" in result.output.lower() or "15020" in result.output
        assert "Test Season" in result.output


def test_seasons_get_grid_format(runner: CliRunner) -> None:
    """The seasons get command should support grid format."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020", "--format", "grid"])
        assert result.exit_code == 0
        # Grid format should have borders
        assert "+" in result.output or "|" in result.output


def test_seasons_get_with_no_saved_tokens(runner: CliRunner) -> None:
    """Seasons get should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["seasons", "get", "--season-id", "15020"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_seasons_get_with_env_var(runner: CliRunner) -> None:
    """The season ID can be provided via GAMESHEET_SEASON_ID environment variable."""
    with (
        patch("gamesheet_sdk.cli.commands.seasons._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_get.return_value = SeasonDetail(
            id="15020",
            association_id="38",
            league_id="1148580",
            title="Test Season",
            external_id="uuid",
            start_date="2026-01-01",
            end_date="2026-12-31",
            sport="hockey",
            stats_year="2026",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        result = runner.invoke(cli, ["seasons", "get"], env={"GAMESHEET_SEASON_ID": "15020"})
        assert result.exit_code == 0
        mock_get.assert_called_once()
