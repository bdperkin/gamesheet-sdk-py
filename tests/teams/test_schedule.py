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
    fetch_calendar_raw,
    list_events,
    list_games,
    list_practices,
    list_schedule,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_CALENDAR_PATH,
    TEAMS_REFRESH_PATH,
)

_CALENDAR_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_PATH}"
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
