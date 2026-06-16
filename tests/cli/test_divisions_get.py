"""Tests for divisions get command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.divisions import Division

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_divisions_get(runner: CliRunner) -> None:
    """The divisions get command should retrieve a single division."""
    with (
        patch("gamesheet_sdk.cli.commands.divisions._get_division_action") as mock_action,
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
        assert result.exit_code == 0
        assert result.output
        assert mock_action.called
