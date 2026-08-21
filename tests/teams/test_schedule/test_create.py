# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for creating schedule events, games, and practices."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    CreatedGameResult,
    create_calendar_event_raw,
    create_event,
    create_game,
    create_practice,
    create_schedule_game_raw,
)
from tests.teams.test_schedule.conftest import (
    CALENDAR_EVENTS_URL,
    REFRESH_URL,
    SCHEDULE_GAME_URL,
    make_session,
)


@responses.activate
def test_create_calendar_event_raw_success() -> None:
    """Test create_calendar_event_raw HTTP success."""
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
        json={"success": True, "data": {"id": "evt-new-1", "title": "Test Event"}},
        status=200,
    )
    session = make_session()
    result = create_calendar_event_raw(session, {"title": "Test Event"})
    assert result["success"] is True
    assert result["data"]["id"] == "evt-new-1"


@responses.activate
def test_create_calendar_event_raw_unauthorized() -> None:
    """Test create_calendar_event_raw returns 401 raises AuthenticationError."""
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
        json={"error": "unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid refresh token"},
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_error() -> None:
    """Test create_calendar_event_raw returns 400 raises GameSheetError."""
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
        body="Validation failed",
        status=400,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="POST /api/calendar/events returned HTTP 400"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_invalid_json() -> None:
    """Test create_calendar_event_raw invalid JSON response raises GameSheetError."""
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
        body="Not json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse calendar event creation JSON response"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_calendar_event_raw_non_dict() -> None:
    """Test create_calendar_event_raw non-dict response raises GameSheetError."""
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
        json=["item1"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format from calendar event creation API"):
        create_calendar_event_raw(session, {"title": "Test"})


@responses.activate
def test_create_event_non_repeating() -> None:
    """Test create_event for non-repeating event."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
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
    session = make_session()
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
        CALENDAR_EVENTS_URL,
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
    session = make_session()
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
        CALENDAR_EVENTS_URL,
        json={"data": "not a dict"},
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="expected dict data for created calendar event"):
        create_event(session, team_id, "Title", "2026-08-21T13:30", "14:30")


@responses.activate
def test_create_practice_non_repeating() -> None:
    """Test create_practice for non-repeating practice."""
    team_id = "18d94244-2c6b-48ed-aa05-af47819e1825"
    responses.add(
        responses.POST,
        CALENDAR_EVENTS_URL,
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
    session = make_session()
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
        CALENDAR_EVENTS_URL,
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
    session = make_session()
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
        SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = make_session()
    res = create_schedule_game_raw(session, {"game_number": "123"})
    assert res == {"success": True}


@responses.activate
def test_create_schedule_game_raw_unauthorized() -> None:
    """Test create_schedule_game_raw returns 401 raises AuthenticationError."""
    responses.add(
        responses.POST,
        SCHEDULE_GAME_URL,
        json={"error": "unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid refresh token"},
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_error() -> None:
    """Test create_schedule_game_raw returns 400 raises GameSheetError."""
    responses.add(
        responses.POST,
        SCHEDULE_GAME_URL,
        body="Bad Request",
        status=400,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="POST /api/schedule-game returned HTTP 400"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_invalid_json() -> None:
    """Test create_schedule_game_raw invalid JSON response raises GameSheetError."""
    responses.add(
        responses.POST,
        SCHEDULE_GAME_URL,
        body="Not json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse schedule-game creation JSON response"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_schedule_game_raw_non_dict() -> None:
    """Test create_schedule_game_raw non-dict response raises GameSheetError."""
    responses.add(
        responses.POST,
        SCHEDULE_GAME_URL,
        json=["unexpected"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format from schedule-game API"):
        create_schedule_game_raw(session, {"game_number": "123"})


@responses.activate
def test_create_game_success_home() -> None:
    """Test create_game as home team with full payload."""
    responses.add(
        responses.POST,
        SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = make_session()
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
        SCHEDULE_GAME_URL,
        json={"success": True},
        status=200,
    )
    session = make_session()
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
    session = make_session()
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
