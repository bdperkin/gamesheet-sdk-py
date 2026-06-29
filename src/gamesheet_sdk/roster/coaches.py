# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coach roster operations."""

from __future__ import annotations

from typing import Any

from gamesheet_sdk.roster.helpers import get_team_for_roster_update, update_team_roster
from gamesheet_sdk.roster.models import Coach, parse_coach
from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response


def get_coach(session: Session, season_id: str, coach_id: str) -> Coach:
    """Get a single coach by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param coach_id: The coach identifier to retrieve.
    :type coach_id: str
    :returns: Return value.
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
    :type session: Session
    :param season_id: The season identifier whose coaches to list.
    :type season_id: str
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        season has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/coaches"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "teams,divisions"},
    )
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
    :type session: Session
    :param season_id: The season identifier to create the coach in.
    :type season_id: str
    :param first_name: Coach's first name.
    :type first_name: str
    :param last_name: Coach's last name.
    :type last_name: str
    :param external_id: Optional external identifier for the coach.
    :type external_id: str | None
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :type position: str | None
    :param team_id: Optional team identifier to associate the coach with.
    :type team_id: str | None
    :returns: Return value.
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


def update_coach(
    session: Session,
    season_id: str,
    coach_id: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    external_id: str | None = None,
    position: str | None = None,
) -> Coach:
    """Update an existing coach in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. At least one field
    must be provided for update.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the coach.
    :type season_id: str
    :param coach_id: The coach identifier to update.
    :type coach_id: str
    :param first_name: Optional updated first name.
    :type first_name: str | None
    :param last_name: Optional updated last name.
    :type last_name: str | None
    :param external_id: Optional updated external identifier.
    :type external_id: str | None
    :param position: Optional updated position.
    :type position: str | None
    :returns: The updated :class:`Coach`.
    :rtype: Coach
    :raises ValueError: If no fields are provided for update.
    """
    if all(v is None for v in (first_name, last_name, external_id, position)):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)
    # Fetch current coach to get all fields
    current_coach = get_coach(session, season_id, coach_id)
    # Build payload with updated values, preserving current for unchanged fields
    payload: dict[str, Any] = {
        "data": {
            "id": coach_id,
            "type": "coaches",
            "attributes": {
                "first_name": first_name if first_name is not None else current_coach.first_name,
                "last_name": last_name if last_name is not None else current_coach.last_name,
            },
        },
    }
    # Add optional fields
    if external_id is not None:
        payload["data"]["attributes"]["external_id"] = external_id
    elif current_coach.external_id:
        payload["data"]["attributes"]["external_id"] = current_coach.external_id
    if position is not None:
        payload["data"]["attributes"]["position"] = position
    elif current_coach.position:
        payload["data"]["attributes"]["position"] = current_coach.position
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH coach")
    body: dict[str, Any] = response.json()
    return parse_coach(body["data"])


def list_team_coaches(session: Session, season_id: str, team_id: str) -> list[Coach]:
    """Return every coach for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier whose coaches to list.
    :type team_id: str
    :returns: A list of :class:`Coach`, in the order the server returned them. The list may be empty if the
        team has no coaches.
    :rtype: list[Coach]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(
        endpoint,
        headers=JSONAPI_HEADERS,
        params={"include": "players,coaches"},
    )
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


def get_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    coach_id: str,
) -> Coach:
    """Get a single coach from a team's roster.

    This function retrieves team roster metadata (position, status, signature) that is only available in the
    team context, unlike :func:`get_coach` which fetches from the season-level coaches endpoint without roster
    metadata. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param coach_id: The coach identifier to retrieve.
    :type coach_id: str
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

    This function performs two operations: (1) creates the coach at the season level, (2) updates the
    team's roster to include the new coach with position and other metadata.  The supplied
    :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to add the coach to.
    :type team_id: str
    :param first_name: Coach's first name.
    :type first_name: str
    :param last_name: Coach's last name.
    :type last_name: str
    :param external_id: Optional external identifier for the coach.
    :type external_id: str | None
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :type position: str | None
    :returns: Return value.
    :rtype: Coach
    """
    # Step 1: Create the coach at the season level (without "type" field for team context)
    endpoint = f"/api/seasons/{season_id}/coaches"
    payload: dict[str, Any] = {
        "data": {"attributes": {"first_name": first_name, "last_name": last_name}},
    }
    if external_id:
        payload["data"]["attributes"]["external_id"] = external_id
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST coach")
    coach = parse_coach(response.json()["data"])
    # Step 2: Fetch current team data and update roster
    team_data = get_team_for_roster_update(session, season_id, team_id)
    roster = team_data.get("data", {}).get("attributes", {}).get("roster", {})
    coaches_roster = roster.get("coaches", [])
    coach_entry: dict[str, Any] = {"id": coach.id, "status": "coaching"}
    if position:
        coach_entry["position"] = position
    coaches_roster.append(coach_entry)
    roster["coaches"] = coaches_roster
    # Step 3: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        team_data.get("data", {}).get("attributes", {}),
        team_data.get("data", {}).get("relationships", {}),
    )
    # Return the coach with roster metadata populated
    if position:
        coach.position = position
    coach.status = "coaching"
    return coach


def update_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    coach_id: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    external_id: str | None = None,
    position: str | None = None,
) -> Coach:
    """Update a coach and update the team's roster in one operation.

    This function performs two operations: (1) updates the coach at the season level,
    (2) updates the team's roster with any position changes.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier.
    :type team_id: str
    :param coach_id: The coach identifier to update.
    :type coach_id: str
    :param first_name: Optional updated first name.
    :type first_name: str | None
    :param last_name: Optional updated last name.
    :type last_name: str | None
    :param external_id: Optional updated external identifier.
    :type external_id: str | None
    :param position: Optional updated position.
    :type position: str | None
    :returns: The updated :class:`Coach`.
    :rtype: Coach
    :raises ValueError: If no fields are provided for update.
    """
    if all(v is None for v in (first_name, last_name, external_id, position)):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)
    # Step 1: Update the coach at season level (without "type" field for team context)
    current_coach = get_team_coach(session, season_id, team_id, coach_id)
    payload: dict[str, Any] = {
        "data": {
            "id": coach_id,
            "attributes": {
                "first_name": first_name if first_name is not None else current_coach.first_name,
                "last_name": last_name if last_name is not None else current_coach.last_name,
            },
        },
    }
    # Add optional fields
    if external_id is not None:
        payload["data"]["attributes"]["external_id"] = external_id
    elif current_coach.external_id:
        payload["data"]["attributes"]["external_id"] = current_coach.external_id
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH team coach")
    body: dict[str, Any] = response.json()
    coach = parse_coach(body["data"])
    # Step 2: Update team roster with position changes if needed
    if position is not None and position != current_coach.position:
        team_data = get_team_for_roster_update(session, season_id, team_id)
        roster = team_data.get("data", {}).get("attributes", {}).get("roster", {})
        # Update the coach's position in the roster
        for coach_entry in roster.get("coaches", []):
            if coach_entry.get("id") == coach_id:
                coach_entry["position"] = position
                break
        update_team_roster(
            session,
            season_id,
            team_id,
            roster,
            team_data.get("data", {}).get("attributes", {}),
            team_data.get("data", {}).get("relationships", {}),
        )
        coach.position = position
    coach.status = getattr(current_coach, "status", None) or "coaching"
    return coach


def assign_coach(
    session: Session,
    season_id: str,
    coach_id: str,
    team_id: str,
    *,
    position: str | None = None,
) -> Coach:
    """Assign an existing coach to a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param coach_id: The coach identifier to assign.
    :type coach_id: str
    :param team_id: The team identifier to assign the coach to.
    :type team_id: str
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :type position: str | None
    :returns: The :class:`Coach` with roster metadata populated.
    :rtype: Coach
    :raises GameSheetError: If the coach is already assigned to the team.
    """
    # Step 1: Fetch the coach to ensure it exists
    coach = get_coach(session, season_id, coach_id)
    # Step 2: Fetch current team data
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 3: Add coach to roster
    roster = current_attrs.get("roster", {})
    coaches_roster = roster.get("coaches", [])
    # Check if coach is already on the roster
    for existing_coach in coaches_roster:
        if existing_coach.get("id") == coach_id:
            from gamesheet_sdk.exceptions import GameSheetError

            msg = f"Coach {coach_id} is already assigned to team {team_id}"
            raise GameSheetError(msg)
    coach_entry: dict[str, Any] = {"id": coach_id, "status": "coaching"}
    if position:
        coach_entry["position"] = position
    coaches_roster.append(coach_entry)
    roster["coaches"] = coaches_roster
    # Step 4: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        current_attrs,
        current_relationships,
    )
    # Return the coach with roster metadata populated
    if position:
        coach.position = position
    coach.status = "coaching"
    return coach


def unassign_coach(
    session: Session,
    season_id: str,
    coach_id: str,
    team_id: str,
) -> None:
    """Unassign a coach from a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param coach_id: The coach identifier to unassign.
    :type coach_id: str
    :param team_id: The team identifier to unassign the coach from.
    :type team_id: str
    :raises GameSheetError: If the coach is not assigned to the team.
    """
    # Step 1: Fetch current team data
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 2: Remove coach from roster
    roster = current_attrs.get("roster", {})
    coaches_roster = roster.get("coaches", [])
    # Find and remove the coach
    original_count = len(coaches_roster)
    coaches_roster = [c for c in coaches_roster if c.get("id") != coach_id]
    if len(coaches_roster) == original_count:
        from gamesheet_sdk.exceptions import GameSheetError

        msg = f"Coach {coach_id} is not assigned to team {team_id}"
        raise GameSheetError(msg)
    roster["coaches"] = coaches_roster
    # Step 3: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        current_attrs,
        current_relationships,
    )


def assign_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    coach_id: str,
    *,
    position: str | None = None,
) -> Coach:
    """Assign an existing coach to a team's roster (team-scoped alias).

    This is an alias for :func:`assign_coach` provided for consistency with the team-scoped command structure.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to assign the coach to.
    :type team_id: str
    :param coach_id: The coach identifier to assign.
    :type coach_id: str
    :param position: Optional position (Head Coach, Assistant Coach, etc.).
    :type position: str | None
    :returns: Return value.
    :rtype: Coach
    """
    return assign_coach(session, season_id, coach_id, team_id, position=position)


def unassign_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    coach_id: str,
) -> None:
    """Unassign a coach from a team's roster (team-scoped alias).

    This is an alias for :func:`unassign_coach` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier.
    :type season_id: str
    :param team_id: The team identifier to unassign the coach from.
    :type team_id: str
    :param coach_id: The coach identifier to unassign.
    :type coach_id: str
    """
    unassign_coach(session, season_id, coach_id, team_id)
