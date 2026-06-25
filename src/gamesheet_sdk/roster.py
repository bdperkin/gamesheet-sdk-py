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
    model. Includes both base player data and roster-specific metadata (position, jersey, etc.).
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
    designation: str | None = Field(default=None, description="Player's designation (team roster only).")
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
            # designation is stored as "duty" in the roster
            # Map back: "captain" -> "Captain", "alternate captain" -> "Alternate Captain"
            if player.duty:
                player.designation = player.duty.title()
            player.status = metadata.get("status")
            player.starting = metadata.get("starting")
            player.added_at_game_time = metadata.get("added_at_game_time")
            player.affiliated = metadata.get("affiliated")
        players.append(player)
    return players


def create_player(
    session: Session,
    season_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
    team_id: str | None = None,
) -> Player:
    """Create a new player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier to create the player in.
    :param first_name: Player's first name.
    :param last_name: Player's last name.
    :param external_id: Optional external identifier for the player.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :param team_id: Optional team identifier to associate the player with.
    :returns: The created :class:`Player`.
    :rtype: Player
    """
    endpoint = f"/api/seasons/{season_id}/players"
    payload: dict[str, Any] = {
        "data": {
            "type": "players",
            "attributes": {
                "first_name": first_name,
                "last_name": last_name,
            },
        },
    }
    if external_id:
        payload["data"]["attributes"]["external_id"] = external_id
    if jersey:
        payload["data"]["attributes"]["jersey"] = jersey
    if position:
        payload["data"]["attributes"]["position"] = position
    if status:
        payload["data"]["attributes"]["status"] = status
    if designation:
        payload["data"]["attributes"]["designation"] = designation
    if team_id:
        payload["data"]["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    body: dict[str, Any] = response.json()
    return _parse_player(body["data"])


def create_coach(
    session: Session,
    season_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    position: str | None = None,
    team_id: str | None = None,
) -> Coach:
    """Create a new coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier to create the coach in.
    :param first_name: Coach's first name.
    :param last_name: Coach's last name.
    :param external_id: Optional external identifier for the coach.
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :param team_id: Optional team identifier to associate the coach with.
    :returns: The created :class:`Coach`.
    :rtype: Coach
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    payload: dict[str, Any] = {
        "data": {
            "type": "coaches",
            "attributes": {
                "first_name": first_name,
                "last_name": last_name,
            },
        },
    }
    if external_id:
        payload["data"]["attributes"]["external_id"] = external_id
    if position:
        payload["data"]["attributes"]["position"] = position
    if team_id:
        payload["data"]["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST coach")
    body: dict[str, Any] = response.json()
    return _parse_coach(body["data"])


def _get_team_for_roster_update(session: Session, season_id: str, team_id: str) -> dict[str, Any]:
    """Fetch team data for roster update.

    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :returns: The team data dict from the JSON:API response.
    :rtype: dict[str, Any]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "association,league,season,division,players,coaches"},
    )
    handle_response(response, endpoint, "GET team for roster update")
    data: dict[str, Any] = response.json()
    return data


def _update_team_roster(
    session: Session,
    season_id: str,
    team_id: str,
    roster: dict[str, Any],
    current_attrs: dict[str, Any],
    current_relationships: dict[str, Any],
) -> None:
    """Update team's roster via PATCH to teams-v2 endpoint.

    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :param roster: The updated roster dict.
    :param current_attrs: Current team attributes.
    :param current_relationships: Current team relationships.
    """
    endpoint = f"/api/seasons/{season_id}/teams-v2/{team_id}"
    payload = {
        "data": {
            "id": team_id,
            "type": "teams",
            "attributes": {
                "title": current_attrs.get("title", ""),
                "external_id": current_attrs.get("external_id"),
                "roster": roster,
                "data": current_attrs.get("data", {}),
                "logo_url": current_attrs.get("logo_url"),
            },
            "relationships": {
                "division": {
                    "data": {
                        "id": current_relationships.get("division", {}).get("data", {}).get("id"),
                        "type": "divisions",
                    },
                },
            },
        },
    }
    response = session.patch(endpoint, json=payload, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "PATCH team roster")


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


def create_team_player(  # pylint: disable=too-many-locals
    session: Session,
    season_id: str,
    team_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> Player:
    """Create a new player and add to the specified team's roster.

    This function performs two operations: (1) creates the player at the season level,
    (2) updates the team's roster to include the new player with position and other metadata.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to add the player to.
    :param first_name: Player's first name.
    :param last_name: Player's last name.
    :param external_id: Optional external identifier for the player.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :returns: The created :class:`Player`.
    :rtype: Player
    """
    # Step 1: Create the player at the season level
    player = create_player(session, season_id, first_name, last_name, external_id=external_id)
    # Step 2: Fetch current team data
    team_data = _get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 3: Add player to roster
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    player_entry: dict[str, Any] = {
        "id": player.id,
        "affiliated": False,
        "status": "playing",
        "starting": False,
        "added_at_game_time": False,
    }
    if jersey:
        player_entry["number"] = jersey
    if position:
        player_entry["position"] = position.lower()
    if status:
        # Map UI status values to API status values
        status_map = {"Regular": "playing", "Affiliated": "affiliated"}
        player_entry["status"] = status_map.get(status, status.lower())
        # If status is Affiliated, set affiliated flag
        if status == "Affiliated":
            player_entry["affiliated"] = True
    if designation:
        # Designation is stored as "duty" in the roster
        # Map: "Captain" -> "captain", "Alternate Captain" -> "alternate captain"
        player_entry["duty"] = designation.lower()
    players_roster.append(player_entry)
    roster["players"] = players_roster
    # Step 4: Update team roster
    _update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    # Return the player with roster metadata populated
    if jersey:
        player.number = jersey
    if position:
        player.position = position
    if status:
        player.status = status
    if designation:
        player.designation = designation
    return player


def create_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    position: str | None = None,
) -> Coach:
    """Create a new coach and add to the specified team's roster.

    This function performs two operations: (1) creates the coach at the season level,
    (2) updates the team's roster to include the new coach with position and other metadata.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to add the coach to.
    :param first_name: Coach's first name.
    :param last_name: Coach's last name.
    :param external_id: Optional external identifier for the coach.
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :returns: The created :class:`Coach`.
    :rtype: Coach
    """
    # Step 1: Create the coach at the season level
    coach = create_coach(session, season_id, first_name, last_name, external_id=external_id)
    # Step 2: Fetch current team data
    team_data = _get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 3: Add coach to roster
    roster = current_attrs.get("roster", {})
    coaches_roster = roster.get("coaches", [])
    coach_entry: dict[str, Any] = {"id": coach.id, "status": "coaching"}
    if position:
        coach_entry["position"] = position
    coaches_roster.append(coach_entry)
    roster["coaches"] = coaches_roster
    # Step 4: Update team roster
    _update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    # Return the coach with roster metadata populated
    if position:
        coach.position = position
    coach.status = "coaching"
    return coach
