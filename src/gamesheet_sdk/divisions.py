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
    external_id: str | None = Field(
        default=None,
        description="External identifier for integration with third-party systems.",
    )
    team_count: int | None = Field(
        default=None,
        description=(
            "Number of teams in this division " "(populated when fetched with include_team_counts=True)."
        ),
    )
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


def list_divisions(session: Session, season_id: str, *, include_team_counts: bool = False) -> list[Division]:
    """Return every division in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    Note: The GameSheet API returns all divisions, so this function filters client-side to only
    include divisions that belong to the specified season (via the relationships.season.data.id field).

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose divisions to list.
    :type season_id: str
    :param include_team_counts: If True, fetch and populate team_count for each division (requires an
        additional API call per division).
    :type include_team_counts: bool
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
        provided, a UUID will be generated by the server.
    :type external_id: str | None
    :returns: The newly created :class:`Division`.
    :rtype: Division
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    import uuid  # pylint: disable=import-outside-toplevel

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

    response = session.post(
        endpoint,
        json=payload,
        headers={"Accept": _JSONAPI_CONTENT_TYPE, "Content-Type": _JSONAPI_CONTENT_TYPE},
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
        _err_msg = (f"POST {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def update_division(
    session: Session,
    division_id: str,
    *,
    title: str | None = None,
    external_id: str | None = None,
) -> Division:
    """Update an existing division.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    At least one of title or external_id must be provided.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param division_id: The division identifier to update.
    :type division_id: str
    :param title: Optional new display name for the division.
    :type title: str | None
    :param external_id: Optional new external identifier.
    :type external_id: str | None
    :returns: The updated :class:`Division`.
    :rtype: Division
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    :raises ValueError: If neither title nor external_id is provided.
    """
    if title is None and external_id is None:
        raise ValueError("At least one of title or external_id must be provided")

    endpoint = f"/api/divisions/{division_id}"

    # Build attributes dict with only provided fields
    attributes: dict[str, Any] = {}
    if title is not None:
        attributes["title"] = title
    if external_id is not None:
        attributes["external_id"] = external_id

    payload = {
        "data": {
            "type": "divisions",
            "id": division_id,
            "attributes": attributes,
        },
    }

    response = session.patch(
        endpoint,
        json=payload,
        headers={"Accept": _JSONAPI_CONTENT_TYPE, "Content-Type": _JSONAPI_CONTENT_TYPE},
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
        _err_msg = (f"PATCH {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse(body["data"])
