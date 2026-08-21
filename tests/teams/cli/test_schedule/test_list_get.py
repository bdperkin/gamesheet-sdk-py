# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for main schedule list, get, export, and subscribe CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from click.exceptions import Exit

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    ScheduleEventDetail,
)
from tests.teams.cli.test_schedule.conftest import get_sample_events

if TYPE_CHECKING:
    from click.testing import CliRunner


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
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
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
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
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
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
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
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
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
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
        ),
    ):
        result = runner.invoke(cli, ["schedule", "ls", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output


def test_schedule_bare_default(runner: CliRunner) -> None:
    """Test bare `gamesheet-teams schedule` runs list by default using envvar."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
        ),
    ):
        result = runner.invoke(cli, ["schedule"], env={"GAMESHEET_TEAM_ID": "team-123"})

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output


def test_schedule_events_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events list -t team-123`."""
    events = [e for e in get_sample_events() if e.type == "event"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=events,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "events", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    assert "Hawks vs Eagles" not in result.output


def test_schedule_events_ls_and_default(runner: CliRunner) -> None:
    """Test `events ls` and bare `events` invoking list."""
    events = [e for e in get_sample_events() if e.type == "event"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=events,
        ),
    ):
        r1 = runner.invoke(cli, ["schedule", "events", "ls", "-t", "team-123"])
        assert r1.exit_code == 0
        assert "Team Pizza Party" in r1.output

        r2 = runner.invoke(cli, ["schedule", "events"], env={"GAMESHEET_TEAM_ID": "team-123"})
        assert r2.exit_code == 0
        assert "Team Pizza Party" in r2.output


def test_schedule_games_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games list -t team-123`."""
    games = [e for e in get_sample_events() if e.type == "game"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=games,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "games", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Hawks vs Eagles" in result.output
    assert "Team Pizza Party" not in result.output


def test_schedule_games_ls_and_default(runner: CliRunner) -> None:
    """Test `games ls` and bare `games` invoking list."""
    games = [e for e in get_sample_events() if e.type == "game"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=games,
        ),
    ):
        r1 = runner.invoke(cli, ["schedule", "games", "ls", "-t", "team-123"])
        assert r1.exit_code == 0
        assert "Hawks vs Eagles" in r1.output

        r2 = runner.invoke(cli, ["schedule", "games"], env={"GAMESHEET_TEAM_ID": "team-123"})
        assert r2.exit_code == 0
        assert "Hawks vs Eagles" in r2.output


def test_schedule_practices_list(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices list -t team-123`."""
    practices = [e for e in get_sample_events() if e.type == "practice"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=practices,
        ),
    ):
        result = runner.invoke(cli, ["schedule", "practices", "list", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Morning Skate" in result.output
    assert "Team Pizza Party" not in result.output


def test_schedule_practices_ls_and_default(runner: CliRunner) -> None:
    """Test `practices ls` and bare `practices` invoking list."""
    practices = [e for e in get_sample_events() if e.type == "practice"]
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=practices,
        ),
    ):
        r1 = runner.invoke(cli, ["schedule", "practices", "ls", "-t", "team-123"])
        assert r1.exit_code == 0
        assert "Morning Skate" in r1.output

        r2 = runner.invoke(cli, ["schedule", "practices"], env={"GAMESHEET_TEAM_ID": "team-123"})
        assert r2.exit_code == 0
        assert "Morning Skate" in r2.output


def test_schedule_list_missing_team_id(runner: CliRunner) -> None:
    """Test missing team ID exits with code 2."""
    result = runner.invoke(cli, ["schedule", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_events_missing_team_id(runner: CliRunner) -> None:
    """Test missing team ID on events list exits with code 2."""
    result = runner.invoke(cli, ["schedule", "events", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_games_missing_team_id(runner: CliRunner) -> None:
    """Test missing team ID on games list exits with code 2."""
    result = runner.invoke(cli, ["schedule", "games", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_practices_missing_team_id(runner: CliRunner) -> None:
    """Test missing team ID on practices list exits with code 2."""
    result = runner.invoke(cli, ["schedule", "practices", "list"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_list_action_error(runner: CliRunner) -> None:
    """Test action error in schedule list propagates properly."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            side_effect=Exit(1),
        ),
    ):
        result = runner.invoke(cli, ["schedule", "list", "-t", "team-123"])
        assert result.exit_code == 1


def test_schedule_export_stub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule export` command."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "export", "-t", "team-123"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_list_event_data_flag(runner: CliRunner) -> None:
    """Test `schedule list --event-data` passes include_event_data=True."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=get_sample_events(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "list", "-t", "team-123", "--include-event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_events_list_event_data_flag(runner: CliRunner) -> None:
    """Test `schedule events list --include-event-data` flag."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=[],
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
    """Test `schedule games list --include-event-data` flag."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=[],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "list", "-t", "team-123", "--include-event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def test_schedule_practices_list_event_data_flag(runner: CliRunner) -> None:
    """Test `schedule practices list --include-event-data` flag."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=[],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "list", "-t", "team-123", "--include-event-data"],
        )

    assert result.exit_code == 0
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_event_data") is True


def _sample_event_detail() -> ScheduleEventDetail:
    """Return sample ScheduleEventDetail for get command tests.

    Returns:
        ScheduleEventDetail: Sample ScheduleEventDetail instance.

    """
    return ScheduleEventDetail(
        id="evt-101",
        type="event",
        eventDate="2026-08-20",
        eventTime="17:00",
        eventTitle="Team Pizza Party",
        eventLocation="Clubhouse",
        eventData={"notes": "Bring extra napkins"},
        availability=[{"player": "John Doe", "status": "yes"}],
    )


def _sample_game_detail() -> ScheduleEventDetail:
    """Return sample ScheduleEventDetail representing a scheduled game.

    Returns:
        ScheduleEventDetail: Sample ScheduleEventDetail instance.

    """
    return ScheduleEventDetail(
        id=202,
        type="game",
        eventDate="2026-08-22",
        eventTime="19:00",
        eventTitle="Hawks vs Eagles",
        eventLocation="Arena A",
        eventData={"game_number": "GM-202", "home_team_id": "525015"},
    )


def _sample_practice_detail() -> ScheduleEventDetail:
    """Return sample ScheduleEventDetail representing a practice.

    Returns:
        ScheduleEventDetail: Sample ScheduleEventDetail instance.

    """
    return ScheduleEventDetail(
        id="prac-303",
        type="practice",
        eventDate="2026-08-24",
        eventTime="06:00",
        eventTitle="Morning Skate",
        eventLocation="Rink 2",
    )


def test_schedule_get_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "get", "--help"])
    assert result.exit_code == 0
    assert "get" in result.output.lower()
    assert "--event-id" in result.output
    assert "--type" in result.output
    assert "--availability" in result.output
    assert "--fields" in result.output


def test_schedule_get_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get -e evt-101` renders event detail table."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "get", "-e", "evt-101"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    assert "evt-101" in result.output
    assert "Clubhouse" in result.output
    mock_action.assert_called_once()


def test_schedule_get_aliases(runner: CliRunner) -> None:
    """Test `schedule show` and `schedule view` aliases."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=_sample_event_detail(),
        ),
    ):
        for alias in ("show", "view"):
            result = runner.invoke(cli, ["schedule", alias, "-e", "evt-101"])
            assert result.exit_code == 0
            assert "Team Pizza Party" in result.output


def test_schedule_get_json_and_yaml(runner: CliRunner) -> None:
    """Test `schedule get -e evt-101 --format json` and `--format yaml`."""
    detail = _sample_event_detail()
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=detail,
        ),
    ):
        r_json = runner.invoke(cli, ["schedule", "get", "-e", "evt-101", "--format", "json"])
        assert r_json.exit_code == 0
        parsed = json.loads(r_json.output)
        assert parsed[0]["eventTitle"] == "Team Pizza Party"

        r_yaml = runner.invoke(cli, ["schedule", "get", "-e", "evt-101", "--format", "yaml"])
        assert r_yaml.exit_code == 0
        assert "eventTitle: Team Pizza Party" in r_yaml.output


def test_schedule_get_fields_and_availability(runner: CliRunner) -> None:
    """Test `schedule get -e evt-101 --fields ... --availability`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.main.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "get",
                "-e",
                "evt-101",
                "--fields",
                "eventTitle,eventLocation",
                "--availability",
                "-t",
                "team-123",
            ],
        )

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    assert "Clubhouse" in result.output
    assert "17:00" not in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_availability") is True
    assert kwargs.get("team_id") == "team-123"


def test_schedule_get_missing_event_id(runner: CliRunner) -> None:
    """Test `schedule get` missing required event ID exits with code 2."""
    result = runner.invoke(cli, ["schedule", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_events_get_command(runner: CliRunner) -> None:
    """Test `schedule events get -e evt-101` command."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "events", "get", "-e", "evt-101"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    mock_action.assert_called_once()


def test_schedule_events_get_aliases(runner: CliRunner) -> None:
    """Test `schedule events show` and `schedule events view` aliases."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.events.run_action_or_exit",
            return_value=_sample_event_detail(),
        ),
    ):
        for alias in ("show", "view"):
            result = runner.invoke(cli, ["schedule", "events", alias, "-e", "evt-101"])
            assert result.exit_code == 0
            assert "Team Pizza Party" in result.output


def test_schedule_events_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule events get` without event ID exits with code 2."""
    result = runner.invoke(cli, ["schedule", "events", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_games_get_command(runner: CliRunner) -> None:
    """Test `schedule games get -g 202` command."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=_sample_game_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "games", "get", "-g", "202"])

    assert result.exit_code == 0
    assert "Hawks vs Eagles" in result.output
    mock_action.assert_called_once()


def test_schedule_games_get_aliases(runner: CliRunner) -> None:
    """Test `schedule games show` and `schedule games view` aliases."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=_sample_game_detail(),
        ),
    ):
        for alias in ("show", "view"):
            result = runner.invoke(cli, ["schedule", "games", alias, "-g", "202"])
            assert result.exit_code == 0
            assert "Hawks vs Eagles" in result.output


def test_schedule_games_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule games get` without game ID exits with code 2."""
    result = runner.invoke(cli, ["schedule", "games", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_practices_get_command(runner: CliRunner) -> None:
    """Test `schedule practices get -p prac-303` command."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=_sample_practice_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "practices", "get", "-p", "prac-303"])

    assert result.exit_code == 0
    assert "Morning Skate" in result.output
    mock_action.assert_called_once()


def test_schedule_practices_get_aliases(runner: CliRunner) -> None:
    """Test `schedule practices show` and `schedule practices view` aliases."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.practices.run_action_or_exit",
            return_value=_sample_practice_detail(),
        ),
    ):
        for alias in ("show", "view"):
            result = runner.invoke(cli, ["schedule", "practices", alias, "-p", "prac-303"])
            assert result.exit_code == 0
            assert "Morning Skate" in result.output


def test_schedule_practices_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule practices get` without practice ID exits with code 2."""
    result = runner.invoke(cli, ["schedule", "practices", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_subscribe_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "subscribe", "--help"])
    assert result.exit_code == 0
    assert "subscribe" in result.output.lower()
    assert "--team-id" in result.output
    assert "--apple-calendar" in result.output
    assert "--google-calendar" in result.output
    assert "--calendar-url" in result.output


def test_schedule_subscribe_default_output(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123` output."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "googleCalendar" in result.output
    assert "calendarUrl" in result.output
    assert "webcal://" in result.output
    assert "https://calendar.google.com/calendar/r?cid=" in result.output


def test_schedule_subscribe_alias_sub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule sub -t team-123` alias."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "sub", "-t", team_id])
    assert result.exit_code == 0
    assert "webcal://" in result.output


def test_schedule_subscribe_apple_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123 --apple`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--apple"])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "googleCalendar" not in result.output


def test_schedule_subscribe_google_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123 --google`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--google"])
    assert result.exit_code == 0
    assert "googleCalendar" in result.output
    assert "calendarUrl" not in result.output


def test_schedule_subscribe_webcal_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123 --webcal`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--webcal"])
    assert result.exit_code == 0
    assert "calendarUrl" in result.output
    assert "googleCalendar" not in result.output


def test_schedule_subscribe_columns_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123 --columns apple,google`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(
        cli,
        ["schedule", "subscribe", "-t", team_id, "--columns", "apple,google"],
    )
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "googleCalendar" in result.output
    assert "calendarUrl" not in result.output


def test_schedule_subscribe_json_format(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -t team-123 --format json`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(
        cli,
        ["schedule", "subscribe", "-t", team_id, "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert "appleCalendar" in data[0]
    assert "googleCalendar" in data[0]


def test_schedule_subscribe_missing_team_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe` missing required team ID."""
    result = runner.invoke(cli, ["schedule", "subscribe"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_subscribe_envvar(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe` using GAMESHEET_TEAM_ID env var."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(
        cli,
        ["schedule", "subscribe"],
        env={"GAMESHEET_TEAM_ID": team_id},
    )
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
