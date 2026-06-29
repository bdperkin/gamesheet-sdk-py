# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster coaches delete command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.main import cli
from tests.helpers import COACH_ID_SECONDARY, SEASON_ID


def test_coaches_delete_requires_coach_id() -> None:
    """Test that delete command requires --coach-id."""
    result = CliRunner().invoke(
        cli,
        [
            "--base-url",
            "https://test.example.com",
            "roster",
            "--season-id",
            SEASON_ID,
            "coaches",
            "delete",
        ],
    )
    assert result.exit_code
    assert "--coach-id" in result.output or "coach-id" in result.output.lower()


def test_coaches_delete_requires_confirmation(mock_session: MagicMock) -> None:
    """Test that delete requires confirmation without --force."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster_coaches._delete_coach_action") as mock_delete,
    ):
        # Answer 'n' to confirmation
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "delete",
                "--coach-id",
                COACH_ID_SECONDARY,
            ],
            input="n\n",
        )
        assert result.exit_code == 1
        mock_delete.assert_not_called()


def test_coaches_delete_with_confirmation(mock_session: MagicMock) -> None:
    """Test successful delete with confirmation."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster_coaches._delete_coach_action") as mock_delete,
    ):
        # Answer 'y' to confirmation
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "delete",
                "--coach-id",
                COACH_ID_SECONDARY,
            ],
            input="y\n",
        )
        assert not result.exit_code
        assert "deleted successfully" in result.output
        mock_delete.assert_called_once_with(mock_session, SEASON_ID, COACH_ID_SECONDARY)


def test_coaches_delete_with_force(mock_session: MagicMock) -> None:
    """Test successful delete with --force flag."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster_coaches._delete_coach_action") as mock_delete,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "delete",
                "--coach-id",
                COACH_ID_SECONDARY,
                "--force",
            ],
        )
        assert not result.exit_code
        assert "deleted successfully" in result.output
        mock_delete.assert_called_once_with(mock_session, SEASON_ID, COACH_ID_SECONDARY)


def test_coaches_delete_error_handling(mock_session: MagicMock) -> None:
    """Test error handling when delete fails."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches._delete_coach_action",
            side_effect=Exception("Delete failed"),
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "delete",
                "--coach-id",
                COACH_ID_SECONDARY,
                "--force",
            ],
        )
        assert result.exit_code == 1
        assert "Error deleting coach" in result.output


def test_coaches_delete_uses_env_var(mock_session: MagicMock) -> None:
    """Test that delete uses GAMESHEET_COACH_ID environment variable."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster_coaches.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster_coaches._delete_coach_action") as mock_delete,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                SEASON_ID,
                "coaches",
                "delete",
                "--force",
            ],
            env={"GAMESHEET_COACH_ID": COACH_ID_SECONDARY},
        )
        assert not result.exit_code
        mock_delete.assert_called_once_with(mock_session, SEASON_ID, COACH_ID_SECONDARY)
