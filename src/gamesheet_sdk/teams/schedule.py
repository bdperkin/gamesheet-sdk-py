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
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_AVAILABILITY_BATCH_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_CALENDAR_PATH,
    TEAMS_PUBLIC_CALENDAR_SERVICE,
    TEAMS_SCHEDULE_GAME_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


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
