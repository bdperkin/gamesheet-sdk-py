# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for referees delete command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.admin.cli.main import cli
from tests.helpers import SEASON_ID

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_referees_delete_with_force(runner: CliRunner) -> None:
    """The referees delete command should work with --force flag."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._delete_referee_action",
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
                "referees",
                "delete",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146200",
                "--force",
            ],
        )
        assert not result.exit_code
        mock_delete.assert_called_once()
        args = mock_delete.call_args[0]
        assert args[1] == SEASON_ID
        assert args[2] == "1146200"
        assert "deleted successfully" in result.output


def test_referees_delete_alias_rm(runner: CliRunner) -> None:
    """The 'rm' alias should invoke the delete command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._delete_referee_action",
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
                "referees",
                "rm",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146201",
                "--force",
            ],
        )
        assert not result.exit_code
        mock_delete.assert_called_once()


def test_referees_delete_alias_remove(runner: CliRunner) -> None:
    """The 'remove' alias should invoke the delete command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._delete_referee_action",
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
                "referees",
                "remove",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146202",
                "--force",
            ],
        )
        assert not result.exit_code
        mock_delete.assert_called_once()


def test_referees_delete_missing_referee_id_shows_error(runner: CliRunner) -> None:
    """Calling 'referees delete' without referee ID should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "delete",
            "--season-id",
            SEASON_ID,
            "--force",
        ],
    )
    assert result.exit_code == 2
    assert "referee-id" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_delete_without_force_prompts_confirmation(runner: CliRunner) -> None:
    """Calling 'referees delete' without --force should prompt for confirmation."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._delete_referee_action",
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
        # User answers 'n' to confirmation
        result = runner.invoke(
            cli,
            [
                "referees",
                "delete",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146203",
            ],
            input="n\n",
        )
        assert result.exit_code == 1
        mock_delete.assert_not_called()
        assert "aborted" in result.output.lower()
