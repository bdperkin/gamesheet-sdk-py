# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games delete CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli


def test_scheduled_delete_command(runner: CliRunner) -> None:
    """Test scheduled game delete command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.games_scheduled._delete_scheduled_game_action",
        ) as mock_delete,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_delete.return_value = None

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-del",
                "scheduled",
                "delete",
                "--game-id",
                "game-del-123",
                "--force",
            ],
        )

        assert not result.exit_code
        assert "Successfully deleted scheduled game game-del-123" in result.output
        mock_delete.assert_called_once()
        args = mock_delete.call_args[0]
        assert args[1] == "season-del"
        assert args[2] == "game-del-123"
