# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster coaches get command."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.roster import Coach
from tests.helpers import SEASON_ID


def test_coaches_get(runner: CliRunner) -> None:
    """The coaches get command should retrieve a single coach."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._get_coach_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Coach(
            id="601",
            season_id=SEASON_ID,
            first_name="Jane",
            last_name="Smith",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            ["roster", "--season-id", SEASON_ID, "coaches", "get", "--coach-id", "601"],
        )
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_coaches_get_with_fields(runner: CliRunner) -> None:
    """The coaches get command should support --fields and JSON format."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._get_coach_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Coach(
            id="601",
            season_id=SEASON_ID,
            first_name="Jane",
            last_name="Smith",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "get",
                "--coach-id",
                "601",
                "--fields",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_coaches_get_empty_fields(runner: CliRunner) -> None:
    """The coaches get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.roster_coaches._get_coach_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Coach(
            id="601",
            season_id=SEASON_ID,
            first_name="Jane",
            last_name="Smith",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "get",
                "--coach-id",
                "601",
                "--fields",
                ",",
            ],
        )
        assert not result.exit_code
        assert result.output
