"""Coverage-focused tests for CLI command bodies.

These tests ensure that command callback functions are executed and measured by coverage, addressing cases
where integration tests may not reach the command body due to Click's invocation mechanics.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.divisions import divisions_group
from gamesheet_sdk.cli.commands.games import (
    brackets_group,
    completed_group,
    scheduled_group,
)
from gamesheet_sdk.cli.commands.roster import coaches_group, players_group


def test_games_scheduled_list_coverage() -> None:
    """Ensure scheduled list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.games.write_output",
        ),
    ):
        # Invoke the command with a mocked context
        result = runner.invoke(
            scheduled_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 0


def test_games_completed_list_coverage() -> None:
    """Ensure completed list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.games.write_output",
        ),
    ):
        result = runner.invoke(
            completed_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 0


def test_games_brackets_list_coverage() -> None:
    """Ensure brackets list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.games.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.games.write_output",
        ),
    ):
        result = runner.invoke(
            brackets_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 0


def test_roster_players_list_coverage() -> None:
    """Ensure players list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.roster.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.roster.write_output",
        ),
    ):
        result = runner.invoke(
            players_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 0


def test_roster_coaches_list_coverage() -> None:
    """Ensure coaches list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.roster.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.roster.write_output",
        ),
    ):
        result = runner.invoke(
            coaches_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert result.exit_code == 0


def test_divisions_list_coverage() -> None:
    """Ensure divisions list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.divisions.write_output",
        ),
    ):
        result = runner.invoke(
            divisions_group,
            ["list", "--season-id", "15020", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 0


def test_divisions_teams_coverage() -> None:
    """Ensure divisions teams command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch(
            "gamesheet_sdk.cli.commands.divisions.write_output",
        ),
    ):
        result = runner.invoke(
            divisions_group,
            ["teams", "--season-id", "15020", "--division-id", "701", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 0
