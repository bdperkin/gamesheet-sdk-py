# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pydantic models for games, locations, broadcasters, and related entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
