# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule practices CLI commands."""

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


def test_practices_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices create --help`."""
    result = runner.invoke(cli, ["schedule", "practices", "create", "--help"])
    assert result.exit_code == 0
    assert "practice" in result.output.lower()
    assert "--start-date-time" in result.output


def test_practices_create_default_title(runner: CliRunner) -> None:
    """Test `schedule practices create` uses default title 'Practice'."""
    mock_created = CalendarEventCreated(
        id="prac-created-1",
        title="Practice",
        type="practice",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "create",
                "-t",
                "team-123",
                "--start",
                "2026-08-30 13:30",
                "--end",
                "2026-08-30 14:30",
                "--location",
                "Polar Ice Wake Forest",
                "--notes",
                "Non-repeating practice",
            ],
        )
        assert result.exit_code == 0
        assert "Practice" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["title"] == "Practice"
        assert kwargs["location"] == "Polar Ice Wake Forest"
        assert kwargs["notes"] == "Non-repeating practice"


def test_practices_create_custom_title_and_aliases(runner: CliRunner) -> None:
    """Test `schedule practices add` and `new` with custom title."""
    mock_created = CalendarEventCreated(id="prac-created-2", title="Power Skating", type="practice")
    for subcmd in ["add", "new"]:
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
                return_value=mock_created,
            ) as mock_action,
        ):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "practices",
                    subcmd,
                    "-t",
                    "team-123",
                    "--title",
                    "Power Skating",
                    "--start",
                    "2026-08-30 15:00",
                    "--duration",
                    "60",
                ],
            )
            assert result.exit_code == 0
            kwargs = mock_action.call_args[1]
            assert kwargs["title"] == "Power Skating"


def test_practices_create_all_day(runner: CliRunner) -> None:
    """Test `schedule practices create --all-day`."""
    mock_created = CalendarEventCreated(id="prac-created-3", title="Camp Day", all_day=True)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "create",
                "-t",
                "team-123",
                "--all-day",
                "--date",
                "2026-08-30",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        kwargs = mock_action.call_args[1]
        assert args[3] == "2026-08-30"
        assert not args[4]
        assert kwargs["all_day"] is True


def test_practices_create_all_day_conflict(runner: CliRunner) -> None:
    """Test `schedule practices create --all-day` with conflicting start-date-time and date."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "create",
            "-t",
            "team-123",
            "--all-day",
            "--start-date-time",
            "2026-08-30",
            "--date",
            "2026-08-30",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_practices_create_all_day_missing_start(runner: CliRunner) -> None:
    """Test `schedule practices create --all-day` without start date raises UsageError."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "create",
            "-t",
            "team-123",
            "--all-day",
        ],
    )
    assert result.exit_code == 2
    assert "required for all-day practices" in result.output


def test_practices_create_repeating(runner: CliRunner) -> None:
    """Test `schedule practices create` with monthly recurrence."""
    mock_created = CalendarEventCreated(id="prac-created-4", title="Monthly Practice")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "create",
                "-t",
                "team-123",
                "--start",
                "2026-08-31 15:30",
                "--duration",
                "60",
                "--repeat",
                "monthly",
                "--repeat-interval",
                "1",
                "--repeat-until",
                "2027-03-19",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["rrule"] == "FREQ=MONTHLY;INTERVAL=1"
        assert kwargs["repeat_until"] == "2027-03-19"


def test_practices_create_envvar(runner: CliRunner) -> None:
    """Test `schedule practices create` using GAMESHEET_TEAM_ID envvar."""
    mock_created = CalendarEventCreated(id="prac-created-5", title="Practice")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "create",
                "--start",
                "2026-08-30 10:00",
                "--duration",
                "60",
            ],
            env={"GAMESHEET_TEAM_ID": "env-team-uuid"},
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[2] == "env-team-uuid"


def test_practices_delete_force(runner: CliRunner) -> None:
    """Test `schedule practices delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="prac-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "delete",
                "-p",
                "prac-101",
                "--force",
                "--future",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-101" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is True
        assert kwargs["all_occurrences"] is False


def test_practices_delete_all(runner: CliRunner) -> None:
    """Test `schedule practices delete --force --all`."""
    mock_res = ScheduleDeleteResult(
        success=True,
        message="Calendar event and all occurrences deleted successfully",
        id="prac-series",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "delete",
                "-p",
                "prac-series",
                "--force",
                "--all",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-series" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["all_occurrences"] is True


def test_practices_delete_prompt(runner: CliRunner) -> None:
    """Test `schedule practices delete` interactive prompt."""
    mock_occ = {"id": "prac-101", "type": "practice", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="prac-101")
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
            [
                "schedule",
                "practices",
                "delete",
                "-p",
                "prac-101",
            ],
            input="y\n2\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-101" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is True


def test_practices_delete_prompt_no(runner: CliRunner) -> None:
    """Test `schedule practices delete` prompt answering no to repeating future."""
    mock_occ = {"id": "prac-101", "type": "practice", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="prac-101")
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
            [
                "schedule",
                "practices",
                "delete",
                "-p",
                "prac-101",
            ],
            input="y\n1\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-101" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is False


def test_practices_delete_conflicts(runner: CliRunner) -> None:
    """Test `schedule practices delete` with conflicting options."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "delete",
            "-p",
            "prac-101",
            "--force",
            "--all",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_practices_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule practices del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="prac-101")
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
        for alias in ("del", "rm", "remove"):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "practices",
                    alias,
                    "-p",
                    "prac-101",
                    "--force",
                    "-F",
                    "json",
                ],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data[0]["success"] is True


def test_practices_update_basic(runner: CliRunner) -> None:
    """Test `schedule practices update` updates practice details."""
    mock_occ = {
        "id": "prac-201",
        "title": "Practice",
        "type": "practice",
        "notes": "Old note",
        "location_name": "Old Rink",
        "start_date": "2026-08-20T06:00:00Z",
        "end_date": "2026-08-20T07:00:00Z",
    }
    mock_updated = CalendarEventCreated(
        id="prac-201",
        title="Updated Practice",
        type="practice",
        notes="New note",
        location_name="New Rink",
    )
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
            [
                "schedule",
                "practices",
                "update",
                "-p",
                "prac-201",
                "--title",
                "Updated Practice",
                "--notes",
                "New note",
                "--location",
                "New Rink",
                "--repeat",
                "daily",
                "--repeat-interval",
                "1",
                "--repeat-until",
                "2026-11-28",
                "--future",
            ],
        )
        assert result.exit_code == 0
        assert "Updated Practice" in result.output
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["rrule"] == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"


def test_practices_update_mutually_exclusive(runner: CliRunner) -> None:
    """Test `schedule practices update` error on --future and --single."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "update",
            "-p",
            "prac-202",
            "--future",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot specify both" in result.output


def test_practices_update_default_single(runner: CliRunner) -> None:
    """Test `schedule practices update` defaults to update_future=False without prompt."""
    mock_occ = {
        "id": "prac-203",
        "title": "Practice",
        "type": "practice",
        "start_date": "2026-08-20T06:00:00Z",
        "end_date": "2026-08-20T07:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="prac-203", title="Practice Edit", type="practice")
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
            [
                "schedule",
                "practices",
                "update",
                "-p",
                "prac-203",
                "--title",
                "Practice Edit",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False


def test_practices_update_future_flag(runner: CliRunner) -> None:
    """Test `schedule practices update` with --future flag."""
    mock_occ = {
        "id": "prac-prompt-yes",
        "title": "Practice",
        "type": "practice",
        "start_date": "2026-08-20T06:00:00Z",
        "end_date": "2026-08-20T07:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="prac-prompt-yes", title="Practice Edit", type="practice")
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
            [
                "schedule",
                "practices",
                "update",
                "-p",
                "prac-prompt-yes",
                "--title",
                "Practice Edit",
                "--future",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True


def test_practices_update_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule practices update` with datetime resolution."""
    mock_occ = {
        "id": "prac-dt-res",
        "title": "Practice",
        "type": "practice",
        "start_date": "2026-08-20T06:00:00Z",
        "end_date": "2026-08-20T07:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="prac-dt-res", title="Practice")
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
            [
                "schedule",
                "practices",
                "update",
                "-p",
                "prac-dt-res",
                "--start",
                "2026-08-21 07:00",
                "--duration",
                "60",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["startDate"] == "2026-08-21T07:00:00Z"
        assert payload_sent["endDate"] == "2026-08-21T08:00:00Z"
