# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test coverage for divisions teams commands."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.commands.divisions import divisions_group
from tests.helpers import ASSOCIATION_ID, SEASON_ID


def test_divisions_teams_get_coverage() -> None:
    """Ensure divisions teams get command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.admin.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.cli.commands.divisions.run_action_or_exit",
            return_value=MagicMock(
                model_dump=lambda **__kw: {"id": "1", "title": "Team 1"},
            ),
        ),
        patch("gamesheet_sdk.admin.cli.commands.divisions.render_list_command"),
    ):
        # Test JSON format
        result = runner.invoke(
            divisions_group,
            ["teams", "get", "--season-id", "100", "--team-id", "1", "-F", "json"],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # Test tabular format
        result = runner.invoke(
            divisions_group,
            ["teams", "get", "--season-id", "100", "--team-id", "1", "-F", "plain"],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_teams_create_coverage() -> None:
    """Ensure divisions teams create command body is covered."""
    runner = CliRunner()

    with (
        patch("gamesheet_sdk.admin.cli.helpers.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.teams.create_team",
            return_value={
                "prototeam": {"title": "New Team"},
                "seasonTeam": {"id": "999"},
            },
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.run_action_or_exit",
            side_effect=lambda session, action, *args, **kw: action(session, *args, **kw),
        ),
        patch("gamesheet_sdk.admin.cli.shared.render_get_command"),
        patch("gamesheet_sdk.admin.cli.helpers.click.secho"),
    ):
        # Test JSON format
        result = runner.invoke(
            divisions_group,
            [
                "teams",
                "create",
                "--season-id",
                "100",
                "--division-id",
                "50",
                "--title",
                "New Team",
                "-F",
                "json",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # Test tabular format
        result = runner.invoke(
            divisions_group,
            [
                "teams",
                "create",
                "--season-id",
                "100",
                "--division-id",
                "50",
                "--title",
                "New Team",
                "-F",
                "plain",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # Test with output file to cover the else branch
        result = runner.invoke(
            divisions_group,
            [
                "teams",
                "create",
                "--season-id",
                "100",
                "--division-id",
                "50",
                "--title",
                "New Team",
                "-F",
                "json",
                "--output",
                str(Path(tempfile.gettempdir()) / "output.json"),
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_teams_update_coverage() -> None:
    """Ensure divisions teams update command body is covered."""
    runner = CliRunner()

    with (
        patch("gamesheet_sdk.admin.cli.helpers.build_authenticated_session"),
        patch(
            "gamesheet_sdk.admin.teams.update_team",
            return_value=MagicMock(
                model_dump=lambda **__kw: {"id": "1", "title": "Updated Team"},
            ),
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.run_action_or_exit",
            side_effect=lambda session, action, *args, **kw: action(session, *args, **kw),
        ),
        patch("gamesheet_sdk.admin.cli.shared.render_list_command"),
    ):
        result = runner.invoke(
            divisions_group,
            [
                "teams",
                "update",
                "--season-id",
                "100",
                "--team-id",
                "1",
                "--title",
                "Updated Team",
                "-F",
                "json",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_teams_delete_coverage() -> None:
    """Ensure divisions teams delete command body is covered."""
    runner = CliRunner()
    with patch("gamesheet_sdk.admin.cli.commands.divisions.run_team_delete"):
        result = runner.invoke(
            divisions_group,
            ["teams", "delete", "--season-id", "100", "--team-id", "1", "--force"],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_teams_update_with_no_fields_shows_error() -> None:
    """Calling 'divisions teams update' with no update fields should show a helpful error."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        result = runner.invoke(
            divisions_group,
            [
                "teams",
                "update",
                "--season-id",
                SEASON_ID,
                "--team-id",
                ASSOCIATION_ID,
            ],
            obj=MagicMock(),
        )
        assert result.exit_code == 1
        assert "at least one field must be provided" in result.output.lower()
