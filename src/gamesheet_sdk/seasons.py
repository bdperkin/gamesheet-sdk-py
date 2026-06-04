"""GameSheet seasons: time periods within a league.

A season is a time period during which games are played within a league (e.g., "2024-2025", "Fall 2024",
etc.). Each season belongs to exactly one league. The dashboard displays seasons after navigating into a
league view. This module talks to the GameSheet JSON:API at ``/api/seasons?league_id={league_id}`` directly
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
_ENDPOINT = "/api/seasons"
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Season(BaseModel):
    """A single season.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons?league_id={id}`` to a flat typed
    model.
    """

    id: str = Field(description="Season identifier (string in JSON:API).")  # noqa: A003
    league_id: str = Field(description="Parent league identifier.")
    title: str = Field(description="Display name of the season.")
    created_at: datetime = Field(description="When the season was created.")
    updated_at: datetime = Field(description="Last time the season was updated.")  # noqa: F841


class SeasonDetail(BaseModel):
    """Detailed information about a specific season.

    Maps the ``data`` object in the JSON:API response of ``GET /api/seasons/{id}`` to a flat typed model,
    including all attributes and relationships.
    """

    id: str = Field(description="Season identifier (string in JSON:API).")  # noqa: A003
    association_id: str = Field(description="Parent association identifier.")
    league_id: str = Field(description="Parent league identifier.")
    title: str = Field(description="Display name of the season.")
    external_id: str = Field(description="External UUID identifier for the season.")
    start_date: str = Field(description="Season start date (ISO format).")
    end_date: str = Field(description="Season end date (ISO format).")
    sport: str = Field(description="Sport type (e.g., 'hockey').")
    stats_year: str = Field(description="Statistics year label (e.g., '2026-2027').")
    live_scoring_mode: str | None = Field(
        default=None,
        description="Live scoring visibility mode (e.g., 'public', 'private').",
    )
    player_of_the_game: str | None = Field(default=None, description="Player of the game configuration.")
    flagging_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Criteria for flagging events (e.g., penalties, notes).",
    )
    flagged_penalties: list[str] = Field(
        default_factory=list,
        description="List of penalty codes that are flagged.",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Season-specific settings and configuration.",
    )
    vendor_data: dict[str, Any] = Field(default_factory=dict, description="Vendor-specific metadata.")
    created_at: datetime = Field(description="When the season was created.")
    updated_at: datetime = Field(description="Last time the season was updated.")  # noqa: F841


def _parse(item: dict[str, Any]) -> Season:
    """Flatten a JSON:API resource object into a :class:`Season`."""
    attrs = item.get("attributes", {})
    # Extract league_id from relationships
    league_id = item.get("relationships", {}).get("league", {}).get("data", {}).get("id", "")
    return Season(
        id=item["id"],
        league_id=league_id,
        **attrs,
    )


def _parse_detail(data: dict[str, Any]) -> SeasonDetail:
    """Flatten a detailed JSON:API resource object into a :class:`SeasonDetail`."""
    attrs = data.get("attributes", {})
    relationships = data.get("relationships", {})
    # Extract IDs from relationships
    association_id = relationships.get("association", {}).get("data", {}).get("id", "")
    league_id = relationships.get("league", {}).get("data", {}).get("id", "")
    return SeasonDetail(
        id=data["id"],
        association_id=association_id,
        league_id=league_id,
        **attrs,
    )


def list_seasons(session: Session, league_id: str) -> list[Season]:
    """Return every season in the specified league.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    Note: The GameSheet API returns all seasons, so this function filters client-side to only
    include seasons that belong to the specified league (via the relationships.league.data.id field).
    :param session: An authenticated :class:`Session`.
    :param league_id: The league identifier whose seasons to list.
    :returns: A list of :class:`Season`, in the order the server returned them. The list may be empty if the
        league has no seasons.
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
    if response.status_code >= 400:

        _err_msg = (f"GET {_ENDPOINT} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    # Parse all seasons and filter to only those belonging to the requested league
    all_seasons = [_parse(item) for item in body.get("data", [])]
    return [s for s in all_seasons if s.league_id == league_id]


def get_season(session: Session, season_id: str) -> SeasonDetail:
    """Return detailed information about a specific season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier to retrieve.
    :returns: A :class:`SeasonDetail` with complete season information.
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response (including 404 if the season doesn't exist).
    """
    endpoint = f"{_ENDPOINT}/{season_id}"
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
            f"Make sure you're using a valid season ID, not a league ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return _parse_detail(body["data"])
