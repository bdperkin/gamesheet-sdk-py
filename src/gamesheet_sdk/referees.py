"""GameSheet referees: officials assigned to games within a season.

A referee is an official who can be assigned to games within a season. Each referee belongs to exactly one
season. The dashboard displays referees after navigating into a season view. This module talks to the
GameSheet JSON:API at ``/api/seasons/{season_id}/referees`` directly with the lightweight
:class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a bearer token has been
obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage state via
:func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Referee(BaseModel):
    """A single referee.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{season_id}/referees`` to a flat
    typed model.
    """

    id: str = Field(description="Referee identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    first_name: str = Field(description="Referee's first name.")
    last_name: str = Field(description="Referee's last name.")
    email: str | None = Field(default=None, description="Referee's email address.")
    created_at: datetime = Field(description="When the referee was created.")
    updated_at: datetime = Field(description="Last time the referee was updated.")


def _parse(item: dict[str, Any]) -> Referee:
    """Flatten a JSON:API resource object into a :class:`Referee`."""
    attrs = item.get("attributes", {})
    # Extract season_id from relationships
    season_id = item.get("relationships", {}).get("season", {}).get("data", {}).get("id", "")
    return Referee(
        id=item["id"],
        season_id=season_id,
        **attrs,
    )


def list_referees(session: Session, season_id: str) -> list[Referee]:
    """Return every referee in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose referees to list.
    :type season_id: str
    :returns: A list of :class:`Referee`, in the order the server returned them. The list may be empty if the
        season has no referees.
    :rtype: list[Referee]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/referees"
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
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item) for item in body.get("data", [])]
