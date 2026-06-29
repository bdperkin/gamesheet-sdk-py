# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared helper functions for roster operations."""

from __future__ import annotations

from typing import Any

from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response


def get_team_for_roster_update(
    session: Session,
    season_id: str,
    team_id: str,
) -> dict[str, Any]:
    """Fetch team data for roster update.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :returns: Dictionary containing the full team JSON:API response with data, attributes, and relationships.
    :rtype: dict[str, Any]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
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

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param roster: The updated roster dict containing players and coaches arrays.
    :type roster: dict[str, Any]
    :param current_attrs: Current team attributes to preserve unchanged fields.
    :type current_attrs: dict[str, Any]
    :param current_relationships: Current team relationships to preserve.
    :type current_relationships: dict[str, Any]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
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
