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
    ScheduleDeleteResult,
    ScheduleEvent,
    ScheduleEventDetail,
    UpdatedGameResult,
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
            "--start-datetime",
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


def test_schedule_delete_game_force(runner: CliRunner) -> None:
    """Test `schedule delete` with numeric game ID and --force."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert "Successfully deleted game 2962920" in result.output
        mock_action.assert_called_once()


def test_schedule_delete_event_force(runner: CliRunner) -> None:
    """Test `schedule delete` with UUID event ID and --force."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert "Successfully deleted event evt-uuid-1" in result.output
        mock_action.assert_called_once()


def test_schedule_delete_prompt_confirm(runner: CliRunner) -> None:
    """Test `schedule delete` interactive prompt confirmation."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert "Successfully deleted game 2962920" in result.output


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
    mock_res = ScheduleDeleteResult(
        success=True,
        message="Occurrence and all future occurrences deleted successfully",
        id="evt-uuid-1",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\ny\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-uuid-1" in result.output
        kwargs = mock_action.call_args[1]
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

    result2 = runner.invoke(
        cli,
        [
            "schedule",
            "delete",
            "-e",
            "evt-1",
            "--force",
            "--all",
            "--future",
        ],
    )
    assert result2.exit_code == 2
    assert "Cannot combine" in result2.output

    result3 = runner.invoke(
        cli,
        [
            "schedule",
            "delete",
            "-e",
            "evt-1",
            "--force",
            "--future",
            "--single",
        ],
    )
    assert result3.exit_code == 2
    assert "Cannot combine" in result3.output


def test_schedule_delete_json_output(runner: CliRunner) -> None:
    """Test `schedule delete -F json`."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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


def test_events_delete_force(runner: CliRunner) -> None:
    """Test `schedule events delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert "Successfully deleted event evt-101" in result.output
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert "Successfully deleted event evt-series" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["all_occurrences"] is True


def test_events_delete_prompt(runner: CliRunner) -> None:
    """Test `schedule events delete` interactive prompt."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\nn\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-101" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is False


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

    result2 = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "delete",
            "-e",
            "evt-101",
            "--force",
            "--all",
            "--future",
        ],
    )
    assert result2.exit_code == 2
    assert "Cannot combine" in result2.output

    result3 = runner.invoke(
        cli,
        [
            "schedule",
            "events",
            "delete",
            "-e",
            "evt-101",
            "--force",
            "--future",
            "--single",
        ],
    )
    assert result3.exit_code == 2
    assert "Cannot combine" in result3.output


def test_events_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule events del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="evt-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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


def test_games_delete_force(runner: CliRunner) -> None:
    """Test `schedule games delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
                "--force",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully deleted game 2962920" in result.output
        mock_action.assert_called_once()


def test_games_delete_prompt_confirm_and_abort(runner: CliRunner) -> None:
    """Test `schedule games delete` interactive confirmation and abortion."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        # Confirm
        res1 = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
            ],
            input="y\n",
        )
        assert res1.exit_code == 0
        assert "Successfully deleted game 2962920" in res1.output

        # Abort
        res2 = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
            ],
            input="n\n",
        )
        assert res2.exit_code == 1
        assert "Aborted" in res2.output


def test_games_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule games del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        for alias in ("del", "rm", "remove"):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "games",
                    alias,
                    "-g",
                    "2962920",
                    "--force",
                    "-F",
                    "json",
                ],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data[0]["success"] is True


def test_practices_delete_force(runner: CliRunner) -> None:
    """Test `schedule practices delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="prac-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="prac-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\ny\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-101" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is True


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

    result2 = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "delete",
            "-p",
            "prac-101",
            "--force",
            "--all",
            "--future",
        ],
    )
    assert result2.exit_code == 2
    assert "Cannot combine" in result2.output

    result3 = runner.invoke(
        cli,
        [
            "schedule",
            "practices",
            "delete",
            "-p",
            "prac-101",
            "--force",
            "--future",
            "--single",
        ],
    )
    assert result3.exit_code == 2
    assert "Cannot combine" in result3.output


def test_practices_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule practices del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="prac-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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


def test_schedule_delete_event_repeating_prompt_no(runner: CliRunner) -> None:
    """Test `schedule delete` event with prompt answering no to repeating future."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\nn\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-uuid-1" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is False


def test_schedule_delete_event_json_output(runner: CliRunner) -> None:
    """Test `schedule delete` on event with -F json."""
    mock_res = ScheduleDeleteResult(success=True, message="Occurrence deleted successfully", id="evt-uuid-1")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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


def test_events_delete_prompt_yes(runner: CliRunner) -> None:
    """Test `schedule events delete` prompt answering yes to repeating future."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="evt-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\ny\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted event evt-101" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is True


def test_practices_delete_prompt_no(runner: CliRunner) -> None:
    """Test `schedule practices delete` prompt answering no to repeating future."""
    mock_res = ScheduleDeleteResult(success=True, message="Deleted", id="prac-101")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            ],
            input="y\nn\n",
        )
        assert result.exit_code == 0
        assert "Successfully deleted practice prac-101" in result.output
        kwargs = mock_action.call_args[1]
        assert kwargs["delete_future"] is False


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
        assert payload_sent["location_name"] == "New Rink"


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
    assert result.exit_code != 0
    assert "Cannot specify both --future and --single" in result.output


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
                "2026-08-21 16:00",
                "--duration",
                "90",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["start_date"] == "2026-08-21T16:00:00Z"
        assert payload_sent["end_date"] == "2026-08-21T17:30:00Z"


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--interval",
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
    assert result.exit_code != 0
    assert "Cannot specify both --future and --single" in result.output


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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


def test_games_update_basic(runner: CliRunner) -> None:
    """Test `schedule games update` updates location, number, scorekeeper."""
    mock_game = {
        "id": 2962945,
        "team_id": 525015,
        "opposing_team_id": 523675,
        "season_id": 15020,
        "division_id": 81419,
        "opposing_division": 81419,
        "association_id": 38,
        "league_id": 1148580,
        "home_flag": True,
        "game_number": "OLD-1",
        "game_type": "regular_season",
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
        "location": "Old Rink",
        "scorekeeper_name": "Old SK",
        "scorekeeper_phone": "555-0000",
        "broadcast_provider": "LIVEBARN",
    }
    mock_updated = UpdatedGameResult(
        success=True,
        id=2962945,
        game_number="NEW-100",
        location="New Arena",
        scorekeeper_name="New SK",
        date_time="2026-08-24T15:00",
        end_time="16:15",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962945",
                "--number",
                "NEW-100",
                "--location",
                "New Arena",
                "--scorekeeper-name",
                "New SK",
            ],
        )
        assert result.exit_code == 0
        assert "NEW-100" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["game_number"] == "NEW-100"
        assert kwargs["location"] == "New Arena"
        assert kwargs["scorekeeper_name"] == "New SK"
        assert kwargs["team_id"] == 525015


def test_games_update_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule games update` with datetime calculation using duration."""
    mock_game = {
        "id": 2962946,
        "team_id": 525015,
        "opposing_team_id": 523675,
        "season_id": 15020,
        "division_id": 81419,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(
        success=True,
        id=2962946,
        date_time="2026-08-25T18:00",
        end_time="19:30",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962946",
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


def test_games_update_aliases(runner: CliRunner) -> None:
    """Test `schedule games set` and `schedule games edit` aliases."""
    mock_game = {
        "id": 2962947,
        "team_id": 525015,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962947)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            side_effect=[mock_game, mock_updated, mock_game, mock_updated],
        ),
    ):
        res1 = runner.invoke(cli, ["schedule", "games", "set", "-g", "2962947"])
        assert res1.exit_code == 0
        res2 = runner.invoke(cli, ["schedule", "games", "edit", "-g", "2962947"])
        assert res2.exit_code == 0


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--number",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "--future",
            "--single",
        ],
    )
    assert result.exit_code != 0
    assert "Cannot specify both --future and --single" in result.output


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--interval",
                "1",
                "--repeat-until",
                "2026-11-28",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["rrule"] == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"


def test_games_update_no_t_in_date_time(runner: CliRunner) -> None:
    """Test `schedule games update` when current game date_time has no T."""
    mock_game = {
        "id": 2962950,
        "team_id": 525015,
        "date_time": "2026-08-24",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962950)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962950",
            ],
        )
        assert result.exit_code == 0


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
                "--start-datetime",
                "2026-08-21 07:00",
                "--duration",
                "60",
                "--single",
            ],
        )
        assert result.exit_code == 0
        payload_sent = mock_action.call_args_list[1][0][3]
        assert payload_sent["start_date"] == "2026-08-21T07:00:00Z"
        assert payload_sent["end_date"] == "2026-08-21T08:00:00Z"


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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
            "gamesheet_sdk.teams.cli.commands.schedule.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.run_action_or_exit",
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
