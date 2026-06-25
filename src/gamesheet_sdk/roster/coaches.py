"""Coach roster operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.roster.helpers import get_team_for_roster_update, update_team_roster
from gamesheet_sdk.roster.models import Coach, parse_coach
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session


def get_coach(session: Session, season_id: str, coach_id: str) -> Coach:
    """Get a single coach by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The parent season identifier.
    :param coach_id: The coach identifier to retrieve.
    :returns: The :class:`Coach` with the specified ID.
    :rtype: Coach
    """
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET coach")
    body: dict[str, Any] = response.json()
    return parse_coach(body["data"])


def list_coaches(session: Session, season_id: str) -> list[Coach]:
    """Return every coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier whose coaches to list.
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        season has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "teams,divisions"})
    handle_response(response, endpoint, "GET coaches")
    body: dict[str, Any] = response.json()
    # Parse all coaches
    all_coaches = [parse_coach(item) for item in body.get("data", [])]
    return all_coaches


def create_coach(
    session: Session,
    season_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    position: str | None = None,
    team_id: str | None = None,
) -> Coach:
    """Create a new coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier to create the coach in.
    :param first_name: Coach's first name.
    :param last_name: Coach's last name.
    :param external_id: Optional external identifier for the coach.
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :param team_id: Optional team identifier to associate the coach with.
    :returns: The created :class:`Coach`.
    :rtype: Coach
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    payload: dict[str, Any] = {
        "data": {
            "type": "coaches",
            "attributes": {
                "first_name": first_name,
                "last_name": last_name,
            },
        },
    }
    if external_id:
        payload["data"]["attributes"]["external_id"] = external_id
    if position:
        payload["data"]["attributes"]["position"] = position
    if team_id:
        payload["data"]["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST coach")
    body: dict[str, Any] = response.json()
    return parse_coach(body["data"])


def list_team_coaches(session: Session, season_id: str, team_id: str) -> list[Coach]:
    """Return every coach for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier whose coaches to list.
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        team has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "players,coaches"})
    handle_response(response, endpoint, "GET team")
    body: dict[str, Any] = response.json()
    included_coaches = {
        item["id"]: item
        for item in body.get(
            "included",
            [],
        )
        if item.get("type") == "coaches"
    }
    roster_metadata = {
        str(c["id"]): c
        for c in body.get("data", {}).get("attributes", {}).get("roster", {}).get("coaches", [])
    }
    coaches = []
    for coach_id, coach_data in included_coaches.items():
        coach = parse_coach(coach_data)
        if coach_id in roster_metadata:
            metadata = roster_metadata[coach_id]
            coach.position = metadata.get("position")
            coach.status = metadata.get("status")
            coach.signature = metadata.get("signature")
        coaches.append(coach)
    return coaches


def get_team_coach(session: Session, season_id: str, team_id: str, coach_id: str) -> Coach:
    """Get a single coach from a team's roster.

    This function retrieves team roster metadata (position, status, signature) that is only available in the
    team context, unlike :func:`get_coach` which fetches from the season-level coaches endpoint without roster
    metadata.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :param coach_id: The coach identifier to retrieve.
    :returns: The :class:`Coach` with team roster metadata populated.
    :rtype: Coach
    :raises GameSheetError: If the coach is not found on the team's roster.
    """
    coaches = list_team_coaches(session, season_id, team_id)
    for coach in coaches:
        if coach.id == coach_id:
            return coach
    from gamesheet_sdk.exceptions import GameSheetError

    msg = f"Coach {coach_id} not found on team {team_id}"
    raise GameSheetError(msg)


def create_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    position: str | None = None,
) -> Coach:
    """Create a new coach and add to the specified team's roster.

    This function performs two operations: (1) creates the coach at the season level,
    (2) updates the team's roster to include the new coach with position and other metadata.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to add the coach to.
    :param first_name: Coach's first name.
    :param last_name: Coach's last name.
    :param external_id: Optional external identifier for the coach.
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :returns: The created :class:`Coach`.
    :rtype: Coach
    """
    # Step 1: Create the coach at the season level
    coach = create_coach(session, season_id, first_name, last_name, external_id=external_id)
    # Step 2: Fetch current team data
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 3: Add coach to roster
    roster = current_attrs.get("roster", {})
    coaches_roster = roster.get("coaches", [])
    coach_entry: dict[str, Any] = {"id": coach.id, "status": "coaching"}
    if position:
        coach_entry["position"] = position
    coaches_roster.append(coach_entry)
    roster["coaches"] = coaches_roster
    # Step 4: Update team roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    # Return the coach with roster metadata populated
    if position:
        coach.position = position
    coach.status = "coaching"
    return coach
