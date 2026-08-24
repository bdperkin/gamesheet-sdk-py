# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Player roster operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.roster.helpers import (
    _add_optional_field,
    _build_player_roster_entry,
    _build_player_update_payload,
    _merge_optional_field,
    _patch_player_record,
    _populate_player_metadata,
    _prepare_player_update,
    _upload_photo,
    get_team_for_roster_update,
    update_team_roster,
)
from gamesheet_sdk.admin.roster.models import Player, parse_player
from gamesheet_sdk.common import errors
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def get_player(session: Session, season_id: str, player_id: str) -> Player:
    """Get a single player by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        player_id (str): The player identifier to retrieve.

    Returns:
        Player: The requested Player model instance.

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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier whose players to list.

    Returns:
        list[Player]: A list of :class:`Player`, in the order the server returned them. The list may be empty
            if the season has no players.

    """
    endpoint = f"/api/seasons/{season_id}/players"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "teams,divisions"},
    )
    handle_response(response, endpoint, "GET players")
    body: dict[str, Any] = response.json()
    return [parse_player(item) for item in body.get("data", [])]


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier to create the player in.
        first_name (str): Player's first name.
        last_name (str): Player's last name.
        external_id (str | None): Optional external identifier for the player.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position (Forward, Defence, Goalie, etc.).
        status (str | None): Optional status (Regular, Affiliated, etc.).
        designation (str | None): Optional designation (Captain, Alternate Captain, etc.).
        team_id (str | None): Optional team identifier to associate the player with.
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
        Player: The newly created Player model instance.

    """
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)

    endpoint = f"/api/seasons/{season_id}/players"
    data: dict[str, Any] = {
        "type": "players",
        "attributes": {
            "first_name": first_name,
            "last_name": last_name,
        },
    }
    attrs = data["attributes"]
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
        data["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }

    payload: dict[str, Any] = {"data": data}

    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the player.
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
    # pylint: disable=duplicate-code
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
    # pylint: enable=duplicate-code

    current_player = get_player(session, season_id, player_id)
    # pylint: disable=duplicate-code
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
        include_type=True,
    )
    # pylint: enable=duplicate-code
    data = _patch_player_record(session, season_id, player_id, payload, "PATCH player")
    return parse_player(data)


def delete_player(session: Session, season_id: str, player_id: str) -> None:
    """Delete a player from the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the player.
        player_id (str): The player identifier to delete.

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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        player_id (str): The player identifier to unassign.
        team_id (str): The team identifier to unassign the player from.

    Raises:
        GameSheetError: If the player is not assigned to the team.

    """
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    original_count = len(players_roster)
    players_roster = [p for p in players_roster if p.get("id") != player_id]
    if len(players_roster) == original_count:
        msg = f"Player {player_id} is not assigned to team {team_id}"
        raise GameSheetError(msg)

    roster["players"] = players_roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        current_attrs,
        current_relationships,
    )


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        player_id (str): The player identifier to assign.
        team_id (str): The team identifier to assign the player to.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position (Forward, Defence, Goalie, etc.).
        status (str | None): Optional status (Regular, Affiliated, etc.).
        designation (str | None): Optional designation (Captain, Alternate Captain, etc.).

    Returns:
        Player: The :class:`Player` with roster metadata populated.

    Raises:
        GameSheetError: If the player is already assigned to the team.

    """
    player = get_player(session, season_id, player_id)
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
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


def get_player_penalty_report(
    session: Session,
    season_id: str,
    player_id: str,
) -> dict[str, Any]:
    """Fetch penalty report for a player.

    First retrieves the player to get their external_id, then fetches the penalty report from the BFF API. The
    supplied :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        player_id (str): The player identifier.

    Returns:
        dict[str, Any]: Penalty report data including player_games, player_penalties, rostered_players, and
            season_players.

    Raises:
        GameSheetError: If the penalty report API returns a non-success status.

    """
    player = get_player(session, season_id, player_id)
    external_id = player.external_id
    bff_url = f"https://bff-dashboard-api-awy26srzoa-nn.a.run.app/reports/player-penalty-report/{external_id}"
    response = session.get(bff_url)
    handle_response(response, bff_url, "GET player penalty report")
    body: dict[str, Any] = response.json()
    if body.get("status") != "success":
        status = body.get("status")
        msg = errors.ERROR_MSG_PENALTY_REPORT_API_STATUS.format(status=status)
        raise GameSheetError(msg)

    data: dict[str, Any] = body["data"]
    return data


__all__ = [
    "_add_optional_field",
    "_merge_optional_field",
    "_upload_photo",
    "assign_player",
    "create_player",
    "delete_player",
    "get_player",
    "get_player_penalty_report",
    "list_players",
    "unassign_player",
    "update_player",
]
