# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Response payload builders for tests."""

from __future__ import annotations

from typing import Any

from tests.helpers.constants import (
    ASSOCIATION_ID,
    COACH_ID_PRIMARY,
    DEFAULT_COACH_FIRST_NAME,
    DEFAULT_COACH_LAST_NAME,
    DEFAULT_PLAYER_FIRST_NAME,
    DEFAULT_PLAYER_LAST_NAME,
    INVITATION_CODE,
    INVITATION_ID,
    LEAGUE_ID,
    PLAYER_ID,
    SEASON_ID,
    TEAM_ID,
    TIMESTAMP_2024_01_01,
)


def jsonapi_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a JSON:API response with data array.

    Args:
        rows (list[dict[str, Any]]): List of JSON:API resource objects

    Returns:
        dict[str, Any]: API response dict with {"data": [...]}

    Examples:
        >>> jsonapi_payload([{"type": "associations", "id": "1", "attributes": {...}}])
        {'data': [{'type': 'associations', 'id': '1', 'attributes': {...}}]}

    """
    return {"data": rows}


def jsonapi_detail_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON:API response with single data object.

    Args:
        data (dict[str, Any]): Single JSON:API resource object

    Returns:
        dict[str, Any]: API response dict with {"data": {...}}

    Examples:
        >>> jsonapi_detail_payload({"type": "associations", "id": "1", "attributes": {...}})
        {'data': {'type': 'associations', 'id': '1', 'attributes': {...}}}

    """
    return {"data": data}


def roster_player_payload(
    player_id: str = PLAYER_ID,
    season_id: str = SEASON_ID,
    *,
    first_name: str = DEFAULT_PLAYER_FIRST_NAME,
    last_name: str = DEFAULT_PLAYER_LAST_NAME,
    external_id: str | None = None,
) -> dict[str, Any]:
    """Build a JSON:API player resource object for roster tests.

    Args:
        player_id (str): Player ID
        season_id (str): Season ID
        first_name (str): First name (defaults to "John")
        last_name (str): Last name (default=s to "Doe")
        external_id (str | None): External ID (optional, defaults to empty string)

    Returns:
        dict[str, Any]: API player resource object
    Examples:
        >>> roster_player_payload()
        {'type': 'players', 'id': '8043169', 'attributes': {...}}

    """
    return {
        "type": "players",
        "id": player_id,
        "attributes": {
            "first_name": first_name,
            "last_name": last_name,
            "jersey": "99",
            "position": "centre",
            "status": "playing",
            "designation": "",
            "affiliated": False,
            "added_at_game_time": False,
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "birthdate": "",
            "hometown": "",
            "country": "",
            "province": "",
            "drafted_by": "",
            "committed_to": "",
            "photo_url": "",
            "external_id": external_id if external_id is not None else "",
            "created_at": TIMESTAMP_2024_01_01,
            "updated_at": TIMESTAMP_2024_01_01,
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": season_id,
                },
            },
        },
    }


def roster_coach_payload(
    coach_id: str = COACH_ID_PRIMARY,
    season_id: str = SEASON_ID,
    *,
    first_name: str = DEFAULT_COACH_FIRST_NAME,
    last_name: str = DEFAULT_COACH_LAST_NAME,
    external_id: str | None = None,
) -> dict[str, Any]:
    """Build a JSON:API coach resource object for roster tests.

    Args:
        coach_id (str): Coach ID
        season_id (str): Season ID
        first_name (str): First name (defaults to "Coach")
        last_name (str): Last name (default=s to "Smith")
        external_id (str | None): External ID (optional, defaults to empty string)

    Returns:
        dict[str, Any]: API coach resource object
    Examples:
        >>> roster_coach_payload()
        {'type': 'coaches', 'id': '1879938', 'attributes': {...}}

    """
    return {
        "type": "coaches",
        "id": coach_id,
        "attributes": {
            "first_name": first_name,
            "last_name": last_name,
            "position": "head_coach",
            "external_id": external_id if external_id is not None else "",
            "created_at": TIMESTAMP_2024_01_01,
            "updated_at": TIMESTAMP_2024_01_01,
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": season_id,
                },
            },
        },
    }


def association_payload(
    association_id: str = ASSOCIATION_ID,
    name: str = "Test Association",
) -> dict[str, Any]:
    """Build a JSON:API association resource object.

    Args:
        association_id (str): Association ID
        name (str): Association name

    Returns:
        dict[str, Any]: API association resource object
    Examples:
        >>> association_payload("1", "Hockey Canada")
        {'type': 'associations', 'id': '1', 'attributes': {'name': 'Hockey Canada'}}

    """
    return {
        "type": "associations",
        "id": association_id,
        "attributes": {
            "name": name,
        },
    }


def league_payload(
    league_id: str = LEAGUE_ID,
    name: str = "Test League",
    association_id: str = ASSOCIATION_ID,
) -> dict[str, Any]:
    """Build a JSON:API league resource object.

    Args:
        league_id (str): League ID
        name (str): League name
        association_id (str): Parent association ID

    Returns:
        dict[str, Any]: API league resource object

    """
    return {
        "type": "leagues",
        "id": league_id,
        "attributes": {
            "name": name,
        },
        "relationships": {
            "association": {
                "data": {
                    "type": "associations",
                    "id": association_id,
                },
            },
        },
    }


def team_payload(
    team_id: str = TEAM_ID,
    *,
    players: list[dict[str, Any]] | None = None,
    coaches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a JSON:API team resource object for roster tests.

    Args:
        team_id (str): Team ID
        players (list[dict[str, Any]] | None): List of player roster entries (defaults to empty list)
        coaches (list[dict[str, Any]] | None): List of coach roster entries (defaults to empty list)

    Returns:
        dict[str, Any]: API team resource object with roster
    Examples:
        >>> team_payload()
        {'type': 'teams', 'id': '12345', 'attributes': {...}, 'relationships': {...}}
        >>> team_payload(players=[{"id": "123", "status": "playing"}])
        {'type': 'teams', 'id': '12345', 'attributes': {'roster': {'players': [...], 'coaches': []}}}

    """
    return {
        "type": "teams",
        "id": team_id,
        "attributes": {
            "title": "Test Team",
            "external_id": "test-123",
            "roster": {
                "players": players or [],
                "coaches": coaches or [],
            },
            "data": {},
            "logo_url": "",
        },
        "relationships": {
            "division": {"data": {"id": "999", "type": "divisions"}},
        },
    }


def invitation_relationship_and_included(
    invitation_id: str = INVITATION_ID,
    code: str = INVITATION_CODE,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build invitation relationship and included data for team responses.

    Returns a tuple of (relationship_data, included_array) that can be used to add invitation data to team
    payloads.

    Args:
        invitation_id (str): Invitation ID
        code (str): Invitation code

    Returns:
        tuple[dict[str, Any], list[dict[str, Any]]]: Tuple of (invitations relationship dict, included array)

    Examples:
        >>> rel, inc = invitation_relationship_and_included("inv-123", "RAPTORS2024")
        >>> # rel = {"invitations": {"data": [{"type": "invitations", "id": "inv-123"}]}}
        >>> # inc = [{"type": "invitations", "id": "inv-123", "attributes": {"code": "RAPTORS2024"}}]

    """
    relationship = {
        "invitations": {
            "data": [
                {
                    "type": "invitations",
                    "id": invitation_id,
                },
            ],
        },
    }
    included = [
        {
            "type": "invitations",
            "id": invitation_id,
            "attributes": {
                "code": code,
            },
        },
    ]
    return relationship, included
