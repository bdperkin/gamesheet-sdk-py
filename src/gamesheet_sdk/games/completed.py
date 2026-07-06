# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Completed game operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gamesheet_sdk.constants import (
    API_SEASONS_GAMES,
    DEFAULT_BASE_URL,
    SCORESHEET_SERVICE_BASE_URL,
    SCORESHEET_SERVICE_GAME,
)
from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import handle_response


def get_completed_game(
    session: Session,
    season_id: str,
    game_id: str,
) -> dict[str, Any]:
    """Get a completed game with full details (JSON:API format).

    Returns the full JSON:API response including rosters, goals, shots, penalties, and all related data. The
    supplied :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to retrieve.
    :type game_id: str
    :returns: The full game data as a dictionary (JSON:API format with data/included/relationships).
    :rtype: dict[str, Any]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_GAMES.format(season_id=season_id, game_id=game_id)}"
    params = {"include": "players,coaches,referees,teams,season,association,league"}
    response = session.get(url, params=params)
    handle_response(response, url, "GET completed game")
    body: dict[str, Any] = response.json()
    return body


def download_completed_game_pdf(
    session: Session,
    game_id: str,
    output_path: str,
) -> None:
    """Download the PDF scoresheet for a completed game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param game_id: The game identifier.
    :type game_id: str
    :param output_path: File path where the PDF will be saved.
    :type output_path: str
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{SCORESHEET_SERVICE_BASE_URL}{SCORESHEET_SERVICE_GAME.format(game_id=game_id)}"
    response = session.get(url)
    handle_response(response, url, "GET scoresheet PDF")
    Path(output_path).write_bytes(response.content)
