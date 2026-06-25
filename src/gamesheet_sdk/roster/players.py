"""Player roster operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.roster.helpers import get_team_for_roster_update, update_team_roster
from gamesheet_sdk.roster.models import Player, parse_player
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session


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
    return parse_player(body["data"])


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
    all_players = [parse_player(item) for item in body.get("data", [])]
    return all_players


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
        player = parse_player(player_data)
        if player_id in roster_metadata:
            metadata = roster_metadata[player_id]
            player.number = metadata.get("number")
            player.position = metadata.get("position")
            player.duty = metadata.get("duty")
            # designation is stored as "duty" in the roster
            # Map back: "captain" -> "Captain", "alternate_captain" -> "Alternate Captain"
            if player.duty:
                player.designation = player.duty.replace("_", " ").title()
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
    return parse_player(body["data"])


def get_team_player(session: Session, season_id: str, team_id: str, player_id: str) -> Player:
    """Get a single player from a team's roster.

    This function retrieves team roster metadata (number, position, status, etc.) that is only available in
    the team context, unlike :func:`get_player` which fetches from the season-level players endpoint without
    roster metadata.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :param player_id: The player identifier to retrieve.
    :returns: The :class:`Player` with team roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is not found on the team's roster.
    """
    players = list_team_players(session, season_id, team_id)
    for player in players:
        if player.id == player_id:
            return player
    from gamesheet_sdk.exceptions import GameSheetError

    msg = f"Player {player_id} not found on team {team_id}"
    raise GameSheetError(msg)


def _build_player_roster_entry(
    player_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> dict[str, Any]:
    """Build a player roster entry dict for team roster updates."""
    entry: dict[str, Any] = {
        "id": player_id,
        "affiliated": False,
        "status": "playing",
        "starting": False,
        "added_at_game_time": False,
    }
    if jersey:
        entry["number"] = jersey
    if position:
        entry["position"] = position.lower()
    if status:
        status_map = {"Regular": "playing", "Affiliated": "affiliated"}
        entry["status"] = status_map.get(status, status.lower())
        if status == "Affiliated":
            entry["affiliated"] = True
    if designation:
        entry["duty"] = designation.lower().replace(" ", "_")
    return entry


def _populate_player_metadata(
    player: Player,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> None:
    """Populate player object with roster metadata."""
    if jersey:
        player.number = jersey
    if position:
        player.position = position
    if status:
        player.status = status
    if designation:
        player.designation = designation


def create_team_player(
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
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 3: Add player to roster
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    player_entry = _build_player_roster_entry(
        player.id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    players_roster.append(player_entry)
    roster["players"] = players_roster
    # Step 4: Update team roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


def assign_player(
    session: Session,
    season_id: str,
    player_id: str,
    team_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> Player:
    """Assign an existing player to a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param player_id: The player identifier to assign.
    :param team_id: The team identifier to assign the player to.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is already assigned to the team.
    """
    player = get_player(session, season_id, player_id)
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    # Check if player is already on the roster
    for existing_player in players_roster:
        if existing_player.get("id") == player_id:
            from gamesheet_sdk.exceptions import GameSheetError

            msg = f"Player {player_id} is already assigned to team {team_id}"
            raise GameSheetError(msg)
    player_entry = _build_player_roster_entry(
        player_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    players_roster.append(player_entry)
    roster["players"] = players_roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


def unassign_player(session: Session, season_id: str, player_id: str, team_id: str) -> None:
    """Unassign a player from a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param player_id: The player identifier to unassign.
    :param team_id: The team identifier to unassign the player from.
    :raises GameSheetError: If the player is not assigned to the team.
    """
    # Step 1: Fetch current team data
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 2: Remove player from roster
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    # Find and remove the player
    original_count = len(players_roster)
    players_roster = [p for p in players_roster if p.get("id") != player_id]
    if len(players_roster) == original_count:
        from gamesheet_sdk.exceptions import GameSheetError

        msg = f"Player {player_id} is not assigned to team {team_id}"
        raise GameSheetError(msg)
    roster["players"] = players_roster
    # Step 3: Update team roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)


def assign_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> Player:
    """Assign an existing player to a team's roster (team-scoped alias).

    This is an alias for :func:`assign_player` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to assign the player to.
    :param player_id: The player identifier to assign.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    """
    return assign_player(
        session,
        season_id,
        player_id,
        team_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )


def unassign_team_player(session: Session, season_id: str, team_id: str, player_id: str) -> None:
    """Unassign a player from a team's roster (team-scoped alias).

    This is an alias for :func:`unassign_player` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to unassign the player from.
    :param player_id: The player identifier to unassign.
    """
    unassign_player(session, season_id, player_id, team_id)
