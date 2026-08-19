# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule CLI command group."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from click.exceptions import Exit

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import ScheduleEvent

if TYPE_CHECKING:
    from click.testing import CliRunner


def _sample_events() -> list[ScheduleEvent]:
    """Return sample ScheduleEvent objects for CLI tests."""
    return [
        ScheduleEvent(
            id="evt-101",
            type="event",
            eventDate="2026-08-20",
            eventTime="17:00",
            eventTitle="Team Pizza Party",
            eventLocation="Clubhouse",
        ),
        ScheduleEvent(
            id=202,
            type="game",
            eventDate="2026-08-22",
            eventTime="19:00",
            eventTitle="Hawks vs Eagles",
            eventLocation="Arena A",
        ),
        ScheduleEvent(
            id="prac-303",
            type="practice",
            eventDate="2026-08-24",
            eventTime="06:00",
            eventTitle="Morning Skate",
            eventLocation="Rink 2",
        ),
    ]


def test_schedule_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule --help` shows usage and subcommands."""
    result = runner.invoke(cli, ["schedule", "--help"])
    assert result.exit_code == 0
    assert "schedule" in result.output.lower()
    assert "export" in result.output
    assert "subscribe" in result.output
    assert "practices" in result.output
    assert "events" in result.output
    assert "games" in result.output
    assert "list" in result.output


def test_schedule_events_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "events", "--help"])
    assert result.exit_code == 0
    assert "events" in result.output.lower()
    assert "list" in result.output


def test_schedule_games_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "games", "--help"])
    assert result.exit_code == 0
    assert "games" in result.output.lower()
    assert "list" in result.output


def test_schedule_practices_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "practices", "--help"])
    assert result.exit_code == 0
    assert "practices" in result.output.lower()
    assert "list" in result.output


def test_schedule_list_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list -t team-123` renders events table."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    assert "Hawks vs Eagles" in result.output
    assert "Morning Skate" in result.output
    assert "evt-101" in result.output
    assert "202" in result.output
    assert "prac-303" in result.output
    mock_action.assert_called_once()


def test_schedule_list_format_json(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list -t team-123 --format json` produces valid JSON."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "list", "-t", "team-123", "--format", "json"],
        )

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 3
    assert parsed[0]["eventTitle"] == "Team Pizza Party"
    assert parsed[0]["type"] == "event"
    assert parsed[0]["eventDate"] == "2026-08-20"
    assert parsed[0]["eventTime"] == "17:00"
    assert parsed[0]["eventLocation"] == "Clubhouse"
    assert parsed[0]["id"] == "evt-101"


def test_schedule_list_format_yaml(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list -t team-123 --format yaml` produces YAML."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ),
    ):
        result = runner.invoke(
            cli,
            ["schedule", "list", "-t", "team-123", "--format", "yaml"],
        )

    assert result.exit_code == 0
    assert "eventTitle: Team Pizza Party" in result.output


def test_schedule_list_columns_and_month(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list` with --month and --columns options."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "list",
                "-t",
                "team-123",
                "--month",
                "2026-08",
                "--columns",
                "eventTitle,eventDate",
            ],
        )

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("month") == "2026-08"


def test_schedule_list_alias_ls(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule ls -t team-123` alias."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ),
    ):
        result = runner.invoke(cli, ["schedule", "ls", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output


def test_schedule_bare_default(runner: CliRunner) -> None:
    """Test bare `gamesheet-teams schedule` runs list by default using envvar."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ),
    ):
        result = runner.invoke(cli, ["schedule"], env={"GAMESHEET_TEAM_ID": "team-123"})

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output


def test_schedule_events_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events list -t team-123`."""
    events = [e for e in _sample_events() if e.type == "event"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=events,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "events", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output


def test_schedule_events_ls_and_default(runner: CliRunner) -> None:
    """Test `schedule events ls` and bare `schedule events`."""
    events = [e for e in _sample_events() if e.type == "event"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=events,
        ),
    ):
        r_ls = runner.invoke(cli, ["schedule", "events", "ls", "-t", "team-123"])
        r_bare = runner.invoke(cli, ["schedule", "events"], env={"GAMESHEET_TEAM_ID": "team-123"})

    assert r_ls.exit_code == 0
    assert "Team Pizza Party" in r_ls.output
    assert r_bare.exit_code == 0
    assert "Team Pizza Party" in r_bare.output


def test_schedule_games_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games list -t team-123`."""
    games = [e for e in _sample_events() if e.type == "game"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=games,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "games", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Hawks vs Eagles" in result.output


def test_schedule_games_ls_and_default(runner: CliRunner) -> None:
    """Test `schedule games ls` and bare `schedule games`."""
    games = [e for e in _sample_events() if e.type == "game"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=games,
        ),
    ):
        r_ls = runner.invoke(cli, ["schedule", "games", "ls", "-t", "team-123"])
        r_bare = runner.invoke(cli, ["schedule", "games"], env={"GAMESHEET_TEAM_ID": "team-123"})

    assert r_ls.exit_code == 0
    assert "Hawks vs Eagles" in r_ls.output
    assert r_bare.exit_code == 0
    assert "Hawks vs Eagles" in r_bare.output


def test_schedule_practices_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices list -t team-123`."""
    practices = [e for e in _sample_events() if e.type == "practice"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=practices,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "practices", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Morning Skate" in result.output


def test_schedule_practices_ls_and_default(runner: CliRunner) -> None:
    """Test `schedule practices ls` and bare `schedule practices`."""
    practices = [e for e in _sample_events() if e.type == "practice"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=practices,
        ),
    ):
        r_ls = runner.invoke(cli, ["schedule", "practices", "ls", "-t", "team-123"])
        r_bare = runner.invoke(cli, ["schedule", "practices"], env={"GAMESHEET_TEAM_ID": "team-123"})

    assert r_ls.exit_code == 0
    assert "Morning Skate" in r_ls.output
    assert r_bare.exit_code == 0
    assert "Morning Skate" in r_bare.output


def test_schedule_list_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list` errors when --team-id is missing."""
    result = runner.invoke(cli, ["schedule", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "--team-id" in result.output


def test_schedule_events_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events list` errors when --team-id is missing."""
    result = runner.invoke(cli, ["schedule", "events", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "--team-id" in result.output


def test_schedule_games_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games list` errors when --team-id is missing."""
    result = runner.invoke(cli, ["schedule", "games", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "--team-id" in result.output


def test_schedule_practices_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices list` errors when --team-id is missing."""
    result = runner.invoke(cli, ["schedule", "practices", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "--team-id" in result.output


def test_schedule_list_action_error(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list` handles action errors gracefully."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            side_effect=Exit(1),
        ),
    ):
        result = runner.invoke(cli, ["schedule", "list", "-t", "team-123"])

    assert result.exit_code == 1


def test_schedule_export_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule export` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "export"])
    assert result.exit_code == 1
    assert "schedule export is not yet implemented" in result.output


def test_schedule_subscribe_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe` exits 1 with not yet implemented message."""
    result = runner.invoke(cli, ["schedule", "subscribe"])
    assert result.exit_code == 1
    assert "schedule subscribe is not yet implemented" in result.output


def test_schedule_list_event_data_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule list` passes include_event_data=True."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "list", "-t", "team-123", "--event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_events_list_event_data_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events list` passes include_event_data=True."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "events", "list", "-t", "team-123", "--include-event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_games_list_event_data_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games list` passes include_event_data=True."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "list", "-t", "team-123", "--event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_practices_list_event_data_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices list` passes include_event_data=True."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "list", "-t", "team-123", "--include-event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True
