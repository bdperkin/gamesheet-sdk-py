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
            ["teams", "--division-id", "701", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 0


def test_divisions_create_coverage() -> None:
    """Ensure divisions create command body is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Test Division"
    mock_division.id = "80997"
    mock_division.model_dump.return_value = {"id": "80997", "title": "Test Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> MagicMock:
        # Actually call the action to ensure coverage of the nested function
        return action(session, *args)

    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions._create_division_action",
            return_value=mock_division,
        ),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            side_effect=mock_run_action,
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch("gamesheet_sdk.cli.commands.divisions.write_output"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            ["create", "--season-id", "15020", "--title", "Test Division", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 0
        # Verify success message was displayed
        mock_secho.assert_called_once()
        call_args = mock_secho.call_args
        assert "Test Division" in call_args[0][0]
        assert "80997" in call_args[0][0]


def test_divisions_create_with_output_file_coverage() -> None:
    """Ensure divisions create with output file is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Test Division"
    mock_division.id = "80997"
    mock_division.model_dump.return_value = {"id": "80997", "title": "Test Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> MagicMock:
        return action(session, *args)

    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions._create_division_action",
            return_value=mock_division,
        ),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            side_effect=mock_run_action,
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch("gamesheet_sdk.cli.commands.divisions.write_output"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            [
                "create",
                "--season-id",
                "15020",
                "--title",
                "Test Division",
                "-F",
                "json",
                "-o",
                "/tmp/out.json",
            ],
            obj=MagicMock(),
        )
        assert result.exit_code == 0
        # When output file is specified, success message should not be displayed
        mock_secho.assert_not_called()


def test_divisions_update_coverage() -> None:
    """Ensure divisions update command body is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Updated Division"
    mock_division.id = "701"
    mock_division.model_dump.return_value = {"id": "701", "title": "Updated Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> MagicMock:
        return action(session, *args)

    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions._update_division_action",
            return_value=mock_division,
        ),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            side_effect=mock_run_action,
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch("gamesheet_sdk.cli.commands.divisions.write_output"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            ["update", "--division-id", "701", "--title", "Updated Division", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 0
        # Verify success message was displayed
        mock_secho.assert_called_once()
        call_args = mock_secho.call_args
        assert "Updated Division" in call_args[0][0]
        assert "701" in call_args[0][0]


def test_divisions_update_with_no_fields_exits_with_error() -> None:
    """Ensure divisions update without fields shows error."""
    runner = CliRunner()
    with patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"):
        result = runner.invoke(
            divisions_group,
            ["update", "--division-id", "701", "-F", "json"],
            obj=MagicMock(),
        )
        assert result.exit_code == 1
        assert "At least one of --title or --external-id must be provided" in result.output


def test_divisions_update_with_output_file_coverage() -> None:
    """Ensure divisions update with output file is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Updated Division"
    mock_division.id = "701"
    mock_division.model_dump.return_value = {"id": "701", "title": "Updated Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> MagicMock:
        return action(session, *args)

    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions._update_division_action",
            return_value=mock_division,
        ),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            side_effect=mock_run_action,
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render", return_value=""),
        patch("gamesheet_sdk.cli.commands.divisions.write_output"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            [
                "update",
                "--division-id",
                "701",
                "--title",
                "Updated Division",
                "-F",
                "json",
                "-o",
                "/tmp/out.json",
            ],
            obj=MagicMock(),
        )
        assert result.exit_code == 0
        # When output file is specified, success message should not be displayed
        mock_secho.assert_not_called()
