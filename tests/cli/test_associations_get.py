"""Tests for associations get command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.associations import Association
from gamesheet_sdk.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_associations_get(runner: CliRunner) -> None:
    """The associations get command should retrieve a single association."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._get_association_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title="Test Association",
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["associations", "get", "--association-id", "101"])
        assert result.exit_code == 0
        assert result.output
        assert mock_action.called


def test_associations_get_with_fields(runner: CliRunner) -> None:
    """The associations get command should support --fields option."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._get_association_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title="Test Association",
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli, ["associations", "get", "--association-id", "101", "--fields", "id,title"],
        )
        assert result.exit_code == 0
        assert result.output


def test_associations_get_json_format(runner: CliRunner) -> None:
    """The associations get command should support JSON output format."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._get_association_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title="Test Association",
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["associations", "get", "--association-id", "101", "--format", "json"])
        assert result.exit_code == 0
        assert result.output


def test_associations_get_empty_fields(runner: CliRunner) -> None:
    """The associations get command should handle empty fields spec."""
    with (
        patch("gamesheet_sdk.cli.commands.associations._get_association_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title="Test Association",
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["associations", "get", "--association-id", "101", "--fields", ","])
        assert result.exit_code == 0
        assert result.output
