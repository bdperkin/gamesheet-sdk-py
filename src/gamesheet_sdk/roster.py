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

from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response, parse_jsonapi_resource

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session


class Player(BaseModel):  # pylint: disable=too-many-instance-attributes
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
    drafted_by: str | None = Field(
        default=None,
        description="Team that drafted the player.",
    )
    committed_to: str | None = Field(
        default=None,
        description="School/team player committed to.",
    )
    number: str | None = Field(default=None, description="Player's jersey number (team roster only).")
    position: str | None = Field(default=None, description="Player's position (team roster only).")
    duty: str | None = Field(default=None, description="Player's duty (team roster only).")
    status: str | None = Field(default=None, description="Player's status (team roster only).")
    starting: bool | None = Field(default=None, description="Whether player is starting (team roster only).")
    added_at_game_time: bool | None = Field(
        default=None,
        description="Whether player was added at game time (team roster only).",
    )
    affiliated: bool | None = Field(
        default=None,
        description="Whether player is affiliated (team roster only).",
    )
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
    position: str | None = Field(default=None, description="Coach's position (team roster only).")
    status: str | None = Field(default=None, description="Coach's status (team roster only).")
    signature: str | None = Field(default=None, description="Coach's signature (team roster only).")
    created_at: datetime = Field(description="When the coach record was created.")
    updated_at: datetime = Field(description="Last time the coach record was updated.")


def _parse_player(item: dict[str, Any]) -> Player:
    """Flatten a JSON:API resource object into a :class:`Player`."""
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Player(**data)


def _parse_coach(item: dict[str, Any]) -> Coach:
    """Flatten a JSON:API resource object into a :class:`Coach`."""
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Coach(**data)


def get_player(session: Session, season_id: str, player_id: str) -> Player:
    """Get a single player by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The parent season identifier.
    :param player_id: The player identifier to retrieve.
    :returns: The :class:`Player` with the specified ID.
    :rtype: Player
    """
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET player")
    body: dict[str, Any] = response.json()
    return _parse_player(body["data"])


def get_coach(session: Session, season_id: str, coach_id: str) -> Coach:
    """Get a single coach by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The parent season identifier.
    :param coach_id: The coach identifier to retrieve.
    :returns: The :class:`Coach` with the specified ID.
    :rtype: Coach
    """
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET coach")
    body: dict[str, Any] = response.json()
    return _parse_coach(body["data"])


def list_players(session: Session, season_id: str) -> list[Player]:
    """Return every player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier whose players to list.
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        season has no players.
    :rtype: list[Player]
    """
    endpoint = f"/api/seasons/{season_id}/players"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "teams,divisions"})
    handle_response(response, endpoint, "GET players")
    body: dict[str, Any] = response.json()
    # Parse all players
    all_players = [_parse_player(item) for item in body.get("data", [])]
    return all_players


def list_coaches(session: Session, season_id: str) -> list[Coach]:
    """Return every coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier whose coaches to list.
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        season has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "teams,divisions"})
    handle_response(response, endpoint, "GET coaches")
    body: dict[str, Any] = response.json()
    # Parse all coaches
    all_coaches = [_parse_coach(item) for item in body.get("data", [])]
    return all_coaches


def list_team_players(session: Session, season_id: str, team_id: str) -> list[Player]:
    """Return every player for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier whose players to list.
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        team has no players.
    :rtype: list[Player]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "players,coaches"})
    handle_response(response, endpoint, "GET team")
    body: dict[str, Any] = response.json()
    included_players = {
        item["id"]: item
        for item in body.get(
            "included",
            [],
        )
        if item.get("type") == "players"
    }
    roster_metadata = {
        str(p["id"]): p
        for p in body.get("data", {}).get("attributes", {}).get("roster", {}).get("players", [])
    }
    players = []
    for player_id, player_data in included_players.items():
        player = _parse_player(player_data)
        if player_id in roster_metadata:
            metadata = roster_metadata[player_id]
            player.number = metadata.get("number")
            player.position = metadata.get("position")
            player.duty = metadata.get("duty")
            player.status = metadata.get("status")
            player.starting = metadata.get("starting")
            player.added_at_game_time = metadata.get("added_at_game_time")
            player.affiliated = metadata.get("affiliated")
        players.append(player)
    return players


def list_team_coaches(session: Session, season_id: str, team_id: str) -> list[Coach]:
    """Return every coach for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier whose coaches to list.
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        team has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "players,coaches"})
    handle_response(response, endpoint, "GET team")
    body: dict[str, Any] = response.json()
    included_coaches = {
        item["id"]: item
        for item in body.get(
            "included",
            [],
        )
        if item.get("type") == "coaches"
    }
    roster_metadata = {
        str(c["id"]): c
        for c in body.get("data", {}).get("attributes", {}).get("roster", {}).get("coaches", [])
    }
    coaches = []
    for coach_id, coach_data in included_coaches.items():
        coach = _parse_coach(coach_data)
        if coach_id in roster_metadata:
            metadata = roster_metadata[coach_id]
            coach.position = metadata.get("position")
            coach.status = metadata.get("status")
            coach.signature = metadata.get("signature")
        coaches.append(coach)
    return coaches
