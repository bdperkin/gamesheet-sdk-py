# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coach roster operations."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.roster.helpers import (
    get_team_for_roster_update,
    update_team_roster,
)
from gamesheet_sdk.admin.roster.models import Coach, parse_coach
from gamesheet_sdk.common import errors
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def get_coach(session: Session, season_id: str, coach_id: str) -> Coach:
    """Get a single coach by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The parent season identifier.
        coach_id (str): The coach identifier to retrieve.

    Returns:
        Coach: Return value.
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier whose coaches to list.

    Returns:
        list[Coach]: A list of :class:`Coach`, in the order the server returned them. The list may be empty if
            the season has no coaches.
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
    return [parse_coach(item) for item in body.get("data", [])]


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier to create the coach in.
        first_name (str): Coach's first name.
        last_name (str): Coach's last name.
        external_id (str | None): Optional external identifier for the coach.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).
        team_id (str | None): Optional team identifier to associate the coach with.

    Returns:
        Coach: Return value.
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the coach.
        coach_id (str): The coach identifier to update.
        first_name (str | None): Optional updated first name.
        last_name (str | None): Optional updated last name.
        external_id (str | None): Optional updated external identifier.
        position (str | None): Optional updated position.

    Returns:
        Coach: The updated :class:`Coach`.

    Raises:
        ValueError: If no fields are provided for update.
    """
    if all(v is None for v in (first_name, last_name, external_id, position)):
        raise ValueError(errors.ERROR_MSG_AT_LEAST_ONE_FIELD)
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier whose coaches to list.

    Returns:
        list[Coach]: A list of :class:`Coach`, in the order the server returned them. The list may be empty if
            the team has no coaches.
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        coach_id (str): The coach identifier to retrieve.

    Returns:
        Coach: The :class:`Coach` with team roster metadata populated.

    Raises:
        GameSheetError: If the coach is not found on the team's roster.
    """
    coaches = list_team_coaches(session, season_id, team_id)
    for coach in coaches:
        if coach.id == coach_id:
            return coach

    msg = f"Coach {coach_id} not found on team {team_id}"
    raise GameSheetError(msg)


def _build_coach_roster_entry(
    coach_id: str,
    *,
    position: str | None = None,
) -> dict[str, Any]:
    """Build a coach roster entry dict for team roster updates.

    Args:
        coach_id (str): The coach identifier.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).

    Returns:
        dict[str, Any]: Dictionary containing roster entry data ready for team roster update.
    """
    entry: dict[str, Any] = {
        "id": coach_id,
        "status": "coaching",
    }
    if position:
        entry["position"] = position

    return entry


def _populate_coach_metadata(
    coach: Coach,
    *,
    position: str | None = None,
) -> None:
    """Populate coach object with roster metadata.

    Mutates the Coach object in place to set roster-specific fields.

    Args:
        coach (Coach): The Coach instance to populate.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).
    """
    if position:
        coach.position = position

    coach.status = "coaching"


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

    This function performs two operations: (1) creates the coach at the season level, (2) updates the team's
    roster to include the new coach with position and other metadata.  The supplied :class:`Session` must
    already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise
    unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to add the coach to.
        first_name (str): Coach's first name.
        last_name (str): Coach's last name.
        external_id (str | None): Optional external identifier for the coach.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).

    Returns:
        Coach: Return value.
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
    coach_entry = _build_coach_roster_entry(coach.id, position=position)
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
    _populate_coach_metadata(coach, position=position)
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        coach_id (str): The coach identifier to update.
        first_name (str | None): Optional updated first name.
        last_name (str | None): Optional updated last name.
        external_id (str | None): Optional updated external identifier.
        position (str | None): Optional updated position.

    Returns:
        Coach: The updated :class:`Coach`.

    Raises:
        ValueError: If no fields are provided for update.
    """
    if all(v is None for v in (first_name, last_name, external_id, position)):
        raise ValueError(errors.ERROR_MSG_AT_LEAST_ONE_FIELD)
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


def delete_coach(session: Session, season_id: str, coach_id: str) -> None:
    """Delete a coach from the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier containing the coach.
        coach_id (str): The coach identifier to delete.
    """
    endpoint = f"/api/seasons/{season_id}/coaches/{coach_id}"
    response = session.delete(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "DELETE coach")


def unassign_coach(
    session: Session,
    season_id: str,
    coach_id: str,
    team_id: str,
) -> None:
    """Unassign a coach from a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        coach_id (str): The coach identifier to unassign.
        team_id (str): The team identifier to unassign the coach from.

    Raises:
        GameSheetError: If the coach is not assigned to the team.
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


def delete_team_coach(
    session: Session,
    season_id: str,
    team_id: str,
    coach_id: str,
) -> None:
    """Delete a coach from a team's roster and the season.

    This function performs two operations: (1) removes the coach from the team's roster,
    (2) deletes the coach at the season level. The supplied :class:`Session` must already
    carry a bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated
    and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier.
        coach_id (str): The coach identifier to delete.
    """
    # Step 1: Remove coach from team roster (may not be on this team's roster)
    with suppress(GameSheetError):
        unassign_coach(session, season_id, coach_id, team_id)
    # Step 2: Delete the coach at the season level
    delete_coach(session, season_id, coach_id)


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        coach_id (str): The coach identifier to assign.
        team_id (str): The team identifier to assign the coach to.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).

    Returns:
        Coach: The :class:`Coach` with roster metadata populated.

    Raises:
        GameSheetError: If the coach is already assigned to the team.
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
            msg = f"Coach {coach_id} is already assigned to team {team_id}"
            raise GameSheetError(msg)

    coach_entry = _build_coach_roster_entry(coach_id, position=position)
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
    _populate_coach_metadata(coach, position=position)
    return coach


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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to assign the coach to.
        coach_id (str): The coach identifier to assign.
        position (str | None): Optional position (Head Coach, Assistant Coach, etc.).

    Returns:
        Coach: Return value.
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

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        team_id (str): The team identifier to unassign the coach from.
        coach_id (str): The coach identifier to unassign.
    """
    unassign_coach(session, season_id, coach_id, team_id)


def get_coach_penalty_report(
    session: Session,
    season_id: str,
    coach_id: str,
) -> dict[str, Any]:
    """Fetch penalty report for a coach.

    First retrieves the coach to get their external_id, then fetches the penalty report from the BFF API. The
    supplied :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.

    Args:
        session (Session): An authenticated :class:`Session`.
        season_id (str): The season identifier.
        coach_id (str): The coach identifier.

    Returns:
        dict[str, Any]: Penalty report data including coach_games, coach_penalties, rostered_coaches, and
            season_coaches.
    """
    coach = get_coach(session, season_id, coach_id)
    external_id = coach.external_id
    bff_url = f"https://bff-dashboard-api-awy26srzoa-nn.a.run.app/reports/coach-penalty-report/{external_id}"
    response = session.get(bff_url)
    handle_response(response, bff_url, "GET coach penalty report")
    body: dict[str, Any] = response.json()
    if body.get("status") != "success":
        status = body.get("status")
        msg = errors.ERROR_MSG_PENALTY_REPORT_API_STATUS.format(status=status)
        raise GameSheetError(msg)

    data: dict[str, Any] = body["data"]
    return data
