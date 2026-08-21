# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for main schedule update CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    UpdatedGameResult,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_schedule_update_routing_game(runner: CliRunner) -> None:
    """Test top-level `schedule update` with numeric ID routes to game update."""
    mock_game = {
        "id": 2962948,
        "team_id": 525015,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962948, game_number="ROUTED-1")
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
            [
                "schedule",
                "update",
                "-e",
                "2962948",
                "--game-number",
                "ROUTED-1",
            ],
        )
        assert result.exit_code == 0
        assert "ROUTED-1" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["game_number"] == "ROUTED-1"


def test_schedule_update_routing_event(runner: CliRunner) -> None:
    """Test top-level `schedule update` with UUID routes to calendar occurrence update."""
    mock_occ = {
        "id": "uuid-event-123",
        "title": "Old Event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(
        id="uuid-event-123",
        title="Updated Routed Event",
    )
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
                "uuid-event-123",
                "--title",
                "Updated Routed Event",
                "--single",
            ],
        )
        assert result.exit_code == 0
        assert "Updated Routed Event" in result.output
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["title"] == "Updated Routed Event"


def test_schedule_update_game_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule update` on game with datetime resolution."""
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
            [
                "schedule",
                "update",
                "-e",
                "2962949",
                "--start-datetime",
                "2026-08-25 18:00",
                "--duration",
                "90",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["date_time"] == "2026-08-25T18:00"
        assert kwargs["end_time"] == "19:30"


def test_schedule_update_event_mutually_exclusive(runner: CliRunner) -> None:
    """Test `schedule update` with UUID fails on --future and --single."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "update",
            "-e",
            "uuid-evt-err",
            "--type",
            "event",
            "--future",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot specify both" in result.output


def test_schedule_update_event_future_flag(runner: CliRunner) -> None:
    """Test `schedule update` with UUID and --future flag."""
    mock_occ = {
        "id": "uuid-evt-prompt",
        "title": "Old Event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="uuid-evt-prompt", title="Updated")
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
                "uuid-evt-prompt",
                "--title",
                "Updated",
                "--future",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is True


def test_schedule_update_event_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule update` on UUID with datetime resolution and repeat."""
    mock_occ = {
        "id": "uuid-evt-dt",
        "title": "Event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="uuid-evt-dt", title="Event")
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
                "uuid-evt-dt",
                "--start-datetime",
                "2026-08-21 16:00",
                "--duration",
                "90",
                "--repeat",
                "weekly",
                "--interval",
                "2",
                "--by-day",
                "mo,we",
                "--repeat-until",
                "2026-11-28",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["start_date"] == "2026-08-21T16:00:00Z"
        assert payload_sent["end_date"] == "2026-08-21T17:30:00Z"
        assert payload_sent["rrule"] == "FREQ=WEEKLY;INTERVAL=2;UNTIL=20261128T235959Z;BYDAY=MO,WE"


def test_schedule_update_game_no_t_in_date(runner: CliRunner) -> None:
    """Test `schedule update` on game when date_time has no T."""
    mock_game = {
        "id": 2962951,
        "team_id": 525015,
        "date_time": "2026-08-24",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962951)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "update",
                "-e",
                "2962951",
            ],
        )
        assert result.exit_code == 0


def test_schedule_update_event_default_single(runner: CliRunner) -> None:
    """Test `schedule update` on UUID defaults to update_future=False without prompt."""
    mock_occ = {
        "id": "uuid-evt-prompt-no",
        "title": "Old Event",
        "start_date": "2026-08-20T14:00:00Z",
        "end_date": "2026-08-20T15:00:00Z",
    }
    mock_updated = CalendarEventCreated(id="uuid-evt-prompt-no", title="Old Event")
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
                "uuid-evt-prompt-no",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["update_future"] is False
