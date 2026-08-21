# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Team-scoped player roster operations."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.roster import players
from gamesheet_sdk.admin.roster.helpers import (
    _build_player_roster_entry,
    _build_player_update_payload,
    _patch_player_record,
    _populate_player_metadata,
    _prepare_player_update,
    _upload_photo,
    get_team_for_roster_update,
    update_team_roster,
)
from gamesheet_sdk.admin.roster.models import Player, parse_player
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def list_team_players(session: Session, season_id: str, team_id: str) -> list[Player]:
    """Return every player for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier whose players to list.

    Returns:
        list[Player]: A list of :class:`Player`, in the order the server returned them. The list may be empty
            if the team has no players.

    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "players,coaches"},
    )
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
    team_players = []
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

        team_players.append(player)

    return team_players


def get_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
) -> Player:
    """Get a single player from a team's roster.

    This function retrieves team roster metadata (number, position, status, etc.) that is only available in
    the team context, unlike :func:`get_player` which fetches from the season-level players endpoint without
    roster metadata. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        player_id (str): The player identifier to retrieve.

    Returns:
        Player: The :class:`Player` with team roster metadata populated.

    Raises:
        GameSheetError: If the player is not found on the team's roster.

    """
    team_players = list_team_players(session, season_id, team_id)
    for player in team_players:
        if player.id == player_id:
            return player

    msg = f"Player {player_id} not found on team {team_id}"
    raise GameSheetError(msg)


def create_team_player(  # noqa: C901
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
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
) -> Player:
    r"""Create a new player and add to the specified team's roster.

    This function performs two operations: (1) creates the player at the season level, (2) updates the team's
    roster to include the new player with position and other metadata. The supplied :class:`Session` must
    already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise
    unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to add the player to.
        first_name (str): Player's first name.
        last_name (str): Player's last name.
        external_id (str | None): Optional external identifier for the player.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position (Forward, Defence, Goalie, etc.).
        status (str | None): Optional status (Regular, Affiliated, etc.).
        designation (str | None): Optional designation (Captain, Alternate Captain, etc.).
        biography (str | None): Optional biography text.
        height (str | None): Optional height (e.g., "6'2\"").
        weight (str | None): Optional weight (e.g., "185").
        shot_hand (str | None): Optional shooting hand (left, right).
        birthdate (str | None): Optional birthdate (ISO format: YYYY-MM-DD).
        hometown (str | None): Optional hometown.
        country (str | None): Optional country code (e.g., "US", "CA").
        province (str | None): Optional province/state.
        drafted_by (str | None): Optional drafted by team name.
        committed_to (str | None): Optional committed to institution.
        photo_path (str | None): Optional path to a local photo image file.

    Returns:
        Player: The newly created Player model instance with roster metadata populated.

    """
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)

    # Step 1: Create the player at the season level (without "type" field for team context)
    endpoint = f"/api/seasons/{season_id}/players"
    payload: dict[str, Any] = {
        "data": {"attributes": {"first_name": first_name, "last_name": last_name}},
    }
    attrs = payload["data"]["attributes"]
    if external_id:
        attrs["external_id"] = external_id

    if biography:
        attrs["biography"] = biography

    if height:
        attrs["height"] = height

    if weight:
        attrs["weight"] = weight

    if shot_hand:
        attrs["shot_hand"] = shot_hand

    if birthdate:
        attrs["birthdate"] = birthdate

    if hometown:
        attrs["hometown"] = hometown

    if country:
        attrs["country"] = country

    if province:
        attrs["province"] = province

    if drafted_by:
        attrs["drafted_by"] = drafted_by

    if committed_to:
        attrs["committed_to"] = committed_to

    if photo_url:
        attrs["photo_url"] = photo_url

    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    player = parse_player(response.json()["data"])

    # Step 2: Fetch current team data and update roster
    team_data = get_team_for_roster_update(session, season_id, team_id)
    roster = team_data.get("data", {}).get("attributes", {}).get("roster", {})
    players_roster = roster.get("players", [])
    players_roster.append(
        _build_player_roster_entry(
            player.id,
            jersey=jersey,
            position=position,
            status=status,
            designation=designation,
        ),
    )
    roster["players"] = players_roster

    # Step 3: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        team_data.get("data", {}).get("attributes", {}),
        team_data.get("data", {}).get("relationships", {}),
    )
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


def update_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    external_id: str | None = None,
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
    remove_photo: bool = False,
) -> Player:
    r"""Update a player for a specific team.

    This function updates the player at the season level. The supplied :class:`Session` must already carry a
    bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will
    401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        player_id (str): The player identifier to update.
        first_name (str | None): Optional updated first name.
        last_name (str | None): Optional updated last name.
        external_id (str | None): Optional updated external identifier.
        biography (str | None): Optional updated biography text.
        height (str | None): Optional updated height (e.g., "6'2\"").
        weight (str | None): Optional updated weight (e.g., "185").
        shot_hand (str | None): Optional updated shooting hand (left, right).
        birthdate (str | None): Optional updated birthdate (ISO format: YYYY-MM-DD).
        hometown (str | None): Optional updated hometown.
        country (str | None): Optional updated country code (e.g., "US", "CA").
        province (str | None): Optional updated province/state.
        drafted_by (str | None): Optional updated drafted by team name.
        committed_to (str | None): Optional updated committed to institution.
        photo_path (str | None): Optional path to a new photo image file.
        remove_photo (bool): If True, remove the player's photo.

    Returns:
        Player: The updated :class:`Player`.

    """
    photo_url = _prepare_player_update(
        session,
        first_name,
        last_name,
        external_id,
        biography,
        height,
        weight,
        shot_hand,
        birthdate,
        hometown,
        country,
        province,
        drafted_by,
        committed_to,
        photo_path=photo_path,
        remove_photo=remove_photo,
    )

    # Fetch current player to get all fields
    current_player = get_team_player(session, season_id, team_id, player_id)

    # Build payload with updated values (without "type" field for team context)
    payload = _build_player_update_payload(
        player_id,
        current_player,
        first_name=first_name,
        last_name=last_name,
        external_id=external_id,
        biography=biography,
        height=height,
        weight=weight,
        shot_hand=shot_hand,
        birthdate=birthdate,
        hometown=hometown,
        country=country,
        province=province,
        drafted_by=drafted_by,
        committed_to=committed_to,
        photo_url=photo_url,
        remove_photo=remove_photo,
        include_type=False,
    )
    data = _patch_player_record(session, season_id, player_id, payload, "PATCH team player")
    player = parse_player(data)

    # Populate with current roster metadata
    _populate_player_metadata(
        player,
        jersey=getattr(current_player, "jersey", None),
        position=getattr(current_player, "position", None),
        status=getattr(current_player, "status", None),
        designation=getattr(current_player, "designation", None),
    )
    return player


def delete_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
) -> None:
    """Delete a player from a team's roster and the season.

    This function performs two operations: (1) removes the player from the team's roster,
    (2) deletes the player at the season level. The supplied :class:`Session` must already
    carry a bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated
    and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        player_id (str): The player identifier to delete.

    """
    # Step 1: Remove player from team roster (may not be on this team's roster)
    with suppress(GameSheetError):
        players.unassign_player(session, season_id, player_id, team_id)

    # Step 2: Delete the player at the season level
    players.delete_player(session, season_id, player_id)


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to assign the player to.
        player_id (str): The player identifier to assign.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position (Forward, Defence, Goalie, etc.).
        status (str | None): Optional status (Regular, Affiliated, etc.).
        designation (str | None): Optional designation (Captain, Alternate Captain, etc.).

    Returns:
        Player: The :class:`Player` with roster metadata populated.

    """
    return players.assign_player(
        session,
        season_id,
        player_id,
        team_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )


def unassign_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
) -> None:
    """Unassign a player from a team's roster (team-scoped alias).

    This is an alias for :func:`unassign_player` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to unassign the player from.
        player_id (str): The player identifier to unassign.

    """
    players.unassign_player(session, season_id, player_id, team_id)


__all__ = [
    "assign_team_player",
    "create_team_player",
    "delete_team_player",
    "get_team_player",
    "list_team_players",
    "unassign_team_player",
    "update_team_player",
]
