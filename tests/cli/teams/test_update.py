# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams update command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.teams import Team
from tests.helpers import (
    ASSOCIATION_ID,
    DEFAULT_TEAM_NAME,
    SEASON_ID,
)

# Mock team used in tests
_MOCK_TEAM = Team(
    id=ASSOCIATION_ID,
    season_id=SEASON_ID,
    title=DEFAULT_TEAM_NAME,
    division_id="80385",
    logo=None,
    invitation_code="ABC123",
    player_count=0,
    coach_count=0,
    created_at="2026-06-13T18:00:00Z",
    updated_at="2026-06-13T18:00:00Z",
)


def test_teams_update_basic(runner: CliRunner) -> None:
    """The teams update command should work with required arguments."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "Updated Team",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()


def test_teams_update_multiple_fields(runner: CliRunner) -> None:
    """The teams update command should accept multiple fields."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "New Title",
                "--division-id",
                "99999",
                "--external-id",
                "custom-id",
            ],
        )
        assert not result.exit_code


def test_teams_update_remove_logo(runner: CliRunner) -> None:
    """The teams update command should support --remove-logo."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--remove-logo",
            ],
        )
        assert not result.exit_code


def test_teams_update_json_output(runner: CliRunner) -> None:
    """The teams update command should support JSON output."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "Updated Team",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert ASSOCIATION_ID in result.output  # Team ID


def test_teams_update_alias_set_works(runner: CliRunner) -> None:
    """The 'set' alias should invoke the update command."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "set",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "New Title",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()


def test_teams_update_alias_edit_works(runner: CliRunner) -> None:
    """The 'edit' alias should invoke the update command."""
    with (
        patch("gamesheet_sdk.teams.update_team") as mock_update,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_update.return_value = _MOCK_TEAM
        result = runner.invoke(
            cli,
            [
                "teams",
                "edit",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "New Title",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()


def test_teams_update_missing_team_id(runner: CliRunner) -> None:
    """Calling 'teams update' without team-id should show an error."""
    result = runner.invoke(
        cli,
        ["teams", "update", "--season-id", SEASON_ID, "--title", "New"],
    )
    assert result.exit_code == 2  # Usage error
    assert "team-id" in result.output.lower() or "missing option" in result.output.lower()


def test_teams_update_with_no_saved_tokens(runner: CliRunner) -> None:
    """Calling 'teams update' with no saved tokens should fail gracefully."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
                "--title",
                "New Title",
            ],
        )
        assert result.exit_code == 1
        assert "login" in result.output.lower()


def test_teams_update_with_no_fields_shows_error(runner: CliRunner) -> None:
    """Calling 'teams update' with no update fields should show a helpful error."""
    with (
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
            ],
        )
        assert result.exit_code == 1
        assert "at least one field must be provided" in result.output.lower()
