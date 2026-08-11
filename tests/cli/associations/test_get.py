# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for associations get command."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.admin.associations import Association
from gamesheet_sdk.admin.cli.main import cli
from tests.helpers import DEFAULT_ASSOCIATION_NAME

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_associations_get(runner: CliRunner) -> None:
    """The associations get command should retrieve a single association."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._get_association_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title=DEFAULT_ASSOCIATION_NAME,
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(cli, ["associations", "get", "--association-id", "101"])
        assert not result.exit_code
        assert result.output
        assert mock_action.called


def test_associations_get_with_fields(runner: CliRunner) -> None:
    """The associations get command should support --fields option."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._get_association_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title=DEFAULT_ASSOCIATION_NAME,
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            ["associations", "get", "--association-id", "101", "--fields", "id,title"],
        )
        assert not result.exit_code
        assert result.output


def test_associations_get_json_format(runner: CliRunner) -> None:
    """The associations get command should support JSON output format."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._get_association_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title=DEFAULT_ASSOCIATION_NAME,
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            ["associations", "get", "--association-id", "101", "--format", "json"],
        )
        assert not result.exit_code
        assert result.output


def test_associations_get_empty_fields(runner: CliRunner) -> None:
    """The associations get command should handle empty fields spec."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._get_association_action",
        ) as mock_action,
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = Association(
            id="101",
            title=DEFAULT_ASSOCIATION_NAME,
            logo="",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        result = runner.invoke(
            cli,
            ["associations", "get", "--association-id", "101", "--fields", ","],
        )
        assert not result.exit_code
        assert result.output
