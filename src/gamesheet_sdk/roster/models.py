"""Roster data models for players and coaches."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.shared import parse_jsonapi_resource


class Player(BaseModel):
    """A single player.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{id}/players`` to a flat typed
    model. Includes both base player data and roster-specific metadata (position, jersey, etc.).
    """

    id: str = Field(description="Player identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(default=None, description="Player's first name.")
    last_name: str | None = Field(default=None, description="Player's last name.")
    birthdate: str | None = Field(default=None, description="Player's birthdate.")
    photo_url: str | None = Field(default=None, description="URL to player photo.")
    biography: str | None = Field(default=None, description="Player biography.")
    height: str | None = Field(default=None, description="Player height.")
    weight: str | None = Field(default=None, description="Player weight.")
    shot_hand: str | None = Field(default=None, description="Player's shooting hand.")
    province: str | None = Field(default=None, description="Player's province.")
    hometown: str | None = Field(default=None, description="Player's hometown.")
    country: str | None = Field(default=None, description="Player's country.")
    drafted_by: str | None = Field(
        default=None,
        description="Team that drafted the player.",
    )
    committed_to: str | None = Field(
        default=None,
        description="School/team player committed to.",
    )
    number: str | None = Field(default=None, description="Player's jersey number (team roster only).")
    position: str | None = Field(default=None, description="Player's position (team roster only).")
    duty: str | None = Field(default=None, description="Player's duty (team roster only).")
    designation: str | None = Field(default=None, description="Player's designation (team roster only).")
    status: str | None = Field(default=None, description="Player's status (team roster only).")
    starting: bool | None = Field(default=None, description="Whether player is starting (team roster only).")
    added_at_game_time: bool | None = Field(
        default=None,
        description="Whether player was added at game time (team roster only).",
    )
    affiliated: bool | None = Field(
        default=None,
        description="Whether player is affiliated (team roster only).",
    )
    created_at: datetime = Field(description="When the player record was created.")
    updated_at: datetime = Field(description="Last time the player record was updated.")


class Coach(BaseModel):
    """A single coach.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{id}/coaches`` to a flat typed
    model.
    """

    id: str = Field(description="Coach identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(default=None, description="Coach's first name.")
    last_name: str | None = Field(default=None, description="Coach's last name.")
    position: str | None = Field(default=None, description="Coach's position (team roster only).")
    status: str | None = Field(default=None, description="Coach's status (team roster only).")
    signature: str | None = Field(default=None, description="Coach's signature (team roster only).")
    created_at: datetime = Field(description="When the coach record was created.")
    updated_at: datetime = Field(description="Last time the coach record was updated.")


def parse_player(item: dict[str, Any]) -> Player:
    """Flatten a JSON:API resource object into a :class:`Player`."""
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Player(**data)


def parse_coach(item: dict[str, Any]) -> Coach:
    """Flatten a JSON:API resource object into a :class:`Coach`."""
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Coach(**data)
