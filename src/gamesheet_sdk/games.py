# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""GameSheet games: scheduled, completed, and bracket games within a season.

Games represent matchups between teams. This module provides access to three game views:

- **Scheduled games:** Upcoming/future games
- **Completed games:** Finished games with results
- **Bracket games:** Playoff/tournament games

The games data is retrieved from the BFF (Backend For Frontend) API at
the ``/games-list/v1`` endpoint with various filter parameters.

For scheduled game mutations (create/update/delete), the JSON:API-style
``/api/seasons/{id}/schedule`` endpoint is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk import errors
from gamesheet_sdk.constants import (
    API_LOCATIONS,
    API_SEASONS_GAMES,
    API_SEASONS_SCHEDULE,
    API_SEASONS_SCHEDULE_GAME,
    BFF_API_BASE_URL,
    BFF_BROADCASTERS,
    BFF_GAMES_LIST,
    DEFAULT_BASE_URL,
    DEFAULT_GAMES_LIMIT,
    SCORESHEET_SERVICE_BASE_URL,
    SCORESHEET_SERVICE_GAME,
    VALID_GAME_TYPES,
)
from gamesheet_sdk.exceptions import GameSheetError
from gamesheet_sdk.session import Session
from gamesheet_sdk.shared import check_bff_response_status, handle_response


class Broadcaster(BaseModel):
    """A broadcaster/streaming service.

    :var key: Broadcaster key identifier (e.g., "LIVEBARN").
    :var title: Display name of the broadcaster.
    :var url: Broadcaster website URL.
    """

    key: str = Field(description="Broadcaster key identifier.")
    title: str = Field(description="Display name of the broadcaster.")
    url: str = Field(description="Broadcaster website URL.")


class Location(BaseModel):
    """A game location/venue with surface.

    :var id: Location identifier (UUID).
    :var location_name: Venue name (e.g., "140 Ice Den").
    :var surface_name: Surface/rink name (e.g., "Rink #1").
    :var city: City where the location is located.
    :var province_state: Province or state.
    :var country: Country.
    """

    id: str = Field(description="Location identifier (UUID).")
    location_name: str = Field(description="Venue name.")
    surface_name: str = Field(description="Surface/rink name.")
    city: str = Field(description="City where the location is located.")
    province_state: str = Field(description="Province or state.")
    country: str = Field(description="Country.")

    def full_name(self) -> str:
        """Return the full location name as location_name + surface_name.

        :returns: Combined location and surface name.
        :rtype: str
        """
        return f"{self.location_name} {self.surface_name}"


class TeamInfo(BaseModel):
    """Team information within a game.

    :var id: Team identifier.
    :var title: Team name.
    :var division_id: Division identifier.
    :var division_title: Division name.
    """

    id: int = Field(description="Team identifier.")
    title: str = Field(description="Team name.")
    division_id: int | None = Field(
        default=None,
        alias="divisionId",
        description="Division identifier.",
    )
    division_title: str | None = Field(
        default=None,
        alias="divisionTitle",
        description="Division name.",
    )


class Game(BaseModel):
    """A single game.

    Maps the game objects from the BFF API response.

    :var id: Game identifier.
    :var status: Game status (e.g., completed, scheduled).
    :var date: Game date (YYYY-MM-DD).
    :var time: Game start time.
    :var end_time: Game end time.
    :var time_zone_name: Time zone name.
    :var location: Venue/location of the game.
    :var game_number: Game number or identifier.
    :var game_type: Game type (regular, playoff, etc.).
    :var visitor: Visiting team information.
    :var home: Home team information.
    :var visitor_score: Visitor team score.
    :var home_score: Home team score.
    :var has_shootout: Whether game had a shootout.
    :var has_overtime: Whether game had overtime.
    :var viewed: Whether the user has viewed this game.
    """

    id: int = Field(description="Game identifier.")
    status: str = Field(description="Game status (e.g., completed, scheduled).")
    date: str = Field(description="Game date (YYYY-MM-DD).")
    time: str | None = Field(default=None, description="Game start time.")
    end_time: str | None = Field(
        default=None,
        alias="endTime",
        description="Game end time.",
    )
    time_zone_name: str | None = Field(
        default=None,
        alias="timeZoneName",
        description="Time zone name.",
    )
    location: str | None = Field(
        default=None,
        description="Venue/location of the game.",
    )
    game_number: str | None = Field(
        default=None,
        alias="gameNumber",
        description="Game number or identifier.",
    )
    game_type: str | None = Field(
        default=None,
        alias="gameType",
        description="Game type (regular, playoff, etc.).",
    )
    visitor: TeamInfo = Field(description="Visiting team information.")
    home: TeamInfo = Field(description="Home team information.")
    visitor_score: int | None = Field(
        default=None,
        alias="visitorScore",
        description="Visitor team score.",
    )
    home_score: int | None = Field(
        default=None,
        alias="homeScore",
        description="Home team score.",
    )
    has_shootout: bool | None = Field(
        default=None,
        alias="hasShootout",
        description="Whether game had a shootout.",
    )
    has_overtime: bool | None = Field(
        default=None,
        alias="hasOvertime",
        description="Whether game had overtime.",
    )
    viewed: bool | None = Field(
        default=None,
        description="Whether the user has viewed this game.",
    )
    model_config = {"populate_by_name": True}


class Scorekeeper(BaseModel):
    """Scorekeeper information for a scheduled game.

    :var name: Scorekeeper's full name.
    :var phone: Scorekeeper's phone number.
    """

    name: str = Field(description="Scorekeeper's full name.")
    phone: str = Field(description="Scorekeeper's phone number.")


class GameData(BaseModel):
    """Additional game metadata.

    :var vendors: Vendor information (typically empty dict).
    :var is_valid: Game validation status.
    :var broadcaster: Broadcast provider name.
    :var location_id: Location identifier.
    :var broadcaster_id: Broadcaster identifier.
    :var home_label: Home team label override.
    :var visitor_label: Visitor team label override.
    """

    vendors: dict[str, Any] = Field(
        default_factory=dict,
        description="Vendor information.",
    )
    is_valid: bool = Field(
        default=False,
        alias="isValid",
        description="Game validation status.",
    )
    broadcaster: str = Field(default="", description="Broadcast provider name.")
    location_id: int = Field(
        default=0,
        alias="locationId",
        description="Location identifier.",
    )
    broadcaster_id: int = Field(
        default=0,
        alias="broadcasterId",
        description="Broadcaster identifier.",
    )
    home_label: str = Field(
        default="",
        alias="homeLabel",
        description="Home team label override.",
    )
    visitor_label: str = Field(
        default="",
        alias="visitorLabel",
        description="Visitor team label override.",
    )
    model_config = {"populate_by_name": True}


class RelationshipData(BaseModel):
    """JSON:API relationship data.

    :var id: Related resource identifier.
    :var type: Related resource type.
    """

    id: str = Field(description="Related resource identifier.")
    type: str = Field(description="Related resource type.")


class Relationship(BaseModel):
    """JSON:API relationship wrapper.

    :var data: Relationship data.
    """

    data: RelationshipData = Field(description="Relationship data.")


class ScheduledGameRelationships(BaseModel):
    """Relationships for a scheduled game (JSON:API format).

    :var association: Parent association.
    :var home_division: Home team's division.
    :var home_team: Home team.
    :var league: Parent league.
    :var season: Parent season.
    :var visitor_division: Visitor team's division.
    :var visitor_team: Visitor team.
    """

    association: Relationship | None = Field(
        default=None,
        description="Parent association.",
    )
    home_division: Relationship = Field(
        alias="home_division",
        description="Home team's division.",
    )
    home_team: Relationship = Field(alias="home_team", description="Home team.")
    league: Relationship | None = Field(default=None, description="Parent league.")
    season: Relationship | None = Field(default=None, description="Parent season.")
    visitor_division: Relationship = Field(
        alias="visitor_division",
        description="Visitor team's division.",
    )
    visitor_team: Relationship = Field(
        alias="visitor_team",
        description="Visitor team.",
    )
    model_config = {"populate_by_name": True}


class ScheduledGameAttributes(BaseModel):
    """Attributes for a scheduled game (JSON:API format).

    :var status: Game status.
    :var number: Game number.
    :var scheduled_start_time: Scheduled start time (ISO 8601).
    :var scheduled_time_gmt: Scheduled time in GMT (ISO 8601).
    :var scheduled_end_time: Scheduled end time (ISO 8601).
    :var time_zone_name: IANA time zone name.
    :var location: Venue/location.
    :var category: Game category.
    :var game_type: Game type (exhibition, regular_season, etc.).
    :var scorekeeper: Scorekeeper information.
    :var data: Additional game metadata.
    :var created_at: Creation timestamp (ISO 8601).
    :var updated_at: Last update timestamp (ISO 8601).
    """

    status: str = Field(description="Game status.")
    number: str = Field(description="Game number.")
    scheduled_start_time: str = Field(description="Scheduled start time (ISO 8601).")
    scheduled_time_gmt: str | None = Field(
        default=None,
        description="Scheduled time in GMT (ISO 8601).",
    )
    scheduled_end_time: str = Field(description="Scheduled end time (ISO 8601).")
    time_zone_name: str = Field(description="IANA time zone name.")
    location: str = Field(description="Venue/location.")
    category: str = Field(default="", description="Game category.")
    game_type: str = Field(description="Game type (exhibition, regular_season, etc.).")
    scorekeeper: Scorekeeper = Field(description="Scorekeeper information.")
    data: GameData = Field(description="Additional game metadata.")
    created_at: str | None = Field(
        default=None,
        description="Creation timestamp (ISO 8601).",
    )
    updated_at: str | None = Field(
        default=None,
        description="Last update timestamp (ISO 8601).",
    )


class ScheduledGameData(BaseModel):
    """JSON:API data wrapper for a scheduled game.

    :var type: Resource type (always 'scheduled-games').
    :var id: Game identifier.
    :var attributes: Game attributes.
    :var relationships: Game relationships.
    """

    type: str = Field(description="Resource type.")
    id: str = Field(description="Game identifier.")
    attributes: ScheduledGameAttributes = Field(description="Game attributes.")
    relationships: ScheduledGameRelationships = Field(description="Game relationships.")


class ScheduledGame(BaseModel):
    """A scheduled game (JSON:API format).

    Used for create/get/update operations via the /api/seasons/{id}/schedule endpoint.

    :var data: Game data wrapper.
    """

    data: ScheduledGameData = Field(description="Game data wrapper.")


def _make_request(
    session: Session,
    season_id: str,
    completed: bool | None = None,
    scheduled: bool | None = None,
    brackets: bool | None = None,
) -> list[Game]:
    """Make a request to the BFF games-list endpoint."""
    params: dict[str, Any] = {
        "filter[seasons]": season_id,
        "filter[limit]": str(DEFAULT_GAMES_LIMIT),
        "filter[offset]": "0",
        "filter[sort]": "-start_time",
    }
    # Set filter flags
    if completed is not None:
        params["filter[completed]"] = "true" if completed else "false"
    if scheduled is not None:
        params["filter[scheduled]"] = "true" if scheduled else "false"
    if brackets is not None:
        params["filter[brackets]"] = "true" if brackets else "false"
    url = f"{BFF_API_BASE_URL}{BFF_GAMES_LIST}"
    response = session.get(url, params=params)
    handle_response(response, url, "GET games")
    body: dict[str, Any] = response.json()
    check_bff_response_status(body, url)
    # Parse games from the data array
    games_data = body.get("data", [])
    return [Game(**game_data) for game_data in games_data]


def get_game(session: Session, season_id: str, game_id: int) -> Game:
    """Get a single game by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to retrieve.
    :type game_id: int
    :returns: The :class:`Game` with the specified ID.
    :rtype: Game
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    # Get all games for the season and filter by ID
    # The BFF API doesn't have a single-game endpoint, so we filter client-side
    games = _make_request(session, season_id)
    for game in games:
        if game.id == game_id:
            return game
    # Game not found
    _err_msg = (
        f"Game '{game_id}' not found in season '{season_id}'. "
        f"Make sure you're using a valid game ID and season ID.",
    )
    raise GameSheetError(_err_msg)


def list_scheduled(session: Session, season_id: str) -> list[Game]:
    """Return every scheduled game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose scheduled games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no scheduled games.
    :rtype: list[Game]
    """
    return _make_request(session, season_id, completed=False, scheduled=True)


def list_completed(session: Session, season_id: str) -> list[Game]:
    """Return every completed game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose completed games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no completed games.
    :rtype: list[Game]
    """
    return _make_request(session, season_id, completed=True, scheduled=False)


def list_brackets(session: Session, season_id: str) -> list[Game]:
    """Return every bracket game in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    .. note:: The brackets filter is based on the expected API pattern but has not been verified
        with real bracket data. If this returns unexpected results, the filter parameters may
        need adjustment.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose bracket games to list.
    :type season_id: str
    :returns: A list of :class:`Game`, in the order the server returned them. The list may be empty if the
        season has no bracket games.
    :rtype: list[Game]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response.
    """
    # Try filter[brackets]=true first, fallback to gameType=playoff if needed
    return _make_request(session, season_id, brackets=True)


def list_broadcasters(session: Session) -> list[Broadcaster]:
    """Return the list of valid broadcasters.

    Fetches the current list of broadcaster services from the BFF API. The returned broadcaster keys can be
    used when creating or updating scheduled games.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :returns: A list of :class:`Broadcaster` objects.
    :rtype: list[Broadcaster]
    :raises AuthenticationError: If the server returns 401 or 403.
    :raises GameSheetError: For any other non-2xx response.
    """
    url = f"{BFF_API_BASE_URL}{BFF_BROADCASTERS}"
    response = session.get(url)
    handle_response(response, url, "GET broadcasters")
    body: dict[str, Any] = response.json()
    check_bff_response_status(body, url)
    broadcasters_data = body.get("data", [])
    return [Broadcaster(**b) for b in broadcasters_data]


def validate_broadcaster_key(session: Session, broadcaster: str) -> str:
    """Validate a broadcaster key and return the correctly-cased version.

    Fetches the list of valid broadcasters and performs a case-insensitive match. Returns the broadcaster key
    with the correct casing as stored in the API.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param broadcaster: The broadcaster key to validate (case-insensitive).
    :type broadcaster: str
    :returns: The correctly-cased broadcaster key.
    :rtype: str
    :raises GameSheetError: If the broadcaster key is not valid.
    """
    if not broadcaster:
        return broadcaster
    broadcasters = list_broadcasters(session)
    broadcaster_lower = broadcaster.lower()
    for b in broadcasters:
        if b.key.lower() == broadcaster_lower:
            return b.key
    valid_keys = [b.key for b in broadcasters]
    joined_valid_keys = ", ".join(valid_keys)
    msg = f"Invalid broadcaster '{broadcaster}'. Valid options (case-insensitive): {joined_valid_keys}"
    raise GameSheetError(msg)


def list_locations(session: Session) -> list[Location]:
    """Return the list of valid locations.

    Fetches the current list of locations/venues from the main API. The returned locations include venue name
    and surface name which together form the location identifier used when creating or updating scheduled
    games.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :returns: A list of :class:`Location` objects.
    :rtype: list[Location]
    :raises AuthenticationError: If the server returns 401 or 403.
    :raises GameSheetError: For any other non-2xx response.
    """
    url = f"{DEFAULT_BASE_URL}{API_LOCATIONS}"
    response = session.get(url)
    handle_response(response, url, "GET locations")
    body: dict[str, Any] = response.json()
    return [Location(**loc) for loc in body.get("data", [])]


def get_location(session: Session, location_id: str) -> Location:
    """Get a specific location by ID.

    Fetches the list of all locations and returns the one matching the given ID.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param location_id: The location UUID to retrieve.
    :type location_id: str
    :returns: The :class:`Location` with the specified ID.
    :rtype: Location
    :raises GameSheetError: If the location ID is not found.
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

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param location: The location string to validate (case-insensitive).
    :type location: str
    :returns: The correctly-cased location string.
    :rtype: str
    :raises GameSheetError: If the location is not valid.
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
        f"Use 'gamesheet-sdk-py locations list' to see all valid locations."
    )
    raise GameSheetError(msg)


def validate_game_type(game_type: str) -> None:
    """Validate a game type against the known valid types.

    :param game_type: The game type to validate.
    :type game_type: str
    :raises GameSheetError: If the game type is not valid.
    """
    sorted_game_types = ", ".join(sorted(VALID_GAME_TYPES))
    if game_type not in VALID_GAME_TYPES:
        msg = f"Invalid game type '{game_type}'. Valid options: {sorted_game_types}"
        raise GameSheetError(msg)


# pylint: disable-next=too-many-positional-arguments
def create_scheduled_game(
    session: Session,
    season_id: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    home_team_id: str,
    home_division_id: str,
    visitor_team_id: str,
    visitor_division_id: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    game_type: str,
    time_zone_name: str,
    time_zone_offset: int,
    number: str,
    broadcaster: str = "",
    home_label: str = "",
    visitor_label: str = "",
) -> ScheduledGame:
    """Create a new scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param scheduled_start_time: Scheduled start time (ISO 8601 format).
    :type scheduled_start_time: str
    :param scheduled_end_time: Scheduled end time (ISO 8601 format).
    :type scheduled_end_time: str
    :param home_team_id: Home team identifier.
    :type home_team_id: str
    :param home_division_id: Home team division identifier.
    :type home_division_id: str
    :param visitor_team_id: Visitor team identifier.
    :type visitor_team_id: str
    :param visitor_division_id: Visitor team division identifier.
    :type visitor_division_id: str
    :param location: Game location/venue (default: empty string). Must match format '<location_name>
        <surface_name>' from the API (case-insensitive match, but stored with correct casing).
    :type location: str
    :param scorekeeper_name: Scorekeeper's full name.
    :type scorekeeper_name: str
    :param scorekeeper_phone: Scorekeeper's phone number.
    :type scorekeeper_phone: str
    :param game_type: Game type. Must be one of: playoff, exhibition, tournament, regular_season.
    :type game_type: str
    :param time_zone_name: IANA time zone name.
    :type time_zone_name: str
    :param time_zone_offset: Time zone offset in minutes.
    :type time_zone_offset: int
    :param number: Game number.
    :type number: str
    :param broadcaster: Broadcast provider name (default: empty string). Must match a valid broadcaster key
        from the API (case-insensitive match, but stored with correct casing).
    :type broadcaster: str
    :param home_label: Home team label override (default: empty string).
    :type home_label: str
    :param visitor_label: Visitor team label override (default: empty string).
    :type visitor_label: str
    :returns: The created :class:`ScheduledGame`.
    :rtype: ScheduledGame
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: If the game_type, location, or broadcaster is invalid, or for any other non-2xx
        response.
    """
    # Validate game type
    validate_game_type(game_type)
    # Validate location if provided
    if location:
        location = validate_location(session, location)
    # Validate broadcaster if provided
    if broadcaster:
        broadcaster = validate_broadcaster_key(session, broadcaster)
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE.format(season_id=season_id)}"
    payload = {
        "data": {
            "attributes": {
                "scheduled_start_time": scheduled_start_time,
                "scheduled_end_time": scheduled_end_time,
                "number": number,
                "location": location,
                "scorekeeper": {"name": scorekeeper_name, "phone": scorekeeper_phone},
                "game_type": game_type,
                "time_zone_offset": time_zone_offset,
                "time_zone_name": time_zone_name,
                "data": {
                    "broadcaster": broadcaster,
                    "home_label": home_label,
                    "visitor_label": visitor_label,
                },
                "status": "",
            },
            "relationships": {
                "home_team": {"data": {"id": home_team_id, "type": "teams"}},
                "home_division": {
                    "data": {"id": home_division_id, "type": "divisions"},
                },
                "visitor_team": {"data": {"id": visitor_team_id, "type": "teams"}},
                "visitor_division": {
                    "data": {"id": visitor_division_id, "type": "divisions"},
                },
            },
        },
    }
    response = session.post(url, json=payload)
    handle_response(response, url, "POST scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


def get_scheduled_game(session: Session, season_id: str, game_id: str) -> ScheduledGame:
    """Get a single scheduled game by ID (JSON:API format).

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to retrieve.
    :type game_id: str
    :returns: The :class:`ScheduledGame` with the specified ID.
    :rtype: ScheduledGame
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    response = session.get(url)
    handle_response(response, url, "GET scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


# pylint: disable-next=too-many-positional-arguments
def update_scheduled_game(
    session: Session,
    season_id: str,
    game_id: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    home_team_id: str,
    home_division_id: str,
    visitor_team_id: str,
    visitor_division_id: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    game_type: str,
    time_zone_name: str,
    time_zone_offset: int,
    number: str,
    status: str,
    broadcaster: str = "",
    home_label: str = "",
    visitor_label: str = "",
) -> ScheduledGame:
    """Update a scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to update.
    :type game_id: str
    :param scheduled_start_time: Scheduled start time (ISO 8601 format).
    :type scheduled_start_time: str
    :param scheduled_end_time: Scheduled end time (ISO 8601 format).
    :type scheduled_end_time: str
    :param home_team_id: Home team identifier.
    :type home_team_id: str
    :param home_division_id: Home team division identifier.
    :type home_division_id: str
    :param visitor_team_id: Visitor team identifier.
    :type visitor_team_id: str
    :param visitor_division_id: Visitor team division identifier.
    :type visitor_division_id: str
    :param location: Game location/venue. Must match format '<location_name> <surface_name>' from the API
        (case-insensitive match, but stored with correct casing).
    :type location: str
    :param scorekeeper_name: Scorekeeper's full name.
    :type scorekeeper_name: str
    :param scorekeeper_phone: Scorekeeper's phone number.
    :type scorekeeper_phone: str
    :param game_type: Game type. Must be one of: playoff, exhibition, tournament, regular_season.
    :type game_type: str
    :param time_zone_name: IANA time zone name.
    :type time_zone_name: str
    :param time_zone_offset: Time zone offset in minutes.
    :type time_zone_offset: int
    :param number: Game number.
    :type number: str
    :param status: Game status.
    :type status: str
    :param broadcaster: Broadcast provider name (default: empty string). Must match a valid broadcaster key
        from the API (case-insensitive match, but stored with correct casing).
    :type broadcaster: str
    :param home_label: Home team label override (default: empty string).
    :type home_label: str
    :param visitor_label: Visitor team label override (default: empty string).
    :type visitor_label: str
    :returns: The updated :class:`ScheduledGame`.
    :rtype: ScheduledGame
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: If the game_type, location, or broadcaster is invalid, or for any other non-2xx
        response, including 404 if the game is not found.
    """
    # Validate game type
    validate_game_type(game_type)
    # Validate location (always provided in update, even if empty)
    if location:
        location = validate_location(session, location)
    # Validate broadcaster if provided
    if broadcaster:
        broadcaster = validate_broadcaster_key(session, broadcaster)
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    payload = {
        "data": {
            "attributes": {
                "scheduled_start_time": scheduled_start_time,
                "scheduled_end_time": scheduled_end_time,
                "number": number,
                "location": location,
                "scorekeeper": {"name": scorekeeper_name, "phone": scorekeeper_phone},
                "game_type": game_type,
                "time_zone_offset": time_zone_offset,
                "time_zone_name": time_zone_name,
                "data": {
                    "vendors": {},
                    "is_valid": False,
                    "broadcaster": broadcaster,
                    "location_id": 0,
                    "broadcaster_id": 0,
                    "home_label": home_label,
                    "visitor_label": visitor_label,
                },
                "status": status,
            },
            "relationships": {
                "home_team": {"data": {"id": home_team_id, "type": "teams"}},
                "home_division": {
                    "data": {"id": home_division_id, "type": "divisions"},
                },
                "visitor_team": {"data": {"id": visitor_team_id, "type": "teams"}},
                "visitor_division": {
                    "data": {"id": visitor_division_id, "type": "divisions"},
                },
            },
        },
    }
    response = session.patch(url, json=payload)
    handle_response(response, url, "PATCH scheduled game")
    body: dict[str, Any] = response.json()
    return ScheduledGame(**body)


def delete_scheduled_game(session: Session, season_id: str, game_id: str) -> None:
    """Delete a scheduled game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to delete.
    :type game_id: str
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_SCHEDULE_GAME.format(season_id=season_id, game_id=game_id)}"
    response = session.delete(url)
    handle_response(response, url, "DELETE scheduled game")


def get_completed_game(
    session: Session,
    season_id: str,
    game_id: str,
) -> dict[str, Any]:
    """Get a completed game with full details (JSON:API format).

    Returns the full JSON:API response including rosters, goals, shots, penalties, and all related data. The
    supplied :class:`Session` must already carry a bearer token (e.g. via :meth:`Session.set_bearer_token`);
    the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The parent season identifier.
    :type season_id: str
    :param game_id: The game identifier to retrieve.
    :type game_id: str
    :returns: The full game data as a dictionary (JSON:API format with data/included/relationships).
    :rtype: dict[str, Any]
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{DEFAULT_BASE_URL}{API_SEASONS_GAMES.format(season_id=season_id, game_id=game_id)}"
    params = {"include": "players,coaches,referees,teams,season,association,league"}
    response = session.get(url, params=params)
    handle_response(response, url, "GET completed game")
    body: dict[str, Any] = response.json()
    return body


def download_completed_game_pdf(
    session: Session,
    game_id: str,
    output_path: str,
) -> None:
    """Download the PDF scoresheet for a completed game.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param game_id: The game identifier.
    :type game_id: str
    :param output_path: File path where the PDF will be saved.
    :type output_path: str
    :raises AuthenticationError: If the server returns 401.
    :raises GameSheetError: For any other non-2xx response, including 404 if the game is not found.
    """
    url = f"{SCORESHEET_SERVICE_BASE_URL}{SCORESHEET_SERVICE_GAME.format(game_id=game_id)}"
    response = session.get(url)
    handle_response(response, url, "GET scoresheet PDF")
    Path(output_path).write_bytes(response.content)
