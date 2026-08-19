# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule CLI command group."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from click.exceptions import Exit

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    CreatedGameResult,
    ScheduleEvent,
    ScheduleEventDetail,
)

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


def _sample_event_detail() -> ScheduleEventDetail:
    """Return sample ScheduleEventDetail for CLI tests."""
    return ScheduleEventDetail(
        id="occ-101",
        type="event",
        eventDate="2026-08-20",
        eventTime="17:00",
        eventTitle="Team Pizza Party",
        eventLocation="Clubhouse",
        eventData={"notes": "Bring drinks"},
        availability={"attendees": [{"name": "Player 1"}]},
    )


def test_schedule_get_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get --help` shows usage and options."""
    result = runner.invoke(cli, ["schedule", "get", "--help"])
    assert result.exit_code == 0
    assert "--event-id" in result.output
    assert "--team-id" in result.output
    assert "--availability" in result.output


def test_schedule_get_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get -e occ-101` renders event detail."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "get", "-e", "occ-101"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    mock_action.assert_called_once()


def test_schedule_get_aliases(runner: CliRunner) -> None:
    """Test `schedule show` and `schedule view` aliases for get."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ),
    ):
        r_show = runner.invoke(cli, ["schedule", "show", "-e", "occ-101"])
        r_view = runner.invoke(cli, ["schedule", "view", "-e", "occ-101"])

    assert r_show.exit_code == 0
    assert "Team Pizza Party" in r_show.output
    assert r_view.exit_code == 0
    assert "Team Pizza Party" in r_view.output


def test_schedule_get_json_and_yaml(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get` format options."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ),
    ):
        r_json = runner.invoke(cli, ["schedule", "get", "-e", "occ-101", "--format", "json"])
        r_yaml = runner.invoke(cli, ["schedule", "get", "-e", "occ-101", "--format", "yaml"])

    assert r_json.exit_code == 0
    parsed = json.loads(r_json.output)
    assert parsed[0]["eventTitle"] == "Team Pizza Party"
    assert parsed[0]["type"] == "event"

    assert r_yaml.exit_code == 0
    assert "eventTitle: Team Pizza Party" in r_yaml.output


def test_schedule_get_fields_and_availability(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get` with --fields, --team-id, and --availability."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "get",
                "-e",
                "occ-101",
                "-t",
                "team-123",
                "--availability",
                "--fields",
                "eventTitle,type",
            ],
        )

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("team_id") == "team-123"
    assert kwargs.get("include_availability") is True


def test_schedule_get_missing_event_id(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule get` errors when --event-id is missing."""
    result = runner.invoke(cli, ["schedule", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "--event-id" in result.output


def test_schedule_events_get_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events get -e occ-101`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "events", "get", "-e", "occ-101", "--include-availability"])

    assert result.exit_code == 0
    assert "Team Pizza Party" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_availability") is True


def test_schedule_events_get_aliases(runner: CliRunner) -> None:
    """Test `schedule events show` and `schedule events view`."""
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=_sample_event_detail(),
        ),
    ):
        r_show = runner.invoke(cli, ["schedule", "events", "show", "-e", "occ-101"])
        r_view = runner.invoke(cli, ["schedule", "events", "view", "-e", "occ-101"])

    assert r_show.exit_code == 0
    assert "Team Pizza Party" in r_show.output
    assert r_view.exit_code == 0
    assert "Team Pizza Party" in r_view.output


def test_schedule_events_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule events get` missing option."""
    result = runner.invoke(cli, ["schedule", "events", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_games_get_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games get --game-id gm-202`."""
    game_detail = ScheduleEventDetail(
        id=202,
        type="game",
        eventDate="2026-08-22",
        eventTime="19:00",
        eventTitle="Hawks vs Eagles",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=game_detail,
        ) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "games", "get", "--game-id", "gm-202", "--availability"])

    assert result.exit_code == 0
    assert "Hawks vs Eagles" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_availability") is True


def test_schedule_games_get_aliases(runner: CliRunner) -> None:
    """Test `schedule games show` and `schedule games view`."""
    game_detail = ScheduleEventDetail(id="202", type="game", eventTitle="Hawks vs Eagles")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=game_detail,
        ),
    ):
        r_show = runner.invoke(cli, ["schedule", "games", "show", "-e", "202"])
        r_view = runner.invoke(cli, ["schedule", "games", "view", "-e", "202"])

    assert r_show.exit_code == 0
    assert "Hawks vs Eagles" in r_show.output
    assert r_view.exit_code == 0
    assert "Hawks vs Eagles" in r_view.output


def test_schedule_games_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule games get` missing option."""
    result = runner.invoke(cli, ["schedule", "games", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_practices_get_command(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices get --practice-id pr-303`."""
    practice_detail = ScheduleEventDetail(
        id="prac-303",
        type="practice",
        eventDate="2026-08-24",
        eventTime="06:00",
        eventTitle="Morning Skate",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=practice_detail,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "practices", "get", "--practice-id", "pr-303", "--availability"],
        )

    assert result.exit_code == 0
    assert "Morning Skate" in result.output
    _, kwargs = mock_action.call_args
    assert kwargs.get("include_availability") is True


def test_schedule_practices_get_aliases(runner: CliRunner) -> None:
    """Test `schedule practices show` and `schedule practices view`."""
    practice_detail = ScheduleEventDetail(id="prac-303", type="practice", eventTitle="Morning Skate")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=practice_detail,
        ),
    ):
        r_show = runner.invoke(cli, ["schedule", "practices", "show", "-e", "prac-303"])
        r_view = runner.invoke(cli, ["schedule", "practices", "view", "-e", "prac-303"])

    assert r_show.exit_code == 0
    assert "Morning Skate" in r_show.output
    assert r_view.exit_code == 0
    assert "Morning Skate" in r_view.output


def test_schedule_practices_get_missing_id(runner: CliRunner) -> None:
    """Test `schedule practices get` missing option."""
    result = runner.invoke(cli, ["schedule", "practices", "get"])
    assert result.exit_code == 2
    assert "Missing option" in result.output


def test_schedule_subscribe_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --help`."""
    result = runner.invoke(cli, ["schedule", "subscribe", "--help"])
    assert result.exit_code == 0
    assert "--team-id" in result.output
    assert "--apple" in result.output
    assert "--google" in result.output
    assert "--webcal" in result.output
    assert "--columns" in result.output


def test_schedule_subscribe_default_output(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe` with default options."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "--team-id", team_id])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "googleCalendar" in result.output
    assert "calendarUrl" in result.output
    expected_feed_prefix = (
        f"webcal://api.teams.gamesheet.app/api/public/calendar/teams/{team_id}/calendar.ics#v"
    )
    assert expected_feed_prefix in result.output
    assert "https://calendar.google.com/calendar/r?cid=" in result.output


def test_schedule_subscribe_alias_sub(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule sub` alias."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "sub", "-t", team_id])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output


def test_schedule_subscribe_apple_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --apple` and `--apple-calendar`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--apple"])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "googleCalendar" not in result.output

    result_long = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--apple-calendar"])
    assert result_long.exit_code == 0
    assert "appleCalendar" in result_long.output
    assert "googleCalendar" not in result_long.output


def test_schedule_subscribe_google_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --google` and `--google-calendar`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--google"])
    assert result.exit_code == 0
    assert "googleCalendar" in result.output
    assert "appleCalendar" not in result.output

    result_long = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--google-calendar"])
    assert result_long.exit_code == 0
    assert "googleCalendar" in result_long.output
    assert "appleCalendar" not in result_long.output


def test_schedule_subscribe_webcal_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --webcal` and `--calendar-url`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--webcal"])
    assert result.exit_code == 0
    assert "calendarUrl" in result.output
    assert "googleCalendar" not in result.output

    result_long = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "--calendar-url"])
    assert result_long.exit_code == 0
    assert "calendarUrl" in result_long.output
    assert "googleCalendar" not in result_long.output


def test_schedule_subscribe_columns_flag(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe --columns` with exact and alias names."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "-c", "appleCalendar,calendarUrl"])
    assert result.exit_code == 0
    assert "appleCalendar" in result.output
    assert "calendarUrl" in result.output
    assert "googleCalendar" not in result.output

    result_aliases = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "-c", "google,url"])
    assert result_aliases.exit_code == 0
    assert "googleCalendar" in result_aliases.output
    assert "calendarUrl" in result_aliases.output
    assert "appleCalendar" not in result_aliases.output


def test_schedule_subscribe_json_format(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule subscribe -F json`."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    result = runner.invoke(cli, ["schedule", "subscribe", "-t", team_id, "-F", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert "appleCalendar" in data[0]
    assert "googleCalendar" in data[0]
    assert "calendarUrl" in data[0]


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


# ---------------------------------------------------------------------------
# events create tests
# ---------------------------------------------------------------------------


def test_events_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule events create --help`."""
    result = runner.invoke(cli, ["schedule", "events", "create", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output.lower()
    assert "--start-datetime" in result.output
    assert "--duration" in result.output
    assert "--repeat" in result.output
    assert "--all-day" in result.output


def test_practices_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule practices create --help`."""
    result = runner.invoke(cli, ["schedule", "practices", "create", "--help"])
    assert result.exit_code == 0
    assert "practice" in result.output.lower()
    assert "--start-datetime" in result.output


def test_games_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games create --help`."""
    result = runner.invoke(cli, ["schedule", "games", "create", "--help"])
    assert result.exit_code == 0
    assert "game" in result.output.lower()
    assert "--opposing-team-id" in result.output
    assert "--home" in result.output
    assert "--number" in result.output


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
                "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                    "--start-datetime",
                    "2026-08-21 13:30",
                    "--end-datetime",
                    "2026-08-21 14:30",
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
    """Test `schedule events create` with split --start-date/--start-time and --end-date/--end-time."""
    mock_created = CalendarEventCreated(
        id="evt-created-2",
        title="Team Dinner",
        type="event",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-date",
                "2026-08-21",
                "--start-time",
                "18:00",
                "--end-date",
                "2026-08-21",
                "--end-time",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--end-datetime",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-date",
                "2026-08-25",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        kwargs = mock_action.call_args[1]
        assert args[4] == "2026-08-25"
        assert args[5] == ""
        assert kwargs["all_day"] is True


def test_events_create_all_day_conflict(runner: CliRunner) -> None:
    """Test `schedule events create --all-day` with conflicting start-datetime and start-date."""
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
            "--start-datetime",
            "2026-08-25",
            "--start-date",
            "2026-08-25",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine --start-datetime with --start-date/--start-time" in result.output


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
    """Test `schedule events create` with conflicting start-datetime and start-date."""
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
            "--start-datetime",
            "2026-08-21 10:00",
            "--start-date",
            "2026-08-21",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine --start-datetime with --start-date/--start-time" in result.output


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
            "--start-datetime",
            "2026-08-21 10:00",
        ],
    )
    assert result.exit_code == 2
    assert "At least 2 of --start-datetime, --end-datetime, --duration are required" in result.output


def test_events_create_repeating_weekly(runner: CliRunner) -> None:
    """Test `schedule events create` with weekly recurrence flags."""
    mock_created = CalendarEventCreated(id="evt-created-6", title="Weekly Workout")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
                "2026-08-22 11:30",
                "--duration",
                "60",
                "--repeat",
                "weekly",
                "--interval",
                "1",
                "--by-day",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
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


# ---------------------------------------------------------------------------
# practices create tests
# ---------------------------------------------------------------------------


def test_practices_create_default_title(runner: CliRunner) -> None:
    """Test `schedule practices create` uses default title 'Practice'."""
    mock_created = CalendarEventCreated(
        id="prac-created-1",
        title="Practice",
        type="practice",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
                "2026-08-30 13:30",
                "--end-datetime",
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
                "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                    "--start-datetime",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-date",
                "2026-08-30",
            ],
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        kwargs = mock_action.call_args[1]
        assert args[3] == "2026-08-30"
        assert args[4] == ""
        assert kwargs["all_day"] is True


def test_practices_create_all_day_conflict(runner: CliRunner) -> None:
    """Test `schedule practices create --all-day` with conflicting start-datetime and start-date."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "create",
            "-t",
            "team-123",
            "--all-day",
            "--start-datetime",
            "2026-08-30",
            "--start-date",
            "2026-08-30",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine --start-datetime with --start-date/--start-time" in result.output


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
                "2026-08-31 15:30",
                "--duration",
                "60",
                "--repeat",
                "monthly",
                "--interval",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "practices",
                "create",
                "--start-datetime",
                "2026-08-30 10:00",
                "--duration",
                "60",
            ],
            env={"GAMESHEET_TEAM_ID": "env-team-uuid"},
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[2] == "env-team-uuid"


# ---------------------------------------------------------------------------
# games create tests
# ---------------------------------------------------------------------------


def test_games_create_home_and_aliases(runner: CliRunner) -> None:
    """Test `schedule games create`, `add`, `new` as home team."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
        home_flag=True,
    )
    for subcmd in ["create", "add", "new"]:
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
                return_value=mock_created,
            ) as mock_action,
        ):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "games",
                    subcmd,
                    "-t",
                    "525015",
                    "--opposing-team-id",
                    "523675",
                    "--season-id",
                    "15020",
                    "--division-id",
                    "81419",
                    "--number",
                    "TEST-123",
                    "--home",
                    "--start-datetime",
                    "2026-08-20 12:00",
                    "--end-datetime",
                    "2026-08-20 13:15",
                ],
            )
            assert result.exit_code == 0
            assert "TEST-123" in result.output
            args = mock_action.call_args[0]
            kwargs = mock_action.call_args[1]
            assert args[2] == "525015"
            assert args[3] == "15020"
            assert args[4] == "81419"
            assert args[5] == "523675"
            assert args[6] == "2026-08-20T12:00"
            assert args[7] == "13:15"
            assert kwargs["home_flag"] is True
            assert kwargs["game_number"] == "TEST-123"


def test_games_create_visitor(runner: CliRunner) -> None:
    """Test `schedule games create --visitor`."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
        home_flag=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--number",
                "TEST-123",
                "--visitor",
                "--start-datetime",
                "2026-08-20 12:00",
                "--duration",
                "75",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["home_flag"] is False


def test_games_create_all_options(runner: CliRunner) -> None:
    """Test `schedule games create` with all options provided."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        location="Polar Ice",
        broadcast_provider="LIVEBARN",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--opposing-division-id",
                "81420",
                "--association-id",
                "38",
                "--league-id",
                "1148580",
                "--number",
                "TEST-123",
                "--game-type",
                "playoff",
                "--location",
                "Polar Ice",
                "--scorekeeper-name",
                "Jane Doe",
                "--scorekeeper-phone",
                "555-1234",
                "--broadcaster",
                "LIVEBARN",
                "--time-zone-name",
                "America/New_York",
                "--time-zone-offset",
                "-240",
                "--start-date",
                "2026-08-20",
                "--start-time",
                "12:00",
                "--end-date",
                "2026-08-20",
                "--end-time",
                "13:15",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["opposing_division"] == "81420"
        assert kwargs["association_id"] == "38"
        assert kwargs["league_id"] == "1148580"
        assert kwargs["game_type"] == "playoff"
        assert kwargs["location"] == "Polar Ice"
        assert kwargs["scorekeeper_name"] == "Jane Doe"
        assert kwargs["scorekeeper_phone"] == "555-1234"
        assert kwargs["broadcast_provider"] == "LIVEBARN"
        assert kwargs["time_zone_name"] == "America/New_York"
        assert kwargs["time_zone_offset"] == -240


def test_games_create_missing_required(runner: CliRunner) -> None:
    """Test `schedule games create` missing required options."""
    res = runner.invoke(
        cli,
        [
            "schedule",
            "games",
            "create",
            "-t",
            "525015",
            "--season-id",
            "15020",
        ],
    )
    assert res.exit_code == 2
    assert "Missing option" in res.output


def test_games_create_envvars(runner: CliRunner) -> None:
    """Test `schedule games create` with GAMESHEET_TEAM_ID and GAMESHEET_SEASON_ID envvars."""
    mock_created = CreatedGameResult(success=True, game_number="TEST-123")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_created,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "--opposing-team-id",
                "523675",
                "--division-id",
                "81419",
                "--number",
                "TEST-123",
                "--start-datetime",
                "2026-08-20 12:00",
                "--duration",
                "75",
            ],
            env={
                "GAMESHEET_TEAM_ID": "525015",
                "GAMESHEET_SEASON_ID": "15020",
            },
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[2] == "525015"
        assert args[3] == "15020"


def test_games_create_json_format(runner: CliRunner) -> None:
    """Test `schedule games create -F json`."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_created,
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--number",
                "TEST-123",
                "--start-datetime",
                "2026-08-20 12:00",
                "--duration",
                "75",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["success"] is True
        assert data[0]["game_number"] == "TEST-123"
