"""GameSheet games: scheduled, completed, and bracket games within a season.

Games represent matchups between teams. This module provides access to three game views:
- Scheduled games (upcoming/future games)
- Completed games (finished games with results)
- Bracket games (playoff/tournament games)

The games data is retrieved from the BFF (Backend For Frontend) API at
the BFF API ``/games-list/v1`` endpoint with various filter parameters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.constants import BFF_API_BASE_URL
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session

_ENDPOINT = "/games-list/v1"


class TeamInfo(BaseModel):
    """Team information within a game."""

    id: int = Field(description="Team identifier.")
    title: str = Field(description="Team name.")
    division_id: int | None = Field(default=None, alias="divisionId", description="Division identifier.")
    division_title: str | None = Field(default=None, alias="divisionTitle", description="Division name.")


class Game(BaseModel):
    """A single game.

    Maps the game objects from the BFF API response.
    """

    id: int = Field(description="Game identifier.")
    status: str = Field(description="Game status (e.g., completed, scheduled).")
    date: str = Field(description="Game date (YYYY-MM-DD).")
    time: str | None = Field(default=None, description="Game start time.")
    end_time: str | None = Field(default=None, alias="endTime", description="Game end time.")
    time_zone_name: str | None = Field(default=None, alias="timeZoneName", description="Time zone name.")
    location: str | None = Field(default=None, description="Venue/location of the game.")
    game_number: str | None = Field(
        default=None,
        alias="gameNumber",
        description="Game number or identifier.",
    )
    game_type: str | None = Field(
        default=None,
        alias="gameType",
        description="Game type (regular, playoff, etc.).",
    )
    visitor: TeamInfo = Field(description="Visiting team information.")
    home: TeamInfo = Field(description="Home team information.")
    visitor_score: int | None = Field(default=None, alias="visitorScore", description="Visitor team score.")
    home_score: int | None = Field(default=None, alias="homeScore", description="Home team score.")
    has_shootout: bool | None = Field(
        default=None,
        alias="hasShootout",
        description="Whether game had a shootout.",
    )
    has_overtime: bool | None = Field(
        default=None,
        alias="hasOvertime",
        description="Whether game had overtime.",
    )
    viewed: bool | None = Field(default=None, description="Whether the user has viewed this game.")

    model_config = {"populate_by_name": True}


def _make_request(
    session: Session,
    season_id: str,
    completed: bool | None = None,
    scheduled: bool | None = None,
    brackets: bool | None = None,
) -> list[Game]:
    """Make a request to the BFF games-list endpoint."""
    params: dict[str, Any] = {
        "filter[seasons]": season_id,
        "filter[limit]": "1000",  # Get all games
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

    url = f"{BFF_API_BASE_URL}{_ENDPOINT}"
    response = session.get(url, params=params)

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)

    if response.status_code == 404:
        _err_msg = (
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)

    if response.status_code >= 400:
        _err_msg = (f"GET {url} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()

    # Check for success status
    if body.get("status") != "success":
        _err_msg = (f"BFF API returned non-success status: {body.get('status')}",)
        raise GameSheetError(_err_msg)

    # Parse games from the data array
    games_data = body.get("data", [])
    return [Game(**game_data) for game_data in games_data]


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


def list_scheduled(session: Session, season_id: str) -> list[Game]:
    """Return every scheduled game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose scheduled games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no scheduled games.
    :rtype: list[Game]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    return _make_request(session, season_id, completed=False, scheduled=True)


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
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    return _make_request(session, season_id, completed=True, scheduled=False)


def list_brackets(session: Session, season_id: str) -> list[Game]:
    """Return every bracket game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Note: The brackets filter is based on the expected API pattern but has not been verified
    with real bracket data. If this returns unexpected results, the filter parameters may
    need adjustment.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose bracket games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no bracket games.
    :rtype: list[Game]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    # Try filter[brackets]=true first, fallback to gameType=playoff if needed
    return _make_request(session, season_id, brackets=True)
