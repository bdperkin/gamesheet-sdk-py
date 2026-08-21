# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Additional test coverage for schedule practices CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import CalendarEventCreated, ScheduleDeleteResult

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_practices_delete_prompt_all_occurrences(runner: CliRunner) -> None:
    """Test `schedule practices delete` prompt choosing option 3 (all occurrences)."""
    mock_occ = {"id": "prac-all-opt", "type": "practice", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted all", id="prac-all-opt")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-all-opt"],
            input="y\n3\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["all_occurrences"] is True


def test_practices_delete_prompt_abort(runner: CliRunner) -> None:
    """Test `schedule practices delete` prompt aborting when confirmation is declined."""
    mock_occ = {"id": "prac-abort-1", "type": "practice", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_occ,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-abort-1"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_practices_delete_scoped_abort(runner: CliRunner) -> None:
    """Test `schedule practices delete --all` aborting when confirmation is declined."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-scoped-abort", "--all"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_practices_delete_no_message_fallback(runner: CliRunner) -> None:
    """Test `schedule practices delete` fallback message when result has empty message."""
    mock_res = ScheduleDeleteResult(success=True, message="", id="prac-no-msg")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-no-msg", "--force"],
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-no-msg" in result.output


def test_practices_delete_non_recurring_confirm(runner: CliRunner) -> None:
    """Test `schedule practices delete` on non-recurring practice with confirmation."""
    mock_occ = {"id": "prac-non-rec", "type": "practice", "rrule": None}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="prac-non-rec")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-non-rec"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice" in result.output


def test_practices_delete_single_flag_confirm(runner: CliRunner) -> None:
    """Test `schedule practices delete --single` with confirmation."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="prac-single-flag")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "delete", "-p", "prac-single-flag", "--single"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice" in result.output


def test_practices_update_repeating_prompt_single_choice(runner: CliRunner) -> None:
    """Test `schedule practices update` on recurring practice choosing option 1 (single)."""
    mock_occ = {
        "id": "prac-prompt-rec-1",
        "title": "Old Rec Practice",
        "type": "practice",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="prac-prompt-rec-1", title="Old Rec Practice", type="practice")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "update", "-p", "prac-prompt-rec-1"],
            input="1\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False


def test_practices_update_repeating_prompt_future(runner: CliRunner) -> None:
    """Test `schedule practices update` on recurring practice choosing option 2 (future)."""
    mock_occ = {
        "id": "prac-prompt-rec",
        "title": "Old Rec Practice",
        "type": "practice",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="prac-prompt-rec", title="Old Rec Practice", type="practice")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "update", "-p", "prac-prompt-rec"],
            input="2\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True
