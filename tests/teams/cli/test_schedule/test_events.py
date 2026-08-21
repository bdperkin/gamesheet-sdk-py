# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule events CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    ScheduleDeleteResult,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_events_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events create --help`."""
    result = runner.invoke(cli, ["schedule", "events", "create", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output.lower()
    assert "--start-date-time" in result.output
    assert "--duration" in result.output
    assert "--repeat" in result.output
    assert "--all-day" in result.output


def test_events_create_datetime_and_aliases(runner: CliRunner) -> None:
    """Test `schedule events create`, `add`, `new` with start and end datetime."""
    mock_created = CalendarEventCreated(
        id="evt-created-1",
        title="Team Pizza Party",
        type="event",
        start_time="13:30:00",
        end_time="14:30:00",
    )
    for subcmd in ["create", "add", "new"]:
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
                return_value=mock_created,
            ) as mock_action,
        ):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "events",
                    subcmd,
                    "-t",
                    "team-uuid",
                    "--title",
                    "Team Pizza Party",
                    "--start-date-time",
                    "2026-08-21 13:30",
                    "--end-time",
                    "14:30",
                ],
            )
            assert result.exit_code == 0
            assert "Team Pizza Party" in result.output
            mock_action.assert_called_once()
            args = mock_action.call_args[0]
            assert args[2] == "team-uuid"
            assert args[3] == "Team Pizza Party"
            assert args[4] == "2026-08-21T13:30"
            assert args[5] == "14:30"


def test_events_create_split_datetime(runner: CliRunner) -> None:
    """Test `schedule events create` with split --date and --start/--end."""
    mock_created = CalendarEventCreated(
        id="evt-created-2",
        title="Team Dinner",
        type="event",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Team Dinner",
                "--date",
                "2026-08-21",
                "--start",
                "18:00",
                "--end",
                "20:00",
                "--location",
                "Italian Restaurant",
                "--notes",
                "Bring family",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["location"] == "Italian Restaurant"
        assert kwargs["notes"] == "Bring family"


def test_events_create_duration(runner: CliRunner) -> None:
    """Test `schedule events create` with start datetime and duration."""
    mock_created = CalendarEventCreated(id="evt-created-3", title="Meeting")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Meeting",
                "--start",
                "2026-08-21 10:00",
                "--duration",
                "90",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[4] == "2026-08-21T10:00"
        assert args[5] == "11:30"


def test_events_create_end_datetime_and_duration(runner: CliRunner) -> None:
    """Test `schedule events create` with end datetime and duration."""
    mock_created = CalendarEventCreated(id="evt-created-4", title="Wrapup")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Wrapup",
                "--end",
                "2026-08-21 12:00",
                "--duration",
                "60",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[4] == "2026-08-21T11:00"
        assert args[5] == "12:00"


def test_events_create_all_day(runner: CliRunner) -> None:
    """Test `schedule events create --all-day`."""
    mock_created = CalendarEventCreated(id="evt-created-5", title="Tournament Day", all_day=True)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Tournament Day",
                "--all-day",
                "--date",
                "2026-08-25",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        kwargs = mock_action.call_args[1]
        assert args[4] == "2026-08-25"
        assert not args[5]
        assert kwargs["all_day"] is True


def test_events_create_all_day_conflict(runner: CliRunner) -> None:
    """Test `schedule events create --all-day` with conflicting start-date-time and date."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "create",
            "-t",
            "team-uuid",
            "--title",
            "Tournament Day",
            "--all-day",
            "--start-date-time",
            "2026-08-25",
            "--date",
            "2026-08-25",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_events_create_all_day_missing_start(runner: CliRunner) -> None:
    """Test `schedule events create --all-day` without start date raises UsageError."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "create",
            "-t",
            "team-uuid",
            "--title",
            "Tournament Day",
            "--all-day",
        ],
    )
    assert result.exit_code == 2
    assert "required for all-day events" in result.output


def test_events_create_conflicting_inputs(runner: CliRunner) -> None:
    """Test `schedule events create` with conflicting start-date-time and date."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "create",
            "-t",
            "team-uuid",
            "--title",
            "Test",
            "--start-date-time",
            "2026-08-21 10:00",
            "--date",
            "2026-08-21",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_events_create_insufficient_inputs(runner: CliRunner) -> None:
    """Test `schedule events create` with only start datetime and no duration/end raises UsageError."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "create",
            "-t",
            "team-uuid",
            "--title",
            "Test",
            "--start",
            "2026-08-21 10:00",
        ],
    )
    assert result.exit_code == 2
    assert "At least 2 of" in result.output


def test_events_create_repeating_weekly(runner: CliRunner) -> None:
    """Test `schedule events create` with weekly recurrence flags."""
    mock_created = CalendarEventCreated(id="evt-created-6", title="Weekly Workout")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Weekly Workout",
                "--start",
                "2026-08-22 11:30",
                "--duration",
                "60",
                "--repeat",
                "weekly",
                "--repeat-interval",
                "1",
                "--repeat-by-day",
                "TU,TH",
                "--repeat-until",
                "2027-03-22",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["rrule"] == "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH"
        assert kwargs["repeat_until"] == "2027-03-22"


def test_events_create_direct_rrule(runner: CliRunner) -> None:
    """Test `schedule events create` with direct --rrule flag."""
    mock_created = CalendarEventCreated(id="evt-created-7", title="Custom RRULE")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-uuid",
                "--title",
                "Custom RRULE",
                "--start",
                "2026-08-22 11:30",
                "--duration",
                "60",
                "--rrule",
                "FREQ=MONTHLY;INTERVAL=1",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["rrule"] == "FREQ=MONTHLY;INTERVAL=1"


def test_events_create_missing_required(runner: CliRunner) -> None:
    """Test `schedule events create` missing team ID or title."""
    res1 = runner.invoke(cli, ["schedule", "events", "create", "--title", "Missing Team"])
    assert res1.exit_code == 2

    res2 = runner.invoke(cli, ["schedule", "events", "create", "-t", "team-123"])
    assert res2.exit_code == 2


def test_events_create_envvar(runner: CliRunner) -> None:
    """Test `schedule events create` with GAMESHEET_TEAM_ID envvar."""
    mock_created = CalendarEventCreated(id="evt-created-8", title="Env Team")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "--title",
                "Env Team",
                "--start",
                "2026-08-21 10:00",
                "--duration",
                "60",
            ],
            env={"GAMESHEET_TEAM_ID": "env-team-id"},
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[2] == "env-team-id"


def test_events_create_json_format(runner: CliRunner) -> None:
    """Test `schedule events create -F json`."""
    mock_created = CalendarEventCreated(
        id="evt-created-9",
        title="JSON Event",
        type="event",
        start_time="10:00:00",
        end_time="11:00:00",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_created,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "create",
                "-t",
                "team-123",
                "--title",
                "JSON Event",
                "--start",
                "2026-08-21 10:00",
                "--duration",
                "60",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "evt-created-9"
        assert data[0]["title"] == "JSON Event"


def test_events_delete_force(runner: CliRunner) -> None:
    """Test `schedule events delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "delete",
                "-e",
                "evt-101",
                "--force",
                "--future",
            ],
        )
        assert result.exit_code == 0
        assert "Occurrence deleted successfully" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is True
        assert kwargs["all_occurrences"] is False


def test_events_delete_all(runner: CliRunner) -> None:
    """Test `schedule events delete --force --all`."""
    mock_res = ScheduleDeleteResult(
        success=True,
        message="Calendar event and all occurrences deleted successfully",
        id="evt-series",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "delete",
                "-e",
                "evt-series",
                "--force",
                "--all",
            ],
        )
        assert result.exit_code == 0
        assert "Calendar event and all occurrences deleted successfully" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["all_occurrences"] is True


def test_events_delete_prompt(runner: CliRunner) -> None:
    """Test `schedule events delete` interactive prompt."""
    mock_occ = {"id": "evt-101", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-101")
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
            [
                "schedule",
                "events",
                "delete",
                "-e",
                "evt-101",
            ],
            input="y\n1\n",
        )
        assert result.exit_code == 0
        assert "Occurrence deleted successfully" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is False


def test_events_delete_prompt_yes(runner: CliRunner) -> None:
    """Test `schedule events delete` prompt answering yes to repeating future."""
    mock_occ = {"id": "evt-101", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="evt-101")
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
            [
                "schedule",
                "events",
                "delete",
                "-e",
                "evt-101",
            ],
            input="y\n2\n",
        )
        assert result.exit_code == 0
        assert "Deleted" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is True


def test_events_delete_conflicts(runner: CliRunner) -> None:
    """Test `schedule events delete` with conflicting options."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "delete",
            "-e",
            "evt-101",
            "--force",
            "--all",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_events_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule events del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="evt-101")
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
        for alias in ("del", "rm", "remove"):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "events",
                    alias,
                    "-e",
                    "evt-101",
                    "--force",
                    "-F",
                    "json",
                ],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data[0]["success"] is True


def test_events_update_basic(runner: CliRunner) -> None:
    """Test `schedule events update` updates title, location, notes."""
    mock_occ = {
        "id": "occ-101",
        "title": "Old Title",
        "type": "event",
        "notes": "Old notes",
        "location_name": "Old Rink",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(
        id="occ-101",
        title="New Title",
        type="event",
        notes="New notes",
        location_name="New Rink",
        start_date="2026-08-20T14:00:00Z",
        end_date="2026-08-20T15:00:00Z",
    )
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
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-101",
                "--title",
                "New Title",
                "--notes",
                "New notes",
                "--location",
                "New Rink",
                "--single",
            ],
        )
        assert result.exit_code == 0
        assert "New Title" in result.output
        assert mock_action.call_count == 2
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["title"] == "New Title"
        assert payload_sent["notes"] == "New notes"
        assert payload_sent["locationName"] == "New Rink"


def test_events_update_future_flag(runner: CliRunner) -> None:
    """Test `schedule events update` with --future flag."""
    mock_occ = {
        "id": "occ-102",
        "title": "Repeating Title",
        "type": "event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
        "rrule": "FREQ=WEEKLY;INTERVAL=1",
    }
    mock_updated = CalendarEventCreated(
        id="occ-102",
        title="Updated Repeating Title",
        type="event",
        rrule="FREQ=WEEKLY;INTERVAL=1",
    )
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
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-102",
                "--title",
                "Updated Repeating Title",
                "--future",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True


def test_events_update_mutually_exclusive_scope(runner: CliRunner) -> None:
    """Test `schedule events update` errors when combining --future and --single."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "update",
            "-e",
            "occ-103",
            "--future",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot specify both" in result.output


def test_events_update_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule events update` with date and time changes."""
    mock_occ = {
        "id": "occ-105",
        "title": "Title",
        "type": "event",
        "start_date": "2026-08-20T14:00:00+00:00",
        "end_date": "2026-08-20T15:00:00+00:00",
    }
    mock_updated = CalendarEventCreated(
        id="occ-105",
        title="Title",
        type="event",
        start_date="2026-08-21T16:00:00+00:00",
        end_date="2026-08-21T17:30:00+00:00",
    )
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
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-105",
                "--start",
                "2026-08-21 16:00",
                "--duration",
                "90",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["startDate"] == "2026-08-21T16:00:00Z"
        assert payload_sent["endDate"] == "2026-08-21T17:30:00Z"


def test_events_update_json_output(runner: CliRunner) -> None:
    """Test `schedule events update` with json output format."""
    mock_occ = {
        "id": "occ-106",
        "title": "Title",
        "type": "event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-106", title="New Title", type="event")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            side_effect=[mock_occ, mock_updated],
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-106",
                "--title",
                "New Title",
                "--single",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "occ-106"
        assert data[0]["title"] == "New Title"


def test_events_update_recurrence(runner: CliRunner) -> None:
    """Test `schedule events update` with recurrence options."""
    mock_occ = {
        "id": "occ-rec-1",
        "title": "Rec Event",
        "type": "event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-rec-1", title="Rec Event")
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
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-rec-1",
                "--repeat",
                "daily",
                "--repeat-interval",
                "1",
                "--repeat-until",
                "2026-11-28",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["rrule"] == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"


def test_events_update_default_single(runner: CliRunner) -> None:
    """Test `schedule events update` defaults to update_future=False without prompt."""
    mock_occ = {
        "id": "occ-prompt-no",
        "title": "Old Event",
        "type": "event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="occ-prompt-no", title="Old Event", type="event")
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
            [
                "schedule",
                "events",
                "update",
                "-e",
                "occ-prompt-no",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False
