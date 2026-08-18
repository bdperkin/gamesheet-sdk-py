# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams data from the teams API.

The ``GET /api/teams`` endpoint returns teams associated with the authenticated user.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_TEAMS_PATH

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession


class TeamSummary(BaseModel):
    """Summary of a team for list views.

    Attributes:
        memberId (str | int | None): Member identifier.
        teamId (str | int | None): Team identifier.
        relationship (str | None): User's relationship to the team.
        status (str | None): Team status.
        onboardingCompletedAt (str | None): Timestamp when onboarding was completed.
        teamName (str | None): Name of the team.
        ageCategory (str | None): Age category of the team.
        clubId (str | int | None): Parent club/association identifier.
        joinedAt (str | None): Timestamp when the user joined the team.
        statsYear (str | int | None): Statistics year.

    """

    model_config = ConfigDict(extra="allow")

    memberId: str | int | None = Field(default=None, description="Member identifier.")  # noqa: N815
    teamId: str | int | None = Field(default=None, description="Team identifier.")  # noqa: N815
    relationship: str | None = Field(default=None, description="User's relationship to the team.")
    status: str | None = Field(default=None, description="Team status.")
    onboardingCompletedAt: str | None = Field(  # noqa: N815
        default=None,
        description="Timestamp when onboarding was completed.",
    )
    teamName: str | None = Field(default=None, description="Name of the team.")  # noqa: N815
    ageCategory: str | None = Field(default=None, description="Age category of the team.")  # noqa: N815
    clubId: str | int | None = Field(  # noqa: N815
        default=None,
        description="Parent club/association identifier.",
    )
    joinedAt: str | None = Field(  # noqa: N815
        default=None,
        description="Timestamp when the user joined the team.",
    )
    statsYear: str | int | None = Field(default=None, description="Statistics year.")  # noqa: N815


class TeamDetail(BaseModel):
    """Detailed information for a single team.

    Attributes:
        teamId (str | int | None): Team identifier.
        teamName (str | None): Name of the team.
        status (str | None): Team status.
        relationship (str | None): User's relationship to the team.
        memberId (str | int | None): Member identifier.
        clubId (str | int | None): Parent club/association identifier.
        ageCategory (str | None): Age category of the team.
        statsYear (str | int | None): Statistics year.
        joinedAt (str | None): Timestamp when joined.
        onboardingCompletedAt (str | None): Timestamp when onboarding completed.

    """

    model_config = ConfigDict(extra="allow")

    teamId: str | int | None = Field(default=None, description="Team identifier.")  # noqa: N815
    teamName: str | None = Field(default=None, description="Name of the team.")  # noqa: N815
    status: str | None = Field(default=None, description="Team status.")
    relationship: str | None = Field(default=None, description="User's relationship to the team.")
    memberId: str | int | None = Field(default=None, description="Member identifier.")  # noqa: N815
    clubId: str | int | None = Field(  # noqa: N815
        default=None,
        description="Parent club/association identifier.",
    )
    ageCategory: str | None = Field(default=None, description="Age category of the team.")  # noqa: N815
    statsYear: str | int | None = Field(default=None, description="Statistics year.")  # noqa: N815
    joinedAt: str | None = Field(default=None, description="Timestamp when joined.")  # noqa: N815
    onboardingCompletedAt: str | None = Field(  # noqa: N815
        default=None,
        description="Timestamp when onboarding completed.",
    )


def _parse_team_summary(raw: dict[str, Any]) -> TeamSummary:
    """Parse raw team dictionary into a :class:`TeamSummary`."""
    member_id = raw.get("memberId") if raw.get("memberId") is not None else raw.get("member_id", "")
    team_id = raw.get("teamId") if raw.get("teamId") is not None else raw.get("team_id", raw.get("id", ""))
    relationship = raw.get("relationship", "")
    status = raw.get("status", "")
    onboarding = (
        raw.get("onboardingCompletedAt")
        if raw.get("onboardingCompletedAt") is not None
        else raw.get("onboarding_completed_at", "")
    )
    team_name = (
        raw.get("teamName")
        if raw.get("teamName") is not None
        else raw.get("team_name", raw.get("title", raw.get("name", "")))
    )
    age_category = (
        raw.get("ageCategory") if raw.get("ageCategory") is not None else raw.get("age_category", "")
    )
    club_id = raw.get("clubId") if raw.get("clubId") is not None else raw.get("club_id", "")
    joined_at = raw.get("joinedAt") if raw.get("joinedAt") is not None else raw.get("joined_at", "")
    stats_year = raw.get("statsYear") if raw.get("statsYear") is not None else raw.get("stats_year", "")

    return TeamSummary(
        memberId=str(member_id) if member_id is not None and member_id != "" else "",
        teamId=str(team_id) if team_id is not None and team_id != "" else "",
        relationship=str(relationship) if relationship is not None else "",
        status=str(status) if status is not None else "",
        onboardingCompletedAt=str(onboarding) if onboarding is not None else "",
        teamName=str(team_name) if team_name is not None else "",
        ageCategory=str(age_category) if age_category is not None else "",
        clubId=str(club_id) if club_id is not None and club_id != "" else "",
        joinedAt=str(joined_at) if joined_at is not None else "",
        statsYear=str(stats_year) if stats_year is not None else "",
    )


def fetch_teams_raw(
    session: BaseAuthenticatedSession,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[dict[str, Any]]:
    """Fetch raw teams data from the teams API gateway.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[dict[str, Any]]: List of raw team dictionaries from the API response.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the server returns any other non-2xx status code.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}"
    response = session.get(url, timeout=timeout)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"GET {TEAMS_TEAMS_PATH} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)

    body = response.json()
    if isinstance(body, dict):
        if "teams" in body and isinstance(body["teams"], list):
            return body["teams"]

        data = body.get("data")
        if isinstance(data, dict) and "teams" in data and isinstance(data["teams"], list):
            return data["teams"]

        if isinstance(data, list):
            return data
    elif isinstance(body, list):
        return body

    return []


def _find_team(teams: list[dict[str, Any]], team_id: str | int) -> dict[str, Any]:
    """Find a team by ID within the teams list."""
    target_id = str(team_id)
    for t in teams:
        candidate_id = str(t.get("teamId") or t.get("team_id") or t.get("id") or "")
        if candidate_id == target_id:
            return t

    msg = f"Team '{team_id}' not found."
    raise GameSheetError(msg)


def list_teams(
    session: BaseAuthenticatedSession,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[TeamSummary]:
    """Fetch and summarize all teams available to the authenticated user.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        list[TeamSummary]: List of :class:`TeamSummary` objects.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the server returns a non-2xx status code.

    """
    raw_teams = fetch_teams_raw(session, timeout=timeout)
    return [_parse_team_summary(item) for item in raw_teams]


def get_team(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> TeamDetail:
    """Retrieve detailed information for a specific team.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team to retrieve.
        timeout (float): HTTP request timeout in seconds.

    Returns:
        TeamDetail: :class:`TeamDetail` with team attributes.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the team is not found or the server returns an error.

    """
    raw_teams = fetch_teams_raw(session, timeout=timeout)
    team = _find_team(raw_teams, team_id)
    team_copy = dict(team)
    if "teamId" in team_copy and team_copy["teamId"] is not None:
        team_copy["teamId"] = str(team_copy["teamId"])
    elif "id" in team_copy and team_copy["id"] is not None:
        team_copy["teamId"] = str(team_copy["id"])

    return TeamDetail(**team_copy)
