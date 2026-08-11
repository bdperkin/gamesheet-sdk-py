# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Location operations for games."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gamesheet_sdk.admin.games.models import Location
from gamesheet_sdk.common import errors
from gamesheet_sdk.common.constants import API_LOCATIONS, DEFAULT_BASE_URL
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.shared import handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.common.session import Session


def list_locations(session: Session) -> list[Location]:
    """Return the list of valid locations.

    Fetches the current list of locations/venues from the main API. The returned locations include venue name
    and surface name which together form the location identifier used when creating or updating scheduled
    games.

    Args:
        session (Session): An authenticated :class:`Session`.

    Returns:
        list[Location]: A list of :class:`Location` objects.

    Raises:
        AuthenticationError: If the server returns 401 or 403.
        GameSheetError: For any other non-2xx response.
    """
    url = f"{DEFAULT_BASE_URL}{API_LOCATIONS}"
    response = session.get(url)
    handle_response(response, url, "GET locations")
    body: dict[str, Any] = response.json()
    return [Location(**loc) for loc in body.get("data", [])]


def get_location(session: Session, location_id: str) -> Location:
    """Get a specific location by ID.

    Fetches the list of all locations and returns the one matching the given ID.

    Args:
        session (Session): An authenticated :class:`Session`.
        location_id (str): The location UUID to retrieve.

    Returns:
        Location: The :class:`Location` with the specified ID.

    Raises:
        GameSheetError: If the location ID is not found.
    """
    locations = list_locations(session)
    for loc in locations:
        if loc.id == location_id:
            return loc

    msg = errors.ERROR_MSG_LOCATION_NOT_FOUND.format(location_id=location_id)
    raise GameSheetError(msg)


def validate_location(session: Session, location: str) -> str:
    """Validate a location and return the correctly-cased version.

    Fetches the list of valid locations and performs a case-insensitive match against the concatenation of
    location_name + " " + surface_name. Returns the correctly-cased full location name.

    Args:
        session (Session): An authenticated :class:`Session`.
        location (str): The location string to validate (case- insensitive).

    Returns:
        str: The correctly-cased location string.

    Raises:
        GameSheetError: If the location is not valid.
    """
    if not location:
        return location

    locations = list_locations(session)
    location_lower = location.lower()
    for loc in locations:
        full_name = loc.full_name()
        if full_name.lower() == location_lower:
            return full_name
    # If not found, show a helpful error with examples (limited to first 5)
    examples = [loc.full_name() for loc in locations[:5]]
    joined_examples = ", ".join(examples)
    msg = (
        f"Invalid location '{location}'. Location must match the format "
        f"'<location_name> <surface_name>' (case-insensitive). "
        f"Examples: {joined_examples}... "
        f"Use 'gamesheet-admin locations list' to see all valid locations."
    )
    raise GameSheetError(msg)
