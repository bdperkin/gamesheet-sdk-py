"""GameSheet leagues: divisions within an association.

A league is a division, tier, or other grouping within an association (e.g., "18U AAA", "Bantam", etc.). Each
league belongs to exactly one association. The dashboard displays leagues after navigating into an association
view. This module talks to the GameSheet JSON:API at ``/api/associations/{association_id}/leagues`` directly
with the lightweight :class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a
bearer token has been obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage
state via :func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
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

    id: str = Field(description="League identifier (string in JSON:API).")  # noqa: A003
    association_id: str = Field(description="Parent association identifier.")
    title: str = Field(description="Display name of the league.")
    created_at: datetime = Field(description="When the league was created.")
    updated_at: datetime = Field(description="Last time the league was updated.")  # noqa: F841


def _parse(item: dict[str, Any], association_id: str) -> League:
    """Flatten a JSON:API resource object into a :class:`League`."""
    attrs = item.get("attributes", {})
    return League(
        id=item["id"],
        association_id=association_id,
        **attrs,
    )


def list_leagues(session: Session, association_id: str) -> list[League]:
    """Return every league in the specified association.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param association_id: The association identifier whose leagues to list.
    :returns: A list of :class:`League`, in the order the server returned them. The list may be
        empty if the association has no leagues.
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or
        expired -- run ``gamesheet-sdk-py login`` to refresh).
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
    if response.status_code >= 400:

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item, association_id) for item in body.get("data", [])]
