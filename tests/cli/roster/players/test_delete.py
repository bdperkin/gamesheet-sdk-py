# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for roster players delete command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.main import cli


def test_players_delete_requires_player_id() -> None:
    """Test that delete command requires --player-id."""
    result = CliRunner().invoke(
        cli,
        [
            "--base-url",
            "https://test.example.com",
            "roster",
            "--season-id",
            "15020",
            "players",
            "delete",
        ],
    )
    assert result.exit_code
    assert "--player-id" in result.output or "player-id" in result.output.lower()


def test_players_delete_requires_confirmation(mock_session: MagicMock) -> None:
    """Test that delete requires confirmation without --force."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster._delete_player_action") as mock_delete,
    ):
        # Answer 'n' to confirmation
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                "15020",
                "players",
                "delete",
                "--player-id",
                "8116303",
            ],
            input="n\n",
        )
        assert result.exit_code == 1
        mock_delete.assert_not_called()


def test_players_delete_with_confirmation(mock_session: MagicMock) -> None:
    """Test successful delete with confirmation."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster._delete_player_action") as mock_delete,
    ):
        # Answer 'y' to confirmation
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                "15020",
                "players",
                "delete",
                "--player-id",
                "8116303",
            ],
            input="y\n",
        )
        assert not result.exit_code
        assert "deleted successfully" in result.output
        mock_delete.assert_called_once_with(mock_session, "15020", "8116303")


def test_players_delete_with_force(mock_session: MagicMock) -> None:
    """Test successful delete with --force flag."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster._delete_player_action") as mock_delete,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                "15020",
                "players",
                "delete",
                "--player-id",
                "8116303",
                "--force",
            ],
        )
        assert not result.exit_code
        assert "deleted successfully" in result.output
        mock_delete.assert_called_once_with(mock_session, "15020", "8116303")


def test_players_delete_error_handling(mock_session: MagicMock) -> None:
    """Test error handling when delete fails."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch(
            "gamesheet_sdk.cli.commands.roster._delete_player_action",
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
                "15020",
                "players",
                "delete",
                "--player-id",
                "8116303",
                "--force",
            ],
        )
        assert result.exit_code == 1
        assert "Error deleting player" in result.output


def test_players_delete_uses_env_var(mock_session: MagicMock) -> None:
    """Test that delete uses GAMESHEET_PLAYER_ID environment variable."""
    runner = CliRunner()
    with (
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=mock_session,
        ),
        patch("gamesheet_sdk.cli.commands.roster._delete_player_action") as mock_delete,
    ):
        result = runner.invoke(
            cli,
            [
                "--base-url",
                "https://test.example.com",
                "roster",
                "--season-id",
                "15020",
                "players",
                "delete",
                "--force",
            ],
            env={"GAMESHEET_PLAYER_ID": "8116303"},
        )
        assert not result.exit_code
        mock_delete.assert_called_once_with(mock_session, "15020", "8116303")
