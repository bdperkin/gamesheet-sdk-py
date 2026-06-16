# pylint: disable=too-many-lines
"""GameSheet teams: competing organizations within a season.

A team is a competing organization within a season (e.g., "Raleigh Raptors", "Durham Bulls", etc.). Each team
belongs to exactly one season and may be associated with a division. The dashboard displays teams after
navigating into a season view. This module talks to the GameSheet JSON:API at
``/api/seasons/{season_id}/teams`` directly with the lightweight :class:`gamesheet_sdk.Session` path -- no
Playwright needed for read-only access once a bearer token has been obtained (typically by reading the SPA's
``accessToken`` from the saved browser storage state via :func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

import mimetypes
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Team(BaseModel):
    """A single team.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{season_id}/teams`` to a flat
    typed model.
    """

    id: str = Field(description="Team identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
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
    """Flatten a JSON:API resource object into a :class:`Team`."""
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

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose teams to list.
    :type season_id: str
    :returns: A list of :class:`Team`, in the order the server returned them. The list may be empty if the
        season has no teams.
    :rtype: list[Team]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
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
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
        params=params,
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
    # Build invitation code lookup from included resources
    invitation_codes: dict[str, str] = {}
    for item in body.get("included", []):
        if item.get("type") == "invitations":
            invitation_id = item.get("id")
            code = item.get("attributes", {}).get("code")
            if invitation_id and code:
                invitation_codes[invitation_id] = code
    # Parse teams and match invitation codes via relationships
    teams = []
    for item in body.get("data", []):
        team = _parse(item)
        # Look up invitation code from relationship
        inv_rel = item.get("relationships", {}).get("invitations", {}).get("data")
        if inv_rel:
            # invitations relationship can be single object or array
            inv_id = inv_rel[0]["id"] if isinstance(inv_rel, list) else inv_rel.get("id")
            if inv_id and inv_id in invitation_codes:
                # Update the team with the invitation code using model_copy
                team = team.model_copy(update={"invitation_code": invitation_codes[inv_id]})
        teams.append(team)
    return teams


def get_team(session: Session, season_id: str, team_id: str) -> Team:  # noqa: DOC503
    """Get a single team by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param team_id: The team identifier to retrieve.
    :type team_id: str
    :returns: The :class:`Team` with the specified ID.
    :rtype: Team
    :raises GameSheetError: If the team is not found or for any other non-2xx response from the API.
    :raises AuthenticationError: If the server returns 401 (raised by the internal call to
        :func:`list_teams`). Run ``gamesheet-sdk-py login`` to refresh the bearer token.

    .. note::
        The single-team GET endpoint doesn't support including related invitations,
        so this function fetches all teams in the season (which does include invitations)
        and filters to the requested team. This ensures invitation_code is populated.
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
        f"Make sure you're using a valid team ID and season ID.",
    )
    raise GameSheetError(_err_msg)


def _upload_logo(session: Session, logo_path: str) -> str:
    """Upload a logo image and return its URL."""
    logo_file_path = Path(logo_path)
    if not logo_file_path.exists():
        _err_msg = (f"Logo file not found: {logo_path}",)
        raise GameSheetError(_err_msg)

    mime_type, _ = mimetypes.guess_type(logo_path)
    if not mime_type or not mime_type.startswith("image/"):
        _err_msg = (f"Invalid image file: {logo_path}",)
        raise GameSheetError(_err_msg)

    upload_url_endpoint = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url"
    upload_url_response = session.post(upload_url_endpoint)

    if upload_url_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if upload_url_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url_endpoint} returned HTTP {upload_url_response.status_code}: "
            f"{upload_url_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

    upload_data: dict[str, Any] = upload_url_response.json()
    if upload_data.get("status") != "success":
        _err_msg = (f"Failed to get upload URL: {upload_data}",)
        raise GameSheetError(_err_msg)

    upload_url: str = upload_data["data"]["uploadURL"]
    image_id: str = upload_data["data"]["id"]

    with logo_file_path.open("rb") as f:
        upload_response = session.post(
            upload_url,
            files={"file": (logo_file_path.name, f, mime_type)},
        )

    if upload_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url} returned HTTP {upload_response.status_code}: "
            f"{upload_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

    upload_result: dict[str, Any] = upload_response.json()
    if not upload_result.get("success"):
        _err_msg = (f"Failed to upload logo: {upload_result}",)
        raise GameSheetError(_err_msg)

    return f"https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/{image_id}"


# pylint: disable-next=too-many-locals,too-many-branches
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
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    At least one field must be provided for update. The API requires sending the full team data, so this
    function first fetches the current team to preserve unchanged fields.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the team.
    :type season_id: str
    :param team_id: The team identifier to update.
    :type team_id: str
    :param title: Optional new team name/title.
    :type title: str | None
    :param external_id: Optional new external identifier.
    :type external_id: str | None
    :param division_id: Optional new division identifier.
    :type division_id: str | None
    :param logo_path: Optional path to a new logo image file.
    :type logo_path: str | None
    :param remove_logo: If True, remove the team's logo.
    :type remove_logo: bool
    :returns: The updated :class:`Team`.
    :rtype: Team
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    :raises ValueError: If no fields are provided for update.
    """
    if all(v is None or v is False for v in (title, external_id, division_id, logo_path, remove_logo)):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)

    if logo_path and remove_logo:
        msg = "Cannot both upload a logo and remove it"
        raise ValueError(msg)

    # Fetch current team data to get all fields
    get_endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    get_response = session.get(
        get_endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
        params={"include": "association,league,season,division,players,coaches"},
    )

    if get_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if get_response.status_code == 404:
        _err_msg = (
            f"Team '{team_id}' not found (HTTP 404). "
            f"Make sure you're using a valid team ID. "
            f"To get valid team IDs, run: gamesheet-sdk-py teams list --season-id <SEASON_ID>",
        )
        raise GameSheetError(_err_msg)
    if get_response.status_code >= 400:
        _err_msg = (
            f"GET {get_endpoint} returned HTTP {get_response.status_code}: {get_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

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
        headers={"Accept": _JSONAPI_CONTENT_TYPE, "Content-Type": _JSONAPI_CONTENT_TYPE},
    )

    if update_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if update_response.status_code == 404:
        _err_msg = (
            f"Team '{team_id}' not found (HTTP 404). "
            f"Make sure you're using a valid team ID. "
            f"To get valid team IDs, run: gamesheet-sdk-py teams list --season-id <SEASON_ID>",
        )
        raise GameSheetError(_err_msg)
    if update_response.status_code >= 400:
        _err_msg = (
            f"PATCH {update_endpoint} returned HTTP {update_response.status_code}: "
            f"{update_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

    # If removing logo, send additional DELETE request
    if remove_logo:
        delete_logo_endpoint = f"/api/seasons/{season_id}/teams-v2/{team_id}/logo"
        delete_response = session.delete(
            delete_logo_endpoint,
            headers={"Accept": _JSONAPI_CONTENT_TYPE},
        )
        if delete_response.status_code >= 400:
            _err_msg = (
                f"DELETE {delete_logo_endpoint} returned HTTP {delete_response.status_code}: "
                f"{delete_response.text[:200]!r}",
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

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier to create the team in.
    :type season_id: str
    :param title: The team name/title.
    :type title: str
    :param division_id: The division identifier the team belongs to.
    :type division_id: str
    :param external_id: Optional external identifier for the team.
    :type external_id: str | None
    :param logo_path: Optional path to a local logo image file.
    :type logo_path: str | None
    :returns: The server's response containing prototeam, seasonTeam, member, and invitation data.
    :rtype: dict[str, Any]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    logo_url: str | None = None
    if logo_path:
        logo_url = _upload_logo(session, logo_path)

    create_endpoint = f"https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/seasons/{season_id}/teams"
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
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if create_response.status_code >= 400:
        _err_msg = (
            f"POST {create_endpoint} returned HTTP {create_response.status_code}: "
            f"{create_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

    result: dict[str, Any] = create_response.json()
    if result.get("status") != "success":
        _err_msg = (f"Failed to create team: {result}",)
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

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the team.
    :type season_id: str
    :param team_id: The team identifier to delete.
    :type team_id: str
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"

    response = session.delete(
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
            f"Team '{team_id}' not found (HTTP 404). "
            f"Make sure you're using a valid team ID. "
            f"To get valid team IDs, run: gamesheet-sdk-py teams list --season-id <SEASON_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"DELETE {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
