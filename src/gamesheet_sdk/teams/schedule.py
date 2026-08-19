# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule and calendar data from the teams API.

The ``GET /api/calendar`` endpoint returns calendar events, games, and practices for a specified team.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_CALENDAR_PATH

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
