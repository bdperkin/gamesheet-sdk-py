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
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
    from gamesheet_sdk.teams import Team
_ENDPOINT = "/api/divisions"
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Division(BaseModel):
    """A single division.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/divisions?season_id={id}`` to a flat
    typed model.
    """

    id: str = Field(description="Division identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    title: str = Field(description="Display name of the division.")
    created_at: datetime = Field(description="When the division was created.")
    updated_at: datetime = Field(description="Last time the division was updated.")


def _parse(item: dict[str, Any]) -> Division:
    """Flatten a JSON:API resource object into a :class:`Division`."""
    attrs = item.get("attributes", {})
    # Extract season_id from relationships
    season_id = item.get("relationships", {}).get("season", {}).get("data", {}).get("id", "")
    return Division(
        id=item["id"],
        season_id=season_id,
        **attrs,
    )


def list_divisions(session: Session, season_id: str) -> list[Division]:
    """Return every division in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    Note: The GameSheet API returns all divisions, so this function filters client-side to only
    include divisions that belong to the specified season (via the relationships.season.data.id field).

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose divisions to list.
    :type season_id: str
    :returns: A list of :class:`Division`, in the order the server returned them. The list may be empty if the
        season has no divisions.
    :rtype: list[Division]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
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
    if response.status_code == 404:

        _err_msg = (
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:

        _err_msg = (f"GET {_ENDPOINT} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    # Parse all divisions and filter to only those belonging to the requested season
    all_divisions = [_parse(item) for item in body.get("data", [])]
    return [d for d in all_divisions if d.season_id == season_id]


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
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    from gamesheet_sdk.teams import _parse as parse_team  # pylint: disable=import-outside-toplevel

    endpoint = f"/api/divisions/{division_id}/teams"
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
            f"Division '{division_id}' not found (HTTP 404). "
            f"Make sure you're using a valid division ID. "
            f"To get valid division IDs, run: gamesheet-sdk-py divisions list --season-id <SEASON_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [parse_team(item) for item in body.get("data", [])]
