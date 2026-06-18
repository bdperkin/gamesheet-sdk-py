"""Coverage tests for divisions commands."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.divisions import divisions_group


def test_divisions_list_coverage() -> None:
    """Ensure divisions list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
    ):
        result = runner.invoke(
            divisions_group,
            ["list", "--season-id", "15020", "-F", "json"],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_teams_coverage() -> None:
    """Ensure divisions teams list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.divisions.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
    ):
        result = runner.invoke(
            divisions_group,
            ["teams", "list", "--division-id", "701", "-F", "json"],
            obj=MagicMock(),
        )
        assert not result.exit_code


def test_divisions_create_coverage() -> None:
    """Ensure divisions create command body is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Test Division"
    mock_division.id = "80997"
    mock_division.model_dump.return_value = {"id": "80997", "title": "Test Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> Any:
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
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
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
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
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

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> Any:
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
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
        tempfile.TemporaryDirectory() as tmpdir,
    ):
        output_file = Path(tmpdir, "out.json")
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
                str(output_file),
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # When output file is specified, success message should not be displayed
        mock_secho.assert_not_called()


def test_divisions_update_coverage() -> None:
    """Ensure divisions update command body is covered."""
    runner = CliRunner()
    mock_division = MagicMock()
    mock_division.title = "Updated Division"
    mock_division.id = "701"
    mock_division.model_dump.return_value = {"id": "701", "title": "Updated Division"}

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> Any:
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
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            [
                "update",
                "--season-id",
                "15020",
                "--division-id",
                "701",
                "--title",
                "Updated Division",
                "-F",
                "json",
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
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
            ["update", "--season-id", "15020", "--division-id", "701", "-F", "json"],
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

    def mock_run_action(session: MagicMock, action: MagicMock, *args: MagicMock) -> Any:
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
        patch("gamesheet_sdk.cli.commands.divisions.render_list_command"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
        tempfile.TemporaryDirectory() as tmpdir,
    ):
        output_file = Path(tmpdir, "out.json")
        result = runner.invoke(
            divisions_group,
            [
                "update",
                "--season-id",
                "15020",
                "--division-id",
                "701",
                "--title",
                "Updated Division",
                "-F",
                "json",
                "-o",
                str(output_file),
            ],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # When output file is specified, success message should not be displayed
        mock_secho.assert_not_called()


def test_divisions_delete_coverage() -> None:
    """Ensure divisions delete command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.divisions.run_action_or_exit"),
        patch("gamesheet_sdk.cli.commands.divisions.click.secho") as mock_secho,
    ):
        result = runner.invoke(
            divisions_group,
            ["delete", "--season-id", "15020", "--division-id", "701", "--force"],
            obj=MagicMock(),
        )
        assert not result.exit_code
        # Verify success message was displayed
        mock_secho.assert_called_once()
        call_args = mock_secho.call_args
        assert "701" in call_args[0][0]
        assert "deleted successfully" in call_args[0][0]


def test_divisions_delete_requires_confirmation_without_force() -> None:
    """Ensure divisions delete prompts for confirmation without --force."""
    runner = CliRunner()
    with patch("gamesheet_sdk.cli.commands.divisions.build_authenticated_session"):
        # User declines confirmation (input='n')
        result = runner.invoke(
            divisions_group,
            ["delete", "--season-id", "15020", "--division-id", "701"],
            obj=MagicMock(),
            input="n\n",
        )
        # Should exit without calling delete action
        assert result.exit_code == 1
        assert "Aborted" in result.output or "division" in result.output.lower()
