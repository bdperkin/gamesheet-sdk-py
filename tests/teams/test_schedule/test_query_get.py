# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for retrieving schedule events."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule import (
    CalendarSubscription,
    fetch_availability_raw,
    fetch_event_occurrence_raw,
    fetch_scheduled_game_raw,
    get_calendar_subscription,
    get_event,
    get_game,
    get_practice,
    get_schedule_event,
)
from tests.teams.test_schedule.conftest import (
    AVAILABILITY_URL,
    OCCURRENCE_URL,
    REFRESH_URL,
    SCHEDULE_GAME_URL,
    make_session,
)


@responses.activate
def test_fetch_event_occurrence_raw_success() -> None:
    """Test fetch_event_occurrence_raw successfully retrieves event data."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        json={"success": True, "data": {"id": "occ-101", "type": "event"}},
        status=200,
    )
    session = make_session()
    result = fetch_event_occurrence_raw(session, "occ-101")
    assert result["success"] is True
    assert result["data"]["id"] == "occ-101"


@responses.activate
def test_fetch_event_occurrence_raw_unauthorized() -> None:
    """Test fetch_event_occurrence_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
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
        f"{OCCURRENCE_URL}/occ-101",
        body="Internal Server Error",
        status=500,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/calendar/occurrences/occ-101 returned HTTP 500"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_event_occurrence_raw_invalid_json() -> None:
    """Test fetch_event_occurrence_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        body="not json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse calendar occurrence JSON response"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_event_occurrence_raw_non_dict() -> None:
    """Test fetch_event_occurrence_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format"):
        fetch_event_occurrence_raw(session, "occ-101")


@responses.activate
def test_fetch_availability_raw_success() -> None:
    """Test fetch_availability_raw successfully retrieves availability data."""
    responses.add(
        responses.GET,
        AVAILABILITY_URL,
        json={"success": True, "data": {"attendees": []}},
        status=200,
    )
    session = make_session()
    result = fetch_availability_raw(session, "team-1", "evt-1", "practice")
    assert result["success"] is True
    assert result["data"]["attendees"] == []


@responses.activate
def test_fetch_availability_raw_unauthorized() -> None:
    """Test fetch_availability_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        AVAILABILITY_URL,
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
        AVAILABILITY_URL,
        body="Internal Server Error",
        status=500,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/availability/batch returned HTTP 500"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_fetch_availability_raw_invalid_json() -> None:
    """Test fetch_availability_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.GET,
        AVAILABILITY_URL,
        body="not json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse availability JSON response"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_fetch_availability_raw_non_dict() -> None:
    """Test fetch_availability_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.GET,
        AVAILABILITY_URL,
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Unexpected response format"):
        fetch_availability_raw(session, "team-1", "evt-1", "practice")


@responses.activate
def test_get_schedule_event_success_data_wrapped() -> None:
    """Test get_schedule_event with data wrapped dictionary."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
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
    session = make_session()
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
        f"{OCCURRENCE_URL}/occ-101",
        json={
            "id": "occ-101",
            "type": "game",
            "eventDate": "2026-08-22",
            "eventTitle": "Hawks vs Eagles",
        },
        status=200,
    )
    session = make_session()
    event = get_schedule_event(session, "occ-101")
    assert event.id == "occ-101"
    assert event.type == "game"


@responses.activate
def test_get_schedule_event_malformed_data() -> None:
    """Test get_schedule_event raises GameSheetError if data is not a dict."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        json={"data": "not a dict"},
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Malformed response: expected dict data"):
        get_schedule_event(session, "occ-101")


@responses.activate
def test_get_schedule_event_type_mismatch() -> None:
    """Test get_schedule_event raises GameSheetError if event_type does not match."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "game",
                "eventTitle": "Hawks vs Eagles",
            },
        },
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Event 'occ-101' is of type 'game', expected 'practice'\."):
        get_schedule_event(session, "occ-101", event_type="practice")


@responses.activate
def test_get_schedule_event_with_availability_explicit_team_id() -> None:
    """Test get_schedule_event with include_availability=True and explicit team_id."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
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
        AVAILABILITY_URL,
        json={"success": True, "data": [{"userId": "user-1", "status": "attending"}]},
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/occ-101",
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
        AVAILABILITY_URL,
        json={"data": [{"userId": "user-2", "status": "absent"}]},
        status=200,
    )
    session = make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == [{"userId": "user-2", "status": "absent"}]


@responses.activate
def test_get_schedule_event_with_availability_inferred_team_id_underscore() -> None:
    """Test get_schedule_event with include_availability=True and team_id in event."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
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
        AVAILABILITY_URL,
        json={"attendees": []},
        status=200,
    )
    session = make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_get_schedule_event_with_availability_inferred_team_id_in_event_data_underscore() -> None:
    """Test get_schedule_event with include_availability=True and team_id in eventData."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
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
        AVAILABILITY_URL,
        json={"attendees": []},
        status=200,
    )
    session = make_session()
    event = get_schedule_event(session, "occ-101", include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_get_schedule_event_with_availability_missing_team_id() -> None:
    """Test get_schedule_event raises GameSheetError if team_id cannot be determined."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/occ-101",
        json={
            "data": {
                "id": "occ-101",
                "type": "practice",
                "eventTitle": "Morning Practice",
            },
        },
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Team ID is required to fetch availability"):
        get_schedule_event(session, "occ-101", include_availability=True)


@responses.activate
def test_get_event_success() -> None:
    """Test get_event helper succeeds for 'event' type."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/evt-101",
        json={
            "data": {
                "id": "evt-101",
                "type": "event",
                "eventTitle": "Pizza Party",
            },
        },
        status=200,
    )
    session = make_session()
    event = get_event(session, "evt-101")
    assert event.id == "evt-101"
    assert event.type == "event"


@responses.activate
def test_get_game_success() -> None:
    """Test get_game helper succeeds for 'game' type."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/gm-202",
        json={
            "data": {
                "id": "gm-202",
                "type": "game",
                "eventTitle": "Game 1",
            },
        },
        status=200,
    )
    session = make_session()
    game = get_game(session, "gm-202")
    assert game.id == "gm-202"
    assert game.type == "game"


@responses.activate
def test_get_practice_success() -> None:
    """Test get_practice helper succeeds for 'practice' type."""
    responses.add(
        responses.GET,
        f"{OCCURRENCE_URL}/pr-303",
        json={
            "data": {
                "id": "pr-303",
                "type": "practice",
                "eventTitle": "Practice 1",
            },
        },
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/{occurrence_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"data": {"status": "ok", "attendees": [{"name": "Player 1"}]}},
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/{occurrence_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={away_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/{occurrence_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={home_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/{occurrence_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={away_team_uuid}&event_id={game_numeric_id}&event_type=game",
        json={"attendees": []},
        status=200,
    )
    session = make_session()
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
        f"{OCCURRENCE_URL}/{occurrence_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={event_custom_id}&event_type=event",
        json={"attendees": []},
        status=200,
    )
    session = make_session()
    event = get_schedule_event(session, occurrence_id, include_availability=True)
    assert event.availability == {"attendees": []}


@responses.activate
def test_fetch_scheduled_game_raw_success() -> None:
    """Test fetch_scheduled_game_raw returns raw response dict."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/2959626",
        json={"success": True, "data": {"game_number": "RR-145", "season_id": 15300}},
        status=200,
    )
    session = make_session()
    result = fetch_scheduled_game_raw(session, 2959626)
    assert result["success"] is True
    assert result["data"]["game_number"] == "RR-145"


@responses.activate
def test_fetch_scheduled_game_raw_unauthorized() -> None:
    """Test fetch_scheduled_game_raw raises AuthenticationError on 401."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/2959626",
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_scheduled_game_raw(session, 2959626)


@responses.activate
def test_fetch_scheduled_game_raw_http_error() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError on HTTP >= 400."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/999999",
        body="Not Found",
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="GET /api/schedule-game/999999 returned HTTP 404"):
        fetch_scheduled_game_raw(session, 999999)


@responses.activate
def test_fetch_scheduled_game_raw_invalid_json() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError on JSON decode failure."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/2959626",
        body="not json",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse schedule game JSON response"):
        fetch_scheduled_game_raw(session, 2959626)


@responses.activate
def test_fetch_scheduled_game_raw_non_dict() -> None:
    """Test fetch_scheduled_game_raw raises GameSheetError if response is not a dict."""
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/2959626",
        json=["item1"],
        status=200,
    )
    session = make_session()
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
        f"{SCHEDULE_GAME_URL}/{game_id}",
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
        f"{AVAILABILITY_URL}?prototeam_id={team_uuid}&event_id={game_id}&event_type=game",
        json={"data": [{"player_id": 1, "first_name": "JOHN"}]},
        status=200,
    )
    session = make_session()
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
        f"{SCHEDULE_GAME_URL}/2959626",
        json={"data": "invalid-non-dict"},
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Malformed response: expected dict data for game"):
        get_schedule_event(session, 2959626, event_type="game")


@responses.activate
def test_get_game_with_integer_id() -> None:
    """Test get_game helper fetches game details via schedule-game."""
    game_id = 2959626
    responses.add(
        responses.GET,
        f"{SCHEDULE_GAME_URL}/{game_id}",
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
    session = make_session()
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
