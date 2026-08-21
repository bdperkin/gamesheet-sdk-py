# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Additional test coverage for schedule events CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import CalendarEventCreated, ScheduleDeleteResult

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_events_delete_prompt_all_occurrences(runner: CliRunner) -> None:
    """Test `schedule events delete` prompt choosing option 3 (all occurrences)."""
    mock_occ = {"id": "evt-all-opt", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted all", id="evt-all-opt")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-all-opt"],
            input="y\n3\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["all_occurrences"] is True


def test_events_delete_prompt_abort(runner: CliRunner) -> None:
    """Test `schedule events delete` prompt aborting when confirmation is declined."""
    mock_occ = {"id": "evt-abort-1", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_occ,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-abort-1"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_events_delete_scoped_abort(runner: CliRunner) -> None:
    """Test `schedule events delete --all` aborting when confirmation is declined."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-scoped-abort", "--all"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_events_delete_no_message_fallback(runner: CliRunner) -> None:
    """Test `schedule events delete` fallback message when result has empty message."""
    mock_res = ScheduleDeleteResult(success=True, message="", id="evt-no-msg")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-no-msg", "--force"],
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-no-msg" in result.output


def test_events_delete_non_recurring_confirm(runner: CliRunner) -> None:
    """Test `schedule events delete` on non-recurring event with confirmation."""
    mock_occ = {"id": "evt-non-rec", "type": "event", "rrule": None}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="evt-non-rec")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-non-rec"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Deleted single" in result.output


def test_events_delete_single_flag_confirm(runner: CliRunner) -> None:
    """Test `schedule events delete --single` with confirmation."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="evt-single-flag")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "delete", "-e", "evt-single-flag", "--single"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Deleted single" in result.output


def test_events_update_repeating_prompt_single_choice(runner: CliRunner) -> None:
    """Test `schedule events update` on recurring event choosing option 1 (single)."""
    mock_occ = {
        "id": "occ-prompt-rec-1",
        "title": "Old Rec Event",
        "type": "event",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-prompt-rec-1", title="Old Rec Event", type="event")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "update", "-e", "occ-prompt-rec-1"],
            input="1\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False


def test_events_update_repeating_prompt_future(runner: CliRunner) -> None:
    """Test `schedule events update` on recurring event choosing option 2 (future)."""
    mock_occ = {
        "id": "occ-prompt-rec",
        "title": "Old Rec Event",
        "type": "event",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-prompt-rec", title="Old Rec Event", type="event")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "update", "-e", "occ-prompt-rec"],
            input="2\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True
