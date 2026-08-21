# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams schedule models and validation."""

from __future__ import annotations

import pytest

from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.teams.schedule import (
    CalendarEventCreated,
    CreatedGameResult,
    ScheduleDeleteResult,
    ScheduleEvent,
    ScheduleEventDetail,
    UpdatedGameResult,
    build_rrule,
    validate_game_type,
)


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
    assert not event.type
    assert not event.eventDate
    assert not event.eventTime
    assert not event.eventTitle
    assert not event.eventLocation


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
    assert not detail.type
    assert not detail.eventDate
    assert not detail.eventTime
    assert not detail.eventTitle
    assert not detail.eventLocation
    assert detail.eventData is None
    assert detail.availability is None


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
        is_override=True,
        original_start_date="2026-08-21T13:30:00Z",
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
    assert model.is_override is True
    assert model.original_start_date == "2026-08-21T13:30:00Z"
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


def test_schedule_delete_result_model() -> None:
    """Test ScheduleDeleteResult model instantiation and fields."""
    res = ScheduleDeleteResult(success=True, message="Deleted successfully", id="item-123")
    assert res.success is True
    assert res.message == "Deleted successfully"
    assert res.id == "item-123"


def test_updated_game_result_model() -> None:
    """Test UpdatedGameResult model instantiation."""
    result = UpdatedGameResult(
        success=True,
        id=2962945,
        message="Game updated successfully",
        game_number="TEST-432",
        date_time="2026-08-24T15:00",
        end_time="16:15",
        game_type="regular_season",
        location="Polar Ice Wake Forest",
        team_id=525015,
        opposing_team_id=523675,
        season_id=15020,
        association_id=38,
        league_id=1148580,
        division_id=81419,
        opposing_division=81419,
        home_flag=True,
        time_zone_name="America/New_York",
        time_zone_offset=-240,
        scorekeeper_name="John Doe",
        scorekeeper_phone="555-1234",
        broadcast_provider="LIVEBARN",
    )
    assert result.success is True
    assert result.id == 2962945
    assert result.game_number == "TEST-432"
    assert result.date_time == "2026-08-24T15:00"
    assert result.end_time == "16:15"


def test_build_rrule_with_until() -> None:
    """Test build_rrule with until parameter."""
    rrule = build_rrule("daily", interval=1, until="2026-11-28")
    assert rrule == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"

    rrule2 = build_rrule("weekly", interval=2, by_day="tu,th", until="20261128T235959Z")
    assert rrule2 == "FREQ=WEEKLY;INTERVAL=2;UNTIL=20261128T235959Z;BYDAY=TU,TH"


def test_build_rrule_until_without_z() -> None:
    """Test build_rrule when until has T but no trailing Z."""
    rrule = build_rrule("daily", interval=1, until="20261128T235959")
    assert rrule == "FREQ=DAILY;INTERVAL=1;UNTIL=20261128T235959Z"
