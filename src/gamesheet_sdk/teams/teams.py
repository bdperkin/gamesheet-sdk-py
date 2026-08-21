# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams data from the teams API.

The ``GET /api/teams`` endpoint returns teams associated with the authenticated user.
"""

from __future__ import annotations

import mimetypes
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S
from gamesheet_sdk.common.constants import CLOUDFLARE_IMAGE_DELIVERY_BASE
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_IMAGES_UPLOAD_URL_PATH,
    TEAMS_TEAMS_PATH,
)

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
        teamLogo (str | None): URL of the team logo.
        skill (str | None): Skill level of the team.
        province (str | None): Province or state code of the team.
        isArchived (bool | None): Whether the team is archived.
        seasonTeamsUpdated (int | None): Count of season team instances updated.

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
    teamLogo: str | None = Field(default=None, description="URL of the team logo.")  # noqa: N815
    skill: str | None = Field(default=None, description="Skill level of the team.")
    province: str | None = Field(default=None, description="Province or state code of the team.")
    isArchived: bool | None = Field(default=None, description="Whether the team is archived.")  # noqa: N815
    seasonTeamsUpdated: int | None = Field(  # noqa: N815
        default=None,
        description="Count of season team instances updated.",
    )


def _parse_team_summary(raw: dict[str, Any]) -> TeamSummary:
    """Parse raw team dictionary into a :class:`TeamSummary`.

    Args:
        raw (dict[str, Any]): Raw team dictionary.

    Returns:
        TeamSummary: Parsed team summary model instance.

    """
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
        memberId=str(member_id) if member_id is not None and member_id else "",
        teamId=str(team_id) if team_id is not None and team_id else "",
        relationship=str(relationship) if relationship is not None else "",
        status=str(status) if status is not None else "",
        onboardingCompletedAt=str(onboarding) if onboarding is not None else "",
        teamName=str(team_name) if team_name is not None else "",
        ageCategory=str(age_category) if age_category is not None else "",
        clubId=str(club_id) if club_id is not None and club_id else "",
        joinedAt=str(joined_at) if joined_at is not None else "",
        statsYear=str(stats_year) if stats_year is not None else "",
    )


def upload_team_image(
    session: BaseAuthenticatedSession,
    image_path: str,
    image_type: str = "logo",
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> str:
    """Upload an image to Cloudflare via the Teams upload URL endpoint.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        image_path (str): Path to a local image file.
        image_type (str): Type of image for error messages (e.g., "logo").
        timeout (float): Request timeout in seconds.

    Returns:
        str: The Cloudflare CDN URL for the uploaded image.

    Raises:
        GameSheetError: If the file does not exist, is not an image, or upload fails.
        AuthenticationError: If the server returns 401 Unauthorized.

    """
    image_file_path = Path(image_path)
    if not image_file_path.exists():
        msg = f"{image_type.capitalize()} file not found: {image_path}"
        raise GameSheetError(msg)

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        msg = f"Invalid image file: {image_path}"
        raise GameSheetError(msg)

    upload_url_endpoint = f"{TEAMS_API_GATEWAY}{TEAMS_IMAGES_UPLOAD_URL_PATH}"
    upload_url_response = session.get(upload_url_endpoint, timeout=timeout)
    if upload_url_response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if upload_url_response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = (
            f"GET {TEAMS_IMAGES_UPLOAD_URL_PATH} returned HTTP "
            f"{upload_url_response.status_code}: {upload_url_response.text}"
        )
        raise GameSheetError(msg)

    upload_data: dict[str, Any] = upload_url_response.json()
    data_field = upload_data.get("data")
    data_dict: dict[str, Any] = data_field if isinstance(data_field, dict) else {}
    upload_url: str = (
        upload_data.get("uploadURL")
        or upload_data.get("uploadUrl")
        or data_dict.get("uploadURL")
        or data_dict.get("uploadUrl")
        or ""
    )
    image_id: str = upload_data.get("id") or data_dict.get("id") or ""

    if not upload_url:
        msg = f"Failed to get upload URL: {upload_data}"
        raise GameSheetError(msg)

    if not image_id and upload_url:
        image_id = upload_url.rstrip("/").split("/")[-1]

    with image_file_path.open("rb") as f:
        upload_response = session.post(
            upload_url,
            files={"file": (image_file_path.name, f, mime_type)},
            timeout=timeout,
        )

    if upload_response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = (
            f"Failed to upload {image_type} to {upload_url}: "
            f"HTTP {upload_response.status_code}: {upload_response.text}"
        )
        raise GameSheetError(msg)

    return f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/{image_id}"


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
    """Find a team by ID within the teams list.

    Args:
        teams (list[dict[str, Any]]): List of team dicts.
        team_id (str | int): Team identifier to match.

    Returns:
        dict[str, Any]: Matching team dictionary.

    Raises:
        GameSheetError: If the team is not found.

    """
    target_id = str(team_id)
    for t in teams:
        candidate_id = str(t.get("teamId") or t.get("team_id") or t.get("id") or "")
        if candidate_id == target_id:
            return t

    msg = f"Team '{team_id}' not found."
    raise GameSheetError(msg)


def fetch_team_raw(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Fetch raw data for a single team from the teams API gateway.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, Any]: Raw team dictionary from the API response.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the team is not found or the server returns an error.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}/{team_id}"
    response = session.get(url, timeout=timeout)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"GET {TEAMS_TEAMS_PATH}/{team_id} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)

    body = response.json()
    if isinstance(body, dict):
        if "team" in body and isinstance(body["team"], dict):
            return body["team"]

        if "data" in body and isinstance(body["data"], dict):
            return body["data"]

        return body

    msg = f"Unexpected response format from {url}: {body!r}"
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

    """
    raw_teams = fetch_teams_raw(session, timeout=timeout)
    return [_parse_team_summary(item) for item in raw_teams]


def _normalize_team_dict(team: dict[str, Any]) -> dict[str, Any]:
    """Ensure team dictionary has string teamId if present or id is available.

    Args:
        team (dict[str, Any]): Raw team dictionary.

    Returns:
        dict[str, Any]: Normalized team dictionary with string teamId.

    """
    team_copy = dict(team)
    if "teamId" in team_copy and team_copy["teamId"] is not None:
        team_copy["teamId"] = str(team_copy["teamId"])
    elif "id" in team_copy and team_copy["id"] is not None:
        team_copy["teamId"] = str(team_copy["id"])

    return team_copy


def _build_team_update_payload(
    *,
    team_name: str | None,
    skill: str | None,
    logo_url: str | None,
    age_category: str | None,
    province: str | None,
    extra_fields: dict[str, Any],
) -> dict[str, Any]:
    """Construct PATCH payload for team updates, omitting None values.

    Args:
        team_name (str | None): Optional team name.
        skill (str | None): Optional skill level.
        logo_url (str | None): Optional logo URL.
        age_category (str | None): Optional age category.
        province (str | None): Optional province/state code.
        extra_fields (dict[str, Any]): Additional extra payload fields.

    Returns:
        dict[str, Any]: Filtered update payload dictionary.

    """
    fields: dict[str, Any] = {
        "teamName": team_name,
        "skill": skill,
        "teamLogo": logo_url,
        "ageCategory": age_category,
        "province": province,
        **extra_fields,
    }
    return {k: v for k, v in fields.items() if v is not None}


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

    """
    raw_teams = fetch_teams_raw(session, timeout=timeout)
    team = _find_team(raw_teams, team_id)
    return TeamDetail(**_normalize_team_dict(team))


def update_team(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    team_name: str | None = None,
    skill: str | None = None,
    team_logo: str | None = None,
    age_category: str | None = None,
    province: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
    **extra_fields: Any,
) -> TeamDetail:
    """Update an existing team's metadata.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team to update.
        team_name (str | None): New name of the team.
        skill (str | None): Skill level of the team.
        team_logo (str | None): Local image file path or existing image URL.
        age_category (str | None): Age category of the team.
        province (str | None): Province or state code.
        timeout (float): Request timeout in seconds.
        **extra_fields (Any): Any additional fields to include in the PATCH payload.

    Returns:
        TeamDetail: :class:`TeamDetail` with the updated team attributes.

    Raises:
        GameSheetError: If no update fields are provided or the server returns an error.
        AuthenticationError: If the server returns a 401 Unauthorized status.

    """
    logo_url: str | None = None
    if team_logo is not None:
        if team_logo.startswith(("http://", "https://")):
            logo_url = team_logo
        else:
            logo_url = upload_team_image(session, team_logo, timeout=timeout)

    payload = _build_team_update_payload(
        team_name=team_name,
        skill=skill,
        logo_url=logo_url,
        age_category=age_category,
        province=province,
        extra_fields=extra_fields,
    )
    if not payload:
        msg = "At least one field must be provided for update."
        raise GameSheetError(msg)

    patch_url = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}/{team_id}"
    patch_response = session.patch(patch_url, json=payload, timeout=timeout)
    if patch_response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if patch_response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = (
            f"PATCH {TEAMS_TEAMS_PATH}/{team_id} returned HTTP "
            f"{patch_response.status_code}: {patch_response.text}"
        )
        raise GameSheetError(msg)

    raw_team = fetch_team_raw(session, team_id, timeout=timeout)
    return TeamDetail(**_normalize_team_dict(raw_team))


def archive_team(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> TeamDetail:
    """Archive a team to remove it from active lists while preserving data.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team to archive.
        timeout (float): Request timeout in seconds.

    Returns:
        TeamDetail: :class:`TeamDetail` representing the archived team.

    """
    return update_team(session, team_id, isArchived=True, timeout=timeout)


def restore_team(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> TeamDetail:
    """Restore an archived team back to active lists.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team to restore.
        timeout (float): Request timeout in seconds.

    Returns:
        TeamDetail: :class:`TeamDetail` representing the restored team.

    """
    return update_team(session, team_id, isArchived=False, timeout=timeout)


unarchive_team = restore_team


def delete_team(
    session: BaseAuthenticatedSession,
    team_id: str | int,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> None:
    """Delete a team.

    Args:
        session (BaseAuthenticatedSession): Authenticated HTTP session.
        team_id (str | int): Identifier of the team to delete.
        timeout (float): Request timeout in seconds.

    Raises:
        AuthenticationError: If the server returns a 401 Unauthorized status.
        GameSheetError: If the server returns a non-2xx status code.

    """
    delete_url = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}/{team_id}"
    response = session.delete(delete_url, timeout=timeout)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        msg = "Authentication required: token is invalid or expired. Run `gamesheet-teams login`."
        raise AuthenticationError(msg)

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        msg = f"DELETE {TEAMS_TEAMS_PATH}/{team_id} returned HTTP {response.status_code}: {response.text}"
        raise GameSheetError(msg)
