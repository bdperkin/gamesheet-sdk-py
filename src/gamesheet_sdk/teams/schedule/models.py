# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule and calendar models for the teams SDK."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScheduleEvent(BaseModel):
    """Calendar event or scheduled activity for a team.

    Attributes:
        eventDate (str): Date of the event.
        eventLocation (str): Location or venue of the event.
        eventTime (str): Scheduled time of the event.
        eventTitle (str): Title or summary description of the event.
        id (str | int | None): Event identifier.
        type (str): Type of event (e.g., 'event', 'game', 'practice').

    """

    model_config = ConfigDict(extra="allow")

    eventDate: str = Field(default="", description="Date of the event.")  # noqa: N815
    eventLocation: str = Field(default="", description="Location or venue of the event.")  # noqa: N815
    eventTime: str = Field(default="", description="Scheduled time of the event.")  # noqa: N815
    eventTitle: str = Field(default="", description="Title or summary of the event.")  # noqa: N815
    id: str | int | None = Field(default=None, description="Event identifier.")
    type: str = Field(default="", description="Type of event ('event', 'game', 'practice').")


class ScheduleEventDetail(BaseModel):
    """Detailed metadata for a calendar event occurrence.

    Attributes:
        id (str | int | None): Event identifier.
        type (str): Type of event ('event', 'game', 'practice').
        eventDate (str): Date of the event.
        eventLocation (str): Location or venue of the event.
        eventTime (str): Scheduled time of the event.
        eventTitle (str): Title or summary description of the event.
        eventData (dict[str, Any] | None): Detailed event payload.
        availability (Any): Optional availability data when requested.

    """

    model_config = ConfigDict(extra="allow")

    id: str | int | None = Field(default=None, description="Event identifier.")
    type: str = Field(default="", description="Type of event ('event', 'game', 'practice').")
    eventDate: str = Field(default="", description="Date of the event.")  # noqa: N815
    eventLocation: str = Field(default="", description="Location or venue of the event.")  # noqa: N815
    eventTime: str = Field(default="", description="Scheduled time of the event.")  # noqa: N815
    eventTitle: str = Field(default="", description="Title or summary of the event.")  # noqa: N815
    eventData: dict[str, Any] | None = Field(  # noqa: N815
        default=None,
        description="Detailed event payload.",
    )
    availability: Any = Field(default=None, description="Optional availability data.")


class CalendarSubscription(BaseModel):
    """Calendar subscription URLs for Apple Calendar, Google Calendar, and webcal.

    Attributes:
        appleCalendar (str): Apple Calendar subscription URL (webcal protocol).
        googleCalendar (str): Google Calendar subscription URL.
        calendarUrl (str): Generic calendar subscription feed URL (webcal protocol).

    """

    model_config = ConfigDict(extra="allow")

    appleCalendar: str = Field(  # noqa: N815
        default="",
        description="Apple Calendar subscription URL (webcal protocol).",
    )
    googleCalendar: str = Field(  # noqa: N815
        default="",
        description="Google Calendar subscription URL.",
    )
    calendarUrl: str = Field(  # noqa: N815
        default="",
        description="Generic calendar subscription feed URL (webcal protocol).",
    )


class CalendarEventCreated(BaseModel):
    """Details of a newly created or updated calendar event or practice.

    Attributes:
        id (str | int | None): Event identifier.
        event_id (str | int | None): Parent event identifier.
        team_id (int | str | None): Team identifier.
        prototeam_id (str | None): Prototeam UUID.
        title (str | None): Event title.
        type (str | None): Event type ('event' or 'practice').
        notes (str | None): Event notes / description.
        location_name (str | None): Location or venue name.
        location_address (str | None): Location address.
        location_surface (str | None): Location surface.
        timezone_name (str | None): Timezone name.
        all_day (bool | None): Whether the event is all day.
        is_override (bool | None): Whether this occurrence is an override.
        original_start_date (str | None): Original start date if override.
        rrule (str | None): Recurrence rule string.
        start_date (str | None): Start date/time ISO string.
        end_date (str | None): End date/time ISO string.
        start_time (str | None): Start time.
        end_time (str | None): End time.
        created_by_user_id (int | str | None): Creator user identifier.
        created_at (str | None): Timestamp when created.
        updated_at (str | None): Timestamp when updated.
        deleted_at (str | None): Timestamp when deleted.

    """

    model_config = ConfigDict(extra="allow")

    id: str | int | None = Field(default=None, description="Event identifier.")
    event_id: str | int | None = Field(default=None, description="Parent event identifier.")
    team_id: int | str | None = Field(default=None, description="Team identifier.")
    prototeam_id: str | None = Field(default=None, description="Prototeam UUID.")
    title: str | None = Field(default=None, description="Event title.")
    type: str | None = Field(default=None, description="Event type ('event' or 'practice').")
    notes: str | None = Field(default=None, description="Event notes or description.")
    location_name: str | None = Field(default=None, description="Location or venue name.")
    location_address: str | None = Field(default=None, description="Location address.")
    location_surface: str | None = Field(default=None, description="Location surface.")
    timezone_name: str | None = Field(default=None, description="Timezone name.")
    all_day: bool | None = Field(default=None, description="Whether the event is all day.")
    is_override: bool | None = Field(default=None, description="Whether this occurrence is an override.")
    original_start_date: str | None = Field(
        default=None,
        description="Original start date if override.",
    )
    rrule: str | None = Field(default=None, description="Recurrence rule string.")
    start_date: str | None = Field(default=None, description="Start date/time ISO string.")
    end_date: str | None = Field(default=None, description="End date/time ISO string.")
    start_time: str | None = Field(default=None, description="Start time.")
    end_time: str | None = Field(default=None, description="End time.")
    created_by_user_id: int | str | None = Field(default=None, description="Creator user identifier.")
    created_at: str | None = Field(default=None, description="Timestamp when created.")
    updated_at: str | None = Field(default=None, description="Timestamp when updated.")
    deleted_at: str | None = Field(default=None, description="Timestamp when deleted.")


class CreatedGameResult(BaseModel):
    """Result of creating a scheduled game.

    Attributes:
        success (bool): Whether the game creation succeeded.
        game_number (str | None): Game number.
        date_time (str | None): Start date and time.
        end_time (str | None): End time.
        game_type (str | None): Game type.
        location (str | None): Game location or venue.
        team_id (int | str | None): Team identifier.
        opposing_team_id (int | str | None): Opposing team identifier.
        season_id (int | str | None): Season identifier.
        association_id (int | str | None): Association identifier.
        league_id (int | str | None): League identifier.
        division_id (int | str | None): Division identifier.
        opposing_division (int | str | None): Opposing division identifier.
        home_flag (bool | None): Home team flag.
        time_zone_name (str | None): IANA time zone name.
        time_zone_offset (int | None): Time zone offset in minutes.
        scorekeeper_name (str | None): Scorekeeper name.
        scorekeeper_phone (str | None): Scorekeeper phone.
        broadcast_provider (str | None): Broadcast provider.

    """

    model_config = ConfigDict(extra="allow")

    success: bool = Field(default=True, description="Whether the operation succeeded.")
    game_number: str | None = Field(default=None, description="Game number.")
    date_time: str | None = Field(default=None, description="Start date and time.")
    end_time: str | None = Field(default=None, description="End time.")
    game_type: str | None = Field(default=None, description="Game type.")
    location: str | None = Field(default=None, description="Game location or venue.")
    team_id: int | str | None = Field(default=None, description="Team identifier.")
    opposing_team_id: int | str | None = Field(default=None, description="Opposing team identifier.")
    season_id: int | str | None = Field(default=None, description="Season identifier.")
    association_id: int | str | None = Field(default=None, description="Association identifier.")
    league_id: int | str | None = Field(default=None, description="League identifier.")
    division_id: int | str | None = Field(default=None, description="Division identifier.")
    opposing_division: int | str | None = Field(default=None, description="Opposing division identifier.")
    home_flag: bool | None = Field(default=None, description="Home team flag.")
    time_zone_name: str | None = Field(default=None, description="Time zone name.")
    time_zone_offset: int | None = Field(default=None, description="Time zone offset.")
    scorekeeper_name: str | None = Field(default=None, description="Scorekeeper name.")
    scorekeeper_phone: str | None = Field(default=None, description="Scorekeeper phone.")
    broadcast_provider: str | None = Field(default=None, description="Broadcast provider.")


class UpdatedGameResult(BaseModel):
    """Result of updating a scheduled game.

    Attributes:
        success (bool): Whether the game update succeeded.
        id (int | str | None): Game identifier.
        message (str): Status message.
        game_number (str | None): Game number.
        date_time (str | None): Start date and time.
        end_time (str | None): End time.
        game_type (str | None): Game type.
        location (str | None): Game location or venue.
        team_id (int | str | None): Team identifier.
        opposing_team_id (int | str | None): Opposing team identifier.
        season_id (int | str | None): Season identifier.
        association_id (int | str | None): Association identifier.
        league_id (int | str | None): League identifier.
        division_id (int | str | None): Division identifier.
        opposing_division (int | str | None): Opposing division identifier.
        home_flag (bool | None): Home team flag.
        time_zone_name (str | None): IANA time zone name.
        time_zone_offset (int | None): Time zone offset in minutes.
        scorekeeper_name (str | None): Scorekeeper name.
        scorekeeper_phone (str | None): Scorekeeper phone.
        broadcast_provider (str | None): Broadcast provider.

    """

    model_config = ConfigDict(extra="allow")

    success: bool = Field(default=True, description="Whether the operation succeeded.")
    id: int | str | None = Field(default=None, description="Game identifier.")
    message: str = Field(default="Game updated successfully", description="Status message.")
    game_number: str | None = Field(default=None, description="Game number.")
    date_time: str | None = Field(default=None, description="Start date and time.")
    end_time: str | None = Field(default=None, description="End time.")
    game_type: str | None = Field(default=None, description="Game type.")
    location: str | None = Field(default=None, description="Game location or venue.")
    team_id: int | str | None = Field(default=None, description="Team identifier.")
    opposing_team_id: int | str | None = Field(default=None, description="Opposing team identifier.")
    season_id: int | str | None = Field(default=None, description="Season identifier.")
    association_id: int | str | None = Field(default=None, description="Association identifier.")
    league_id: int | str | None = Field(default=None, description="League identifier.")
    division_id: int | str | None = Field(default=None, description="Division identifier.")
    opposing_division: int | str | None = Field(default=None, description="Opposing division identifier.")
    home_flag: bool | None = Field(default=None, description="Home team flag.")
    time_zone_name: str | None = Field(default=None, description="Time zone name.")
    time_zone_offset: int | None = Field(default=None, description="Time zone offset in minutes.")
    scorekeeper_name: str | None = Field(default=None, description="Scorekeeper name.")
    scorekeeper_phone: str | None = Field(default=None, description="Scorekeeper phone.")
    broadcast_provider: str | None = Field(default=None, description="Broadcast provider.")


class ScheduleDeleteResult(BaseModel):
    """Result returned from a schedule deletion operation.

    Attributes:
        success (bool): Whether the deletion succeeded.
        message (str): Informational message returned by the API or client.
        id (str | int | None): Optional identifier of the deleted resource.

    """

    model_config = ConfigDict(extra="allow")

    success: bool = Field(default=True, description="Whether the deletion was successful.")
    message: str = Field(default="", description="Message returned from deletion operation.")
    id: str | int | None = Field(default=None, description="Identifier of deleted resource.")


__all__ = [
    "CalendarEventCreated",
    "CalendarSubscription",
    "CreatedGameResult",
    "ScheduleDeleteResult",
    "ScheduleEvent",
    "ScheduleEventDetail",
    "UpdatedGameResult",
]
