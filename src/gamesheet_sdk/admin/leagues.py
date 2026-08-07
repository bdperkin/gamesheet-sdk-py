# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet leagues: divisions within an association.

A league is a division, tier, or other grouping within an association (e.g., "18U AAA", "Bantam", etc.). Each
league belongs to exactly one association. The dashboard displays leagues after navigating into an association
view. This module talks to the GameSheet JSON:API at ``/api/associations/{association_id}/leagues`` directly
with the lightweight :class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a
bearer token has been obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage
state via :func:`gamesheet_sdk.common.auth.load_access_token`).

**Example:**

Retrieve all leagues for a given association:
.. code-block:: python
    from gamesheet_sdk.common.auth import load_access_token
    from gamesheet_sdk.admin.leagues import list_leagues
    from gamesheet_sdk.common.session import Session

    # Create authenticated session
    session = Session(base_url=PLAY_GAMESHEET_APP)
    token = load_access_token()
    session.set_bearer_token(token)
    # List leagues for association "12345"
    leagues = list_leagues(session, association_id="12345")
    for league in leagues:
        print(f"{league.title} (ID: {league.id})")
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.admin.shared import parse_jsonapi_resource
from gamesheet_sdk.common.session import Session
from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response
from gamesheet_sdk.common.shared.constants import FIELD_DESC_PARENT_ASSOCIATION_ID

_ENDPOINT_TEMPLATE = "/api/associations/{association_id}/leagues"


class League(BaseModel):
    """A single league.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/associations/{id}/leagues`` to a flat
    typed model.

    Attributes:
        id: League identifier (string in JSON:API).
        association_id: Parent association identifier.
        title: Display name of the league.
        created_at: When the league was created.
        updated_at: Last time the league was updated.
    """

    id: str = Field(description="League identifier (string in JSON:API).")
    association_id: str = Field(description=FIELD_DESC_PARENT_ASSOCIATION_ID)
    title: str = Field(description="Display name of the league.")
    created_at: datetime = Field(description="When the league was created.")
    updated_at: datetime = Field(description="Last time the league was updated.")


def _parse(item: dict[str, Any], association_id: str) -> League:
    """Flatten a JSON:API resource object into a :class:`League`.

    Extracts the ``id`` from the top-level resource object and merges ``attributes`` to produce a flat
    pydantic model. Internal helper for :func:`list_leagues`.

    Args:
        item (dict[str, Any]): A single JSON:API resource object from
            the ``data`` array, with top-level ``id`` and nested
            ``attributes``.
        association_id (str): The parent association identifier to
            attach to the resulting model.

    Returns:
        League: Return value.
    """
    data = parse_jsonapi_resource(item)
    data["association_id"] = association_id
    return League(**data)


def get_league(session: Session, association_id: str, league_id: str) -> League:
    """Get a single league by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        association_id (str): The parent association identifier.
        league_id (str): The league identifier to retrieve.

    Returns:
        League: Return value.
    """
    endpoint = f"{_ENDPOINT_TEMPLATE.format(association_id=association_id)}/{league_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET league")
    body: dict[str, Any] = response.json()
    return _parse(body["data"], association_id)


def list_leagues(session: Session, association_id: str) -> list[League]:
    """Return every league in the specified association.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        association_id (str): The association identifier whose leagues
            to list.

    Returns:
        list[League]: A list of :class:`League`, in the order the server
        returned them. The list may be empty if the association has no
        leagues.
    """
    endpoint = _ENDPOINT_TEMPLATE.format(association_id=association_id)
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET leagues")
    body: dict[str, Any] = response.json()
    return [_parse(item, association_id) for item in body.get("data", [])]
