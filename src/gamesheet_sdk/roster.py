"""GameSheet roster: players and coaches within a season.

Roster data represents the people associated with teams in a season - both players and coaches.
This module provides access to:
- Players (players)
- Coaches (coaches)

Each view talks to the GameSheet JSON:API at ``/api/seasons/{season_id}/players`` and
``/api/seasons/{season_id}/coaches`` directly with the lightweight :class:`gamesheet_sdk.Session`
path -- no Playwright needed for read-only access once a bearer token has been obtained.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Player(BaseModel):
    """A single player.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{id}/players`` to a flat typed
    model.
    """

    id: str = Field(description="Player identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(default=None, description="Player's first name.")
    last_name: str | None = Field(default=None, description="Player's last name.")
    birthdate: str | None = Field(default=None, description="Player's birthdate.")
    photo_url: str | None = Field(default=None, description="URL to player photo.")
    biography: str | None = Field(default=None, description="Player biography.")
    height: str | None = Field(default=None, description="Player height.")
    weight: str | None = Field(default=None, description="Player weight.")
    shot_hand: str | None = Field(default=None, description="Player's shooting hand.")
    province: str | None = Field(default=None, description="Player's province.")
    hometown: str | None = Field(default=None, description="Player's hometown.")
    country: str | None = Field(default=None, description="Player's country.")
    drafted_by: str | None = Field(default=None, description="Team that drafted the player.")
    committed_to: str | None = Field(default=None, description="School/team player committed to.")
    created_at: datetime = Field(description="When the player record was created.")
    updated_at: datetime = Field(description="Last time the player record was updated.")


class Coach(BaseModel):
    """A single coach.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{id}/coaches`` to a flat typed
    model.
    """

    id: str = Field(description="Coach identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(default=None, description="Coach's first name.")
    last_name: str | None = Field(default=None, description="Coach's last name.")
    created_at: datetime = Field(description="When the coach record was created.")
    updated_at: datetime = Field(description="Last time the coach record was updated.")


def _parse_player(item: dict[str, Any]) -> Player:
    """Flatten a JSON:API resource object into a :class:`Player`."""
    attrs = item.get("attributes", {})
    # Extract season_id from relationships
    season_id = item.get("relationships", {}).get("season", {}).get("data", {}).get("id", "")
    return Player(
        id=item["id"],
        season_id=season_id,
        **attrs,
    )


def _parse_coach(item: dict[str, Any]) -> Coach:
    """Flatten a JSON:API resource object into a :class:`Coach`."""
    attrs = item.get("attributes", {})
    # Extract season_id from relationships
    season_id = item.get("relationships", {}).get("season", {}).get("data", {}).get("id", "")
    return Coach(
        id=item["id"],
        season_id=season_id,
        **attrs,
    )


def get_player(session: Session, season_id: str, player_id: str) -> Player:
    """Get a single player by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param player_id: The player identifier to retrieve.
    :type player_id: str
    :returns: The :class:`Player` with the specified ID.
    :rtype: Player
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response, including 404 if the player is not found.
    """
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Player '{player_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid player ID and season ID.",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse_player(body["data"])


def get_coach(session: Session, season_id: str, coach_id: str) -> Coach:
    """Get a single coach by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param coach_id: The coach identifier to retrieve.
    :type coach_id: str
    :returns: The :class:`Coach` with the specified ID.
    :rtype: Coach
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response, including 404 if the coach is not found.
    """
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Coach '{coach_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid coach ID and season ID.",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse_coach(body["data"])


def list_players(session: Session, season_id: str) -> list[Player]:
    """Return every player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose players to list.
    :type season_id: str
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        season has no players.
    :rtype: list[Player]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/players"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
        params={"include": "teams,divisions"},
    )
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

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    # Parse all players
    all_players = [_parse_player(item) for item in body.get("data", [])]
    return all_players


def list_coaches(session: Session, season_id: str) -> list[Coach]:
    """Return every coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose coaches to list.
    :type season_id: str
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        season has no coaches.
    :rtype: list[Coach]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
        params={"include": "teams,divisions"},
    )
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

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    # Parse all coaches
    all_coaches = [_parse_coach(item) for item in body.get("data", [])]
    return all_coaches
