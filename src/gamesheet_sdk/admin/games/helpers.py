# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared helper functions for games operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.games.models import Game
from gamesheet_sdk.common.constants import (
    BFF_API_BASE_URL,
    BFF_GAMES_LIST,
    DEFAULT_GAMES_LIMIT,
    VALID_GAME_TYPES,
)
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import check_bff_response_status, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def _make_request(
    session: Session,
    season_id: str,
    *,
    completed: bool | None = None,
    scheduled: bool | None = None,
    brackets: bool | None = None,
) -> list[Game]:
    """Make a request to the BFF games-list endpoint.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        completed (bool | None): Filter for completed games.
        scheduled (bool | None): Filter for scheduled games.
        brackets (bool | None): Filter for bracket games.

    Returns:
        list[Game]: A list of :class:`Game` objects.

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

    Args:
        game_type (str): The game type to validate.

    Raises:
        GameSheetError: If the game type is not valid.

    """
    sorted_game_types = ", ".join(sorted(VALID_GAME_TYPES))
    if game_type not in VALID_GAME_TYPES:
        msg = f"Invalid game type '{game_type}'. Valid options: {sorted_game_types}"
        raise GameSheetError(msg)
