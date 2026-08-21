# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for main schedule delete CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    ScheduleDeleteResult,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_schedule_delete_game_force(runner: CliRunner) -> None:
    """Test `schedule delete` with numeric game ID and --force."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "delete",
                "-e",
                "2962920",
                "--force",
            ],
        )
        assert result.exit_code == 0
        assert "Game deleted successfully" in result.output
        mock_action.assert_called_once()


def test_schedule_delete_event_force(runner: CliRunner) -> None:
    """Test `schedule delete` with UUID event ID and --force."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "delete",
                "-e",
                "evt-uuid-1",
                "--force",
                "--single",
            ],
        )
        assert result.exit_code == 0
        assert "Occurrence deleted successfully" in result.output
        mock_action.assert_called_once()


def test_schedule_delete_prompt_confirm(runner: CliRunner) -> None:
    """Test `schedule delete` interactive prompt confirmation."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
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
            [
                "schedule",
                "delete",
                "-e",
                "2962920",
            ],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Game deleted successfully" in result.output


def test_schedule_delete_prompt_abort(runner: CliRunner) -> None:
    """Test `schedule delete` interactive prompt abort."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "delete",
            "-e",
            "2962920",
        ],
        input="n\n",
    )
    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_schedule_delete_event_repeating_prompt(runner: CliRunner) -> None:
    """Test `schedule delete` event with prompt answering yes to repeating future."""
    mock_occ = {"id": "evt-uuid-1", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(
        success=True,
        message="Occurrence and all future occurrences deleted successfully",
        id="evt-uuid-1",
    )
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
            [
                "schedule",
                "delete",
                "-e",
                "evt-uuid-1",
            ],
            input="y\n2\n",
        )
        assert result.exit_code == 0
        assert "Occurrence and all future occurrences deleted successfully" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is True


def test_schedule_delete_conflicting_flags(runner: CliRunner) -> None:
    """Test `schedule delete` with conflicting flags raises UsageError."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "delete",
            "-e",
            "evt-1",
            "--force",
            "--all",
            "--single",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output


def test_schedule_delete_json_output(runner: CliRunner) -> None:
    """Test `schedule delete -F json`."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
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
            [
                "schedule",
                "delete",
                "-e",
                "2962920",
                "--force",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["success"] is True
        assert data[0]["id"] == "2962920"


def test_schedule_delete_event_repeating_prompt_no(runner: CliRunner) -> None:
    """Test `schedule delete` event with prompt choosing single occurrence."""
    mock_occ = {"id": "evt-uuid-1", "type": "event", "rrule": "FREQ=WEEKLY;INTERVAL=1"}
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
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
            [
                "schedule",
                "delete",
                "-e",
                "evt-uuid-1",
            ],
            input="y\n1\n",
        )
        assert result.exit_code == 0
        assert "Occurrence deleted successfully" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["delete_future"] is False


def test_schedule_delete_event_json_output(runner: CliRunner) -> None:
    """Test `schedule delete` on event with -F json."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
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
            [
                "schedule",
                "delete",
                "-e",
                "evt-uuid-1",
                "--force",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["success"] is True
        assert data[0]["id"] == "evt-uuid-1"
