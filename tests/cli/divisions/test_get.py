# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for divisions get command."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.divisions import Division


def test_divisions_get(runner: CliRunner) -> None:
    """The divisions get command should retrieve a single division."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.divisions._get_division_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Division(
            id="301",
            season_id="15020",
            title="Test Division",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["divisions", "get", "--division-id", "301"])
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_divisions_get_with_fields(runner: CliRunner) -> None:
    """The divisions get command should support --fields and JSON format."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.divisions._get_division_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Division(
            id="301",
            season_id="15020",
            title="Test Division",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "divisions",
                "get",
                "--division-id",
                "301",
                "--fields",
                "id",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert result.output


def test_divisions_get_empty_fields(runner: CliRunner) -> None:
    """The divisions get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.divisions._get_division_action",
        ) as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Division(
            id="301",
            season_id="15020",
            title="Test Division",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            ["divisions", "get", "--division-id", "301", "--fields", ","],
        )
        assert not result.exit_code
        assert result.output
