# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Seasons data from the teams API.

The ``GET /api/seasons`` endpoint returns season metadata, configurations, penalty codes, and assigned teams
for the authenticated user.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_SEASONS_PATH

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


class SeasonSummary(BaseModel):
    """Summary of a season for list views.

    Attributes:
        association_id (str): Parent association identifier.
        association_title (str): Parent association display name.
        id (str): Season identifier.
        league_id (str): League ID from nested league object.
        league_title (str): League display name.
        leagueId (str): Parent league identifier.
        stats_year (str): Statistics year label.
        title (str): Display name of the season.

    """

    model_config = ConfigDict(extra="allow")

    association_id: str = Field(default="", description="Parent association identifier.")
    association_title: str = Field(default="", description="Parent association display name.")
    id: str = Field(description="Season identifier.")
    league_id: str = Field(default="", description="League ID from league object.")
    league_title: str = Field(default="", description="League display name.")
    leagueId: str = Field(default="", description="Parent league identifier.")  # noqa: N815
    stats_year: str = Field(default="", description="Statistics year label.")
    title: str = Field(description="Display name of the season.")


class SeasonDetail(BaseModel):
    """Detailed season metadata with penaltyCodes and teams excluded.

    Attributes:
        id (str | int | None): Season identifier.
        title (str | None): Display name of the season.
        stats_year (str | int | None): Statistics year label.
        leagueId (str | int | None): Parent league identifier.

    """

    model_config = ConfigDict(extra="allow")

    id: str | int | None = Field(default=None, description="Season identifier.")
    title: str | None = Field(default=None, description="Display name of the season.")
    stats_year: str | int | None = Field(default=None, description="Statistics year label.")
    leagueId: str | int | None = Field(default=None, description="Parent league identifier.")  # noqa: N815


class PenaltyCode(BaseModel):
    """A penalty code configured for a season.

    Attributes:
        code (str): Penalty code identifier.
        name (str): Penalty name or description.

    """

    model_config = ConfigDict(extra="allow")

    code: str = Field(default="", description="Penalty code identifier.")
    name: str = Field(default="", description="Penalty name or description.")


class SeasonTeam(BaseModel):
    """A team participating in a season.

    Attributes:
        id (str): Team identifier.
        title (str): Team display name.

    """

    model_config = ConfigDict(extra="allow")

    id: str = Field(default="", description="Team identifier.")
    title: str = Field(default="", description="Team display name.")


def _parse_season_summary(raw: dict[str, Any]) -> SeasonSummary:
    """Parse raw season dictionary into a :class:`SeasonSummary`."""
    assoc = raw.get("association") or {}
    league = raw.get("league") or {}
    assoc_id = assoc.get("id") if isinstance(assoc, dict) else ""
    assoc_title = assoc.get("title", "") if isinstance(assoc, dict) else ""
    league_id = league.get("id") if isinstance(league, dict) else ""
    league_title = league.get("title", "") if isinstance(league, dict) else ""
    league_id_attr = raw.get("leagueId")

    return SeasonSummary(
        association_id=str(assoc_id) if assoc_id is not None and assoc_id != "" else "",
        association_title=str(assoc_title) if assoc_title is not None else "",
        id=str(raw.get("id", "")),
        league_id=str(league_id) if league_id is not None and league_id != "" else "",
        league_title=str(league_title) if league_title is not None else "",
        leagueId=str(league_id_attr) if league_id_attr is not None and league_id_attr != "" else "",
        stats_year=str(raw.get("stats_year", "") or ""),
        title=str(raw.get("title", "") or ""),
    )


def fetch_seasons_raw(
    session: BaseAuthenticatedSession,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[dict[str, Any]]:
    """Fetch raw seasons data from the teams API gateway.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[dict[str, Any]]: List of raw season dictionaries from the API response.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the server returns any other non-2xx status code.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_SEASONS_PATH}"
    response = session.get(url, timeout=timeout)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"GET {TEAMS_SEASONS_PATH} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)

    body = response.json()
    if isinstance(body, dict):
        if "seasons" in body and isinstance(body["seasons"], list):
            return body["seasons"]

        data = body.get("data")
        if isinstance(data, dict) and "seasons" in data and isinstance(data["seasons"], list):
            return data["seasons"]

        if isinstance(data, list):
            return data
    elif isinstance(body, list):
        return body

    return []


def _find_season(seasons: list[dict[str, Any]], season_id: str | int) -> dict[str, Any]:
    """Find a season by ID within the seasons list."""
    target_id = str(season_id)
    for s in seasons:
        if str(s.get("id", "")) == target_id:
            return s

    msg = f"Season '{season_id}' not found."
    raise GameSheetError(msg)


def list_seasons(
    session: BaseAuthenticatedSession,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[SeasonSummary]:
    """Fetch and summarize all seasons available to the authenticated user.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[SeasonSummary]: List of :class:`SeasonSummary` objects.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the server returns a non-2xx status code.

    """
    raw_seasons = fetch_seasons_raw(session, timeout=timeout)
    return [_parse_season_summary(item) for item in raw_seasons]


def get_season(
    session: BaseAuthenticatedSession,
    season_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> SeasonDetail:
    """Retrieve detailed information for a specific season, excluding penaltyCodes and teams.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        season_id (str | int): Identifier of the season to retrieve.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        SeasonDetail: :class:`SeasonDetail` with season attributes (excluding penaltyCodes and teams).

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the season is not found or the server returns an error.

    """
    raw_seasons = fetch_seasons_raw(session, timeout=timeout)
    season = _find_season(raw_seasons, season_id)
    filtered = {k: v for k, v in season.items() if k not in ("penaltyCodes", "teams")}
    if "id" in filtered:
        filtered["id"] = str(filtered["id"]) if filtered["id"] is not None else ""

    if "leagueId" in filtered:
        filtered["leagueId"] = str(filtered["leagueId"]) if filtered["leagueId"] is not None else ""

    return SeasonDetail(**filtered)


def get_season_penalty_codes(
    session: BaseAuthenticatedSession,
    season_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[PenaltyCode]:
    """Retrieve all penalty codes configured for a specific season.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        season_id (str | int): Identifier of the season.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[PenaltyCode]: List of :class:`PenaltyCode` objects for the season.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the season is not found or the server returns an error.

    """
    raw_seasons = fetch_seasons_raw(session, timeout=timeout)
    season = _find_season(raw_seasons, season_id)
    penalty_codes = season.get("penaltyCodes", [])
    if not isinstance(penalty_codes, list):
        return []

    result: list[PenaltyCode] = []
    for item in penalty_codes:
        if isinstance(item, dict):
            item_dict = dict(item)
            if "code" in item_dict and item_dict["code"] is not None:
                item_dict["code"] = str(item_dict["code"])

            result.append(PenaltyCode(**item_dict))
        else:
            result.append(PenaltyCode(code=str(item)))

    return result


def get_season_teams(
    session: BaseAuthenticatedSession,
    season_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[SeasonTeam]:
    """Retrieve all teams participating in a specific season.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        season_id (str | int): Identifier of the season.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[SeasonTeam]: List of :class:`SeasonTeam` objects for the season.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the season is not found or the server returns an error.

    """
    raw_seasons = fetch_seasons_raw(session, timeout=timeout)
    season = _find_season(raw_seasons, season_id)
    teams = season.get("teams", [])
    if not isinstance(teams, list):
        return []

    result: list[SeasonTeam] = []
    for item in teams:
        if isinstance(item, dict):
            item_dict = dict(item)
            if "id" in item_dict and item_dict["id"] is not None:
                item_dict["id"] = str(item_dict["id"])

            result.append(SeasonTeam(**item_dict))
        else:
            result.append(SeasonTeam(id=str(item)))

    return result
