# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams create command."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli


def test_teams_create_basic(runner: CliRunner) -> None:
    """The teams create command should work with required arguments."""
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id", "title": "Test Team"},
            "seasonTeam": {"id": 123, "divisionId": 80385},
            "invitation": {"code": "ABC123"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
            ],
        )
        assert not result.exit_code
        mock_create.assert_called_once()


def test_teams_create_with_external_id(runner: CliRunner) -> None:
    """The teams create command should accept external-id."""
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id"},
            "seasonTeam": {"id": 123},
            "invitation": {"code": "XYZ"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
                "--external-id",
                "custom-id",
            ],
        )
        assert not result.exit_code


def test_teams_create_json_output(runner: CliRunner) -> None:
    """The teams create command should support JSON output."""
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id", "title": "Test Team"},
            "seasonTeam": {"id": 123, "divisionId": 80385},
            "invitation": {"code": "ABC123"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert "123" in result.output  # Team ID


def test_teams_create_alias_add_works(runner: CliRunner) -> None:
    """The 'add' alias should invoke the create command."""
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id"},
            "seasonTeam": {"id": 123},
            "invitation": {"code": "XYZ"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "add",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
            ],
        )
        assert not result.exit_code
        mock_create.assert_called_once()


def test_teams_create_alias_new_works(runner: CliRunner) -> None:
    """The 'new' alias should invoke the create command."""
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id"},
            "seasonTeam": {"id": 123},
            "invitation": {"code": "XYZ"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "new",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
            ],
        )
        assert not result.exit_code
        mock_create.assert_called_once()


def test_teams_create_with_output_file(runner: CliRunner, tmp_path: Any) -> None:
    """The teams create command should support --output flag."""
    output_file = tmp_path / "team.json"
    with (
        patch("gamesheet_sdk.teams.create_team") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = {
            "prototeam": {"id": "proto-id", "title": "Test Team"},
            "seasonTeam": {"id": 123, "divisionId": 80385},
            "invitation": {"code": "ABC123"},
        }
        result = runner.invoke(
            cli,
            [
                "teams",
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
                "--output",
                str(output_file),
            ],
        )
        assert not result.exit_code
        assert output_file.exists()
        # When output goes to file, no success message should be printed
        assert "created successfully" not in result.output


def test_teams_create_missing_required_args(runner: CliRunner) -> None:
    """Calling 'teams create' without required args should show an error."""
    result = runner.invoke(cli, ["teams", "create", "--season-id", "15020"])
    assert result.exit_code == 2  # Usage error
    assert "title" in result.output.lower() or "missing option" in result.output.lower()


def test_teams_create_with_no_saved_tokens(runner: CliRunner) -> None:
    """Calling 'teams create' with no saved tokens should fail gracefully."""
    with (
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value=None),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value=None),
    ):
        result = runner.invoke(
            cli,
            [
                "teams",
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Team",
                "--division-id",
                "80385",
            ],
        )
        assert result.exit_code == 1
        assert "login" in result.output.lower()
