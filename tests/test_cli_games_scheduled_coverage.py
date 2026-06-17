"""Test coverage for games scheduled get command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.games import games_group


def test_games_scheduled_get_coverage() -> None:
    """Ensure games scheduled get command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=MagicMock(
                model_dump=lambda **_: {"id": 123, "status": "scheduled", "date": "2024-01-01"},
            ),
        ),
        patch("gamesheet_sdk.cli.commands.games.render_get_command"),
    ):
        result = runner.invoke(
            games_group,
            ["--season-id", "100", "scheduled", "get", "--game-id", "123", "-F", "json"],
            obj=MagicMock(),
        )
        assert not result.exit_code
