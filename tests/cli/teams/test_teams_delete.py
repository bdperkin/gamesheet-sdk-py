"""Tests for teams delete command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_teams_delete_basic(runner: CliRunner) -> None:
    """The teams delete command should delete a team."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._delete_team_action") as mock_delete,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_delete.return_value = None
        result = runner.invoke(
            cli,
            ["teams", "delete", "--season-id", "15020", "--team-id", "123"],
        )
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        mock_delete.assert_called_once()


def test_teams_delete_alias_rm(runner: CliRunner) -> None:
    """The 'rm' alias should invoke the delete command."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._delete_team_action") as mock_delete,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_delete.return_value = None
        result = runner.invoke(
            cli,
            ["teams", "rm", "--season-id", "15020", "--team-id", "123"],
        )
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        mock_delete.assert_called_once()


def test_teams_delete_alias_remove(runner: CliRunner) -> None:
    """The 'remove' alias should invoke the delete command."""
    with (
        patch("gamesheet_sdk.cli.commands.teams._delete_team_action") as mock_delete,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_delete.return_value = None
        result = runner.invoke(
            cli,
            ["teams", "remove", "--season-id", "15020", "--team-id", "123"],
        )
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        mock_delete.assert_called_once()


def test_teams_delete_missing_team_id(runner: CliRunner) -> None:
    """Calling 'teams delete' without team-id should show an error."""
    result = runner.invoke(cli, ["teams", "delete", "--season-id", "15020"])
    assert result.exit_code == 2  # Usage error
    assert "team-id" in result.output.lower() or "missing option" in result.output.lower()


def test_teams_delete_with_no_saved_tokens(runner: CliRunner) -> None:
    """Calling 'teams delete' with no saved tokens should fail gracefully."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
    ):
        result = runner.invoke(
            cli,
            ["teams", "delete", "--season-id", "15020", "--team-id", "123"],
        )
        assert result.exit_code == 1
        assert "login" in result.output.lower()
