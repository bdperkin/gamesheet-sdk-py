# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet teams: competing organizations within a season.

A team is a competing organization within a season (e.g., "Raleigh Raptors", "Durham Bulls", etc.). Each team
belongs to exactly one season and may be associated with a division. The dashboard displays teams after
navigating into a season view. This module talks to the GameSheet JSON:API at
``/api/seasons/{season_id}/teams`` directly with the lightweight :class:`gamesheet_sdk.Session` path -- no
Playwright needed for read-only access once a bearer token has been obtained (typically by reading the SPA's
``accessToken`` from the saved browser storage state via :func:`gamesheet_sdk.common.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.admin.shared import (
    build_invitation_code_lookup,
    get_invitation_code_from_relationship,
)
from gamesheet_sdk.common import errors
from gamesheet_sdk.common.constants import BFF_API_BASE_URL
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.common.shared import JSONAPI_CONTENT_TYPE, JSONAPI_HEADERS
from gamesheet_sdk.common.shared.constants import FIELD_DESC_PARENT_SEASON_ID
from gamesheet_sdk.common.shared.gamesheet_http import handle_season_scoped_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


class Team(BaseModel):
    """A single team.

    Maps the ``data[*]`` items in the JSON: API response of ``GET /api/seasons/{season_id}/teams`` to a flat
    typed model.

    Attributes:
        id (str): Team identifier (string in JSON:API).
        season_id (str): Parent season identifier.
        title (str): Team name/title.
        division_id (str | None): Division identifier if team belongs to a division.
        logo (str | None): URL to the team logo image.
        invitation_code (str | None): Invitation code for joining the team.
        player_count (int | None): Number of players on the team.
        coach_count (int | None): Number of coaches on the team.
        created_at (datetime): When the team was created.
        updated_at (datetime): Last time the team was updated.
    """

    id: str = Field(description="Team identifier (string in JSON:API).")
    season_id: str = Field(description=FIELD_DESC_PARENT_SEASON_ID)
    title: str = Field(description="Team name/title.")
    division_id: str | None = Field(
        default=None,
        description="Division identifier if team belongs to a division.",
    )
    logo: str | None = Field(
        default=None,
        description="URL to the team logo image.",
    )
    invitation_code: str | None = Field(
        default=None,
        description="Invitation code for joining the team.",
    )
    player_count: int | None = Field(
        default=None,
        description="Number of players on the team.",
    )
    coach_count: int | None = Field(
        default=None,
        description="Number of coaches on the team.",
    )
    created_at: datetime = Field(description="When the team was created.")
    updated_at: datetime = Field(description="Last time the team was updated.")


def _parse(item: dict[str, Any]) -> Team:
    """Flatten a JSON:API resource object into a :class:`Team`.

    Args:
        item (dict[str, Any]): A JSON:API resource object with ``id``, ``attributes``, and ``relationships``
            keys.

    Returns:
        Team: Parsed Team model instance.
    """
    attrs = item.get("attributes", {})
    relationships = item.get("relationships", {})
    # Extract season_id and division_id from relationships
    season_id = relationships.get("season", {}).get("data", {}).get("id", "")
    division_data = relationships.get("division", {}).get("data")
    division_id = division_data.get("id") if division_data else None
    # Extract optional fields with safe defaults
    # Note: API returns logo_url not logo
    logo = attrs.get("logo_url")
    # invitation_code comes from included invitations relationship (populated by caller)
    invitation_code = None
    # Count roster players and coaches from embedded roster data
    roster = attrs.get("roster", {})
    player_count = len(roster.get("players", []))
    coach_count = len(roster.get("coaches", []))
    return Team(
        id=item["id"],
        season_id=season_id,
        division_id=division_id,
        logo=logo,
        invitation_code=invitation_code,
        player_count=player_count,
        coach_count=coach_count,
        title=attrs["title"],
        created_at=attrs["created_at"],
        updated_at=attrs["updated_at"],
    )


def list_teams(session: Session, season_id: str) -> list[Team]:
    """Return every team in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier whose teams to list.

    Returns:
        list[Team]: A list of :class:`Team`, in the order the server returned them. The list may be empty if
            the season has no teams.
    """
    endpoint = f"/api/seasons/{season_id}/teams"
    # Request sparse fieldset including logo_url and roster (for player/coach counts)
    # Include invitations relationship to get invitation codes
    params = {
        "fields[teams]": "title,logo_url,roster,created_at,updated_at",
        "include": "invitations",
    }
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params=params,
    )
    handle_season_scoped_response(response, endpoint, season_id)
    body: dict[str, Any] = response.json()
    # Build invitation code lookup from included resources
    invitation_codes = build_invitation_code_lookup(body)
    # Parse teams and match invitation codes via relationships
    teams = []
    for item in body.get("data", []):
        team = _parse(item)
        # Look up invitation code from relationship
        invitation_code = get_invitation_code_from_relationship(item, invitation_codes)
        if invitation_code:
            # Update the team with the invitation code using model_copy
            team = team.model_copy(update={"invitation_code": invitation_code})

        teams.append(team)

    return teams


def get_team(session: Session, season_id: str, team_id: str) -> Team:
    """Get a single team by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        team_id (str): The team identifier to retrieve.

    Returns:
        Team: The :class:`Team` with the specified ID.

    Raises:
        GameSheetError: If the team is not found or for any other non-2xx response from the API.

    Notes:
        The single-team GET endpoint doesn't support including related invitations, so this function fetches
        all teams in the season (which does include invitations) and filters to the requested team. This
        ensures invitation_code is populated.
    """
    # The single-team endpoint (/api/seasons/{season_id}/teams/{team_id}) doesn't
    # honor the include=invitations parameter, so we use the list endpoint instead
    # which does properly include invitation data
    all_teams = list_teams(session, season_id)
    # Find the requested team
    for team in all_teams:
        if team.id == team_id:
            return team
    # Team not found
    _err_msg = (
        f"Team '{team_id}' not found in season '{season_id}'. "
        f"Make sure you're using a valid team ID and season ID."
    )
    raise GameSheetError(_err_msg)


def _upload_logo(session: Session, logo_path: str) -> str:
    """Upload a logo image and return its URL.

    Args:
        session (Session): An authenticated :class:`Session`.
        logo_path (str): Path to a local logo image file.

    Returns:
        str: The Cloudflare CDN URL for the uploaded logo.

    Raises:
        GameSheetError: If the file is not found, is not a valid image, or the upload fails.
        AuthenticationError: If the server returns 401.
    """
    from gamesheet_sdk.common.shared import upload_image

    return upload_image(session, logo_path, "logo")


def _handle_team_response_errors(
    response: Any,
    endpoint: str,
    team_id: str,
    season_id: str,
) -> None:
    """Check response for common errors and raise appropriate exceptions.

    Args:
        response (Any): The HTTP response object.
        endpoint (str): The API endpoint that was called.
        team_id (str): The team identifier.
        season_id (str): The season identifier.

    Raises:
        AuthenticationError: If the response is 401.
        GameSheetError: For 404 or other non-2xx responses.
    """
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 404:
        _err_msg = errors.ERROR_MSG_404_TEAM.format(
            team_id=team_id,
            season_id=season_id,
        )
        raise GameSheetError(_err_msg)

    if response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_GENERIC_HTTP.format(
            context="",
            endpoint=endpoint,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(_err_msg)


def update_team(
    session: Session,
    season_id: str,
    team_id: str,
    *,
    title: str | None = None,
    external_id: str | None = None,
    division_id: str | None = None,
    logo_path: str | None = None,
    remove_logo: bool = False,
) -> Team:
    """Update an existing team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. At least one field
    must be provided for update. The API requires sending the full team data, so this function first fetches
    the current team to preserve unchanged fields.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the team.
        team_id (str): The team identifier to update.
        title (str | None): Optional new team name/title.
        external_id (str | None): Optional new external identifier.
        division_id (str | None): Optional new division identifier.
        logo_path (str | None): Optional path to a new logo image file.
        remove_logo (bool): If True, remove the team's logo.

    Returns:
        Team: The updated :class:`Team`.

    Raises:
        GameSheetError: For any other non-2xx response.
        ValueError: If no fields are provided for update.
    """
    if all(v is None or v is False for v in (title, external_id, division_id, logo_path, remove_logo)):
        raise ValueError(errors.ERROR_MSG_AT_LEAST_ONE_FIELD)

    if logo_path and remove_logo:
        raise ValueError(errors.ERROR_MSG_CANNOT_UPLOAD_AND_REMOVE_LOGO)
    # Fetch current team data to get all fields
    get_endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    get_response = session.get(
        get_endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "association,league,season,division,players,coaches"},
    )
    _handle_team_response_errors(
        get_response,
        f"GET {get_endpoint}",
        team_id,
        season_id,
    )
    current_data: dict[str, Any] = get_response.json()
    current_attrs = current_data.get("data", {}).get("attributes", {})
    current_relationships = current_data.get("data", {}).get("relationships", {})
    # Build updated attributes, preserving current values for unchanged fields
    updated_attrs: dict[str, Any] = {
        "title": title if title is not None else current_attrs.get("title", ""),
        "external_id": external_id if external_id is not None else current_attrs.get("external_id"),
        "roster": current_attrs.get("roster", {}),
        "data": current_attrs.get("data", {}),
    }
    # Handle logo
    if logo_path:
        logo_url = _upload_logo(session, logo_path)
        updated_attrs["logo_url"] = logo_url
    elif remove_logo:
        updated_attrs["logo_url"] = ""  # Empty string for removal
    else:
        updated_attrs["logo_url"] = current_attrs.get("logo_url")
    # Build updated relationships, preserving current values for unchanged fields
    updated_division_id = (
        division_id
        if division_id is not None
        else current_relationships.get("division", {}).get("data", {}).get("id")
    )
    update_endpoint = f"/api/seasons/{season_id}/teams-v2/{team_id}"
    payload = {
        "data": {
            "id": team_id,
            "type": "teams",
            "attributes": updated_attrs,
            "relationships": {
                "division": {
                    "data": {
                        "id": updated_division_id,
                        "type": "divisions",
                    },
                },
            },
        },
    }
    update_response = session.patch(
        update_endpoint,
        json=payload,
        headers={
            "Accept": JSONAPI_CONTENT_TYPE,
            "Content-Type": JSONAPI_CONTENT_TYPE,
        },
    )
    _handle_team_response_errors(
        update_response,
        f"PATCH {update_endpoint}",
        team_id,
        season_id,
    )
    # If removing logo, send additional DELETE request
    if remove_logo:
        delete_logo_endpoint = f"/api/seasons/{season_id}/teams-v2/{team_id}/logo"
        delete_response = session.delete(
            delete_logo_endpoint,
            headers=JSONAPI_HEADERS,
        )
        if delete_response.status_code >= 400:
            _err_msg = errors.ERROR_MSG_HTTP_DELETE.format(
                endpoint=delete_logo_endpoint,
                status_code=delete_response.status_code,
                text=repr(delete_response.text[:200]),
            )
            raise GameSheetError(_err_msg)

    body: dict[str, Any] = update_response.json()
    return _parse(body["data"])


def create_team(
    session: Session,
    season_id: str,
    title: str,
    division_id: str,
    *,
    external_id: str | None = None,
    logo_path: str | None = None,
) -> dict[str, Any]:
    """Create a new team within the specified season.

    This operation requires three sequential POSTs:
    1. Request an upload URL for the logo (if logo_path is provided)
    2. Upload the logo to the returned URL (if logo_path is provided)
    3. Create the team with the logo URL

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier to create the team in.
        title (str): The team name/title.
        division_id (str): The division identifier the team belongs to.
        external_id (str | None): Optional external identifier for the team.
        logo_path (str | None): Optional path to a local logo image file.

    Returns:
        dict[str, Any]: The server's response containing prototeam, seasonTeam, member, and invitation data.

    Raises:
        AuthenticationError: If the server returns 401.
        GameSheetError: For any other non-2xx response.
    """
    logo_url: str | None = None
    if logo_path:
        logo_url = _upload_logo(session, logo_path)

    create_endpoint = f"{BFF_API_BASE_URL}/dwg/seasons/{season_id}/teams"
    payload: dict[str, str | int] = {
        "title": title,
        "divisionId": int(division_id),
    }
    if external_id:
        payload["externalId"] = external_id

    if logo_url:
        payload["logo"] = logo_url

    create_response = session.post(create_endpoint, json=payload)
    if create_response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if create_response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_HTTP_POST.format(
            endpoint=create_endpoint,
            status_code=create_response.status_code,
            text=repr(create_response.text[:200]),
        )
        raise GameSheetError(_err_msg)

    result: dict[str, Any] = create_response.json()
    if result.get("status") != "success":
        _err_msg = f"Failed to create team: {result}"
        raise GameSheetError(_err_msg)

    data: dict[str, Any] = result["data"]
    return data


def delete_team(
    session: Session,
    season_id: str,
    team_id: str,
) -> None:
    """Delete a team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the team.
        team_id (str): The team identifier to delete.

    Raises:
        AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired -- run
            ``gamesheet-admin login`` to refresh).
        GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.delete(
        endpoint,
        headers=JSONAPI_HEADERS,
    )
    if response.status_code == 401:
        raise AuthenticationError(errors.ERROR_MSG_401_EXPIRED)

    if response.status_code == 404:
        _err_msg = errors.ERROR_MSG_404_TEAM.format(
            team_id=team_id,
            season_id=season_id,
        )
        raise GameSheetError(_err_msg)

    if response.status_code >= 400:
        _err_msg = errors.ERROR_MSG_HTTP_DELETE.format(
            endpoint=endpoint,
            status_code=response.status_code,
            text=repr(response.text[:200]),
        )
        raise GameSheetError(_err_msg)
