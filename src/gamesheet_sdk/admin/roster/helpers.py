# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared helper functions for roster operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common import errors
from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response, upload_image

if TYPE_CHECKING:
    from gamesheet_sdk.admin.roster.models import Player
    from gamesheet_sdk.common.session import Session


def _upload_photo(session: Session, photo_path: str) -> str:
    """Upload a photo image and return its URL.

    Args:
        session (Session): An authenticated :class:`Session`.
        photo_path (str): Path to a local photo image file.

    Returns:
        str: The Cloudflare CDN URL for the uploaded photo.

    """
    return upload_image(session, photo_path, "photo")


def _prepare_player_update(
    session: Session,
    *values: object,
    photo_path: str | None = None,
    remove_photo: bool = False,
) -> str | None:
    """Validate player update arguments and upload photo if provided.

    Args:
        session (Session): An authenticated :class:`Session`.
        *values (object): Update field values to check.
        photo_path (str | None): Optional local photo image file path.
        remove_photo (bool): If True, indicates photo removal.

    Returns:
        str | None: Uploaded photo CDN URL if photo_path was provided, otherwise None.

    Raises:
        ValueError: If no fields are provided for update or both photo_path and remove_photo are set.

    """
    if all(v is None or v is False for v in (*values, photo_path, remove_photo)):
        raise ValueError(errors.ERROR_MSG_AT_LEAST_ONE_FIELD)

    if photo_path and remove_photo:
        raise ValueError(errors.ERROR_MSG_CANNOT_UPLOAD_AND_REMOVE_PHOTO)

    if photo_path:
        return _upload_photo(session, photo_path)

    return None


def _add_optional_field(attrs: dict[str, Any], key: str, value: object) -> None:
    """Add a field to attrs dict if value is truthy.

    Args:
        attrs (dict[str, Any]): The attributes dictionary to update.
        key (str): The attribute key name.
        value (Any): The value to add (only added if truthy).

    """
    if value:
        attrs[key] = value


def _merge_optional_field(
    attrs: dict[str, Any],
    key: str,
    new_value: object,
    current_value: object,
) -> None:
    """Merge an optional field into attrs dict, preferring new value over current.

    Args:
        attrs (dict[str, Any]): The attributes dictionary to update.
        key (str): The attribute key name.
        new_value (Any): The new value (may be None).
        current_value (Any): The current value from existing record.

    """
    if new_value is not None:
        attrs[key] = new_value
    elif current_value:
        attrs[key] = current_value


def _build_player_update_payload(
    player_id: str,
    current_player: Player,
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
    photo_url: str | None = None,
    remove_photo: bool = False,
    include_type: bool = True,
) -> dict[str, Any]:
    """Build JSON:API payload for updating a player.

    Args:
        player_id (str): The player identifier.
        current_player (Player): Existing player model instance.
        first_name (str | None): Optional updated first name.
        last_name (str | None): Optional updated last name.
        external_id (str | None): Optional updated external identifier.
        biography (str | None): Optional updated biography text.
        height (str | None): Optional updated height.
        weight (str | None): Optional updated weight.
        shot_hand (str | None): Optional updated shooting hand.
        birthdate (str | None): Optional updated birthdate.
        hometown (str | None): Optional updated hometown.
        country (str | None): Optional updated country.
        province (str | None): Optional updated province.
        drafted_by (str | None): Optional updated drafted by team.
        committed_to (str | None): Optional updated committed to institution.
        photo_url (str | None): Optional photo CDN URL.
        remove_photo (bool): Whether to remove the photo.
        include_type (bool): Whether to include 'type': 'players' in data dict.

    Returns:
        dict[str, Any]: JSON:API payload dict ready for PATCH request.

    """
    data_dict: dict[str, Any] = {
        "id": player_id,
        "attributes": {
            "first_name": first_name if first_name is not None else current_player.first_name,
            "last_name": last_name if last_name is not None else current_player.last_name,
        },
    }
    if include_type:
        data_dict["type"] = "players"

    attrs = data_dict["attributes"]
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

    if photo_url:
        attrs["photo_url"] = photo_url
    elif remove_photo:
        attrs["photo_url"] = ""
    elif current_player.photo_url:
        attrs["photo_url"] = current_player.photo_url

    return {"data": data_dict}


def _patch_player_record(
    session: Session,
    season_id: str,
    player_id: str,
    payload: dict[str, Any],
    context: str = "PATCH player",
) -> dict[str, Any]:
    """Execute PATCH request to update a player record.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        player_id (str): The player identifier.
        payload (dict[str, Any]): JSON:API payload dict.
        context (str): Context description for error handling.

    Returns:
        dict[str, Any]: JSON:API resource object for the updated player from response 'data'.

    """
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, context)
    body: dict[str, Any] = response.json()
    data: dict[str, Any] = body["data"]
    return data


def _build_player_roster_entry(
    player_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> dict[str, Any]:
    """Build a player roster entry dict for team roster updates.

    Args:
        player_id (str): The player identifier.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position (Forward, Defence, Goalie, etc.).
        status (str | None): Optional status (Regular, Affiliated, etc.).
        designation (str | None): Optional designation (Captain, Alternate Captain, etc.).

    Returns:
        dict[str, Any]: Dictionary containing roster entry data ready for team roster update.

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

    Args:
        player (Player): The Player instance to populate.
        jersey (str | None): Optional jersey number.
        position (str | None): Optional position.
        status (str | None): Optional status.
        designation (str | None): Optional designation.

    """
    if jersey:
        player.number = jersey

    if position:
        player.position = position

    if status:
        player.status = status

    if designation:
        player.designation = designation


def get_team_for_roster_update(
    session: Session,
    season_id: str,
    team_id: str,
) -> dict[str, Any]:
    """Fetch team data for roster update.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.

    Returns:
        dict[str, Any]: Dictionary containing the full team JSON:API response with data, attributes, and
            relationships.

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


def update_team_roster(
    session: Session,
    season_id: str,
    team_id: str,
    roster: dict[str, Any],
    current_attrs: dict[str, Any],
    current_relationships: dict[str, Any],
) -> None:
    """Update team's roster via PATCH to teams-v2 endpoint.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        roster (dict[str, Any]): The updated roster dict containing players and coaches arrays.
        current_attrs (dict[str, Any]): Current team attributes to preserve unchanged fields.
        current_relationships (dict[str, Any]): Current team relationships to preserve.

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
