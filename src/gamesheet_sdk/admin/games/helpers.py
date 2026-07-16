# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared helper functions for games operations."""

from __future__ import annotations

from typing import Any

from gamesheet_sdk.admin.games.models import Game
from gamesheet_sdk.common.constants import (
    BFF_API_BASE_URL,
    BFF_GAMES_LIST,
    DEFAULT_GAMES_LIMIT,
    VALID_GAME_TYPES,
)
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.session import Session
from gamesheet_sdk.common.shared import check_bff_response_status, handle_response


def _make_request(
    session: Session,
    season_id: str,
    completed: bool | None = None,
    scheduled: bool | None = None,
    brackets: bool | None = None,
) -> list[Game]:
    """Make a request to the BFF games-list endpoint.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param completed: Filter for completed games.
    :type completed: bool | None
    :param scheduled: Filter for scheduled games.
    :type scheduled: bool | None
    :param brackets: Filter for bracket games.
    :type brackets: bool | None
    :returns: A list of :class:`Game` objects.
    :rtype: list[Game]
    :raises GameSheetError: For any non-2xx response.
    """
    params: dict[str, Any] = {
        "filter[seasons]": season_id,
        "filter[limit]": str(DEFAULT_GAMES_LIMIT),
        "filter[offset]": "0",
        "filter[sort]": "-start_time",
    }
    # Set filter flags
    if completed is not None:
        params["filter[completed]"] = "true" if completed else "false"
    if scheduled is not None:
        params["filter[scheduled]"] = "true" if scheduled else "false"
    if brackets is not None:
        params["filter[brackets]"] = "true" if brackets else "false"
    url = f"{BFF_API_BASE_URL}{BFF_GAMES_LIST}"
    response = session.get(url, params=params)
    handle_response(response, url, "GET games")
    body: dict[str, Any] = response.json()
    check_bff_response_status(body, url)
    # Parse games from the data array
    games_data = body.get("data", [])
    return [Game(**game_data) for game_data in games_data]


def validate_game_type(game_type: str) -> None:
    """Validate a game type against the known valid types.

    :param game_type: The game type to validate.
    :type game_type: str
    :raises GameSheetError: If the game type is not valid.
    """
    sorted_game_types = ", ".join(sorted(VALID_GAME_TYPES))
    if game_type not in VALID_GAME_TYPES:
        msg = f"Invalid game type '{game_type}'. Valid options: {sorted_game_types}"
        raise GameSheetError(msg)
