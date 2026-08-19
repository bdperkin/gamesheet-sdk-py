# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the teams schedule domain module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import responses

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    CalendarSubscription,
    CreatedGameResult,
    ScheduleEvent,
    ScheduleEventDetail,
    build_rrule,
    create_calendar_event_raw,
    create_event,
    create_game,
    create_practice,
    create_schedule_game_raw,
    fetch_availability_raw,
    fetch_calendar_raw,
    fetch_event_occurrence_raw,
    fetch_scheduled_game_raw,
    get_calendar_subscription,
    get_event,
    get_game,
    get_practice,
    get_schedule_event,
    list_events,
    list_games,
    list_practices,
    list_schedule,
    validate_game_type,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_AVAILABILITY_BATCH_PATH,
    TEAMS_CALENDAR_EVENTS_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_CALENDAR_PATH,
    TEAMS_REFRESH_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

_CALENDAR_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_PATH}"
_CALENDAR_EVENTS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_EVENTS_PATH}"
_OCCURRENCE_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_OCCURRENCES_PATH}"
_SCHEDULE_GAME_URL = f"{TEAMS_API_GATEWAY}{TEAMS_SCHEDULE_GAME_PATH}"
_AVAILABILITY_URL = f"{TEAMS_API_GATEWAY}{TEAMS_AVAILABILITY_BATCH_PATH}"
_REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"


def _make_session() -> TeamsAuthenticatedSession:
    """Create a test TeamsAuthenticatedSession."""
    config = Config()
    return TeamsAuthenticatedSession(
        config,
        access_token="test-access",
        refresh_token="test-refresh",
    )


def _sample_calendar_data() -> list[dict[str, Any]]:
    """Return sample calendar event data list."""
    return [
        {
            "id": "evt-101",
            "type": "event",
            "eventDate": "2026-08-20",
            "eventTime": "17:00",
            "eventTitle": "Team Pizza Party",
            "eventLocation": "Clubhouse",
            "eventData": {"notes": "Bring drinks"},
            "customField": "extra",
        },
        {
            "id": 202,
            "type": "game",
            "eventDate": "2026-08-22",
            "eventTime": "19:00",
            "eventTitle": "Hawks vs Eagles",
            "eventLocation": "Arena A",
            "eventData": {"homeTeam": "Hawks", "awayTeam": "Eagles"},
        },
        {
            "id": "prac-303",
            "type": "practice",
            "eventDate": "2026-08-24",
            "eventTime": "06:00",
            "eventTitle": "Morning Skate",
            "eventLocation": "Rink 2",
            "eventData": {"drills": ["skating", "passing"]},
        },
    ]


def test_schedule_event_model() -> None:
    """Test ScheduleEvent model creation and default values."""
    event = ScheduleEvent(
        id="evt-1",
        type="game",
        eventDate="2026-08-18",
        eventTime="18:30",
        eventTitle="Championship Game",
        eventLocation="Main Arena",
        extraAttr="allowed",
    )
    assert event.id == "evt-1"
    assert event.type == "game"
    assert event.eventDate == "2026-08-18"
    assert event.eventTime == "18:30"
    assert event.eventTitle == "Championship Game"
    assert event.eventLocation == "Main Arena"
    assert (event.model_extra or {}).get("extraAttr") == "allowed"


def test_schedule_event_model_defaults() -> None:
    """Test ScheduleEvent model with empty defaults."""
    event = ScheduleEvent()
    assert event.id is None
    assert event.type == ""
    assert event.eventDate == ""
    assert event.eventTime == ""
    assert event.eventTitle == ""
    assert event.eventLocation == ""


@responses.activate
def test_fetch_calendar_raw_success() -> None:
    """Test fetch_calendar_raw successfully retrieves calendar data."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    result = fetch_calendar_raw(session, "team-123", month="all")
    assert result["success"] is True
    assert len(result["data"]) == 3


@responses.activate
def test_fetch_calendar_raw_with_month() -> None:
    """Test fetch_calendar_raw with specific month param."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": []},
        status=200,
    )
    session = _make_session()
    result = fetch_calendar_raw(session, "team-123", month="2026-08")
    assert result["data"] == []


@responses.activate
def test_fetch_calendar_raw_unauthorized() -> None:
    """Test fetch_calendar_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_calendar_raw(session, "team-123")


def test_fetch_calendar_raw_direct_401() -> None:
    """Test fetch_calendar_raw handles 401 directly from session.get."""
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_session.get.return_value = mock_resp

    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_calendar_raw(mock_session, "team-123")


@responses.activate
def test_fetch_calendar_raw_server_error() -> None:
    """Test fetch_calendar_raw raises GameSheetError on 500."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        body="Internal Server Error",
        status=500,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/calendar returned HTTP 500"):
        fetch_calendar_raw(session, "team-123")


@responses.activate
def test_fetch_calendar_raw_invalid_json() -> None:
    """Test fetch_calendar_raw raises GameSheetError on invalid JSON response."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        body="not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse calendar JSON response"):
        fetch_calendar_raw(session, "team-123")


@responses.activate
def test_fetch_calendar_raw_non_dict_response() -> None:
    """Test fetch_calendar_raw raises GameSheetError if JSON is not a dict."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json=["not", "a", "dict"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format"):
        fetch_calendar_raw(session, "team-123")


@responses.activate
def test_list_schedule_all() -> None:
    """Test list_schedule returns all event types when event_type is None."""
    data: list[Any] = list(_sample_calendar_data())
    # Add a non-dict item to test resilience
    data.append("not a dict")
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": data},
        status=200,
    )
    session = _make_session()
    events = list_schedule(session, "team-123")
    assert len(events) == 3
    assert events[0].id == "evt-101"
    assert events[0].type == "event"
    assert events[1].id == 202
    assert events[1].type == "game"
    assert events[2].id == "prac-303"
    assert events[2].type == "practice"


@responses.activate
def test_list_schedule_malformed_data_field() -> None:
    """Test list_schedule raises GameSheetError if data field is not a list."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": "not a list"},
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Malformed response: 'data' field is not a list"):
        list_schedule(session, "team-123")


@responses.activate
def test_list_events() -> None:
    """Test list_events returns only 'event' type items."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    events = list_events(session, "team-123")
    assert len(events) == 1
    assert events[0].id == "evt-101"
    assert events[0].type == "event"
    assert events[0].eventTitle == "Team Pizza Party"


@responses.activate
def test_list_games() -> None:
    """Test list_games returns only 'game' type items."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    games = list_games(session, "team-123")
    assert len(games) == 1
    assert games[0].id == 202
    assert games[0].type == "game"
    assert games[0].eventTitle == "Hawks vs Eagles"


@responses.activate
def test_list_practices() -> None:
    """Test list_practices returns only 'practice' type items."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    practices = list_practices(session, "team-123")
    assert len(practices) == 1
    assert practices[0].id == "prac-303"
    assert practices[0].type == "practice"
    assert practices[0].eventTitle == "Morning Skate"
    assert "eventData" not in practices[0].model_dump(mode="json")


@responses.activate
def test_list_schedule_include_event_data() -> None:
    """Test list_schedule includes eventData when include_event_data=True."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    events = list_schedule(session, "team-123", include_event_data=True)
    assert len(events) == 3
    dump0 = events[0].model_dump(mode="json")
    assert "eventData" in dump0
    assert dump0["eventData"] == {"notes": "Bring drinks"}
    dump1 = events[1].model_dump(mode="json")
    assert dump1["eventData"] == {"homeTeam": "Hawks", "awayTeam": "Eagles"}


@responses.activate
def test_list_events_include_event_data() -> None:
    """Test list_events forwards include_event_data=True."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    events = list_events(session, "team-123", include_event_data=True)
    assert len(events) == 1
    dump = events[0].model_dump(mode="json")
    assert dump["eventData"] == {"notes": "Bring drinks"}


@responses.activate
def test_list_games_include_event_data() -> None:
    """Test list_games forwards include_event_data=True."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    games = list_games(session, "team-123", include_event_data=True)
    assert len(games) == 1
    dump = games[0].model_dump(mode="json")
    assert dump["eventData"] == {"homeTeam": "Hawks", "awayTeam": "Eagles"}


@responses.activate
def test_list_practices_include_event_data() -> None:
    """Test list_practices forwards include_event_data=True."""
    responses.add(
        responses.GET,
        _CALENDAR_URL,
        json={"success": True, "data": _sample_calendar_data()},
        status=200,
    )
    session = _make_session()
    practices = list_practices(session, "team-123", include_event_data=True)
    assert len(practices) == 1
    dump = practices[0].model_dump(mode="json")
    assert dump["eventData"] == {"drills": ["skating", "passing"]}


def test_schedule_event_detail_model() -> None:
    """Test ScheduleEventDetail model creation and default values."""
    detail = ScheduleEventDetail(
        id="occ-1",
        type="game",
        eventDate="2026-08-18",
        eventTime="19:00",
        eventTitle="Big Game",
        eventLocation="Main Rink",
        eventData={"notes": "Game notes"},
        availability={"players": [{"id": 1, "status": "yes"}]},
        extraProp="value",
    )
    assert detail.id == "occ-1"
    assert detail.type == "game"
    assert detail.eventDate == "2026-08-18"
    assert detail.eventTime == "19:00"
    assert detail.eventTitle == "Big Game"
    assert detail.eventLocation == "Main Rink"
    assert detail.eventData == {"notes": "Game notes"}
    assert detail.availability == {"players": [{"id": 1, "status": "yes"}]}
    assert (detail.model_extra or {}).get("extraProp") == "value"


def test_schedule_event_detail_defaults() -> None:
    """Test ScheduleEventDetail default values."""
    detail = ScheduleEventDetail()
    assert detail.id is None
    assert detail.type == ""
    assert detail.eventDate == ""
    assert detail.eventTime == ""
    assert detail.eventTitle == ""
    assert detail.eventLocation == ""
    assert detail.eventData is None
    assert detail.availability is None


@responses.activate
def test_fetch_event_occurrence_raw_success() -> None:
    """Test fetch_event_occurrence_raw successfully retrieves event data."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={"success": True, "data": {"id": "occ-101", "type": "event"}},
        status=200,
    )
    session = _make_session()
    result = fetch_event_occurrence_raw(session, "occ-101")
    assert result["success"] is True
    assert result["data"]["id"] == "occ-101"


@responses.activate
def test_fetch_event_occurrence_raw_unauthorized() -> None:
    """Test fetch_event_occurrence_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_event_occurrence_raw(session, "occ-101")


def test_fetch_event_occurrence_raw_direct_401() -> None:
    """Test fetch_event_occurrence_raw handles direct 401."""
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_session.get.return_value = mock_resp

    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_event_occurrence_raw(mock_session, "occ-101")


@responses.activate
def test_fetch_event_occurrence_raw_server_error() -> None:
    """Test fetch_event_occurrence_raw raises GameSheetError on 500."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        body="Internal Server Error",
        status=500,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/calendar/occurrences/occ-101 returned HTTP 500"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_event_occurrence_raw_invalid_json() -> None:
    """Test fetch_event_occurrence_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        body="not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse calendar occurrence JSON response"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_event_occurrence_raw_non_dict() -> None:
    """Test fetch_event_occurrence_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json=["not", "a", "dict"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_availability_raw_success() -> None:
    """Test fetch_availability_raw successfully retrieves availability data."""
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"success": True, "data": {"attendees": []}},
        status=200,
    )
    session = _make_session()
    result = fetch_availability_raw(session, "team-1", "evt-1", "practice")
    assert result["success"] is True
    assert result["data"]["attendees"] == []


@responses.activate
def test_fetch_availability_raw_unauthorized() -> None:
    """Test fetch_availability_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


def test_fetch_availability_raw_direct_401() -> None:
    """Test fetch_availability_raw handles direct 401."""
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_session.get.return_value = mock_resp

    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_availability_raw(mock_session, "team-1", "evt-1", "practice")


@responses.activate
def test_fetch_availability_raw_server_error() -> None:
    """Test fetch_availability_raw raises GameSheetError on 500."""
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        body="Internal Server Error",
        status=500,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/availability/batch returned HTTP 500"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_fetch_availability_raw_invalid_json() -> None:
    """Test fetch_availability_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        body="not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse availability JSON response"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_fetch_availability_raw_non_dict() -> None:
    """Test fetch_availability_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json=["not", "a", "dict"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_get_schedule_event_success_data_wrapped() -> None:
    """Test get_schedule_event with data wrapped dictionary."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "success": True,
            "data": {
                "id": "occ-101",
                "type": "event",
                "eventDate": "2026-08-20",
                "eventTime": "17:00",
                "eventTitle": "Team Pizza Party",
                "eventLocation": "Clubhouse",
                "eventData": {"notes": "Bring drinks"},
                "teamId": "team-123",
            },
        },
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, "occ-101")
    assert event.id == "occ-101"
    assert event.type == "event"
    assert event.eventTitle == "Team Pizza Party"
    assert event.eventData == {"notes": "Bring drinks"}
    assert event.availability is None


@responses.activate
def test_get_schedule_event_success_unwrapped() -> None:
    """Test get_schedule_event when response is not wrapped in 'data' key."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "id": "occ-101",
            "type": "game",
            "eventDate": "2026-08-22",
            "eventTitle": "Hawks vs Eagles",
        },
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, "occ-101")
    assert event.id == "occ-101"
    assert event.type == "game"


@responses.activate
def test_get_schedule_event_malformed_data() -> None:
    """Test get_schedule_event raises GameSheetError if data is not a dict."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={"data": "not a dict"},
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Malformed response: expected dict data"):
        get_schedule_event(session, "occ-101")


@responses.activate
def test_get_schedule_event_type_mismatch() -> None:
    """Test get_schedule_event raises GameSheetError if event_type does not match."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "game",
                "eventTitle": "Hawks vs Eagles",
            },
        },
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Event 'occ-101' is of type 'game', expected 'practice'\."):
        get_schedule_event(session, "occ-101", event_type="practice")


@responses.activate
def test_get_schedule_event_with_availability_explicit_team_id() -> None:
    """Test get_schedule_event with include_availability=True and explicit team_id."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "eventTitle": "Morning Practice",
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"success": True, "data": [{"userId": "user-1", "status": "attending"}]},
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(
        session,
        "occ-101",
        include_availability=True,
        team_id="team-999",
    )
    assert event.availability == [{"userId": "user-1", "status": "attending"}]


@responses.activate
def test_get_schedule_event_with_availability_inferred_team_id() -> None:
    """Test get_schedule_event with include_availability=True and teamId in eventData."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "eventTitle": "Morning Practice",
                "eventData": {"teamId": "team-888"},
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"data": [{"userId": "user-2", "status": "absent"}]},
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == [{"userId": "user-2", "status": "absent"}]


@responses.activate
def test_get_schedule_event_with_availability_inferred_team_id_underscore() -> None:
    """Test get_schedule_event with include_availability=True and team_id in event."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "team_id": "team-777",
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_get_schedule_event_with_availability_inferred_team_id_in_event_data_underscore() -> None:
    """Test get_schedule_event with include_availability=True and team_id in eventData."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "eventData": {"team_id": "team-666"},
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        _AVAILABILITY_URL,
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_get_schedule_event_with_availability_missing_team_id() -> None:
    """Test get_schedule_event raises GameSheetError if team_id cannot be determined."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "eventTitle": "Morning Practice",
            },
        },
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Team ID is required to fetch availability"):
        get_schedule_event(session, "occ-101", include_availability=True)


@responses.activate
def test_get_event_success() -> None:
    """Test get_event helper succeeds for 'event' type."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/evt-101",
        json={
            "data": {
                "id": "evt-101",
                "type": "event",
                "eventTitle": "Pizza Party",
            },
        },
        status=200,
    )
    session = _make_session()
    event = get_event(session, "evt-101")
    assert event.id == "evt-101"
    assert event.type == "event"


@responses.activate
def test_get_game_success() -> None:
    """Test get_game helper succeeds for 'game' type."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/gm-202",
        json={
            "data": {
                "id": "gm-202",
                "type": "game",
                "eventTitle": "Game 1",
            },
        },
        status=200,
    )
    session = _make_session()
    game = get_game(session, "gm-202")
    assert game.id == "gm-202"
    assert game.type == "game"


@responses.activate
def test_get_practice_success() -> None:
    """Test get_practice helper succeeds for 'practice' type."""
    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/pr-303",
        json={
            "data": {
                "id": "pr-303",
                "type": "practice",
                "eventTitle": "Practice 1",
            },
        },
        status=200,
    )
    session = _make_session()
    practice = get_practice(session, "pr-303")
    assert practice.id == "pr-303"
    assert practice.type == "practice"


@responses.activate
def test_get_schedule_game_availability_resolves_integer_game_id() -> None:
    """Test get_schedule_event resolves game ID from eventData.id for availability."""
    occurrence_id = "2a9ba235-2410-4fc8-8f7b-c0b00c33c3d4"
    game_numeric_id = 2959527
    team_uuid = "248d959c-279e-4492-805d-eb1a3e717323"

    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/{occurrence_id}",
        json={
            "data": {
                "id": occurrence_id,
                "type": "game",
                "eventTitle": "Hawks vs Eagles",
                "eventData": {
                    "id": game_numeric_id,
                    "homeTeamId": team_uuid,
                    "awayTeamId": "other-team-id",
                },
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"data": {"status": "ok", "attendees": [{"name": "Player 1"}]}},
        status=200,
    )
    session = _make_session()
    game = get_schedule_event(session, occurrence_id, include_availability=True)
    assert game.id == occurrence_id
    assert game.type == "game"
    assert game.availability == {"status": "ok", "attendees": [{"name": "Player 1"}]}


@responses.activate
def test_get_schedule_game_availability_with_game_id_and_away_team() -> None:
    """Test get_schedule_event resolves gameId and awayTeamId for availability."""
    occurrence_id = "2a9ba235-2410-4fc8-8f7b-c0b00c33c3d4"
    game_numeric_id = 2959527
    away_team_uuid = "away-team-uuid-123"

    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/{occurrence_id}",
        json={
            "data": {
                "id": occurrence_id,
                "type": "game",
                "gameId": game_numeric_id,
                "eventTitle": "Hawks vs Eagles",
                "eventData": {
                    "awayTeamId": away_team_uuid,
                },
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={away_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    game = get_schedule_event(session, occurrence_id, include_availability=True)
    assert game.availability == {"attendees": []}


@responses.activate
def test_get_schedule_game_availability_with_event_data_game_id_and_home_team_underscore() -> None:
    """Test get_schedule_event resolves eventData.game_id and home_team_id."""
    occurrence_id = "2a9ba235-2410-4fc8-8f7b-c0b00c33c3d4"
    game_numeric_id = 2959527
    home_team_uuid = "home-team-uuid-456"

    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/{occurrence_id}",
        json={
            "data": {
                "id": occurrence_id,
                "type": "game",
                "eventTitle": "Hawks vs Eagles",
                "eventData": {
                    "game_id": game_numeric_id,
                    "home_team_id": home_team_uuid,
                },
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={home_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    game = get_schedule_event(session, occurrence_id, include_availability=True)
    assert game.availability == {"attendees": []}


@responses.activate
def test_get_schedule_game_availability_with_event_data_away_team_underscore() -> None:
    """Test get_schedule_event resolves away_team_id when home team is not present."""
    occurrence_id = "2a9ba235-2410-4fc8-8f7b-c0b00c33c3d4"
    game_numeric_id = 2959527
    away_team_uuid = "away-team-uuid-789"

    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/{occurrence_id}",
        json={
            "data": {
                "id": occurrence_id,
                "type": "game",
                "eventTitle": "Hawks vs Eagles",
                "eventData": {
                    "eventId": game_numeric_id,
                    "away_team_id": away_team_uuid,
                },
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={away_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    game = get_schedule_event(session, occurrence_id, include_availability=True)
    assert game.availability == {"attendees": []}


@responses.activate
def test_get_schedule_event_availability_with_event_id_field() -> None:
    """Test get_schedule_event resolves eventId or event_id for non-game event types."""
    occurrence_id = "occ-999"
    event_custom_id = "custom-evt-uuid"
    team_uuid = "team-uuid-111"

    responses.add(
        responses.GET,
        f"{_OCCURRENCE_URL}/{occurrence_id}",
        json={
            "data": {
                "id": occurrence_id,
                "type": "event",
                "eventId": event_custom_id,
                "teamId": team_uuid,
                "eventTitle": "Banquet",
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={event_custom_id}&event_type=event",
        json={"attendees": []},
        status=200,
    )
    session = _make_session()
    event = get_schedule_event(session, occurrence_id, include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_fetch_scheduled_game_raw_success() -> None:
    """Test fetch_scheduled_game_raw returns raw response dict."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/2959626",
        json={"success": True, "data": {"game_number": "RR-145", "season_id": 15300}},
        status=200,
    )
    session = _make_session()
    result = fetch_scheduled_game_raw(session, 2959626)
    assert result["success"] is True
    assert result["data"]["game_number"] == "RR-145"


@responses.activate
def test_fetch_scheduled_game_raw_unauthorized() -> None:
    """Test fetch_scheduled_game_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/2959626",
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_scheduled_game_raw(session, 2959626)


@responses.activate
def test_fetch_scheduled_game_raw_http_error() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError on HTTP >= 400."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/999999",
        body="Not Found",
        status=404,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="GET /api/schedule-game/999999 returned HTTP 404"):
        fetch_scheduled_game_raw(session, 999999)


@responses.activate
def test_fetch_scheduled_game_raw_invalid_json() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError on JSON decode failure."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/2959626",
        body="not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse schedule game JSON response"):
        fetch_scheduled_game_raw(session, 2959626)


@responses.activate
def test_fetch_scheduled_game_raw_non_dict() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError if response is not a dict."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/2959626",
        json=["item1"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(
        GameSheetError,
        match="Unexpected response format from schedule game API",
    ):
        fetch_scheduled_game_raw(session, 2959626)


@responses.activate
def test_get_schedule_event_with_numeric_string_game_id() -> None:
    """Test get_schedule_event dispatches numeric string ID to schedule-game."""
    game_id = "2959626"
    team_uuid = "248d959c-279e-4492-805d-eb1a3e717323"
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/{game_id}",
        json={
            "success": True,
            "data": {
                "date_time": "2027-02-28T08:15",
                "end_time": "2027-02-28T09:35",
                "game_number": "RR-145",
                "game_type": "regular_season",
                "location": "Polar Ice Wake Forest",
                "home_prototeam_id": team_uuid,
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={game_id}&event_type=game",
        json={"data": [{"player_id": 1, "first_name": "JOHN"}]},
        status=200,
    )
    session = _make_session()
    game = get_schedule_event(session, game_id, include_availability=True)
    assert game.id == 2959626
    assert game.type == "game"
    assert game.eventDate == "2027-02-28"
    assert game.eventTime == "08:15"
    assert game.eventLocation == "Polar Ice Wake Forest"
    assert game.eventTitle == "RR-145"
    assert game.availability == [{"player_id": 1, "first_name": "JOHN"}]


@responses.activate
def test_get_schedule_event_game_malformed_response() -> None:
    """Test get_schedule_event raises GameSheetError if game data is not a dict."""
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/2959626",
        json={"data": "invalid-non-dict"},
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Malformed response: expected dict data for game"):
        get_schedule_event(session, 2959626, event_type="game")


@responses.activate
def test_get_game_with_integer_id() -> None:
    """Test get_game helper fetches game details via schedule-game."""
    game_id = 2959626
    responses.add(
        responses.GET,
        f"{_SCHEDULE_GAME_URL}/{game_id}",
        json={
            "success": True,
            "data": {
                "id": game_id,
                "game_number": "RR-145",
                "date_time": "2027-02-28",
            },
        },
        status=200,
    )
    session = _make_session()
    game = get_game(session, game_id)
    assert game.id == 2959626
    assert game.type == "game"
    assert game.eventDate == "2027-02-28"
    assert game.eventTitle == "RR-145"


def test_get_calendar_subscription_default_timestamp() -> None:
    """Test get_calendar_subscription with default timestamp."""
    team_id = "248d959c-279e-4492-805d-eb1a3e717323"
    sub = get_calendar_subscription(team_id)
    assert isinstance(sub, CalendarSubscription)
    expected_apple_prefix = (
        f"webcal://api.teams.gamesheet.app/api/public/calendar/teams/{team_id}/calendar.ics#v"
    )
    assert sub.appleCalendar.startswith(expected_apple_prefix)
    expected_google_prefix = (
        "https://calendar.google.com/calendar/r?cid="
        "webcal%3A%2F%2Fapi.teams.gamesheet.app%2Fapi%2Fpublic%2Fcalendar%2Fteams%2F"
    )
    assert sub.googleCalendar.startswith(expected_google_prefix)
    assert sub.calendarUrl == sub.appleCalendar


def test_get_calendar_subscription_explicit_timestamp() -> None:
    """Test get_calendar_subscription with explicit timestamp."""
    team_id = "test-team-uuid"
    timestamp_hours = 496427
    sub = get_calendar_subscription(team_id, timestamp_hours=timestamp_hours)
    expected_feed = (
        f"webcal://api.teams.gamesheet.app/api/public/calendar/teams/{team_id}/"
        f"calendar.ics#v{timestamp_hours}"
    )
    expected_google = (
        f"https://calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fapi.teams.gamesheet.app%2Fapi%2Fpublic%2F"
        f"calendar%2Fteams%2F{team_id}%2Fcalendar.ics%23v{timestamp_hours}"
    )
    assert sub.appleCalendar == expected_feed
    assert sub.googleCalendar == expected_google
    assert sub.calendarUrl == expected_feed
    dump = sub.model_dump(mode="json")
    assert dump["appleCalendar"] == expected_feed
    assert dump["googleCalendar"] == expected_google
    assert dump["calendarUrl"] == expected_feed


def test_calendar_event_created_model() -> None:
    """Test CalendarEventCreated model instantiation."""
    model = CalendarEventCreated(
        id="a1e62678-4d11-4968-bc95-ad2c047b6727",
        team_id=525015,
        prototeam_id="18d94244-2c6b-48ed-aa05-af47819e1825",
        title="Non-repeating Event Title",
        type="event",
        notes="Notes here",
        location_name="Polar Ice",
        location_address="123 Main St",
        location_surface="Rink 1",
        timezone_name="America/New_York",
        all_day=False,
        rrule="DTSTART=20260821T133000;FREQ=DAILY;COUNT=1",
        start_time="13:30:00",
        end_time="14:30:00",
        created_by_user_id=10417,
        created_at="2026-08-19T12:30:20Z",
        updated_at="2026-08-19T12:30:20Z",
        deleted_at=None,
    )
    assert model.id == "a1e62678-4d11-4968-bc95-ad2c047b6727"
    assert model.team_id == 525015
    assert model.prototeam_id == "18d94244-2c6b-48ed-aa05-af47819e1825"
    assert model.title == "Non-repeating Event Title"
    assert model.type == "event"
    assert model.notes == "Notes here"
    assert model.location_name == "Polar Ice"
    assert model.location_address == "123 Main St"
    assert model.location_surface == "Rink 1"
    assert model.timezone_name == "America/New_York"
    assert model.all_day is False
    assert model.rrule == "DTSTART=20260821T133000;FREQ=DAILY;COUNT=1"
    assert model.start_time == "13:30:00"
    assert model.end_time == "14:30:00"
    assert model.created_by_user_id == 10417
    assert model.created_at == "2026-08-19T12:30:20Z"
    assert model.updated_at == "2026-08-19T12:30:20Z"
    assert model.deleted_at is None


def test_created_game_result_model() -> None:
    """Test CreatedGameResult model instantiation."""
    res = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        date_time="2026-08-20T12:00",
        end_time="13:15",
        game_type="regular_season",
        location="Polar Ice",
        team_id=525015,
        opposing_team_id=523675,
        season_id=15020,
        association_id=38,
        league_id=1148580,
        division_id=81419,
        home_flag=True,
    )
    assert res.success is True
    assert res.game_number == "TEST-123"
    assert res.team_id == 525015
    assert res.home_flag is True


def test_validate_game_type_valid() -> None:
    """Test validate_game_type with valid game types."""
    for gt in ["regular_season", "playoff", "exhibition", "tournament"]:
        validate_game_type(gt)


def test_validate_game_type_invalid() -> None:
    """Test validate_game_type with invalid game type raises GameSheetError."""
    with pytest.raises(GameSheetError, match="Invalid game type 'invalid_type'"):
        validate_game_type("invalid_type")


def test_build_rrule() -> None:
    """Test build_rrule helper function with various parameters."""
    assert build_rrule(None) is None
    assert build_rrule("") is None
    assert build_rrule("FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH") == "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH"

    # Daily
    assert build_rrule("daily") == "FREQ=DAILY;INTERVAL=1"
    assert build_rrule("DAILY", interval=3) == "FREQ=DAILY;INTERVAL=3"

    # Weekly
    assert build_rrule("weekly") == "FREQ=WEEKLY;INTERVAL=1"
    assert build_rrule("weekly", interval=2, by_day="TU,TH") == "FREQ=WEEKLY;INTERVAL=2;BYDAY=TU,TH"
    assert build_rrule("weekly", by_day=["tuesday", "thursday"]) == "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH"
    assert build_rrule("weekly", by_day="mon, wed, fri") == "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR"
    assert build_rrule("weekly", by_day=", ") == "FREQ=WEEKLY;INTERVAL=1"
    assert build_rrule("weekly", by_day=["", " "]) == "FREQ=WEEKLY;INTERVAL=1"

    # Monthly
    assert build_rrule("monthly") == "FREQ=MONTHLY;INTERVAL=1"
    assert build_rrule("monthly", interval=2) == "FREQ=MONTHLY;INTERVAL=2"

    # Invalid frequency
    with pytest.raises(GameSheetError, match="Invalid repeat frequency 'yearly'"):
        build_rrule("yearly")


@responses.activate
def test_create_calendar_event_raw_success() -> None:
    """Test create_calendar_event_raw HTTP success."""
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={"success": True, "data": {"id": "evt-new-1", "title": "Test Event"}},
        status=200,
    )
    session = _make_session()
    result = create_calendar_event_raw(session, {"title": "Test Event"})
    assert result["success"] is True
    assert result["data"]["id"] == "evt-new-1"


@responses.activate
def test_create_calendar_event_raw_unauthorized() -> None:
    """Test create_calendar_event_raw returns 401 raises AuthenticationError."""
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={"error": "unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid refresh token"},
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_error() -> None:
    """Test create_calendar_event_raw returns 400 raises GameSheetError."""
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        body="Validation failed",
        status=400,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="POST /api/calendar/events returned HTTP 400"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_invalid_json() -> None:
    """Test create_calendar_event_raw invalid JSON response raises GameSheetError."""
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        body="Not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse calendar event creation JSON response"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_non_dict() -> None:
    """Test create_calendar_event_raw non-dict response raises GameSheetError."""
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json=["item1"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format from calendar event creation API"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_event_non_repeating() -> None:
    """Test create_event for non-repeating event."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={
            "success": True,
            "data": {
                "id": "a1e62678-4d11-4968-bc95-ad2c047b6727",
                "team_id": 525015,
                "prototeam_id": team_id,
                "title": "Non-repeating Event Title",
                "type": "event",
                "notes": "Non repeating event notes.",
                "location_name": "Polar Ice Wake Forest",
                "timezone_name": "America/New_York",
                "all_day": False,
                "start_time": "13:30:00",
                "end_time": "14:30:00",
            },
        },
        status=200,
    )
    session = _make_session()
    evt = create_event(
        session,
        team_id,
        "Non-repeating Event Title",
        "2026-08-21T13:30",
        "14:30",
        location="Polar Ice Wake Forest",
        notes="Non repeating event notes.",
        timezone="America/New_York",
    )
    assert isinstance(evt, CalendarEventCreated)
    assert evt.id == "a1e62678-4d11-4968-bc95-ad2c047b6727"
    assert evt.title == "Non-repeating Event Title"
    assert evt.type == "event"
    assert evt.notes == "Non repeating event notes."


@responses.activate
def test_create_event_repeating_weekly() -> None:
    """Test create_event for weekly repeating event with rrule and repeat_until."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={
            "success": True,
            "data": {
                "id": "b8ca65a0-9626-4673-a46b-b9f3f831151a",
                "team_id": 525015,
                "prototeam_id": team_id,
                "title": "Weekly Event",
                "type": "event",
                "notes": "Weekly Event Notes",
                "location_name": "Extreme Ice Center",
                "timezone_name": "America/New_York",
                "all_day": False,
                "rrule": "DTSTART=20260825T113000;FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH;UNTIL=20270322T235959Z",
                "start_time": "11:30:00",
                "end_time": "12:30:00",
            },
        },
        status=200,
    )
    session = _make_session()
    evt = create_event(
        session,
        team_id,
        "Weekly Event",
        "2026-08-22T11:30",
        "12:30",
        location="Extreme Ice Center",
        notes="Weekly Event Notes",
        timezone="America/New_York",
        rrule="FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH",
        repeat_until="2027-03-22",
    )
    assert evt.id == "b8ca65a0-9626-4673-a46b-b9f3f831151a"
    assert evt.type == "event"
    assert "FREQ=WEEKLY" in (evt.rrule or "")


@responses.activate
def test_create_event_malformed_response() -> None:
    """Test create_event with malformed response raises GameSheetError."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={"data": "not a dict"},
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="expected dict data for created calendar event"):
        create_event(session, team_id, "Title", "2026-08-21T13:30", "14:30")


@responses.activate
def test_create_practice_non_repeating() -> None:
    """Test create_practice for non-repeating practice."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={
            "success": True,
            "data": {
                "id": "d257e1ae-89cc-477f-b9db-79a02292ab4c",
                "team_id": 525015,
                "prototeam_id": team_id,
                "title": "Practice",
                "type": "practice",
                "notes": "Non-repeating practice",
                "location_name": "Polar Ice Wake Forest",
                "timezone_name": "America/New_York",
                "all_day": False,
                "start_time": "13:30:00",
                "end_time": "14:30:00",
            },
        },
        status=200,
    )
    session = _make_session()
    prac = create_practice(
        session,
        team_id,
        "2026-08-30T13:30",
        "14:30",
        notes="Non-repeating practice",
        location="Polar Ice Wake Forest",
        timezone="America/New_York",
    )
    assert prac.id == "d257e1ae-89cc-477f-b9db-79a02292ab4c"
    assert prac.type == "practice"
    assert prac.title == "Practice"


@responses.activate
def test_create_practice_repeating_monthly() -> None:
    """Test create_practice for repeating monthly practice."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        _CALENDAR_EVENTS_URL,
        json={
            "success": True,
            "data": {
                "id": "561efea6-f016-4a63-8b93-60729c957d11",
                "team_id": 525015,
                "prototeam_id": team_id,
                "title": "Monthly Practice",
                "type": "practice",
                "notes": "Repeating practice",
                "location_name": "Polar Ice Wake Forest",
                "timezone_name": "America/New_York",
                "all_day": False,
                "rrule": "DTSTART=20260831T153000;FREQ=MONTHLY;INTERVAL=1;UNTIL=20270319T235959Z",
                "start_time": "15:30:00",
                "end_time": "16:30:00",
            },
        },
        status=200,
    )
    session = _make_session()
    prac = create_practice(
        session,
        team_id,
        "2026-08-31T15:30",
        "16:30",
        title="Monthly Practice",
        rrule="FREQ=MONTHLY;INTERVAL=1",
        repeat_until="2027-03-19",
    )
    assert prac.id == "561efea6-f016-4a63-8b93-60729c957d11"
    assert prac.type == "practice"


@responses.activate
def test_create_schedule_game_raw_success() -> None:
    """Test create_schedule_game_raw HTTP success."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = _make_session()
    res = create_schedule_game_raw(session, {"game_number": "123"})
    assert res == {"success": True}


@responses.activate
def test_create_schedule_game_raw_unauthorized() -> None:
    """Test create_schedule_game_raw returns 401 raises AuthenticationError."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        json={"error": "unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid refresh token"},
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_error() -> None:
    """Test create_schedule_game_raw returns 400 raises GameSheetError."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        body="Bad Request",
        status=400,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="POST /api/schedule-game returned HTTP 400"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_invalid_json() -> None:
    """Test create_schedule_game_raw invalid JSON response raises GameSheetError."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        body="Not json",
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Failed to parse schedule-game creation JSON response"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_non_dict() -> None:
    """Test create_schedule_game_raw non-dict response raises GameSheetError."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        json=["unexpected"],
        status=200,
    )
    session = _make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format from schedule-game API"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_game_success_home() -> None:
    """Test create_game as home team with full payload."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = _make_session()
    game = create_game(
        session,
        team_id=525015,
        season_id=15020,
        division_id=81419,
        opposing_team_id=523675,
        date_time="2026-08-20T12:00",
        end_time="13:15",
        home_flag=True,
        opposing_division=81419,
        association_id=38,
        league_id=1148580,
        game_number="TEST-123",
        game_type="regular_season",
        location="Polar Ice Wake Forest Forest",
        scorekeeper_name="Scorekeeper Name",
        scorekeeper_phone="Scorekeeper Phone",
        broadcast_provider="LIVEBARN",
        time_zone_name="America/New_York",
        time_zone_offset=-240,
    )
    assert isinstance(game, CreatedGameResult)
    assert game.success is True
    assert game.game_number == "TEST-123"
    assert game.team_id == 525015
    assert game.opposing_team_id == 523675
    assert game.home_flag is True
    assert game.location == "Polar Ice Wake Forest Forest"


@responses.activate
def test_create_game_visitor_defaults() -> None:
    """Test create_game as visitor with defaults for optional values."""
    responses.add(
        responses.POST,
        _SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = _make_session()
    game = create_game(
        session,
        team_id="525015",
        season_id="15020",
        division_id="81419",
        opposing_team_id="523675",
        date_time="2026-08-20T12:00",
        end_time="13:15",
        home_flag=False,
    )
    assert game.success is True
    assert game.home_flag is False
    assert game.opposing_division == 81419  # Defaults to division_id
    assert game.game_type == "regular_season"


def test_create_game_invalid_type() -> None:
    """Test create_game with invalid game_type raises GameSheetError."""
    session = _make_session()
    with pytest.raises(GameSheetError, match="Invalid game type 'invalid_game_type'"):
        create_game(
            session,
            team_id=525015,
            season_id=15020,
            division_id=81419,
            opposing_team_id=523675,
            date_time="2026-08-20T12:00",
            end_time="13:15",
            game_type="invalid_game_type",
        )
