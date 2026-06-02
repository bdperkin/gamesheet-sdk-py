"""GameSheet associations: the top-level organizational unit of the platform.

An association corresponds to a league operator (a hockey association, a tournament series, a district body,
etc.). The dashboard's first view after login lists the associations the signed-in user has access to.

This module talks to the GameSheet JSON:API at ``/api/associations`` directly with the lightweight
:class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a bearer token has been
obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage state via
:func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from gamesheet_sdk.session import Session

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

# pylint: disable=ungrouped-imports
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

_ENDPOINT = "/api/associations"
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Association(BaseModel):
    """A single association.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/associations`` to a flat typed model.
    """

    id: str = Field(description="Association identifier (string in JSON:API).")  # noqa: A003
    title: str = Field(description="Display name of the association.")
    logo: str = Field(default="", description="Logo asset URL, possibly empty.")
    created_at: datetime = Field(description="When the association was created.")
    updated_at: datetime = Field(description="Last time the association was updated.")  # noqa: F841


def _parse(item: dict[str, Any]) -> Association:
    """Flatten a JSON:API resource object into an :class:`Association`."""
    return Association(id=item["id"], **item.get("attributes", {}))


def list_associations(session: Session) -> list[Association]:
    """Return every association the authenticated user can see.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :returns: A list of :class:`Association`, in the order the server returned them. The list may be empty
        if the user has access to no associations.
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired
        -- run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    response = session.get(
        _ENDPOINT,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {_ENDPOINT} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item) for item in body.get("data", [])]
