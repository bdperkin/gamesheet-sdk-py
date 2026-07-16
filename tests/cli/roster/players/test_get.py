# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster players get command."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.roster import Player
from tests.helpers import CLI_TEST_SEASON_ID, DEFAULT_PLAYER_LAST_NAME, SEASON_ID


def test_players_get(runner: CliRunner) -> None:
    """The players get command should retrieve a single player."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_players._get_player_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id=CLI_TEST_SEASON_ID,
            season_id=SEASON_ID,
            first_name="John",
            last_name=DEFAULT_PLAYER_LAST_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "roster",
                "--season-id",
                SEASON_ID,
                "players",
                "get",
                "--player-id",
                CLI_TEST_SEASON_ID,
            ],
        )
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_players_get_with_fields(runner: CliRunner) -> None:
    """The players get command should support --fields and JSON format."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_players._get_player_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id=CLI_TEST_SEASON_ID,
            season_id=SEASON_ID,
            first_name="John",
            last_name=DEFAULT_PLAYER_LAST_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "roster",
                "--season-id",
                SEASON_ID,
                "players",
                "get",
                "--player-id",
                CLI_TEST_SEASON_ID,
                "--fields",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_players_get_empty_fields(runner: CliRunner) -> None:
    """The players get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_players._get_player_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Player(
            id=CLI_TEST_SEASON_ID,
            season_id=SEASON_ID,
            first_name="John",
            last_name=DEFAULT_PLAYER_LAST_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "roster",
                "--season-id",
                SEASON_ID,
                "players",
                "get",
                "--player-id",
                CLI_TEST_SEASON_ID,
                "--fields",
                ",",
            ],
        )
        assert not result.exit_code
        assert result.output
