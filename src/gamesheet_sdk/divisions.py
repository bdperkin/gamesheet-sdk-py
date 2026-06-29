# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet divisions: organizational groupings within a season.

A division is a grouping of teams within a season (e.g., "U13 AAA", "Bantam A", etc.). Each division belongs
to exactly one season. The dashboard displays divisions after navigating into a season view. This module talks
to the GameSheet JSON:API at ``/api/divisions?season_id={season_id}`` directly with the lightweight
:class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a bearer token has been
obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage state via
:func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import (
    JSONAPI_HEADERS,
    handle_response,
    parse_jsonapi_resource,
)
from gamesheet_sdk.shared.jsonapi import (
    build_invitation_code_lookup,
    get_invitation_code_from_relationship,
)
from gamesheet_sdk.teams import Team

_ENDPOINT = "/api/divisions"


class Division(BaseModel):
    """A single division.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/divisions?season_id={id}`` to a flat
    typed model.

    :var id: Division identifier (string in JSON:API).
    :var season_id: Parent season identifier.
    :var title: Display name of the division.
    :var external_id: External identifier for integration with third-party systems.
    :var team_count: Number of teams in this division (populated when fetched with include_team_counts=True).
    :var created_at: When the division was created.
    :var updated_at: Last time the division was updated.
    """

    id: str = Field(description="Division identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    title: str = Field(description="Display name of the division.")
    external_id: str | None = Field(
        default=None,
        description="External identifier for integration with third-party systems.",
    )
    team_count: int | None = Field(
        default=None,
        description=(
            "Number of teams in this division (populated when fetched with include_team_counts=True)."
        ),
    )
    created_at: datetime = Field(description="When the division was created.")
    updated_at: datetime = Field(description="Last time the division was updated.")


def _parse(item: dict[str, Any]) -> Division:
    """Flatten a JSON:API resource object into a :class:`Division`.

    :param item: A JSON:API resource object with ``id`` and ``attributes`` keys.
    :type item: dict[str, Any]
    :returns: Parsed Division model instance.
    :rtype: Division
    """
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Division(**data)


def list_division_teams(session: Session, division_id: str) -> list[Team]:
    """Return every team in the specified division.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param division_id: The division identifier whose teams to list.
    :type division_id: str
    :returns: A list of :class:`Team`, in the order the server returned them. The list may be empty if the
        division has no teams.
    :rtype: list[Team]
    """
    from gamesheet_sdk.teams import _parse as parse_team

    endpoint = f"/api/divisions/{division_id}/teams"
    # Request sparse fieldset including logo_url and roster (for player/coach counts)
    # Include invitations relationship to get invitation codes
    params = {
        "fields[teams]": "title,logo_url,roster,created_at,updated_at",
        "include": "invitations",
    }
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params=params)
    handle_response(response, endpoint, "GET division teams")
    body: dict[str, Any] = response.json()
    # Build invitation code lookup from included resources
    invitation_codes = build_invitation_code_lookup(body)
    # Parse teams and match invitation codes via relationships
    teams = []
    for item in body.get("data", []):
        team = parse_team(item)
        # Look up invitation code from relationship
        invitation_code = get_invitation_code_from_relationship(item, invitation_codes)
        if invitation_code:
            # Update the team with the invitation code using model_copy
            team = team.model_copy(update={"invitation_code": invitation_code})
        teams.append(team)
    return teams


def get_division(
    session: Session,
    division_id: str,
    *,
    include_team_count: bool = True,
) -> Division:
    """Get a single division by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param division_id: The division identifier to retrieve.
    :type division_id: str
    :param include_team_count: If ``True`` (default), fetch and populate ``team_count`` for the division
        (requires an additional API call).
    :type include_team_count: bool
    :returns: The requested Division model instance.
    :rtype: Division
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"{_ENDPOINT}/{division_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET division")
    body: dict[str, Any] = response.json()
    division = _parse(body["data"])
    # If requested, fetch team count for this division
    if include_team_count:
        teams = list_division_teams(session, division.id)
        division.team_count = len(teams)
    return division


def list_divisions(
    session: Session,
    season_id: str,
    *,
    include_team_counts: bool = False,
) -> list[Division]:
    """Return every division in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    .. note:: The GameSheet API returns all divisions, so this function filters client-side to only
        include divisions that belong to the specified season (via the
        ``relationships.season.data.id`` field).

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose divisions to list.
    :type season_id: str
    :param include_team_counts: If ``True``, fetch and populate ``team_count`` for each division (requires an
        additional API call per division).
    :type include_team_counts: bool
    :returns: A list of :class:`Division`, in the order the server returned them. The list may be empty if the
        season has no divisions.
    :rtype: list[Division]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    response = session.get(_ENDPOINT, headers=JSONAPI_HEADERS)
    handle_response(response, _ENDPOINT, "GET divisions")
    body: dict[str, Any] = response.json()
    # Parse all divisions and filter to only those belonging to the requested season
    all_divisions = [_parse(item) for item in body.get("data", [])]
    divisions = [d for d in all_divisions if d.season_id == season_id]
    # If requested, fetch team counts for each division
    if include_team_counts:
        for division in divisions:
            teams = list_division_teams(session, division.id)
            division.team_count = len(teams)
    return divisions


def create_division(
    session: Session,
    season_id: str,
    title: str,
    *,
    external_id: str | None = None,
) -> Division:
    """Create a new division in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier in which to create the division.
    :type season_id: str
    :param title: The display name of the division.
    :type title: str
    :param external_id: Optional external identifier for integration with third-party systems. If not
        provided, a UUID will be generated automatically.
    :type external_id: str | None
    :returns: The newly created Division model instance.
    :rtype: Division
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    import uuid

    endpoint = f"/api/seasons/{season_id}/divisions"
    # Generate external_id if not provided
    if external_id is None:
        external_id = str(uuid.uuid4())
    payload = {
        "data": {
            "type": "divisions",
            "attributes": {
                "title": title,
                "external_id": external_id,
                "settings": {},
            },
            "relationships": {
                "season": {
                    "data": {
                        "id": season_id,
                        "type": "seasons",
                    },
                },
            },
        },
    }
    response = session.post(endpoint, json=payload, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "POST division")
    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def update_division(
    session: Session,
    season_id: str,
    division_id: str,
    *,
    title: str | None = None,
    external_id: str | None = None,
) -> Division:
    """Update an existing division.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. At least one of
    title or external_id must be provided.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the division.
    :type season_id: str
    :param division_id: The division identifier to update.
    :type division_id: str
    :param title: Optional new display name for the division.
    :type title: str | None
    :param external_id: Optional new external identifier.
    :type external_id: str | None
    :returns: The updated :class:`Division`.
    :rtype: Division
    :raises ValueError: If neither title nor external_id is provided.
    """
    if title is None is external_id:
        msg = "At least one of title or external_id must be provided"
        raise ValueError(msg)
    # GameSheet API requires title to always be present in PATCH payload.
    # If user didn't provide a new title, fetch the current one.
    if title is None:
        # Fetch current division to get existing title
        get_response = session.get(
            f"/api/divisions/{division_id}",
            headers=JSONAPI_HEADERS,
        )
        if get_response.status_code == 200:
            current_data = get_response.json()
            title = current_data.get("data", {}).get("attributes", {}).get("title", "")
        else:
            # If we can't fetch the current title, the PATCH will fail anyway
            # Let it proceed and return the API's error
            title = ""
    endpoint = f"/api/seasons/{season_id}/divisions/{division_id}"
    # Build attributes dict - title is always required by the API
    attributes: dict[str, Any] = {
        "title": title,
        "settings": {},  # GameSheet API requires settings to be present in PATCH
    }
    if external_id is not None:
        attributes["external_id"] = external_id
    payload = {
        "data": {
            "type": "divisions",
            "id": division_id,
            "attributes": attributes,
            "relationships": {
                "season": {
                    "data": {
                        "id": season_id,
                        "type": "seasons",
                    },
                },
            },
        },
    }
    response = session.patch(endpoint, json=payload, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "PATCH division")
    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def delete_division(
    session: Session,
    season_id: str,
    division_id: str,
) -> None:
    """Delete a division.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the division.
    :type season_id: str
    :param division_id: The division identifier to delete.
    :type division_id: str
    """
    endpoint = f"/api/seasons/{season_id}/divisions/{division_id}"
    response = session.delete(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "DELETE division")
