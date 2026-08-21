# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for updating schedule events, games, and practices."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule import (
    _fetch_and_verify_occurrence_dict,
    update_calendar_occurrence,
    update_calendar_occurrence_raw,
    update_event,
    update_game,
    update_practice,
    update_schedule_game_raw,
)
from tests.teams.test_schedule.conftest import (
    OCCURRENCE_URL,
    REFRESH_URL,
    SCHEDULE_GAME_URL,
    make_session,
)


@responses.activate
def test_update_schedule_game_raw_success() -> None:
    """Test update_schedule_game_raw with successful response."""
    game_id = 2962945
    payload = {"date_time": "2026-08-24T15:00", "end_time": "16:15"}
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        json={"success": True},
        status=200,
    )
    session = make_session()
    result = update_schedule_game_raw(session, game_id, payload)
    assert result == {"success": True}


@responses.activate
def test_update_schedule_game_raw_unauthorized() -> None:
    """Test update_schedule_game_raw raises AuthenticationError on 401."""
    game_id = 2962945
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        update_schedule_game_raw(session, game_id, {})


@responses.activate
def test_update_schedule_game_raw_error() -> None:
    """Test update_schedule_game_raw raises GameSheetError on HTTP error."""
    game_id = 2962945
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        json={"error": "Game not found"},
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="PUT /api/schedule-game/2962945 returned HTTP 404"):
        update_schedule_game_raw(session, game_id, {})


@responses.activate
def test_update_schedule_game_raw_invalid_json() -> None:
    """Test update_schedule_game_raw raises GameSheetError on non-JSON response."""
    game_id = 2962945
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        body="invalid json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse schedule game update JSON response"):
        update_schedule_game_raw(session, game_id, {})


@responses.activate
def test_update_schedule_game_raw_non_dict_json() -> None:
    """Test update_schedule_game_raw raises GameSheetError on non-dict JSON."""
    game_id = 2962945
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format from schedule game API"):
        update_schedule_game_raw(session, game_id, {})


@responses.activate
def test_update_game_success() -> None:
    """Test update_game helper builds payload and returns UpdatedGameResult."""
    game_id = 2962945
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/{game_id}",
        json={"success": True, "message": "Updated"},
        status=200,
    )
    session = make_session()
    res = update_game(
        session,
        game_id,
        team_id=525015,
        season_id=15020,
        division_id=81419,
        opposing_team_id=523675,
        opposing_division=81419,
        association_id=38,
        league_id=1148580,
        home_flag=True,
        date_time="2026-08-24T15:00",
        end_time="16:15",
        game_number="TEST-432",
        game_type="regular_season",
        location="Polar Ice Wake Forest",
        scorekeeper_name="Jane Doe",
        scorekeeper_phone="555-5678",
        broadcast_provider="LIVEBARN",
        time_zone_name="America/New_York",
        time_zone_offset=-240,
    )
    assert res.success is True
    assert res.id == 2962945
    assert res.message == "Updated"
    assert res.team_id == 525015
    assert res.game_number == "TEST-432"
    assert res.game_type == "regular_season"


def test_update_game_invalid_type() -> None:
    """Test update_game raises GameSheetError for invalid game type."""
    session = make_session()
    with pytest.raises(GameSheetError, match="Invalid game type 'unknown_type'"):
        update_game(session, 12345, game_type="unknown_type")


@responses.activate
def test_update_calendar_occurrence_raw_success() -> None:
    """Test update_calendar_occurrence_raw with success."""
    occ_id = "f51217ec-4cd0-4d82-a03c-fdbd65110858"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "event_id": "a1e62678-4d11-4968-bc95-ad2c047b6727",
                "title": "Updated Event",
                "type": "event",
                "start_date": "2026-08-21T14:30:00Z",
                "end_date": "2026-08-21T15:30:00Z",
            },
        },
        status=200,
    )
    session = make_session()
    result = update_calendar_occurrence_raw(session, occ_id, {"title": "Updated Event"})
    assert result["success"] is True
    assert result["data"]["title"] == "Updated Event"


@responses.activate
def test_update_calendar_occurrence_raw_with_future() -> None:
    """Test update_calendar_occurrence_raw appends updateFuture query param."""
    occ_id = "ddf68b33-6fd6-482b-997b-1997b27cf42d"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}?updateFuture=true",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "title": "Updated Practice",
                "type": "practice",
            },
        },
        status=200,
    )
    session = make_session()
    result = update_calendar_occurrence_raw(
        session,
        occ_id,
        {"title": "Updated Practice"},
        update_future=True,
    )
    assert result["success"] is True


@responses.activate
def test_update_calendar_occurrence_raw_unauthorized() -> None:
    """Test update_calendar_occurrence_raw raises AuthenticationError on 401."""
    occ_id = "occ-401"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        update_calendar_occurrence_raw(session, occ_id, {})


@responses.activate
def test_update_calendar_occurrence_raw_error() -> None:
    """Test update_calendar_occurrence_raw raises GameSheetError on error response."""
    occ_id = "occ-404"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={"error": "Occurrence not found"},
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="PUT /api/calendar/occurrences/occ-404 returned HTTP 404"):
        update_calendar_occurrence_raw(session, occ_id, {})


@responses.activate
def test_update_calendar_occurrence_raw_invalid_json() -> None:
    """Test update_calendar_occurrence_raw raises GameSheetError on non-JSON response."""
    occ_id = "occ-inv-json"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        body="invalid json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse update calendar occurrence JSON response"):
        update_calendar_occurrence_raw(session, occ_id, {})


@responses.activate
def test_update_calendar_occurrence_raw_non_dict() -> None:
    """Test update_calendar_occurrence_raw raises GameSheetError on non-dict JSON."""
    occ_id = "occ-non-dict"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(
        GameSheetError,
        match="Unexpected response format from calendar occurrence update API",
    ):
        update_calendar_occurrence_raw(session, occ_id, {})


@responses.activate
def test_update_calendar_occurrence_malformed_data() -> None:
    """Test update_calendar_occurrence raises GameSheetError when data is not a dict."""
    occ_id = "occ-bad-data"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={"success": True, "data": "not a dict"},
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Malformed response: expected dict data"):
        update_calendar_occurrence(session, occ_id, {})


@responses.activate
def test_update_event_helper() -> None:
    """Test update_event helper sends payload and returns CalendarEventCreated."""
    occ_id = "f51217ec-4cd0-4d82-a03c-fdbd65110858"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "event_id": "a1e62678-4d11-4968-bc95-ad2c047b6727",
                "team_id": 525015,
                "title": "Non-repeating Event Title 2",
                "type": "event",
                "notes": "Modified notes",
                "location_name": "Polar Ice Garner",
                "start_date": "2026-08-21T14:30:00Z",
                "end_date": "2026-08-21T15:30:00Z",
                "is_override": True,
            },
        },
        status=200,
    )
    session = make_session()
    res = update_event(
        session,
        occ_id,
        title="Non-repeating Event Title 2",
        notes="Modified notes",
        location_name="Polar Ice Garner",
        start_date="2026-08-21T14:30:00+00:00",
        end_date="2026-08-21T15:30:00+00:00",
    )
    assert res.id == occ_id
    assert res.event_id == "a1e62678-4d11-4968-bc95-ad2c047b6727"
    assert res.title == "Non-repeating Event Title 2"
    assert res.is_override is True


@responses.activate
def test_update_practice_helper() -> None:
    """Test update_practice helper sends payload with rrule and update_future."""
    occ_id = "ddf68b33-6fd6-482b-997b-1997b27cf42d"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}?updateFuture=true",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "event_id": "b0b929e3-b2a9-4297-941e-c7916aa12619",
                "team_id": 525015,
                "title": "Updated Practice",
                "type": "practice",
                "notes": "Practice Notes",
                "location_name": "Polar Ice Wake Forest",
                "start_date": "2026-08-31T14:00:00Z",
                "end_date": "2026-08-31T15:00:00Z",
                "rrule": "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z",
            },
        },
        status=200,
    )
    session = make_session()
    res = update_practice(
        session,
        occ_id,
        title="Updated Practice",
        notes="Practice Notes",
        location_name="Polar Ice Wake Forest",
        start_date="2026-08-31T14:00:00+00:00",
        end_date="2026-08-31T15:00:00+00:00",
        rrule="FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z",
        update_future=True,
    )
    assert res.id == occ_id
    assert res.title == "Updated Practice"
    assert res.type == "practice"
    assert res.rrule == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"


@responses.activate
def test_update_game_all_defaults() -> None:
    """Test update_game with string digit ID and no optional fields."""
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/2962945",
        json={"success": True},
        status=200,
    )
    session = make_session()
    res = update_game(session, "2962945", season_id="custom-str-season")
    assert res.success is True
    assert res.id == 2962945


@responses.activate
def test_update_calendar_occurrence_all_defaults() -> None:
    """Test update_calendar_occurrence with empty payload."""


@responses.activate
def test_update_game_partial_fields() -> None:
    """Test update_game with partial fields (season_id None)."""
    responses.add(
        responses.PUT,
        f"{SCHEDULE_GAME_URL}/2962945",
        json={"success": True},
        status=200,
    )
    session = make_session()
    res = update_game(session, 2962945, team_id=525015)
    assert res.success is True
    assert res.team_id == 525015


@responses.activate
def test_update_event_partial_fields() -> None:
    """Test update_event with only title provided."""
    occ_id = "occ-part-1"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {"id": occ_id, "title": "New Title"},
        },
        status=200,
    )
    session = make_session()
    res = update_event(session, occ_id, title="New Title")
    assert res.id == occ_id
    assert res.title == "New Title"


@responses.activate
def test_update_practice_partial_fields() -> None:
    """Test update_practice with only start_date provided."""
    occ_id = "occ-part-2"
    responses.add(
        responses.PUT,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {"id": occ_id, "start_date": "2026-08-21T14:30:00Z"},
        },
        status=200,
    )
    session = make_session()
    res = update_practice(session, occ_id, start_date="2026-08-21T14:30:00Z")
    assert res.id == occ_id


@responses.activate
def test_fetch_and_verify_occurrence_dict_camel_case() -> None:
    """Test _fetch_and_verify_occurrence_dict normalizes camelCase fields."""
    occ_id = "occ-camel"
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "type": "practice",
                "startDate": "2026-08-23T13:30:00+00:00",
                "endDate": "2026-08-23T14:30:00+00:00",
                "locationName": "Polar Ice",
                "locationAddress": "123 Main St",
                "locationSurface": "Rink 1",
                "timezoneName": "America/New_York",
                "teamId": 525015,
                "eventId": "evt-555",
            },
        },
        status=200,
    )
    session = make_session()
    d = _fetch_and_verify_occurrence_dict(session, occ_id, event_type="practice", timeout=10.0)
    assert d["start_date"] == "2026-08-23T13:30:00+00:00"
    assert d["end_date"] == "2026-08-23T14:30:00+00:00"
    assert d["location_name"] == "Polar Ice"
    assert d["location_address"] == "123 Main St"
    assert d["location_surface"] == "Rink 1"
    assert d["timezone_name"] == "America/New_York"
    assert d["team_id"] == 525015
    assert d["event_id"] == "evt-555"


@responses.activate
def test_fetch_and_verify_occurrence_dict_mismatched_type() -> None:
    """Test _fetch_and_verify_occurrence_dict raises GameSheetError on type mismatch."""
    occ_id = "occ-mismatch"
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": {
                "id": occ_id,
                "type": "event",
            },
        },
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="is of type 'event', expected 'practice'"):
        _fetch_and_verify_occurrence_dict(session, occ_id, event_type="practice", timeout=10.0)


@responses.activate
def test_fetch_and_verify_occurrence_dict_malformed() -> None:
    """Test _fetch_and_verify_occurrence_dict raises GameSheetError on non-dict data."""
    occ_id = "occ-malformed"
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/{occ_id}",
        json={
            "success": True,
            "data": "not a dict",
        },
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="expected dict data"):
        _fetch_and_verify_occurrence_dict(session, occ_id, event_type=None, timeout=10.0)
