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
    ScheduleEvent,
    ScheduleEventDetail,
    fetch_availability_raw,
    fetch_calendar_raw,
    fetch_event_occurrence_raw,
    fetch_scheduled_game_raw,
    get_event,
    get_game,
    get_practice,
    get_schedule_event,
    list_events,
    list_games,
    list_practices,
    list_schedule,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_AVAILABILITY_BATCH_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_CALENDAR_PATH,
    TEAMS_REFRESH_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

_CALENDAR_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_PATH}"
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
