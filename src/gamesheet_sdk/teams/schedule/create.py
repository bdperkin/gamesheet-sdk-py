# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Creation functions and helpers for events, games, and practices."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.cli.datetime_helpers import (
    get_local_timezone_name,
    get_local_timezone_offset,
)
from gamesheet_sdk.common.constants import VALID_GAME_TYPES
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule.constants import DAY_NAME_MAP
from gamesheet_sdk.teams.schedule.models import (
    CalendarEventCreated,
    CreatedGameResult,
)
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_CALENDAR_EVENTS_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


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
    until: str | None = None,
) -> str | None:
    """Build an RRULE string for recurring events.

    Args:
        frequency (str | None): Recurrence frequency ('daily', 'weekly', 'monthly').
        interval (int): Recurrence interval in units of frequency (default: 1).
        by_day (str | list[str] | None): Days of week for weekly recurrence (e.g., 'TU,TH', 'mon,wed').
        until (str | None): Recurrence end date (e.g. '2026-11-28' or '20261128T235959Z', default: None).

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

    if until:
        until_clean = until.strip().replace("-", "").replace(":", "")
        if "T" not in until_clean:
            until_clean = f"{until_clean}T235959Z"
        elif not until_clean.endswith("Z"):
            until_clean = f"{until_clean}Z"

        parts.append(f"UNTIL={until_clean}")

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
        GameSheetError: If the server returns malformed data.

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


__all__ = [
    "build_rrule",
    "create_calendar_event_raw",
    "create_event",
    "create_game",
    "create_practice",
    "create_schedule_game_raw",
    "validate_game_type",
]
