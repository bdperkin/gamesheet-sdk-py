# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Deletion functions and raw handlers for schedule resources."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.schedule.models import ScheduleDeleteResult
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_CALENDAR_EVENTS_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


def delete_schedule_game_raw(
    session: BaseAuthenticatedSession,
    game_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Execute raw HTTP DELETE request to delete a scheduled game via DELETE /api/schedule-game/{game_id}.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        game_id (str | int): ID of the scheduled game to delete.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    path = f"{TEAMS_SCHEDULE_GAME_PATH}/{game_id}"
    url = f"{TEAMS_API_GATEWAY}{path}"
    resp = session.delete(url, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"DELETE {path} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse delete game JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from schedule-game API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def delete_game(
    session: BaseAuthenticatedSession,
    game_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleDeleteResult:
    """Delete a scheduled game.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        game_id (str | int): Identifier of the scheduled game.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleDeleteResult: Result of deletion containing success flag and message.

    """
    raw = delete_schedule_game_raw(session, game_id, timeout=timeout)
    msg = str(raw.get("message") or "Game deleted successfully")
    return ScheduleDeleteResult(success=True, message=msg, id=game_id)


def delete_calendar_event_raw(
    session: BaseAuthenticatedSession,
    event_id: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Execute raw HTTP DELETE request to delete a calendar event series.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str): ID of the calendar event series to delete.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    path = f"{TEAMS_CALENDAR_EVENTS_PATH}/{event_id}"
    url = f"{TEAMS_API_GATEWAY}{path}"
    resp = session.delete(url, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"DELETE {path} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse delete calendar event JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from calendar event delete API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def delete_calendar_event(
    session: BaseAuthenticatedSession,
    event_id: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleDeleteResult:
    """Delete a calendar event and all of its occurrences.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str): Identifier of the calendar event series.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleDeleteResult: Result of deletion containing success flag and message.

    """
    raw = delete_calendar_event_raw(session, event_id, timeout=timeout)
    raw_data = raw.get("data")
    msg_val = raw_data.get("message") if isinstance(raw_data, dict) else None
    msg = str(
        msg_val or raw.get("message") or "Calendar event and all occurrences deleted successfully",
    )
    return ScheduleDeleteResult(success=True, message=msg, id=event_id)


def delete_calendar_occurrence_raw(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    *,
    delete_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Execute raw HTTP DELETE request to delete a calendar occurrence.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): ID of the calendar occurrence to delete.
        delete_future (bool): Whether to delete this and all future occurrences.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Parsed JSON response from the API.

    Raises:
        AuthenticationError: If the user is not authenticated (401).
        GameSheetError: If the server returns an error or malformed response.

    """
    path = f"{TEAMS_CALENDAR_OCCURRENCES_PATH}/{occurrence_id}"
    url = f"{TEAMS_API_GATEWAY}{path}"
    params = {"deleteFuture": "true" if delete_future else "false"}
    resp = session.delete(url, params=params, timeout=timeout)

    if resp.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if resp.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"DELETE {path} returned HTTP {resp.status_code}: {resp.text}"
        raise GameSheetError(msg)

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse delete calendar occurrence JSON response: {exc}"
        raise GameSheetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Unexpected response format from calendar occurrence delete API: expected a JSON object."
        raise GameSheetError(msg)

    return data


def delete_calendar_occurrence(
    session: BaseAuthenticatedSession,
    occurrence_id: str,
    *,
    delete_future: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleDeleteResult:
    """Delete a calendar occurrence (optionally including all future occurrences).

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        occurrence_id (str): Identifier of the occurrence.
        delete_future (bool): If True, delete this and all future occurrences.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleDeleteResult: Result of deletion containing success flag and message.

    """
    raw = delete_calendar_occurrence_raw(
        session,
        occurrence_id,
        delete_future=delete_future,
        timeout=timeout,
    )
    raw_data = raw.get("data")
    msg_val = raw_data.get("message") if isinstance(raw_data, dict) else None
    fallback_msg = (
        "Occurrence and all future occurrences deleted successfully"
        if delete_future
        else "Occurrence deleted successfully"
    )
    msg = str(msg_val or raw.get("message") or fallback_msg)
    return ScheduleDeleteResult(success=True, message=msg, id=occurrence_id)


def delete_event(
    session: BaseAuthenticatedSession,
    event_id: str,
    *,
    delete_future: bool = False,
    all_occurrences: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleDeleteResult:
    """Delete a calendar event series or occurrence.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        event_id (str): Identifier of the calendar event or occurrence.
        delete_future (bool): If True, delete this and all future occurrences.
        all_occurrences (bool): If True, delete the entire event series via /api/calendar/events.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleDeleteResult: Result of deletion containing success flag and message.

    """
    if all_occurrences:
        return delete_calendar_event(session, event_id, timeout=timeout)

    return delete_calendar_occurrence(session, event_id, delete_future=delete_future, timeout=timeout)


def delete_practice(
    session: BaseAuthenticatedSession,
    practice_id: str,
    *,
    delete_future: bool = False,
    all_occurrences: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> ScheduleDeleteResult:
    """Delete a practice calendar event series or occurrence.

    Args:
        session (BaseAuthenticatedSession): Authenticated session instance.
        practice_id (str): Identifier of the practice event or occurrence.
        delete_future (bool): If True, delete this and all future occurrences.
        all_occurrences (bool): If True, delete the entire practice series via /api/calendar/events.
        timeout (float): Request timeout in seconds.

    Returns:
        ScheduleDeleteResult: Result of deletion containing success flag and message.

    """
    if all_occurrences:
        return delete_calendar_event(session, practice_id, timeout=timeout)

    return delete_calendar_occurrence(session, practice_id, delete_future=delete_future, timeout=timeout)


__all__ = [
    "delete_calendar_event",
    "delete_calendar_event_raw",
    "delete_calendar_occurrence",
    "delete_calendar_occurrence_raw",
    "delete_event",
    "delete_game",
    "delete_practice",
    "delete_schedule_game_raw",
]
