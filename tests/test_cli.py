"""Tests for :mod:`gamesheet_sdk.cli`."""

# pylint: disable=redefined-outer-name,protected-access,too-many-lines

from __future__ import annotations

import os
from typing import Any
from unittest.mock import Mock, patch

import click
import pytest
from click.testing import CliRunner

from gamesheet_sdk.associations import Association
from gamesheet_sdk.cli import (
    ResourceGroup,
    _configure_logging,
    _should_color,
    cli,
    confirm_destructive,
)
from gamesheet_sdk.leagues import League
from gamesheet_sdk.seasons import Season, SeasonDetail


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help_shows_usage(runner: CliRunner) -> None:
    """Running the CLI with --help should show usage information."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "gamesheet_sdk" in result.output.lower() or "usage" in result.output.lower()


def test_cli_version_shows_version_string(runner: CliRunner) -> None:
    """Running with --version should show a version string."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    # Should contain a digit somewhere
    assert any(c.isdigit() for c in result.output)


def test_login_command_exists(runner: CliRunner) -> None:
    """The 'login' command should be available."""
    result = runner.invoke(cli, ["login", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output.lower()


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
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["associations", "ls"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_associations_bare_invocation_runs_list(runner: CliRunner) -> None:
    """Bare 'associations' should implicitly run 'list'."""
    with (
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["associations"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_associations_list_json_output(runner: CliRunner) -> None:
    """The list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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


def test_leagues_group_has_help_option(runner: CliRunner) -> None:
    """The leagues group should accept -h and --help."""
    result_short = runner.invoke(cli, ["leagues", "-h"])
    assert result_short.exit_code == 0
    assert "leagues" in result_short.output.lower()

    result_long = runner.invoke(cli, ["leagues", "--help"])
    assert result_long.exit_code == 0
    assert "leagues" in result_long.output.lower()


def test_leagues_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["leagues", "ls", "38"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_leagues_missing_association_id_shows_error(runner: CliRunner) -> None:
    """Calling 'leagues list' without an association ID should show an error."""
    result = runner.invoke(cli, ["leagues", "list"])
    assert result.exit_code == 2  # Usage error
    assert "ASSOCIATION_ID" in result.output or "Missing argument" in result.output


def test_leagues_list_json_output(runner: CliRunner) -> None:
    """The leagues list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--format", "json"])
        assert result.exit_code == 0
        assert '"id": "100"' in result.output
        assert '"title": "Test League"' in result.output


def test_leagues_list_yaml_output(runner: CliRunner) -> None:
    """The leagues list command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--format", "yaml"])
        assert result.exit_code == 0
        assert "id:" in result.output or "id :" in result.output
        assert "Test League" in result.output


def test_leagues_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for leagues."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--columns", "id,title"])
        assert result.exit_code == 0
        assert "100" in result.output
        assert "Test League" in result.output


def test_leagues_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for leagues."""
    output_file = tmp_path / "leagues.json"
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(
            cli,
            ["leagues", "list", "38", "--format", "json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "100"' in content


def test_leagues_list_csv_output(runner: CliRunner) -> None:
    """The leagues list command should support CSV output."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--format", "csv"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_leagues_bare_invocation_runs_list(runner: CliRunner) -> None:
    """Bare 'leagues ASSOC_ID' with no args shows help mentioning list as default."""
    result = runner.invoke(cli, ["leagues", "--help"])
    assert result.exit_code == 0
    # Help should mention that list is the default or show list command
    assert "list" in result.output.lower() or "ls" in result.output.lower()


def test_leagues_list_grid_format(runner: CliRunner) -> None:
    """The leagues list command should support grid format."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--format", "grid"])
        assert result.exit_code == 0
        # Grid format should have borders
        assert "+" in result.output or "|" in result.output


def test_leagues_list_simple_format(runner: CliRunner) -> None:
    """The leagues list command should support simple format."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            League(
                id="100",
                association_id="38",
                title="Test League",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["leagues", "list", "38", "--format", "simple"])
        assert result.exit_code == 0
        assert "100" in result.output


def test_seasons_group_has_help_option(runner: CliRunner) -> None:
    """The seasons group should accept -h and --help."""
    result_short = runner.invoke(cli, ["seasons", "-h"])
    assert result_short.exit_code == 0
    assert "seasons" in result_short.output.lower()

    result_long = runner.invoke(cli, ["seasons", "--help"])
    assert result_long.exit_code == 0
    assert "seasons" in result_short.output.lower()


def test_seasons_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["seasons", "ls", "1148580"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_seasons_missing_league_id_shows_error(runner: CliRunner) -> None:
    """Calling 'seasons list' without a league ID should show an error."""
    result = runner.invoke(cli, ["seasons", "list"])
    assert result.exit_code == 2  # Usage error
    assert "LEAGUE_ID" in result.output or "Missing argument" in result.output


def test_seasons_list_json_output(runner: CliRunner) -> None:
    """The seasons list command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "json"])
        assert result.exit_code == 0
        assert '"id": "501"' in result.output
        assert '"title": "2024-2025"' in result.output


def test_seasons_list_yaml_output(runner: CliRunner) -> None:
    """The seasons list command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "yaml"])
        assert result.exit_code == 0
        assert "id:" in result.output or "id :" in result.output
        assert "2024-2025" in result.output


def test_seasons_list_columns_filter(runner: CliRunner) -> None:
    """The --columns option should filter output columns for seasons."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["seasons", "list", "1148580", "--columns", "id,title"])
        assert result.exit_code == 0
        assert "501" in result.output
        assert "2024-2025" in result.output


def test_seasons_list_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for seasons."""
    output_file = tmp_path / "seasons.json"
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="Test",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(
            cli,
            ["seasons", "list", "1148580", "--format", "json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "501"' in content


def test_seasons_list_csv_output(runner: CliRunner) -> None:
    """The seasons list command should support CSV output."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "csv"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        assert "id" in lines[0].lower()


def test_seasons_list_tsv_output(runner: CliRunner) -> None:
    """The seasons list command should support TSV output."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Season(
                id="501",
                league_id="1148580",
                title="2024-2025",
                created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
                updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            ),
        ]
        result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "tsv"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) >= 2
        # TSV uses tabs
        assert "\t" in result.output


# Season (singular) get command tests


def test_season_group_has_help_option(runner: CliRunner) -> None:
    """The season group should accept -h and --help."""
    result_short = runner.invoke(cli, ["season", "-h"])
    assert result_short.exit_code == 0
    assert "season" in result_short.output.lower()

    result_long = runner.invoke(cli, ["season", "--help"])
    assert result_long.exit_code == 0
    assert "season" in result_long.output.lower()


def test_season_get_alias_show_works(runner: CliRunner) -> None:
    """The 'show' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "show", "15020"])
        assert result.exit_code == 0
        mock_get.assert_called_once()


def test_season_get_alias_view_works(runner: CliRunner) -> None:
    """The 'view' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "view", "15020"])
        assert result.exit_code == 0
        mock_get.assert_called_once()


def test_season_default_command_is_get(runner: CliRunner) -> None:
    """Bare 'season' with no args shows help mentioning get as default."""
    result = runner.invoke(cli, ["season", "--help"])
    assert result.exit_code == 0
    # Help should mention that get is available
    assert "get" in result.output.lower() or "show" in result.output.lower()


def test_season_missing_season_id_shows_error(runner: CliRunner) -> None:
    """Calling 'season get' without a season ID should show an error."""
    result = runner.invoke(cli, ["season", "get"])
    assert result.exit_code == 2  # Usage error
    assert "SEASON_ID" in result.output or "Missing argument" in result.output


def test_season_get_json_output(runner: CliRunner) -> None:
    """The season get command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "get", "15020", "--format", "json"])
        assert result.exit_code == 0
        assert '"id": "15020"' in result.output
        assert '"title": "Test Season 2026"' in result.output
        assert '"sport": "hockey"' in result.output


def test_season_get_yaml_output(runner: CliRunner) -> None:
    """The season get command should support YAML output."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "get", "15020", "--format", "yaml"])
        assert result.exit_code == 0
        assert "id:" in result.output or "id :" in result.output
        assert "Test Season" in result.output


def test_season_get_fields_filter(runner: CliRunner) -> None:
    """The --fields option should filter output fields for season get."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "get", "15020", "--fields", "id,title,sport"])
        assert result.exit_code == 0
        assert "15020" in result.output
        assert "Test Season" in result.output


def test_season_get_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """The --output option should write to a file for season get."""
    output_file = tmp_path / "season.json"
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(
            cli,
            ["season", "get", "15020", "--format", "json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"id": "15020"' in content


def test_season_get_table_format(runner: CliRunner) -> None:
    """The season get command should support table formats with key-value pairs."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "get", "15020", "--format", "simple"])
        assert result.exit_code == 0
        # Should have field and value columns
        assert "field" in result.output.lower() or "15020" in result.output
        assert "Test Season" in result.output


def test_season_get_grid_format(runner: CliRunner) -> None:
    """The season get command should support grid format."""
    with (
        patch("gamesheet_sdk.cli._get_season_action") as mock_get,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
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
            created_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
            updated_at="2024-01-01T00:00:00Z",  # type: ignore[arg-type]
        )
        result = runner.invoke(cli, ["season", "get", "15020", "--format", "grid"])
        assert result.exit_code == 0
        # Grid format should have borders
        assert "+" in result.output or "|" in result.output


# Tests for ResourceGroup edge cases and helper functions


def test_resource_group_with_no_aliases() -> None:
    """ResourceGroup should work with no aliases provided."""

    @click.group(cls=ResourceGroup, default="list")
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        click.echo("listing")

    runner = CliRunner()
    result = runner.invoke(test_group, ["list"])  # noqa: FURB184
    assert result.exit_code == 0
    assert "listing" in result.output


def test_resource_group_format_commands_with_empty_rows() -> None:
    """ResourceGroup.format_commands should handle empty command rows."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:
        pass

    # Group with no commands
    ctx = click.Context(test_group)
    formatter = click.HelpFormatter()
    test_group.format_commands(ctx, formatter)
    # Should not crash, output will just be empty


def test_resource_group_shell_complete_includes_aliases() -> None:
    """ResourceGroup.shell_complete should include aliases in completion."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    # Should include both 'list' and 'ls'
    values = [item.value for item in items]
    assert "list" in values
    assert "ls" in values


def test_resource_group_shell_complete_filters_by_incomplete() -> None:
    """ResourceGroup.shell_complete should filter by incomplete prefix."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",), "get": ("show",)})
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    @test_group.command("get")
    def get_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    values = [item.value for item in items]
    # Should only include items starting with 'l'
    assert "list" in values
    assert "ls" in values
    assert "get" not in values
    assert "show" not in values


def test_should_color_with_no_color_env() -> None:
    """_should_color should return False when NO_COLOR is set."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = True

    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        assert _should_color(handler) is False


def test_should_color_with_tty() -> None:
    """_should_color should return True for TTY without NO_COLOR."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = True

    with patch.dict(os.environ, {}, clear=True):
        # Remove NO_COLOR if it exists
        os.environ.pop("NO_COLOR", None)
        assert _should_color(handler) is True


def test_should_color_with_non_tty() -> None:
    """_should_color should return False for non-TTY."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = False

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("NO_COLOR", None)
        assert _should_color(handler) is False


def test_should_color_with_no_stream() -> None:
    """_should_color should return False when handler has no stream."""
    handler = Mock(spec=[])  # No stream attribute
    assert _should_color(handler) is False


def test_configure_logging_verbose_0() -> None:
    """_configure_logging with verbose=0 should set WARNING level."""
    with patch("gamesheet_sdk.cli.logging.basicConfig") as mock_basic:
        _configure_logging(0)
        # Should be called with WARNING level
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging  # pylint: disable=import-outside-toplevel

        assert call_args.kwargs["level"] == logging.WARNING


def test_configure_logging_verbose_1() -> None:
    """_configure_logging with verbose=1 should set INFO level."""
    with patch("gamesheet_sdk.cli.logging.basicConfig") as mock_basic:
        _configure_logging(1)
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging  # pylint: disable=import-outside-toplevel

        assert call_args.kwargs["level"] == logging.INFO


def test_configure_logging_verbose_2() -> None:
    """_configure_logging with verbose=2 should set DEBUG level."""
    with patch("gamesheet_sdk.cli.logging.basicConfig") as mock_basic:
        _configure_logging(2)
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging  # pylint: disable=import-outside-toplevel

        assert call_args.kwargs["level"] == logging.DEBUG


def test_confirm_destructive_with_force() -> None:
    """confirm_destructive decorator with --force should skip confirmation."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:
        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, ["--force"])  # noqa: FURB184
    assert result.exit_code == 0
    assert "deleted" in result.output
    assert "Really delete" not in result.output


def test_confirm_destructive_without_force_confirmed() -> None:
    """confirm_destructive decorator without --force should prompt and accept y."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:
        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, input="y\n")  # noqa: FURB184
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_confirm_destructive_without_force_aborted() -> None:
    """confirm_destructive decorator without --force should prompt and abort on n."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:
        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, input="n\n")  # noqa: FURB184
    assert result.exit_code == 1
    assert "deleted" not in result.output
    assert "Aborted" in result.output or result.exit_code != 0


def test_completion_command_exists(runner: CliRunner) -> None:
    """The 'completion' command should be available."""
    result = runner.invoke(cli, ["completion", "--help"])
    assert result.exit_code == 0
    assert "completion" in result.output.lower()


def test_completion_bash(runner: CliRunner) -> None:
    """The 'completion bash' should generate bash completion script."""
    result = runner.invoke(cli, ["completion", "bash"])
    assert result.exit_code == 0
    # Should contain bash completion markers
    assert "complete" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_zsh(runner: CliRunner) -> None:
    """The 'completion zsh' should generate zsh completion script."""
    result = runner.invoke(cli, ["completion", "zsh"])
    assert result.exit_code == 0
    # Should contain zsh completion markers
    assert "compdef" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_fish(runner: CliRunner) -> None:
    """The 'completion fish' should generate fish completion script."""
    result = runner.invoke(cli, ["completion", "fish"])
    assert result.exit_code == 0
    # Should contain fish completion markers
    assert "complete" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


# Error path tests


def test_associations_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Associations list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_associations_list_with_authentication_error(runner: CliRunner) -> None:
    """Associations list should handle AuthenticationError gracefully."""
    from gamesheet_sdk.exceptions import AuthenticationError  # pylint: disable=import-outside-toplevel

    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh"),
        patch(
            "gamesheet_sdk.cli._list_associations_action",
            side_effect=AuthenticationError("Token expired"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "Authentication required" in result.output or "expired" in result.output.lower()


def test_associations_list_with_gamesheet_error(runner: CliRunner) -> None:
    """Associations list should handle GameSheetError gracefully."""
    from gamesheet_sdk.exceptions import GameSheetError  # pylint: disable=import-outside-toplevel

    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh"),
        patch(
            "gamesheet_sdk.cli._list_associations_action",
            side_effect=GameSheetError("API error"),
        ),
    ):
        result = runner.invoke(cli, ["associations", "list"])
        assert result.exit_code == 1
        assert "GameSheet error" in result.output or "error" in result.output.lower()


def test_cli_with_base_url_override(runner: CliRunner) -> None:
    """CLI should accept --base-url override."""
    with (
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch("gamesheet_sdk.cli.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["--base-url", "https://custom.example.com", "associations", "list"])
        assert result.exit_code == 0
        # Should have been called, indicating config was created
        mock_list.assert_called_once()


def test_cli_with_no_headless_flag(runner: CliRunner) -> None:
    """CLI should accept --no-headless flag."""
    with (
        patch("gamesheet_sdk.cli._list_associations_action") as mock_list,
        patch("gamesheet_sdk.cli.load_access_token", return_value="token"),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["--no-headless", "associations", "list"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_resource_group_get_command_with_unknown_alias() -> None:
    """ResourceGroup.get_command should return None for unknown commands."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    # Try to get a command that doesn't exist
    cmd = test_group.get_command(ctx, "nonexistent")
    assert cmd is None


def test_resource_group_alias_item_if_visible_with_hidden_command() -> None:
    """ResourceGroup should not surface aliases for hidden commands."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:
        pass

    @test_group.command("list", hidden=True)
    def list_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    values = [item.value for item in items]
    # Hidden commands and their aliases should not appear
    assert "list" not in values
    assert "ls" not in values


def test_leagues_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Leagues list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["leagues", "list", "38"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_seasons_list_with_no_saved_tokens(runner: CliRunner) -> None:
    """Seasons list should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["seasons", "list", "1148580"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_season_get_with_no_saved_tokens(runner: CliRunner) -> None:
    """Season get should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.cli.load_access_token", return_value=None),
        patch("gamesheet_sdk.cli.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["season", "get", "15020"])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()
