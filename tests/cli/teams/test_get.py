# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams get command."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.teams import Team
from tests.helpers import DEFAULT_TEAM_NAME, SEASON_ID

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_teams_get(runner: CliRunner) -> None:
    """The teams get command should retrieve a single team."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id=SEASON_ID,
            title=DEFAULT_TEAM_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            ["teams", "get", "--season-id", SEASON_ID, "--team-id", "401"],
        )
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_teams_get_with_fields(runner: CliRunner) -> None:
    """The teams get command should support --columns and JSON format."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id=SEASON_ID,
            title=DEFAULT_TEAM_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            [
                "teams",
                "get",
                "--season-id",
                SEASON_ID,
                "--team-id",
                "401",
                "--columns",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_teams_get_empty_fields(runner: CliRunner) -> None:
    """The teams get command should handle empty fields spec."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.teams._get_team_action") as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Team(
            id="401",
            season_id=SEASON_ID,
            title=DEFAULT_TEAM_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            [
                "teams",
                "get",
                "--season-id",
                SEASON_ID,
                "--team-id",
                "401",
                "--columns",
                ",",
            ],
        )
        assert not result.exit_code
        assert result.output
