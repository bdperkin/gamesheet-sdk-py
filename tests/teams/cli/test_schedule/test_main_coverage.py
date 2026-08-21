# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Additional test coverage for main schedule CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import CalendarEventCreated, ScheduleDeleteResult, UpdatedGameResult

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_main_schedule_delete_game_no_message_fallback(runner: CliRunner) -> None:
    """Test `schedule delete` for a game with empty message fallback."""
    mock_res = ScheduleDeleteResult(success=True, message="", id=2962920)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "2962920", "--force"],
        )
        assert result.exit_code == 0
        assert "Successfully deleted game 2962920" in result.output


def test_main_schedule_delete_event_prompt_all(runner: CliRunner) -> None:
    """Test `schedule delete` for recurring event choosing option 3 (all occurrences)."""
    mock_occ = {"id": "evt-all-choice", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted all", id="evt-all-choice")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-all-choice"],
            input="y\n3\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["all_occurrences"] is True


def test_main_schedule_delete_event_prompt_abort(runner: CliRunner) -> None:
    """Test `schedule delete` for recurring event aborting confirmation."""
    mock_occ = {"id": "evt-abort-opt", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_occ,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-abort-opt"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_main_schedule_delete_scoped_abort(runner: CliRunner) -> None:
    """Test `schedule delete --all` aborting on confirmation."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-scoped-abort", "--all"],
            input="n\n",
        )
        assert result.exit_code == 1
        assert "Aborted." in result.output


def test_main_schedule_delete_event_no_message_fallback(runner: CliRunner) -> None:
    """Test `schedule delete` for an event with empty message fallback."""
    mock_res = ScheduleDeleteResult(success=True, message="", id="evt-no-msg-2")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-no-msg-2", "--force"],
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-no-msg-2" in result.output


def test_main_schedule_delete_non_recurring_confirm(runner: CliRunner) -> None:
    """Test `schedule delete` on non-recurring event with confirmation."""
    mock_occ = {"id": "evt-main-non-rec", "type": "event", "rrule": None}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="evt-main-non-rec")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_occ, mock_res],
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-main-non-rec"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Deleted single" in result.output


def test_main_schedule_delete_single_flag_confirm(runner: CliRunner) -> None:
    """Test `schedule delete --single` with confirmation."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted single", id="evt-main-single-flag")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "delete", "-e", "evt-main-single-flag", "--single"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Deleted single" in result.output


def test_main_schedule_update_game_type(runner: CliRunner) -> None:
    """Test top-level `schedule update` with game type."""
    mock_game = {
        "id": 2962949,
        "team_id": 525015,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962949)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "update", "-e", "2962949", "--game-type", "regular_season"],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["game_type"] == "regular_season"


def test_main_schedule_update_event_prompt_single_choice(runner: CliRunner) -> None:
    """Test `schedule update` on recurring event choosing option 1 (single)."""
    mock_occ = {
        "id": "occ-prompt-main-1",
        "title": "Old Title",
        "type": "event",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-prompt-main-1", title="Old Title", type="event")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "update", "-e", "occ-prompt-main-1"],
            input="1\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False


def test_main_schedule_update_event_prompt_future_notes_location(runner: CliRunner) -> None:
    """Test `schedule update` on recurring event choosing future with notes and location."""
    mock_occ = {
        "id": "occ-prompt-main",
        "title": "Old Title",
        "type": "event",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-prompt-main", title="Old Title", type="event")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "update",
                "-e",
                "occ-prompt-main",
                "--notes",
                "Updated notes",
                "--location",
                "Updated Arena",
            ],
            input="2\n",
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["notes"] == "Updated notes"
        assert payload_sent["locationName"] == "Updated Arena"
