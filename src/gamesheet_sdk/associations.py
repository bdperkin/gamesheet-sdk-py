"""GameSheet associations: the top-level organizational unit of the platform.

An association corresponds to a league operator (a hockey association, a tournament series, a district body,
etc.). The dashboard's first view after login lists the associations the signed-in user has access to. This
module talks to the GameSheet JSON:API at ``/api/associations`` directly with the lightweight
:class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a bearer token has been
obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage state via
:func:`gamesheet_sdk.auth.load_access_token`).
Examples:
    Retrieve all associations accessible by the authenticated user::
        from gamesheet_sdk.auth import load_access_token
        from gamesheet_sdk.session import Session
        from gamesheet_sdk.associations import list_associations
        # Load the saved access token from previous login
        token = load_access_token()
        # Create an authenticated session
        session = Session(base_url="https://gamesheet.app")
        session.set_bearer_token(token)
        # Fetch all associations
        associations = list_associations(session)
        # Display results
        for assoc in associations:
            print(f"{assoc.title} (ID: {assoc.id})")
            print(f"  Created: {assoc.created_at}")
            print(f"  Logo: {assoc.logo or '(none)'}")
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response, parse_jsonapi_resource

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session

_ENDPOINT = "/api/associations"


class Association(BaseModel):
    """A single association.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/associations`` to a flat typed model.
    Attributes:
        id: Association identifier (string in JSON:API).
        title: Display name of the association.
        logo: Logo asset URL, possibly empty string.
        created_at: When the association was created.
        updated_at: Last time the association was updated.
    """

    id: str = Field(description="Association identifier (string in JSON:API).")
    title: str = Field(description="Display name of the association.")
    logo: str = Field(default="", description="Logo asset URL, possibly empty.")
    created_at: datetime = Field(description="When the association was created.")
    updated_at: datetime = Field(description="Last time the association was updated.")


def _parse(item: dict[str, Any]) -> Association:
    """Flatten a JSON:API resource object into an :class:`Association`.

    :param item: A JSON:API resource object with ``id`` and ``attributes`` keys.
    :returns: An :class:`Association` instance with flattened fields.
    """
    return Association(**parse_jsonapi_resource(item))


def get_association(session: Session, association_id: str) -> Association:
    """Get a single association by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param association_id: The association identifier to retrieve.
    :type association_id: str
    :returns: The :class:`Association` with the specified ID.
    :rtype: Association
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response, including 404 if the association is not found.
    """
    endpoint = f"{_ENDPOINT}/{association_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET association")
    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def list_associations(session: Session) -> list[Association]:
    """Return every association the authenticated user can see.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :returns: A list of :class:`Association`, in the order the server returned them. The list may be empty if
        the user has access to no associations.
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    response = session.get(_ENDPOINT, headers=JSONAPI_HEADERS)
    handle_response(response, _ENDPOINT, "GET associations")
    body: dict[str, Any] = response.json()
    return [_parse(item) for item in body.get("data", [])]
