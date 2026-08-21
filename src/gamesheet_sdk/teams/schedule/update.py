# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Update functions and raw handlers for schedule resources."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule.create import validate_game_type
from gamesheet_sdk.teams.schedule.models import (
    CalendarEventCreated,
    UpdatedGameResult,
)
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


def update_schedule_game_raw(
    session: BaseAuthenticatedSession,
    game_id: int | str,
    payload: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Execute raw HTTP PUT request to update a scheduled game via PUT /api/schedule-game/{game_id}.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        game_id (int | str): Identifier of the scheduled game to update.
        payload (dict[str, Any]): Game update payload.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    path = f"{TEAMS_SCHEDULE_GAME_PATH}/{game_id}"
    url = f"{TEAMS_API_GATEWAY}{path}"
    resp = session.put(url, json=payload, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"PUT {path} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, Exception) as exc:
        msg = f"Failed to parse schedule game update JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from schedule game API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def update_game(
    session: BaseAuthenticatedSession,
    game_id: int | str,
    *,
    team_id: int | str | None = None,
    season_id: int | str | None = None,
    division_id: int | str | None = None,
    opposing_team_id: int | str | None = None,
    opposing_division: int | str | None = None,
    association_id: int | str | None = None,
    league_id: int | str | None = None,
    home_flag: bool | None = None,
    date_time: str | None = None,
    end_time: str | None = None,
    game_number: str | None = None,
    game_type: str | None = None,
    location: str | None = None,
    scorekeeper_name: str | None = None,
    scorekeeper_phone: str | None = None,
    broadcast_provider: str | None = None,
    time_zone_name: str | None = None,
    time_zone_offset: int | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> UpdatedGameResult:
    """Update a scheduled game via the teams schedule-game endpoint.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        game_id (int | str): Identifier of the game to update.
        team_id (int | str | None): Team identifier.
        season_id (int | str | None): Season identifier.
        division_id (int | str | None): Division identifier.
        opposing_team_id (int | str | None): Opposing team identifier.
        opposing_division (int | str | None): Opposing division identifier.
        association_id (int | str | None): Association identifier.
        league_id (int | str | None): League identifier.
        home_flag (bool | None): Whether the team is the home team.
        date_time (str | None): Start date/time (e.g. '2026-08-24T15:00').
        end_time (str | None): End time (e.g. '16:15').
        game_number (str | None): Game number.
        game_type (str | None): Game type.
        location (str | None): Game location / venue.
        scorekeeper_name (str | None): Scorekeeper name.
        scorekeeper_phone (str | None): Scorekeeper phone.
        broadcast_provider (str | None): Broadcast provider key.
        time_zone_name (str | None): IANA timezone name.
        time_zone_offset (int | None): Timezone offset in minutes.
        timeout (float): Request timeout in seconds.

    Returns:
        UpdatedGameResult: Result containing updated game details.

    """
    if game_type is not None:
        validate_game_type(game_type)

    def _to_int_or_val(v: int | str | None) -> int | str | None:
        if v is None:
            return None

        return int(v) if (isinstance(v, int) or (isinstance(v, str) and v.isdigit())) else v

    fields: dict[str, Any] = {
        "season_id": _to_int_or_val(season_id),
        "association_id": _to_int_or_val(association_id),
        "league_id": _to_int_or_val(league_id),
        "division_id": _to_int_or_val(division_id),
        "team_id": _to_int_or_val(team_id),
        "home_flag": home_flag,
        "opposing_division": _to_int_or_val(opposing_division),
        "opposing_team_id": _to_int_or_val(opposing_team_id),
        "date_time": date_time,
        "end_time": end_time,
        "time_zone_name": time_zone_name,
        "time_zone_offset": time_zone_offset,
        "game_number": game_number,
        "game_type": game_type,
        "location": location,
        "scorekeeper_name": scorekeeper_name,
        "scorekeeper_phone": scorekeeper_phone,
        "broadcast_provider": broadcast_provider,
    }
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}

    raw = update_schedule_game_raw(session, game_id, payload, timeout=timeout)
    msg = str(raw.get("message") or "Game updated successfully")

    return UpdatedGameResult(
        success=bool(raw.get("success", True)),
        id=_to_int_or_val(game_id),
        message=msg,
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
        opposing_division=_to_int_or_val(opposing_division),
        home_flag=home_flag,
        time_zone_name=time_zone_name,
        time_zone_offset=time_zone_offset,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
    )


def update_calendar_occurrence_raw(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    payload: dict[str, Any],
    *,
    update_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Execute raw HTTP PUT request to update an occurrence via PUT /api/calendar/occurrences/{occurrence_id}.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): Identifier of the occurrence to update.
        payload (dict[str, Any]): Occurrence update payload.
        update_future (bool): Whether to update this and all future occurrences (default: False).
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    path = f"{TEAMS_CALENDAR_OCCURRENCES_PATH}/{occurrence_id}"
    url = f"{TEAMS_API_GATEWAY}{path}"
    params = {"updateFuture": "true"} if update_future else None
    resp = session.put(url, json=payload, params=params, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code not in {200, 201, 204}:
        msg = f"PUT /api/calendar/occurrences/{occurrence_id} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except Exception as exc:
        msg = f"Failed to parse update calendar occurrence JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = f"Unexpected response format from calendar occurrence update API: {data!r}"
        raise GameSheetError(msg)

    return data


def update_calendar_occurrence(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    payload: dict[str, Any],
    *,
    update_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CalendarEventCreated:
    """Update a calendar occurrence and return validated CalendarEventCreated model.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): UUID of the occurrence to update.
        payload (dict[str, Any]): Dictionary containing fields to update.
        update_future (bool): If True, updates this and all future occurrences.
        timeout (float): Request timeout in seconds.

    Returns:
        CalendarEventCreated: Validated response model.

    Raises:
        GameSheetError: If the server returns an error.

    """
    raw = update_calendar_occurrence_raw(
        session,
        occurrence_id,
        payload,
        update_future=update_future,
        timeout=timeout,
    )
    inner_data = raw.get("data")
    if not isinstance(inner_data, dict):
        msg = f"Malformed response: expected dict data for calendar occurrence update, got {inner_data!r}"
        raise GameSheetError(msg)

    return CalendarEventCreated.model_validate(inner_data)


def update_event(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    *,
    title: str | None = None,
    notes: str | None = None,
    location_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    rrule: str | None = None,
    update_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CalendarEventCreated:
    """Update a non-game calendar event occurrence.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): Occurrence identifier (UUID).
        title (str | None): Event title.
        notes (str | None): Event notes / description.
        location_name (str | None): Venue / location name.
        start_date (str | None): ISO formatted start datetime (UTC).
        end_date (str | None): ISO formatted end datetime (UTC).
        rrule (str | None): RRULE recurrence rule string.
        update_future (bool): Update future occurrences if recurring.
        timeout (float): Request timeout in seconds.

    Returns:
        CalendarEventCreated: Validated response model.

    """
    fields: dict[str, Any] = {
        "title": title,
        "notes": notes,
        "location_name": location_name,
        "start_date": start_date,
        "end_date": end_date,
        "rrule": rrule,
    }
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}

    return update_calendar_occurrence(
        session,
        occurrence_id,
        payload,
        update_future=update_future,
        timeout=timeout,
    )


def update_practice(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    *,
    title: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    notes: str | None = None,
    location_name: str | None = None,
    rrule: str | None = None,
    update_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CalendarEventCreated:
    """Update a practice occurrence.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): Identifier of the occurrence to update.
        title (str | None): Practice title.
        start_date (str | None): ISO start datetime string.
        end_date (str | None): ISO end datetime string.
        notes (str | None): Practice notes or description.
        location_name (str | None): Venue or location address.
        rrule (str | None): Recurrence rule.
        update_future (bool): If True, update this and future occurrences.
        timeout (float): Request timeout in seconds.

    Returns:
        CalendarEventCreated: Updated occurrence details model.

    """
    return update_event(
        session,
        occurrence_id,
        title=title,
        notes=notes,
        location_name=location_name,
        start_date=start_date,
        end_date=end_date,
        rrule=rrule,
        update_future=update_future,
        timeout=timeout,
    )


__all__ = [
    "update_calendar_occurrence",
    "update_calendar_occurrence_raw",
    "update_event",
    "update_game",
    "update_practice",
    "update_schedule_game_raw",
]
