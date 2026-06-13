"""GameSheet teams: competing organizations within a season.

A team is a competing organization within a season (e.g., "Raleigh Raptors", "Durham Bulls", etc.). Each team
belongs to exactly one season and may be associated with a division. The dashboard displays teams after
navigating into a season view. This module talks to the GameSheet JSON:API at
``/api/seasons/{season_id}/teams`` directly with the lightweight :class:`gamesheet_sdk.Session` path -- no
Playwright needed for read-only access once a bearer token has been obtained (typically by reading the SPA's
``accessToken`` from the saved browser storage state via :func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
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
    logo = attrs.get("logo")
    invitation_code = attrs.get("invitation_code")
    player_count = attrs.get("player_count")
    coach_count = attrs.get("coach_count")
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
    # Request sparse fieldset including logo, invitation_code, player_count, coach_count
    params = {
        "fields[teams]": "title,logo,invitation_code,player_count,coach_count,created_at,updated_at",
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
    return [_parse(item) for item in body.get("data", [])]
