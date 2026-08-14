# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Scheduled game CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.games.helpers import _make_request, validate_game_type
from gamesheet_sdk.admin.games.models import Game, ScheduledGame
from gamesheet_sdk.common.constants import (
    API_SEASONS_SCHEDULE,
    API_SEASONS_SCHEDULE_GAME,
    DEFAULT_BASE_URL,
)
from gamesheet_sdk.common.shared import handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def list_scheduled(session: Session, season_id: str) -> list[Game]:
    """Return every scheduled game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier whose scheduled games to list.

    Returns:
        list[Game]: A list of :class:`Game`, in the order the server returned them. The list may be empty if
            the season has no scheduled games.

    """
    return _make_request(session, season_id, completed=False, scheduled=True)


def create_scheduled_game(
    session: Session,
    season_id: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    home_team_id: str,
    home_division_id: str,
    visitor_team_id: str,
    visitor_division_id: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    game_type: str,
    time_zone_name: str,
    time_zone_offset: int,
    number: str,
    broadcaster: str = "",
    home_label: str = "",
    visitor_label: str = "",
) -> ScheduledGame:
    """Create a new scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        scheduled_start_time (str): Scheduled start time (ISO 8601 format).
        scheduled_end_time (str): Scheduled end time (ISO 8601 format).
        home_team_id (str): Home team identifier.
        home_division_id (str): Home team division identifier.
        visitor_team_id (str): Visitor team identifier.
        visitor_division_id (str): Visitor team division identifier.
        location (str): Game location/venue (default: empty string). Must match format '<location_name>
            <surface_name>' from the API (case-insensitive match, but stored with correct casing).
        scorekeeper_name (str): Scorekeeper's full name.
        scorekeeper_phone (str): Scorekeeper's phone number.
        game_type (str): Game type. Must be one of: playoff, exhibition, tournament, regular_season.
        time_zone_name (str): IANA time zone name.
        time_zone_offset (int): Time zone offset in minutes.
        number (str): Game number.
        broadcaster (str): Broadcast provider name (default: empty string). Must match a valid broadcaster key
            from the API (case-insensitive match, but stored with correct casing).
        home_label (str): Home team label override (default: empty string).
        visitor_label (str): Visitor team label override (default: empty string).

    Returns:
        ScheduledGame: The created :class:`ScheduledGame`.

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: If the game_type, location, or broadcaster is invalid, or for any other non-2xx
            response.

    """
    # Import here to avoid circular dependency
    from gamesheet_sdk.admin.games.broadcasters import (  # noqa: PLC0415
        validate_broadcaster_key,
    )
    from gamesheet_sdk.admin.games.locations import (  # noqa: PLC0415
        validate_location,
    )

    # Validate game type
    validate_game_type(game_type)
    # Validate location if provided
    if location:
        location = validate_location(session, location)
    # Validate broadcaster if provided
    if broadcaster:
        broadcaster = validate_broadcaster_key(session, broadcaster)

    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE.format(season_id=season_id)}"
    payload = {
        "data": {
            "attributes": {
                "scheduled_start_time": scheduled_start_time,
                "scheduled_end_time": scheduled_end_time,
                "number": number,
                "location": location,
                "scorekeeper": {"name": scorekeeper_name, "phone": scorekeeper_phone},
                "game_type": game_type,
                "time_zone_offset": time_zone_offset,
                "time_zone_name": time_zone_name,
                "data": {
                    "broadcaster": broadcaster,
                    "home_label": home_label,
                    "visitor_label": visitor_label,
                },
                "status": "",
            },
            "relationships": {
                "home_team": {"data": {"id": home_team_id, "type": "teams"}},
                "home_division": {
                    "data": {"id": home_division_id, "type": "divisions"},
                },
                "visitor_team": {"data": {"id": visitor_team_id, "type": "teams"}},
                "visitor_division": {
                    "data": {"id": visitor_division_id, "type": "divisions"},
                },
            },
        },
    }
    response = session.post(url, json=payload)
    handle_response(response, url, "POST scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


def get_scheduled_game(session: Session, season_id: str, game_id: str) -> ScheduledGame:
    """Get a single scheduled game by ID (JSON:API format).

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        game_id (str): The game identifier to retrieve.

    Returns:
        ScheduledGame: The :class:`ScheduledGame` with the specified ID.

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: For any other non-2xx response, including 404 if the game is not found.

    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    response = session.get(url)
    handle_response(response, url, "GET scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


def update_scheduled_game(
    session: Session,
    season_id: str,
    game_id: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    home_team_id: str,
    home_division_id: str,
    visitor_team_id: str,
    visitor_division_id: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    game_type: str,
    time_zone_name: str,
    time_zone_offset: int,
    number: str,
    status: str,
    broadcaster: str = "",
    home_label: str = "",
    visitor_label: str = "",
) -> ScheduledGame:
    """Update a scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        game_id (str): The game identifier to update.
        scheduled_start_time (str): Scheduled start time (ISO 8601 format).
        scheduled_end_time (str): Scheduled end time (ISO 8601 format).
        home_team_id (str): Home team identifier.
        home_division_id (str): Home team division identifier.
        visitor_team_id (str): Visitor team identifier.
        visitor_division_id (str): Visitor team division identifier.
        location (str): Game location/venue. Must match format '<location_name> <surface_name>' from the API
            (case- insensitive match, but stored with correct casing).
        scorekeeper_name (str): Scorekeeper's full name.
        scorekeeper_phone (str): Scorekeeper's phone number.
        game_type (str): Game type. Must be one of: playoff, exhibition, tournament, regular_season.
        time_zone_name (str): IANA time zone name.
        time_zone_offset (int): Time zone offset in minutes.
        number (str): Game number.
        status (str): Game status.
        broadcaster (str): Broadcast provider name (default: empty string). Must match a valid broadcaster key
            from the API (case-insensitive match, but stored with correct casing).
        home_label (str): Home team label override (default: empty string).
        visitor_label (str): Visitor team label override (default: empty string).

    Returns:
        ScheduledGame: The updated :class:`ScheduledGame`.

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: If the game_type, location, or broadcaster is invalid, or for any other non-2xx
            response, including 404 if the game is not found.

    """
    # Import here to avoid circular dependency
    from gamesheet_sdk.admin.games.broadcasters import (  # noqa: PLC0415
        validate_broadcaster_key,
    )
    from gamesheet_sdk.admin.games.locations import (  # noqa: PLC0415
        validate_location,
    )

    # Validate game type
    validate_game_type(game_type)
    # Validate location (always provided in update, even if empty)
    if location:
        location = validate_location(session, location)
    # Validate broadcaster if provided
    if broadcaster:
        broadcaster = validate_broadcaster_key(session, broadcaster)

    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    payload = {
        "data": {
            "attributes": {
                "scheduled_start_time": scheduled_start_time,
                "scheduled_end_time": scheduled_end_time,
                "number": number,
                "location": location,
                "scorekeeper": {"name": scorekeeper_name, "phone": scorekeeper_phone},
                "game_type": game_type,
                "time_zone_offset": time_zone_offset,
                "time_zone_name": time_zone_name,
                "data": {
                    "vendors": {},
                    "is_valid": False,
                    "broadcaster": broadcaster,
                    "location_id": 0,
                    "broadcaster_id": 0,
                    "home_label": home_label,
                    "visitor_label": visitor_label,
                },
                "status": status,
            },
            "relationships": {
                "home_team": {"data": {"id": home_team_id, "type": "teams"}},
                "home_division": {
                    "data": {"id": home_division_id, "type": "divisions"},
                },
                "visitor_team": {"data": {"id": visitor_team_id, "type": "teams"}},
                "visitor_division": {
                    "data": {"id": visitor_division_id, "type": "divisions"},
                },
            },
        },
    }
    response = session.patch(url, json=payload)
    handle_response(response, url, "PATCH scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


def delete_scheduled_game(session: Session, season_id: str, game_id: str) -> None:
    """Delete a scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        game_id (str): The game identifier to delete.

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: For any other non-2xx response, including 404 if the game is not found.

    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    response = session.delete(url)
    handle_response(response, url, "DELETE scheduled game")
