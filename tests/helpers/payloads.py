"""Response payload builders for tests."""

from __future__ import annotations

from typing import Any


def jsonapi_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a JSON:API response with data array.

    Args:
        rows: List of JSON:API resource objects

    Returns:
        JSON:API response dict with {"data": [...]}

    Example:
        >>> jsonapi_payload([{"type": "associations", "id": "1", "attributes": {...}}])
        {'data': [{'type': 'associations', 'id': '1', 'attributes': {...}}]}
    """
    return {"data": rows}


def jsonapi_detail_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON:API response with single data object.

    Args:
        data: Single JSON:API resource object

    Returns:
        JSON:API response dict with {"data": {...}}

    Example:
        >>> jsonapi_detail_payload({"type": "associations", "id": "1", "attributes": {...}})
        {'data': {'type': 'associations', 'id': '1', 'attributes': {...}}}
    """
    return {"data": data}


def bff_payload(items: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    """Build a BFF API successful response.

    Args:
        items: List of items or single item for the response

    Returns:
        BFF response dict with {"status": "success", "data": ...}

    Example:
        >>> bff_payload([{"id": 1, "name": "Test"}])
        {'status': 'success', 'data': [{'id': 1, 'name': 'Test'}]}
    """
    return {"status": "success", "data": items}


def roster_player_payload(
    player_id: str = "8043169",
    season_id: str = "15020",
) -> dict[str, Any]:
    """Build a JSON:API player resource object for roster tests.

    Args:
        player_id: Player ID
        season_id: Season ID

    Returns:
        JSON:API player resource object

    Example:
        >>> roster_player_payload()
        {'type': 'players', 'id': '8043169', 'attributes': {...}, 'relationships': {...}}
    """
    return {
        "type": "players",
        "id": player_id,
        "attributes": {
            "external_id": "BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
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
    coach_id: str = "1868550",
    season_id: str = "15020",
    external_id: str | None = "530b7441-1db6-437e-8e5f-777ab3f6cd6c",
) -> dict[str, Any]:
    """Build a JSON:API coach resource object for roster tests.

    Args:
        coach_id: Coach ID
        season_id: Season ID
        external_id: External ID (None for no external ID)

    Returns:
        JSON:API coach resource object

    Example:
        >>> roster_coach_payload()
        {'type': 'coaches', 'id': '1868550', 'attributes': {...}, 'relationships': {...}}
    """
    return {
        "type": "coaches",
        "id": coach_id,
        "attributes": {
            "external_id": external_id,
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
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
