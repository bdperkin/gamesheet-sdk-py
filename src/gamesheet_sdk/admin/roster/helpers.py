# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared helper functions for roster operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


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

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: For any other non-2xx response.
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

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: For any other non-2xx response.
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
