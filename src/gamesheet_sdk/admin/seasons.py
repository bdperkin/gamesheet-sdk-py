# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet seasons: time periods within a league.

A season is a time period during which games are played within a league (e.g., "2024-2025", "Fall 2024",
etc.). Each season belongs to exactly one league. The dashboard displays seasons after navigating into a
league view. This module talks to the GameSheet JSON:API at ``/api/seasons?league_id={league_id}`` directly
with the lightweight :class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a
bearer token has been obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage
state via :func:`gamesheet_sdk.common.auth.load_access_token`). When filters are provided, the BFF API
endpoint is used instead.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.common import errors
from gamesheet_sdk.common.constants import BFF_API_BASE_URL
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.common.session import Session
from gamesheet_sdk.common.shared import JSONAPI_HEADERS
from gamesheet_sdk.common.shared.constants import (
    FIELD_DESC_PARENT_ASSOCIATION_ID,
    FIELD_DESC_PARENT_LEAGUE_ID,
)

_ENDPOINT = "/api/seasons"


class Season(BaseModel):
    """A single season.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons?league_id={id}`` to a flat typed
    model.
    """

    id: str = Field(description="Season identifier (string in JSON:API).")
    league_id: str = Field(description=FIELD_DESC_PARENT_LEAGUE_ID)
    title: str = Field(description="Display name of the season.")
    created_at: datetime = Field(description="When the season was created.")
    updated_at: datetime = Field(description="Last time the season was updated.")


class SeasonDetail(BaseModel):
    """Detailed information about a specific season.

    Maps the ``data`` object in the JSON:API response of ``GET /api/seasons/{id}`` to a flat typed model,
    including all attributes and relationships.
    """

    id: str = Field(description="Season identifier (string in JSON:API).")
    association_id: str = Field(description=FIELD_DESC_PARENT_ASSOCIATION_ID)
    league_id: str = Field(description=FIELD_DESC_PARENT_LEAGUE_ID)
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
    player_of_the_game: str | None = Field(
        default=None,
        description="Player of the game configuration.",
    )
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
    vendor_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Vendor-specific metadata.",
    )
    created_at: datetime = Field(description="When the season was created.")
    updated_at: datetime = Field(description="Last time the season was updated.")


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


def _parse_bff_season(item: dict[str, Any], league_id: str) -> Season:
    """Parse a season from the BFF API response.

    Note: The BFF API does not return created_at/updated_at, so we use the current time.
    """
    now = datetime.now()
    return Season(
        id=str(item["id"]),
        league_id=league_id,
        title=item.get("title", ""),
        created_at=now,
        updated_at=now,
    )


# pylint: disable-next=too-many-branches
def _list_seasons_bff(
    session: Session,
    league_id: str,
    *,
    starts_after: str | None,
    ends_before: str | None,
    status: str | None,
    stats_year: str | None,
    title: str | None,
) -> list[Season]:
    """List seasons using the BFF API with filters."""
    params: dict[str, str] = {
        "page[number]": "1",
        "page[size]": "1000",
        "sort": "-start_date",
    }
    if starts_after:
        params["filter[starts_after]"] = starts_after

    if ends_before:
        params["filter[ends_before]"] = ends_before

    if status:
        params["filter[status]"] = status

    if stats_year:
        params["filter[stats_year]"] = stats_year

    if title:
        params["filter[title]"] = title

    url = f"{BFF_API_BASE_URL}/leagues/{league_id}/seasons"
    response = session.get(url, params=params)
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 404:
        _err_msg = errors.ERROR_MSG_404_LEAGUE.format(league_id=league_id)
        raise GameSheetError(_err_msg)

    if response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_HTTP_GET.format(
            endpoint=url,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    if body.get("status") != "success":
        status = body.get("status")
        _err_msg = errors.ERROR_MSG_BFF_NON_SUCCESS_SIMPLE.format(status=status)
        raise GameSheetError(_err_msg)

    data = body.get("data", [])
    if isinstance(data, dict):
        items = data.get("items", [])
    else:
        items = data

    return [_parse_bff_season(item, league_id) for item in items]


def list_seasons(
    session: Session,
    league_id: str,
    *,
    starts_after: str | None = None,
    ends_before: str | None = None,
    status: str | None = None,
    stats_year: str | None = None,
    title: str | None = None,
) -> list[Season]:
    """Return every season in the specified league.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. When filters are
    provided, the BFF API endpoint is used. Otherwise, the JSON:API endpoint is used and results are filtered
    client-side.

    Args:
        session (Session): An authenticated :class:`Session`.
        league_id (str): The league identifier whose seasons to list.
        starts_after (str | None): Optional filter for seasons starting
            after this date (ISO format: YYYY-MM-DD).
        ends_before (str | None): Optional filter for seasons ending
            before this date (ISO format: YYYY-MM-DD).
        status (str | None): Optional status filter (e.g., 'archived',
            'active', 'all').
        stats_year (str | None): Optional statistics year filter (e.g.,
            '2026-2027').
        title (str | None): Optional title search filter (free-form
            text).

    Returns:
        list[Season]: A list of :class:`Season`, in the order the server
        returned them. The list may be empty if the league has no
        seasons.

    Raises:
        AuthenticationError: If the server returns 401 (the bearer is
            missing, malformed, or expired -- run ``gamesheet-admin
            login`` to refresh).
        GameSheetError: For any other non-2xx response.
    """
    has_filters = any([starts_after, ends_before, status, stats_year, title])
    if has_filters:
        return _list_seasons_bff(
            session,
            league_id,
            starts_after=starts_after,
            ends_before=ends_before,
            status=status,
            stats_year=stats_year,
            title=title,
        )

    response = session.get(
        _ENDPOINT,
        headers=JSONAPI_HEADERS,
    )
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_HTTP_GET.format(
            endpoint=_ENDPOINT,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    # Parse all seasons and filter to only those belonging to the requested league
    all_seasons = [_parse(item) for item in body.get("data", [])]
    return [s for s in all_seasons if s.league_id == league_id]


def get_season(session: Session, season_id: str) -> SeasonDetail:
    """Return detailed information about a specific season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier to retrieve.

    Returns:
        SeasonDetail: A :class:`SeasonDetail` with complete season
        information.

    Raises:
        AuthenticationError: If the server returns 401 (the bearer is
            missing, malformed, or expired -- run ``gamesheet-admin
            login`` to refresh).
        GameSheetError: For any other non-2xx response (including 404 if
            the season doesn't exist).
    """
    endpoint = f"{_ENDPOINT}/{season_id}"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
    )
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 404:
        _err_msg = errors.ERROR_MSG_404_SEASON.format(season_id=season_id)
        raise GameSheetError(_err_msg)

    if response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_HTTP_GET.format(
            endpoint=endpoint,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse_detail(body["data"])
