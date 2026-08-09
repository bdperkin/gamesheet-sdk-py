# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for leagues get command."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.leagues import League
from tests.helpers import DEFAULT_LEAGUE_NAME


def test_leagues_get(runner: CliRunner) -> None:
    """The leagues get command should retrieve a single league."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.leagues._get_league_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = League(
            id="201",
            association_id="1001",
            title=DEFAULT_LEAGUE_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            ["leagues", "get", "--association-id", "1001", "--league-id", "201"],
        )
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_leagues_get_with_fields(runner: CliRunner) -> None:
    """The leagues get command should support --fields and JSON format."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.leagues._get_league_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = League(
            id="201",
            association_id="1001",
            title=DEFAULT_LEAGUE_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            [
                "leagues",
                "get",
                "--association-id",
                "1001",
                "--league-id",
                "201",
                "--fields",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_leagues_get_empty_fields(runner: CliRunner) -> None:
    """The leagues get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.leagues._get_league_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = League(
            id="201",
            association_id="1001",
            title=DEFAULT_LEAGUE_NAME,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            [
                "leagues",
                "get",
                "--association-id",
                "1001",
                "--league-id",
                "201",
                "--fields",
                ",",
            ],
        )
        assert not result.exit_code
        assert result.output
