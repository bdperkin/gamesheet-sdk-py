# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT
# pylint: disable=too-many-lines

"""Player roster operations."""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from gamesheet_sdk.exceptions import GameSheetError
from gamesheet_sdk.roster.helpers import get_team_for_roster_update, update_team_roster
from gamesheet_sdk.roster.models import Player, parse_player
from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response


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
    :returns: The requested Player model instance.
    :rtype: Player
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
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
    :type session: Session
    :param season_id: The season identifier whose players to list.
    :type season_id: str
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        season has no players.
    :rtype: list[Player]
    """
    endpoint = f"/api/seasons/{season_id}/players"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "teams,divisions"},
    )
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
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier whose players to list.
    :type team_id: str
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        team has no players.
    :rtype: list[Player]
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


def _upload_photo(session: Session, photo_path: str) -> str:
    """Upload a photo image and return its URL.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param photo_path: Path to a local photo image file.
    :type photo_path: str
    :returns: The Cloudflare CDN URL for the uploaded photo.
    :rtype: str
    :raises GameSheetError: If the file is not found, is not a valid image, or the upload fails.
    :raises AuthenticationError: If the server returns 401.
    """
    from gamesheet_sdk.shared import upload_image

    return upload_image(session, photo_path, "photo")


def _add_optional_field(attrs: dict[str, Any], key: str, value: Any) -> None:
    """Add a field to attrs dict if value is truthy.

    :param attrs: The attributes dictionary to update.
    :type attrs: dict[str, Any]
    :param key: The attribute key name.
    :type key: str
    :param value: The value to add (only added if truthy).
    :type value: Any
    """
    if value:
        attrs[key] = value


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
    r"""Create a new player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier to create the player in.
    :type season_id: str
    :param first_name: Player's first name.
    :type first_name: str
    :param last_name: Player's last name.
    :type last_name: str
    :param external_id: Optional external identifier for the player.
    :type external_id: str | None
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :type position: str | None
    :param status: Optional status (Regular, Affiliated, etc.).
    :type status: str | None
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :type designation: str | None
    :param team_id: Optional team identifier to associate the player with.
    :type team_id: str | None
    :param biography: Optional biography text.
    :type biography: str | None
    :param height: Optional height (e.g., "6'2\"").
    :type height: str | None
    :param weight: Optional weight (e.g., "185").
    :type weight: str | None
    :param shot_hand: Optional shooting hand (left, right).
    :type shot_hand: str | None
    :param birthdate: Optional birthdate (ISO format: YYYY-MM-DD).
    :type birthdate: str | None
    :param hometown: Optional hometown.
    :type hometown: str | None
    :param country: Optional country code (e.g., "US", "CA").
    :type country: str | None
    :param province: Optional province/state.
    :type province: str | None
    :param drafted_by: Optional drafted by team name.
    :type drafted_by: str | None
    :param committed_to: Optional committed to institution.
    :type committed_to: str | None
    :param photo_path: Optional path to a local photo image file.
    :type photo_path: str | None
    :returns: The newly created Player model instance.
    :rtype: Player
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, or if photo upload fails.
    """
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
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
    attrs = payload["data"]["attributes"]
    # Add optional fields using helper to reduce complexity
    _add_optional_field(attrs, "external_id", external_id)
    _add_optional_field(attrs, "jersey", jersey)
    _add_optional_field(attrs, "position", position)
    _add_optional_field(attrs, "status", status)
    _add_optional_field(attrs, "designation", designation)
    _add_optional_field(attrs, "biography", biography)
    _add_optional_field(attrs, "height", height)
    _add_optional_field(attrs, "weight", weight)
    _add_optional_field(attrs, "shot_hand", shot_hand)
    _add_optional_field(attrs, "birthdate", birthdate)
    _add_optional_field(attrs, "hometown", hometown)
    _add_optional_field(attrs, "country", country)
    _add_optional_field(attrs, "province", province)
    _add_optional_field(attrs, "drafted_by", drafted_by)
    _add_optional_field(attrs, "committed_to", committed_to)
    _add_optional_field(attrs, "photo_url", photo_url)
    if team_id:
        payload["data"]["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


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
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param player_id: The player identifier to retrieve.
    :type player_id: str
    :returns: The :class:`Player` with team roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is not found on the team's roster.
    """
    players = list_team_players(session, season_id, team_id)
    for player in players:
        if player.id == player_id:
            return player
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
    """Build a player roster entry dict for team roster updates.

    :param player_id: The player identifier.
    :type player_id: str
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :type position: str | None
    :param status: Optional status (Regular, Affiliated, etc.).
    :type status: str | None
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :type designation: str | None
    :returns: Dictionary containing roster entry data ready for team roster update.
    :rtype: dict[str, Any]
    """
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
    """Populate player object with roster metadata.

    Mutates the Player object in place to set roster-specific fields.

    :param player: The Player instance to populate.
    :type player: Player
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position.
    :type position: str | None
    :param status: Optional status.
    :type status: str | None
    :param designation: Optional designation.
    :type designation: str | None
    """
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

    This function performs two operations: (1) creates the player at the season level, (2) updates the
    team's roster to include the new player with position and other metadata.  The supplied
    :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to add the player to.
    :type team_id: str
    :param first_name: Player's first name.
    :type first_name: str
    :param last_name: Player's last name.
    :type last_name: str
    :param external_id: Optional external identifier for the player.
    :type external_id: str | None
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :type position: str | None
    :param status: Optional status (Regular, Affiliated, etc.).
    :type status: str | None
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :type designation: str | None
    :param biography: Optional biography text.
    :type biography: str | None
    :param height: Optional height (e.g., "6'2\"").
    :type height: str | None
    :param weight: Optional weight (e.g., "185").
    :type weight: str | None
    :param shot_hand: Optional shooting hand (left, right).
    :type shot_hand: str | None
    :param birthdate: Optional birthdate (ISO format: YYYY-MM-DD).
    :type birthdate: str | None
    :param hometown: Optional hometown.
    :type hometown: str | None
    :param country: Optional country code (e.g., "US", "CA").
    :type country: str | None
    :param province: Optional province/state.
    :type province: str | None
    :param drafted_by: Optional drafted by team name.
    :type drafted_by: str | None
    :param committed_to: Optional committed to institution.
    :type committed_to: str | None
    :param photo_path: Optional path to a local photo image file.
    :type photo_path: str | None
    :returns: The newly created Player model instance with roster metadata populated.
    :rtype: Player
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, or if photo upload fails.
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


def _merge_optional_field(
    attrs: dict[str, Any],
    key: str,
    new_value: Any,
    current_value: Any,
) -> None:
    """Merge an optional field into attrs dict, preferring new value over current.

    :param attrs: The attributes dictionary to update.
    :type attrs: dict[str, Any]
    :param key: The attribute key name.
    :type key: str
    :param new_value: The new value (may be None).
    :type new_value: Any
    :param current_value: The current value from existing record.
    :type current_value: Any
    """
    if new_value is not None:
        attrs[key] = new_value
    elif current_value:
        attrs[key] = current_value


def update_player(
    session: Session,
    season_id: str,
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
    r"""Update an existing player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. At least one field
    must be provided for update.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the player.
    :type season_id: str
    :param player_id: The player identifier to update.
    :type player_id: str
    :param first_name: Optional updated first name.
    :type first_name: str | None
    :param last_name: Optional updated last name.
    :type last_name: str | None
    :param external_id: Optional updated external identifier.
    :type external_id: str | None
    :param biography: Optional updated biography text.
    :type biography: str | None
    :param height: Optional updated height (e.g., "6'2\"").
    :type height: str | None
    :param weight: Optional updated weight (e.g., "185").
    :type weight: str | None
    :param shot_hand: Optional updated shooting hand (left, right).
    :type shot_hand: str | None
    :param birthdate: Optional updated birthdate (ISO format: YYYY-MM-DD).
    :type birthdate: str | None
    :param hometown: Optional updated hometown.
    :type hometown: str | None
    :param country: Optional updated country code (e.g., "US", "CA").
    :type country: str | None
    :param province: Optional updated province/state.
    :type province: str | None
    :param drafted_by: Optional updated drafted by team name.
    :type drafted_by: str | None
    :param committed_to: Optional updated committed to institution.
    :type committed_to: str | None
    :param photo_path: Optional path to a new photo image file.
    :type photo_path: str | None
    :param remove_photo: If True, remove the player's photo.
    :type remove_photo: bool
    :returns: The updated :class:`Player`.
    :rtype: Player
    :raises ValueError: If no fields are provided for update or both photo_path and remove_photo are set.
    """
    if all(
        v is None or v is False
        for v in (
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
            photo_path,
            remove_photo,
        )
    ):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)
    if photo_path and remove_photo:
        msg = "Cannot both upload a photo and remove it"
        raise ValueError(msg)
    # Handle photo upload/removal
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
    # Fetch current player to get all fields
    current_player = get_player(session, season_id, player_id)
    # Build payload with updated values, preserving current for unchanged fields
    payload: dict[str, Any] = {
        "data": {
            "id": player_id,
            "type": "players",
            "attributes": {
                "first_name": first_name if first_name is not None else current_player.first_name,
                "last_name": last_name if last_name is not None else current_player.last_name,
            },
        },
    }
    attrs = payload["data"]["attributes"]
    # Handle optional fields using helper to reduce complexity
    _merge_optional_field(attrs, "external_id", external_id, current_player.external_id)
    _merge_optional_field(attrs, "biography", biography, current_player.biography)
    _merge_optional_field(attrs, "height", height, current_player.height)
    _merge_optional_field(attrs, "weight", weight, current_player.weight)
    _merge_optional_field(attrs, "shot_hand", shot_hand, current_player.shot_hand)
    _merge_optional_field(
        attrs,
        "birthdate",
        birthdate,
        str(current_player.birthdate) if current_player.birthdate else None,
    )
    _merge_optional_field(attrs, "hometown", hometown, current_player.hometown)
    _merge_optional_field(attrs, "country", country, current_player.country)
    _merge_optional_field(attrs, "province", province, current_player.province)
    _merge_optional_field(attrs, "drafted_by", drafted_by, current_player.drafted_by)
    _merge_optional_field(
        attrs,
        "committed_to",
        committed_to,
        current_player.committed_to,
    )
    # Handle photo
    if photo_url:
        attrs["photo_url"] = photo_url
    elif remove_photo:
        attrs["photo_url"] = ""
    elif current_player.photo_url:
        attrs["photo_url"] = current_player.photo_url
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


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
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param player_id: The player identifier to update.
    :type player_id: str
    :param first_name: Optional updated first name.
    :type first_name: str | None
    :param last_name: Optional updated last name.
    :type last_name: str | None
    :param external_id: Optional updated external identifier.
    :type external_id: str | None
    :param biography: Optional updated biography text.
    :type biography: str | None
    :param height: Optional updated height (e.g., "6'2\"").
    :type height: str | None
    :param weight: Optional updated weight (e.g., "185").
    :type weight: str | None
    :param shot_hand: Optional updated shooting hand (left, right).
    :type shot_hand: str | None
    :param birthdate: Optional updated birthdate (ISO format: YYYY-MM-DD).
    :type birthdate: str | None
    :param hometown: Optional updated hometown.
    :type hometown: str | None
    :param country: Optional updated country code (e.g., "US", "CA").
    :type country: str | None
    :param province: Optional updated province/state.
    :type province: str | None
    :param drafted_by: Optional updated drafted by team name.
    :type drafted_by: str | None
    :param committed_to: Optional updated committed to institution.
    :type committed_to: str | None
    :param photo_path: Optional path to a new photo image file.
    :type photo_path: str | None
    :param remove_photo: If True, remove the player's photo.
    :type remove_photo: bool
    :returns: The updated :class:`Player`.
    :rtype: Player
    :raises ValueError: If no fields are provided for update or both photo_path and remove_photo are set.
    """
    if all(
        v is None or v is False
        for v in (
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
            photo_path,
            remove_photo,
        )
    ):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)
    if photo_path and remove_photo:
        msg = "Cannot both upload a photo and remove it"
        raise ValueError(msg)
    # Handle photo upload/removal
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
    # Fetch current player to get all fields
    current_player = get_team_player(session, season_id, team_id, player_id)
    # Build payload with updated values (without "type" field for team context)
    payload: dict[str, Any] = {
        "data": {
            "id": player_id,
            "attributes": {
                "first_name": (first_name if first_name is not None else current_player.first_name),
                "last_name": (last_name if last_name is not None else current_player.last_name),
            },
        },
    }
    attrs = payload["data"]["attributes"]
    # Handle optional fields using helper to reduce complexity
    _merge_optional_field(attrs, "external_id", external_id, current_player.external_id)
    _merge_optional_field(attrs, "biography", biography, current_player.biography)
    _merge_optional_field(attrs, "height", height, current_player.height)
    _merge_optional_field(attrs, "weight", weight, current_player.weight)
    _merge_optional_field(attrs, "shot_hand", shot_hand, current_player.shot_hand)
    _merge_optional_field(
        attrs,
        "birthdate",
        birthdate,
        str(current_player.birthdate) if current_player.birthdate else None,
    )
    _merge_optional_field(attrs, "hometown", hometown, current_player.hometown)
    _merge_optional_field(attrs, "country", country, current_player.country)
    _merge_optional_field(attrs, "province", province, current_player.province)
    _merge_optional_field(attrs, "drafted_by", drafted_by, current_player.drafted_by)
    _merge_optional_field(
        attrs,
        "committed_to",
        committed_to,
        current_player.committed_to,
    )
    # Handle photo
    if photo_url:
        attrs["photo_url"] = photo_url
    elif remove_photo:
        attrs["photo_url"] = ""
    elif current_player.photo_url:
        attrs["photo_url"] = current_player.photo_url
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH team player")
    body: dict[str, Any] = response.json()
    player = parse_player(body["data"])
    # Populate with current roster metadata
    _populate_player_metadata(
        player,
        jersey=getattr(current_player, "jersey", None),
        position=getattr(current_player, "position", None),
        status=getattr(current_player, "status", None),
        designation=getattr(current_player, "designation", None),
    )
    return player


def delete_player(session: Session, season_id: str, player_id: str) -> None:
    """Delete a player from the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the player.
    :type season_id: str
    :param player_id: The player identifier to delete.
    :type player_id: str
    """
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.delete(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "DELETE player")


def unassign_player(
    session: Session,
    season_id: str,
    player_id: str,
    team_id: str,
) -> None:
    """Unassign a player from a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param player_id: The player identifier to unassign.
    :type player_id: str
    :param team_id: The team identifier to unassign the player from.
    :type team_id: str
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
        msg = f"Player {player_id} is not assigned to team {team_id}"
        raise GameSheetError(msg)
    roster["players"] = players_roster
    # Step 3: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        current_attrs,
        current_relationships,
    )


def delete_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
) -> None:
    """Delete a player from a team's roster and the season.

    This function performs two operations: (1) removes the player from the team's roster,
    (2) deletes the player at the season level. The supplied :class:`Session` must already
    carry a bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise
    unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param player_id: The player identifier to delete.
    :type player_id: str
    """
    # Step 1: Remove player from team roster (may not be on this team's roster)
    with suppress(GameSheetError):
        unassign_player(session, season_id, player_id, team_id)
    # Step 2: Delete the player at the season level
    delete_player(session, season_id, player_id)


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
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param player_id: The player identifier to assign.
    :type player_id: str
    :param team_id: The team identifier to assign the player to.
    :type team_id: str
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :type position: str | None
    :param status: Optional status (Regular, Affiliated, etc.).
    :type status: str | None
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :type designation: str | None
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is already assigned to the team.
    :raises AuthenticationError: If the server returns 401.
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
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        current_attrs,
        current_relationships,
    )
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


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
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to assign the player to.
    :type team_id: str
    :param player_id: The player identifier to assign.
    :type player_id: str
    :param jersey: Optional jersey number.
    :type jersey: str | None
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :type position: str | None
    :param status: Optional status (Regular, Affiliated, etc.).
    :type status: str | None
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :type designation: str | None
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is already assigned to the team.
    :raises AuthenticationError: If the server returns 401.
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
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to unassign the player from.
    :type team_id: str
    :param player_id: The player identifier to unassign.
    :type player_id: str
    """
    unassign_player(session, season_id, player_id, team_id)


def get_player_penalty_report(
    session: Session,
    season_id: str,
    player_id: str,
) -> dict[str, Any]:
    """Fetch penalty report for a player.

    First retrieves the player to get their external_id, then fetches the penalty report from the BFF API. The
    supplied :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param player_id: The player identifier.
    :type player_id: str
    :returns: Penalty report data including player_games, player_penalties, rostered_players, and
        season_players.
    :rtype: dict[str, Any]
    """
    player = get_player(session, season_id, player_id)
    external_id = player.external_id
    bff_url = f"https://bff-dashboard-api-awy26srzoa-nn.a.run.app/reports/player-penalty-report/{external_id}"
    response = session.get(bff_url)
    handle_response(response, bff_url, "GET player penalty report")
    body: dict[str, Any] = response.json()
    if body.get("status") != "success":
        status = body.get("status")
        msg = f"Penalty report API returned status: {status}"
        raise GameSheetError(msg)
    data: dict[str, Any] = body["data"]
    return data
