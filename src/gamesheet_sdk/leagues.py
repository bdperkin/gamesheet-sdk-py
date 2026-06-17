"""GameSheet leagues: divisions within an association.

A league is a division, tier, or other grouping within an association (e.g., "18U AAA", "Bantam", etc.). Each
league belongs to exactly one association. The dashboard displays leagues after navigating into an association
view. This module talks to the GameSheet JSON:API at ``/api/associations/{association_id}/leagues`` directly
with the lightweight :class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a
bearer token has been obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage
state via :func:`gamesheet_sdk.auth.load_access_token`).
Example
-------
Retrieve all leagues for a given association:
.. code-block:: python
    from gamesheet_sdk.auth import load_access_token
    from gamesheet_sdk.leagues import list_leagues
    from gamesheet_sdk.session import Session

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
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
_ENDPOINT_TEMPLATE = "/api/associations/{association_id}/leagues"
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class League(BaseModel):
    """A single league.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/associations/{id}/leagues`` to a flat
    typed model.
    """

    id: str = Field(description="League identifier (string in JSON:API).")
    association_id: str = Field(description="Parent association identifier.")
    title: str = Field(description="Display name of the league.")
    created_at: datetime = Field(description="When the league was created.")
    updated_at: datetime = Field(description="Last time the league was updated.")


def _parse(item: dict[str, Any], association_id: str) -> League:
    """Flatten a JSON:API resource object into a :class:`League`.

    Extracts the ``id`` from the top-level resource object and merges ``attributes`` to produce a flat
    pydantic model. Internal helper for :func:`list_leagues`.
    :param item: A single JSON:API resource object from the ``data`` array, with top-level ``id`` and nested
        ``attributes``.
    :param association_id: The parent association identifier to attach to the resulting model.
    :returns: A populated :class:`League` instance.
    :raises KeyError: If ``item`` lacks an ``id`` field (malformed JSON:API response).
    """
    attrs = item.get("attributes", {})
    return League(
        id=item["id"],
        association_id=association_id,
        **attrs,
    )


def get_league(session: Session, association_id: str, league_id: str) -> League:
    """Get a single league by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param association_id: The parent association identifier.
    :type association_id: str
    :param league_id: The league identifier to retrieve.
    :type league_id: str
    :returns: The :class:`League` with the specified ID.
    :rtype: League
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response, including 404 if the league is not found.
    """
    endpoint = f"{_ENDPOINT_TEMPLATE.format(association_id=association_id)}/{league_id}"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"League '{league_id}' not found in association '{association_id}' (HTTP 404). "
            f"Make sure you're using a valid league ID and association ID.",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return _parse(body["data"], association_id)


def list_leagues(session: Session, association_id: str) -> list[League]:
    """Return every league in the specified association.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param association_id: The association identifier whose leagues to list.
    :returns: A list of :class:`League`, in the order the server returned them. The list may be empty if the
        association has no leagues.
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = _ENDPOINT_TEMPLATE.format(association_id=association_id)
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Association '{association_id}' not found (HTTP 404). "
            f"Make sure you're using a valid association ID. "
            f"To see all associations you have access to, run: gamesheet-sdk-py associations list",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item, association_id) for item in body.get("data", [])]
