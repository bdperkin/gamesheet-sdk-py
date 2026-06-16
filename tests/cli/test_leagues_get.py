"""Tests for leagues get command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.leagues import League

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_leagues_get(runner: CliRunner) -> None:
    """The leagues get command should retrieve a single league."""
    with (
        patch("gamesheet_sdk.cli.commands.leagues._get_league_action") as mock_action,
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="tok"),
    ):
        mock_action.return_value = League(
            id="201",
            association_id="1001",
            title="Test League",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        result = runner.invoke(cli, ["leagues", "get", "--association-id", "1001", "--league-id", "201"])
        assert result.exit_code == 0
        assert result.output
        assert mock_action.called
