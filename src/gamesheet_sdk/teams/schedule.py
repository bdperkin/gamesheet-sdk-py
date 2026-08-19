# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule and calendar data from the teams API.

The ``GET /api/calendar`` endpoint returns calendar events, games, and practices for a specified team.
The ``GET /api/calendar/occurrences/{id}`` endpoint returns detailed event occurrence data.
The ``GET /api/availability/batch`` endpoint returns player/coach availability for an event.
"""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.cli.datetime_helpers import (
    get_local_timezone_name,
    get_local_timezone_offset,
)
from gamesheet_sdk.common.constants import VALID_GAME_TYPES
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_AVAILABILITY_BATCH_PATH,
    TEAMS_CALENDAR_EVENTS_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_CALENDAR_PATH,
    TEAMS_PUBLIC_CALENDAR_SERVICE,
    TEAMS_SCHEDULE_GAME_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession

DAY_NAME_MAP: dict[str, str] = {
    "mo": "MO",
    "mon": "MO",
    "monday": "MO",
    "tu": "TU",
    "tue": "TU",
    "tues": "TU",
    "tuesday": "TU",
    "we": "WE",
    "wed": "WE",
    "wednesday": "WE",
    "th": "TH",
    "thu": "TH",
    "thurs": "TH",
    "thursday": "TH",
    "fr": "FR",
    "fri": "FR",
    "friday": "FR",
    "sa": "SA",
    "sat": "SA",
    "saturday": "SA",
    "su": "SU",
    "sun": "SU",
    "sunday": "SU",
}


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
    """Details of a newly created calendar event or practice.

    Attributes:
        id (str | int | None): Event identifier.
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
        rrule (str | None): Recurrence rule string.
        start_time (str | None): Start time.
        end_time (str | None): End time.
        created_by_user_id (int | str | None): Creator user identifier.
        created_at (str | None): Timestamp when created.
        updated_at (str | None): Timestamp when updated.
        deleted_at (str | None): Timestamp when deleted.

    """

    model_config = ConfigDict(extra="allow")

    id: str | int | None = Field(default=None, description="Event identifier.")
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
    rrule: str | None = Field(default=None, description="Recurrence rule string.")
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


def fetch_calendar_raw(
    session: BaseAuthenticatedSession,
    team_id: str,
    *,
    month: str = "all",
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Fetch raw calendar data from the teams API for a specified team.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events (default: 'all').
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the calendar API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_PATH}"
    params = {"teamId": team_id, "month": month}
    resp = session.get(url, params=params, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"GET {TEAMS_CALENDAR_PATH} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse calendar JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from calendar API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def list_schedule(
    session: BaseAuthenticatedSession,
    team_id: str,
    *,
    event_type: str | None = None,
    month: str = "all",
    include_event_data: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[ScheduleEvent]:
    """List schedule events for a team, optionally filtered by event type.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str): Team identifier.
        event_type (str | None): Optional event type filter ('event', 'game', 'practice').
        month (str): Month filter for calendar events (default: 'all').
        include_event_data (bool): Whether to include detailed eventData in models (default: False).
        timeout (float): Request timeout in seconds.

    Returns:
        list[ScheduleEvent]: List of parsed schedule event models.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed data.

    """
    raw = fetch_calendar_raw(session, team_id, month=month, timeout=timeout)
    raw_events = raw.get("data", [])
    if not isinstance(raw_events, list):
        msg = "Malformed response: 'data' field is not a list."
        raise GameSheetError(msg)

    events: list[ScheduleEvent] = []
    for item in raw_events:
        if not isinstance(item, dict):
            continue

        if event_type is not None:
            item_type = str(item.get("type", "")).lower()
            if item_type != event_type.lower():
                continue

        item_dict = dict(item)
        if not include_event_data:
            item_dict.pop("eventData", None)

        events.append(ScheduleEvent.model_validate(item_dict))

    return events


def list_events(
    session: BaseAuthenticatedSession,
    team_id: str,
    *,
    month: str = "all",
    include_event_data: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[ScheduleEvent]:
    """List calendar events ('event' type) for a team.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events (default: 'all').
        include_event_data (bool): Whether to include detailed eventData in models (default: False).
        timeout (float): Request timeout in seconds.

    Returns:
        list[ScheduleEvent]: List of calendar events.

    """
    return list_schedule(
        session,
        team_id,
        event_type="event",
        month=month,
        include_event_data=include_event_data,
        timeout=timeout,
    )


def list_games(
    session: BaseAuthenticatedSession,
    team_id: str,
    *,
    month: str = "all",
    include_event_data: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[ScheduleEvent]:
    """List scheduled games ('game' type) for a team.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events (default: 'all').
        include_event_data (bool): Whether to include detailed eventData in models (default: False).
        timeout (float): Request timeout in seconds.

    Returns:
        list[ScheduleEvent]: List of scheduled games.

    """
    return list_schedule(
        session,
        team_id,
        event_type="game",
        month=month,
        include_event_data=include_event_data,
        timeout=timeout,
    )


def list_practices(
    session: BaseAuthenticatedSession,
    team_id: str,
    *,
    month: str = "all",
    include_event_data: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[ScheduleEvent]:
    """List practices ('practice' type) for a team.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events (default: 'all').
        include_event_data (bool): Whether to include detailed eventData in models (default: False).
        timeout (float): Request timeout in seconds.

    Returns:
        list[ScheduleEvent]: List of team practices.

    """
    return list_schedule(
        session,
        team_id,
        event_type="practice",
        month=month,
        include_event_data=include_event_data,
        timeout=timeout,
    )


def fetch_event_occurrence_raw(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Fetch raw calendar event occurrence data from the teams API.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str | int): Identifier of the event occurrence.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the calendar occurrences API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_OCCURRENCES_PATH}/{event_id}"
    resp = session.get(url, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        endpoint = f"{TEAMS_CALENDAR_OCCURRENCES_PATH}/{event_id}"
        msg = f"GET {endpoint} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse calendar occurrence JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from calendar occurrences API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def fetch_scheduled_game_raw(
    session: BaseAuthenticatedSession,
    game_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Fetch raw game details from the teams schedule-game API.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        game_id (str | int): Identifier of the scheduled game.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the schedule-game API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_SCHEDULE_GAME_PATH}/{game_id}"
    resp = session.get(url, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        endpoint = f"{TEAMS_SCHEDULE_GAME_PATH}/{game_id}"
        msg = f"GET {endpoint} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse schedule game JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from schedule game API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def fetch_availability_raw(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    event_id: str | int,
    event_type: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Fetch batch availability data for a team event.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str | int): Team identifier (prototeam ID).
        event_id (str | int): Event identifier.
        event_type (str): Type of event (e.g., 'event', 'game', 'practice').
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the availability API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_AVAILABILITY_BATCH_PATH}"
    params = {
        "prototeam_id": str(team_id),
        "event_id": str(event_id),
        "event_type": event_type,
    }
    resp = session.get(url, params=params, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"GET {TEAMS_AVAILABILITY_BATCH_PATH} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse availability JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from availability API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def _resolve_availability_event_id(
    event_dict: dict[str, Any],
    fallback_event_id: str | int,
    resolved_type: str,
) -> str | int:
    """Resolve the event ID to use for fetching availability.

    For games, the game ID is typically an integer found in `id`, `eventData.id`,
    `eventData.gameId`, `gameId`, or `eventId`. For events and practices,
    the event ID is typically the occurrence/event UUID.
    """
    raw_event_data = event_dict.get("eventData")
    event_data_dict: dict[str, Any] = raw_event_data if isinstance(raw_event_data, dict) else {}
    if resolved_type.lower() == "game":
        game_id: str | int = (
            event_dict.get("gameId")
            or event_dict.get("game_id")
            or event_data_dict.get("gameId")
            or event_data_dict.get("game_id")
            or event_dict.get("eventId")
            or event_dict.get("event_id")
            or event_data_dict.get("eventId")
            or event_data_dict.get("event_id")
            or event_data_dict.get("id")
            or (
                event_dict.get("id")
                if (isinstance(event_dict.get("id"), int) or str(event_dict.get("id", "")).isdigit())
                else None
            )
            or fallback_event_id
        )
        return game_id

    return (
        event_dict.get("eventId")
        or event_dict.get("event_id")
        or event_data_dict.get("eventId")
        or event_data_dict.get("event_id")
        or event_dict.get("id")
        or event_data_dict.get("id")
        or fallback_event_id
    )


def _resolve_effective_team_id(
    event_dict: dict[str, Any],
    team_id: str | int | None,
) -> str | int | None:
    """Resolve effective team ID from event dict or explicit team ID."""
    if team_id is not None:
        return team_id

    raw_event_data = event_dict.get("eventData")
    event_data_dict = raw_event_data if isinstance(raw_event_data, dict) else {}
    return (
        event_dict.get("teamId")
        or event_dict.get("team_id")
        or event_dict.get("home_prototeam_id")
        or event_dict.get("homeTeamId")
        or event_dict.get("home_team_id")
        or event_dict.get("visitor_prototeam_id")
        or event_dict.get("awayTeamId")
        or event_dict.get("away_team_id")
        or event_data_dict.get("teamId")
        or event_data_dict.get("team_id")
        or event_data_dict.get("homeTeamId")
        or event_data_dict.get("home_team_id")
        or event_data_dict.get("awayTeamId")
        or event_data_dict.get("away_team_id")
    )


def _fetch_and_normalize_game_dict(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    timeout: float,
) -> dict[str, Any]:
    """Fetch and normalize scheduled game dict from API."""
    raw = fetch_scheduled_game_raw(session, event_id, timeout=timeout)
    event_data = raw.get("data") if "data" in raw else raw
    if not isinstance(event_data, dict):
        msg = "Malformed response: expected dict data for game."
        raise GameSheetError(msg)

    event_dict = dict(event_data)
    if "id" not in event_dict or event_dict["id"] is None:
        event_dict["id"] = int(event_id) if str(event_id).isdigit() else event_id

    if "type" not in event_dict or not event_dict["type"]:
        event_dict["type"] = "game"

    if "eventDate" not in event_dict and "date_time" in event_dict:
        date_time_val = str(event_dict["date_time"])
        event_dict["eventDate"] = (
            date_time_val.split("T", maxsplit=1)[0] if "T" in date_time_val else date_time_val
        )

    if "eventTime" not in event_dict and "date_time" in event_dict:
        date_time_val = str(event_dict["date_time"])
        if "T" in date_time_val:
            event_dict["eventTime"] = date_time_val.split("T")[1]

    if "eventLocation" not in event_dict and "location" in event_dict:
        event_dict["eventLocation"] = event_dict.get("location", "")

    if "eventTitle" not in event_dict and "game_number" in event_dict:
        event_dict["eventTitle"] = event_dict.get("game_number", "")

    return event_dict


def _fetch_and_verify_occurrence_dict(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    event_type: str | None,
    timeout: float,
) -> dict[str, Any]:
    """Fetch calendar occurrence and verify event type."""
    raw = fetch_event_occurrence_raw(session, event_id, timeout=timeout)
    event_data = raw.get("data") if "data" in raw else raw
    if not isinstance(event_data, dict):
        msg = "Malformed response: expected dict data for event occurrence."
        raise GameSheetError(msg)

    actual_type = str(event_data.get("type", ""))
    if event_type is not None and actual_type.lower() != event_type.lower():
        msg = f"Event '{event_id}' is of type '{actual_type}', expected '{event_type}'."
        raise GameSheetError(msg)

    return dict(event_data)


def get_schedule_event(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    event_type: str | None = None,
    include_availability: bool = False,
    team_id: str | int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleEventDetail:
    """Retrieve detailed metadata for a calendar event occurrence or scheduled game.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str | int): Identifier of the event occurrence or game ID.
        event_type (str | None): Expected event type ('event', 'game', 'practice').
        include_availability (bool): Whether to fetch and include team availability.
        team_id (str | int | None): Optional team ID (used when fetching availability).
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleEventDetail: Detailed schedule event occurrence or game model.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error, event type mismatches,
            or team ID is missing for availability.

    """
    is_game = (event_type is not None and event_type.lower() == "game") or (
        event_type is None and (isinstance(event_id, int) or str(event_id).isdigit())
    )

    if is_game:
        event_dict = _fetch_and_normalize_game_dict(session, event_id, timeout=timeout)
    else:
        event_dict = _fetch_and_verify_occurrence_dict(
            session,
            event_id,
            event_type=event_type,
            timeout=timeout,
        )

    if include_availability:
        effective_team_id = _resolve_effective_team_id(event_dict, team_id)
        if not effective_team_id:
            msg = (
                f"Team ID is required to fetch availability for event '{event_id}'. "
                "Specify --team-id or set GAMESHEET_TEAM_ID."
            )
            raise GameSheetError(msg)

        resolved_type = str(event_dict.get("type", "")) or (event_type or "")
        avail_event_id = _resolve_availability_event_id(
            event_dict,
            event_id,
            resolved_type,
        )
        avail_raw = fetch_availability_raw(
            session,
            effective_team_id,
            avail_event_id,
            resolved_type,
            timeout=timeout,
        )
        avail_data = avail_raw.get("data") if "data" in avail_raw else avail_raw
        event_dict["availability"] = avail_data

    return ScheduleEventDetail.model_validate(event_dict)


def get_event(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    include_availability: bool = False,
    team_id: str | int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleEventDetail:
    """Retrieve detailed metadata for a calendar event ('event' type).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str | int): Identifier of the event occurrence.
        include_availability (bool): Whether to fetch and include team availability.
        team_id (str | int | None): Optional team ID for availability lookup.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleEventDetail: Event details model.

    """
    return get_schedule_event(
        session,
        event_id,
        event_type="event",
        include_availability=include_availability,
        team_id=team_id,
        timeout=timeout,
    )


def get_game(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    include_availability: bool = False,
    team_id: str | int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleEventDetail:
    """Retrieve detailed metadata for a scheduled game ('game' type).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str | int): Identifier of the game occurrence.
        include_availability (bool): Whether to fetch and include team availability.
        team_id (str | int | None): Optional team ID for availability lookup.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleEventDetail: Game details model.

    """
    return get_schedule_event(
        session,
        event_id,
        event_type="game",
        include_availability=include_availability,
        team_id=team_id,
        timeout=timeout,
    )


def get_practice(
    session: BaseAuthenticatedSession,
    event_id: str | int,
    *,
    include_availability: bool = False,
    team_id: str | int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleEventDetail:
    """Retrieve detailed metadata for a practice ('practice' type).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str | int): Identifier of the practice occurrence.
        include_availability (bool): Whether to fetch and include team availability.
        team_id (str | int | None): Optional team ID for availability lookup.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleEventDetail: Practice details model.

    """
    return get_schedule_event(
        session,
        event_id,
        event_type="practice",
        include_availability=include_availability,
        team_id=team_id,
        timeout=timeout,
    )


def get_calendar_subscription(
    team_id: str,
    *,
    timestamp_hours: int | None = None,
) -> CalendarSubscription:
    """Generate calendar subscription URLs for a team.

    Calculates subscription URLs for Apple Calendar (webcal), Google Calendar, and generic calendar feed.

    Args:
        team_id (str): Team identifier (prototeamId UUID or team ID).
        timestamp_hours (int | None): Optional hours timestamp since Unix epoch for cache busting
            (defaults to current UTC hour).

    Returns:
        CalendarSubscription: Pydantic model with appleCalendar, googleCalendar, and calendarUrl.

    """
    if timestamp_hours is None:
        timestamp_hours = int(time.time() // 3600)

    feed_resource = f"{TEAMS_PUBLIC_CALENDAR_SERVICE}/teams/{team_id}/calendar.ics#v{timestamp_hours}"
    apple_cal = f"webcal://{feed_resource}"
    google_cal = f"https://calendar.google.com/calendar/r?cid={quote(apple_cal, safe='')}"
    cal_url = f"webcal://{feed_resource}"

    return CalendarSubscription(
        appleCalendar=apple_cal,
        googleCalendar=google_cal,
        calendarUrl=cal_url,
    )


def validate_game_type(game_type: str) -> None:
    """Validate a game type against known valid types.

    Args:
        game_type (str): The game type to validate.

    Raises:
        GameSheetError: If the game type is not valid.

    """
    sorted_game_types = ", ".join(sorted(VALID_GAME_TYPES))
    if game_type not in VALID_GAME_TYPES:
        msg = f"Invalid game type '{game_type}'. Valid options: {sorted_game_types}"
        raise GameSheetError(msg)


def build_rrule(
    frequency: str | None,
    *,
    interval: int = 1,
    by_day: str | list[str] | None = None,
) -> str | None:
    """Build an RRULE string for recurring events.

    Args:
        frequency (str | None): Recurrence frequency ('daily', 'weekly', 'monthly').
        interval (int): Recurrence interval in units of frequency (default: 1).
        by_day (str | list[str] | None): Days of week for weekly recurrence (e.g., 'TU,TH', 'mon,wed').

    Returns:
        str | None: Formatted RRULE string or None if frequency is not specified.

    Raises:
        GameSheetError: If frequency is not recognized.

    """
    if not frequency:
        return None

    freq_upper = frequency.strip().upper()
    if freq_upper.startswith("FREQ="):
        return frequency.strip()

    valid_freqs = {"DAILY", "WEEKLY", "MONTHLY"}
    if freq_upper not in valid_freqs:
        msg = f"Invalid repeat frequency '{frequency}'. Valid options: daily, weekly, monthly."
        raise GameSheetError(msg)

    parts: list[str] = [f"FREQ={freq_upper}", f"INTERVAL={interval}"]

    if freq_upper == "WEEKLY" and by_day:
        if isinstance(by_day, str):
            day_tokens = [d.strip() for d in by_day.split(",") if d.strip()]
        else:
            day_tokens = [str(d).strip() for d in by_day if str(d).strip()]

        normalized_days = [DAY_NAME_MAP.get(day.lower(), day.upper()) for day in day_tokens]

        if normalized_days:
            parts.append(f"BYDAY={','.join(normalized_days)}")

    return ";".join(parts)


def create_calendar_event_raw(
    session: BaseAuthenticatedSession,
    payload: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Create a calendar event or practice via POST /api/calendar/events.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        payload (dict[str, Any]): Event creation payload.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_EVENTS_PATH}"
    resp = session.post(url, json=payload, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"POST {TEAMS_CALENDAR_EVENTS_PATH} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse calendar event creation JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from calendar event creation API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def create_event(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    title: str,
    start_date_time: str,
    end_time: str,
    *,
    event_type: str = "event",
    timezone: str | None = None,
    location: str = "",
    notes: str = "",
    all_day: bool = False,
    rrule: str | None = None,
    repeat_until: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CalendarEventCreated:
    """Create a calendar event ('event' or 'practice' type).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str | int): Team identifier (prototeam ID or team ID).
        title (str): Event title.
        start_date_time (str): Start date/time (e.g. '2026-08-21T13:30').
        end_time (str): End time (e.g. '14:30').
        event_type (str): Event type ('event' or 'practice', default: 'event').
        timezone (str | None): Timezone name (defaults to local timezone).
        location (str): Venue or location address (default: empty string).
        notes (str): Event notes or description (default: empty string).
        all_day (bool): Whether event is all day (default: False).
        rrule (str | None): Recurrence rule (default: None).
        repeat_until (str | None): Recurrence end date (e.g. '2027-03-22', default: None).
        timeout (float): Request timeout in seconds.

    Returns:
        CalendarEventCreated: Created event details model.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error.

    """
    tz = timezone if timezone is not None else get_local_timezone_name()
    payload: dict[str, Any] = {
        "teamId": str(team_id),
        "type": event_type,
        "title": title,
        "timezone": tz,
        "location": location,
        "notes": notes,
        "allDay": all_day,
        "startDate": start_date_time,
        "endTime": end_time,
    }
    if rrule:
        payload["rrule"] = rrule

    if repeat_until:
        payload["repeatUntil"] = repeat_until

    raw = create_calendar_event_raw(session, payload, timeout=timeout)
    data = raw.get("data") if "data" in raw else raw
    if not isinstance(data, dict):
        msg = "Malformed response: expected dict data for created calendar event."
        raise GameSheetError(msg)

    return CalendarEventCreated.model_validate(data)


def create_practice(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    start_date_time: str,
    end_time: str,
    *,
    title: str = "Practice",
    timezone: str | None = None,
    location: str = "",
    notes: str = "",
    all_day: bool = False,
    rrule: str | None = None,
    repeat_until: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CalendarEventCreated:
    """Create a practice calendar event ('practice' type).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (str | int): Team identifier (prototeam ID or team ID).
        start_date_time (str): Start date/time (e.g. '2026-08-30T13:30').
        end_time (str): End time (e.g. '14:30').
        title (str): Practice title (default: 'Practice').
        timezone (str | None): Timezone name (defaults to local timezone).
        location (str): Venue or location address (default: empty string).
        notes (str): Notes or description (default: empty string).
        all_day (bool): Whether practice is all day (default: False).
        rrule (str | None): Recurrence rule (default: None).
        repeat_until (str | None): Recurrence end date (default: None).
        timeout (float): Request timeout in seconds.

    Returns:
        CalendarEventCreated: Created practice details model.

    """
    return create_event(
        session,
        team_id,
        title,
        start_date_time,
        end_time,
        event_type="practice",
        timezone=timezone,
        location=location,
        notes=notes,
        all_day=all_day,
        rrule=rrule,
        repeat_until=repeat_until,
        timeout=timeout,
    )


def create_schedule_game_raw(
    session: BaseAuthenticatedSession,
    payload: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Create a scheduled game via POST /api/schedule-game.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        payload (dict[str, Any]): Game creation payload.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_SCHEDULE_GAME_PATH}"
    resp = session.post(url, json=payload, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"POST {TEAMS_SCHEDULE_GAME_PATH} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse schedule-game creation JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from schedule-game API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def create_game(
    session: BaseAuthenticatedSession,
    team_id: int | str,
    season_id: int | str,
    division_id: int | str,
    opposing_team_id: int | str,
    date_time: str,
    end_time: str,
    *,
    home_flag: bool = True,
    opposing_division: int | str | None = None,
    association_id: int | str = 0,
    league_id: int | str = 0,
    game_number: str = "",
    game_type: str = "regular_season",
    location: str = "",
    scorekeeper_name: str = "",
    scorekeeper_phone: str = "",
    broadcast_provider: str = "",
    time_zone_name: str | None = None,
    time_zone_offset: int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CreatedGameResult:
    """Create a scheduled game via the teams schedule-game endpoint.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        team_id (int | str): Team identifier.
        season_id (int | str): Season identifier.
        division_id (int | str): Division identifier.
        opposing_team_id (int | str): Opposing team identifier.
        date_time (str): Start date/time (e.g. '2026-08-20T12:00').
        end_time (str): End time (e.g. '13:15').
        home_flag (bool): Whether the team is the home team (default: True).
        opposing_division (int | str | None): Opposing team division (default: same as division_id).
        association_id (int | str): Parent association identifier (default: 0).
        league_id (int | str): Parent league identifier (default: 0).
        game_number (str): Game number / identifier (default: '').
        game_type (str): Game type (default: 'regular_season'). Must be a valid game type.
        location (str): Game venue / location (default: '').
        scorekeeper_name (str): Scorekeeper full name (default: '').
        scorekeeper_phone (str): Scorekeeper phone number (default: '').
        broadcast_provider (str): Broadcast provider key (default: '').
        time_zone_name (str | None): IANA time zone name (defaults to local timezone).
        time_zone_offset (int | None): Time zone offset in minutes (defaults to local offset).
        timeout (float): Request timeout in seconds.

    Returns:
        CreatedGameResult: Result containing game creation details and status.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the game type is invalid or the server returns an error.

    """
    validate_game_type(game_type)
    tz_name = time_zone_name if time_zone_name is not None else get_local_timezone_name()
    tz_offset = time_zone_offset if time_zone_offset is not None else get_local_timezone_offset()
    opp_div = division_id if opposing_division is None else opposing_division

    def _to_int_or_val(v: int | str) -> int | str:
        return int(v) if (isinstance(v, int) or (isinstance(v, str) and v.isdigit())) else v

    payload: dict[str, Any] = {
        "season_id": _to_int_or_val(season_id),
        "association_id": _to_int_or_val(association_id),
        "league_id": _to_int_or_val(league_id),
        "division_id": _to_int_or_val(division_id),
        "team_id": _to_int_or_val(team_id),
        "home_flag": home_flag,
        "opposing_division": _to_int_or_val(opp_div),
        "opposing_team_id": _to_int_or_val(opposing_team_id),
        "date_time": date_time,
        "end_time": end_time,
        "time_zone_name": tz_name,
        "time_zone_offset": tz_offset,
        "game_number": game_number,
        "game_type": game_type,
        "location": location,
        "scorekeeper_name": scorekeeper_name,
        "scorekeeper_phone": scorekeeper_phone,
        "broadcast_provider": broadcast_provider,
    }

    create_schedule_game_raw(session, payload, timeout=timeout)

    return CreatedGameResult(
        success=True,
        game_number=game_number,
        date_time=date_time,
        end_time=end_time,
        game_type=game_type,
        location=location,
        team_id=_to_int_or_val(team_id),
        opposing_team_id=_to_int_or_val(opposing_team_id),
        season_id=_to_int_or_val(season_id),
        association_id=_to_int_or_val(association_id),
        league_id=_to_int_or_val(league_id),
        division_id=_to_int_or_val(division_id),
        opposing_division=_to_int_or_val(opp_div),
        home_flag=home_flag,
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
    )
