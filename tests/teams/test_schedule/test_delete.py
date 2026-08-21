# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for deleting schedule events, games, and practices."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule import (
    ScheduleDeleteResult,
    delete_calendar_event,
    delete_calendar_event_raw,
    delete_calendar_occurrence,
    delete_calendar_occurrence_raw,
    delete_event,
    delete_game,
    delete_practice,
    delete_schedule_game_raw,
)
from tests.teams.test_schedule.conftest import (
    CALENDAR_EVENTS_URL,
    OCCURRENCE_URL,
    REFRESH_URL,
    SCHEDULE_GAME_URL,
    make_session,
)


@responses.activate
def test_delete_schedule_game_raw_success() -> None:
    """Test delete_schedule_game_raw HTTP success."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
        json={"success": True, "message": "Game deleted successfully"},
        status=200,
    )
    session = make_session()
    result = delete_schedule_game_raw(session, "2962920")
    assert result["success"] is True
    assert result["message"] == "Game deleted successfully"


@responses.activate
def test_delete_schedule_game_raw_unauthorized() -> None:
    """Test delete_schedule_game_raw raises AuthenticationError on 401."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
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
        delete_schedule_game_raw(session, "2962920")


@responses.activate
def test_delete_schedule_game_raw_bad_request() -> None:
    """Test delete_schedule_game_raw raises GameSheetError on HTTP error."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
        json={"success": False, "error": "Game not found"},
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="returned HTTP 404"):
        delete_schedule_game_raw(session, "2962920")


@responses.activate
def test_delete_schedule_game_raw_invalid_json() -> None:
    """Test delete_schedule_game_raw raises GameSheetError on non-JSON response."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
        body="Internal Server Error",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse delete game JSON response"):
        delete_schedule_game_raw(session, "2962920")


@responses.activate
def test_delete_schedule_game_raw_non_dict() -> None:
    """Test delete_schedule_game_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="expected a JSON object"):
        delete_schedule_game_raw(session, "2962920")


@responses.activate
def test_delete_game_success() -> None:
    """Test delete_game high-level function."""
    responses.add(
        responses.DELETE,
        f"{SCHEDULE_GAME_URL}/2962920",
        json={"success": True, "message": "Game deleted successfully"},
        status=200,
    )
    session = make_session()
    res = delete_game(session, 2962920)
    assert isinstance(res, ScheduleDeleteResult)
    assert res.success is True
    assert res.message == "Game deleted successfully"
    assert res.id == 2962920


@responses.activate
def test_delete_calendar_event_raw_success() -> None:
    """Test delete_calendar_event_raw HTTP success."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/a1e62678-4d11-4968-bc95-ad2c047b6727",
        json={
            "success": True,
            "data": {"message": "Calendar event and all occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    result = delete_calendar_event_raw(session, "a1e62678-4d11-4968-bc95-ad2c047b6727")
    assert result["success"] is True
    assert result["data"]["message"] == "Calendar event and all occurrences deleted successfully"


@responses.activate
def test_delete_calendar_event_raw_unauthorized() -> None:
    """Test delete_calendar_event_raw raises AuthenticationError on 401."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-123",
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
        delete_calendar_event_raw(session, "evt-123")


@responses.activate
def test_delete_calendar_event_raw_bad_request() -> None:
    """Test delete_calendar_event_raw raises GameSheetError on HTTP error."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-123",
        json={"success": False, "error": "Event not found"},
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="returned HTTP 404"):
        delete_calendar_event_raw(session, "evt-123")


@responses.activate
def test_delete_calendar_event_raw_invalid_json() -> None:
    """Test delete_calendar_event_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-123",
        body="Invalid JSON",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse delete calendar event JSON response"):
        delete_calendar_event_raw(session, "evt-123")


@responses.activate
def test_delete_calendar_event_raw_non_dict() -> None:
    """Test delete_calendar_event_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-123",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="expected a JSON object"):
        delete_calendar_event_raw(session, "evt-123")


@responses.activate
def test_delete_calendar_event_success() -> None:
    """Test delete_calendar_event high-level function."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-123",
        json={
            "success": True,
            "data": {"message": "Calendar event and all occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    res = delete_calendar_event(session, "evt-123")
    assert isinstance(res, ScheduleDeleteResult)
    assert res.success is True
    assert res.message == "Calendar event and all occurrences deleted successfully"
    assert res.id == "evt-123"


@responses.activate
def test_delete_calendar_occurrence_raw_success() -> None:
    """Test delete_calendar_occurrence_raw HTTP success."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/25de04e6-9293-4b4c-8967-e9bdb0eab41d",
        json={
            "success": True,
            "data": {"message": "Occurrence and all future occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    result = delete_calendar_occurrence_raw(
        session,
        "25de04e6-9293-4b4c-8967-e9bdb0eab41d",
        delete_future=True,
    )
    assert result["success"] is True
    assert result["data"]["message"] == "Occurrence and all future occurrences deleted successfully"


@responses.activate
def test_delete_calendar_occurrence_raw_unauthorized() -> None:
    """Test delete_calendar_occurrence_raw raises AuthenticationError on 401."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
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
        delete_calendar_occurrence_raw(session, "occ-123")


@responses.activate
def test_delete_calendar_occurrence_raw_bad_request() -> None:
    """Test delete_calendar_occurrence_raw raises GameSheetError on HTTP error."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
        json={"success": False, "error": "Occurrence not found"},
        status=404,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="returned HTTP 404"):
        delete_calendar_occurrence_raw(session, "occ-123")


@responses.activate
def test_delete_calendar_occurrence_raw_invalid_json() -> None:
    """Test delete_calendar_occurrence_raw raises GameSheetError on invalid JSON."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
        body="Invalid JSON",
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="Failed to parse delete calendar occurrence JSON response"):
        delete_calendar_occurrence_raw(session, "occ-123")


@responses.activate
def test_delete_calendar_occurrence_raw_non_dict() -> None:
    """Test delete_calendar_occurrence_raw raises GameSheetError on non-dict response."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
        json=["not", "a", "dict"],
        status=200,
    )
    session = make_session()
    with pytest.raises(GameSheetError, match="expected a JSON object"):
        delete_calendar_occurrence_raw(session, "occ-123")


@responses.activate
def test_delete_calendar_occurrence_success_future() -> None:
    """Test delete_calendar_occurrence with delete_future=True."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
        json={
            "success": True,
            "data": {"message": "Occurrence and all future occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    res = delete_calendar_occurrence(session, "occ-123", delete_future=True)
    assert isinstance(res, ScheduleDeleteResult)
    assert res.success is True
    assert res.message == "Occurrence and all future occurrences deleted successfully"
    assert res.id == "occ-123"


@responses.activate
def test_delete_calendar_occurrence_success_single() -> None:
    """Test delete_calendar_occurrence with delete_future=False."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-123",
        json={"success": True, "data": {"message": "Occurrence deleted successfully"}},
        status=200,
    )
    session = make_session()
    res = delete_calendar_occurrence(session, "occ-123", delete_future=False)
    assert isinstance(res, ScheduleDeleteResult)
    assert res.success is True
    assert res.message == "Occurrence deleted successfully"
    assert res.id == "occ-123"


@responses.activate
def test_delete_event_all_occurrences() -> None:
    """Test delete_event with all_occurrences=True delegates to delete_calendar_event."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/evt-series-1",
        json={
            "success": True,
            "data": {"message": "Calendar event and all occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    res = delete_event(session, "evt-series-1", all_occurrences=True)
    assert res.success is True
    assert res.id == "evt-series-1"


@responses.activate
def test_delete_event_occurrence() -> None:
    """Test delete_event with occurrence deletion."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-evt-1",
        json={"success": True, "data": {"message": "Occurrence deleted successfully"}},
        status=200,
    )
    session = make_session()
    res = delete_event(session, "occ-evt-1", delete_future=False)
    assert res.success is True
    assert res.id == "occ-evt-1"


@responses.activate
def test_delete_practice_all_occurrences() -> None:
    """Test delete_practice with all_occurrences=True delegates to delete_calendar_event."""
    responses.add(
        responses.DELETE,
        f"{CALENDAR_EVENTS_URL}/prac-series-1",
        json={
            "success": True,
            "data": {"message": "Calendar event and all occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    res = delete_practice(session, "prac-series-1", all_occurrences=True)
    assert res.success is True
    assert res.id == "prac-series-1"


@responses.activate
def test_delete_practice_occurrence() -> None:
    """Test delete_practice with occurrence deletion."""
    responses.add(
        responses.DELETE,
        f"{OCCURRENCE_URL}/occ-prac-1",
        json={
            "success": True,
            "data": {"message": "Occurrence and all future occurrences deleted successfully"},
        },
        status=200,
    )
    session = make_session()
    res = delete_practice(session, "occ-prac-1", delete_future=True)
    assert res.success is True
    assert res.id == "occ-prac-1"
