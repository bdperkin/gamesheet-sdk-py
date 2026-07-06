# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Bracket and general game list operations."""

from __future__ import annotations

from gamesheet_sdk.exceptions import GameSheetError
from gamesheet_sdk.games.helpers import _make_request
from gamesheet_sdk.games.models import Game
from gamesheet_sdk.session import Session


def list_completed(session: Session, season_id: str) -> list[Game]:
    """Return every completed game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose completed games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no completed games.
    :rtype: list[Game]
    """
    return _make_request(session, season_id, completed=True, scheduled=False)


def list_brackets(session: Session, season_id: str) -> list[Game]:
    """Return every bracket game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    .. note:: The brackets filter is based on the expected API pattern but has not been verified
        with real bracket data. If this returns unexpected results, the filter parameters may
        need adjustment.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose bracket games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no bracket games.
    :rtype: list[Game]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    # Try filter[brackets]=true first, fallback to gameType=playoff if needed
    return _make_request(session, season_id, brackets=True)


def get_game(session: Session, season_id: str, game_id: int) -> Game:
    """Get a single game by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to retrieve.
    :type game_id: int
    :returns: The :class:`Game` with the specified ID.
    :rtype: Game
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    # Get all games for the season and filter by ID
    # The BFF API doesn't have a single-game endpoint, so we filter client-side
    games = _make_request(session, season_id)
    for game in games:
        if game.id == game_id:
            return game
    # Game not found
    _err_msg = (
        f"Game '{game_id}' not found in season '{season_id}'. "
        f"Make sure you're using a valid game ID and season ID.",
    )
    raise GameSheetError(_err_msg)
