# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster data models for players and coaches."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.admin.shared import parse_jsonapi_resource
from gamesheet_sdk.common.shared.constants import (
    FIELD_DESC_COACH_FIRST_NAME,
    FIELD_DESC_COACH_LAST_NAME,
    FIELD_DESC_PARENT_SEASON_ID,
    FIELD_DESC_PLAYER_FIRST_NAME,
    FIELD_DESC_PLAYER_LAST_NAME,
)


class Player(BaseModel):
    """A single player.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{id}/players`` to a flat typed
    model. Includes both base player data and roster-specific metadata (position, jersey, etc.).

    Attributes:
        id: Player identifier (string in JSON:API).
        season_id: Parent season identifier.
        external_id: External identifier.
        first_name: Player's first name.
        last_name: Player's last name.
        birthdate: Player's birthdate.
        photo_url: URL to player photo.
        biography: Player biography.
        height: Player height.
        weight: Player weight.
        shot_hand: Player's shooting hand.
        province: Player's province.
        hometown: Player's hometown.
        country: Player's country.
        drafted_by: Team that drafted the player.
        committed_to: School/team player committed to.
        number: Player's jersey number (team roster only).
        position: Player's position (team roster only).
        duty: Player's duty (team roster only).
        designation: Player's designation (team roster only).
        status: Player's status (team roster only).
        starting: Whether player is starting (team roster only).
        added_at_game_time: Whether player was added at game time (team
            roster only).
        affiliated: Whether player is affiliated (team roster only).
        created_at: When the player record was created.
        updated_at: Last time the player record was updated.
    """

    id: str = Field(description="Player identifier (string in JSON:API).")
    season_id: str = Field(description=FIELD_DESC_PARENT_SEASON_ID)
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(
        default=None,
        description=FIELD_DESC_PLAYER_FIRST_NAME,
    )
    last_name: str | None = Field(default=None, description=FIELD_DESC_PLAYER_LAST_NAME)
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
    number: str | None = Field(
        default=None,
        description="Player's jersey number (team roster only).",
    )
    position: str | None = Field(
        default=None,
        description="Player's position (team roster only).",
    )
    duty: str | None = Field(
        default=None,
        description="Player's duty (team roster only).",
    )
    designation: str | None = Field(
        default=None,
        description="Player's designation (team roster only).",
    )
    status: str | None = Field(
        default=None,
        description="Player's status (team roster only).",
    )
    starting: bool | None = Field(
        default=None,
        description="Whether player is starting (team roster only).",
    )
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

    Attributes:
        id: Coach identifier (string in JSON:API).
        season_id: Parent season identifier.
        external_id: External identifier.
        first_name: Coach's first name.
        last_name: Coach's last name.
        position: Coach's position (team roster only).
        status: Coach's status (team roster only).
        signature: Coach's signature (team roster only).
        created_at: When the coach record was created.
        updated_at: Last time the coach record was updated.
    """

    id: str = Field(description="Coach identifier (string in JSON:API).")
    season_id: str = Field(description=FIELD_DESC_PARENT_SEASON_ID)
    external_id: str | None = Field(default=None, description="External identifier.")
    first_name: str | None = Field(
        default=None,
        description=FIELD_DESC_COACH_FIRST_NAME,
    )
    last_name: str | None = Field(default=None, description=FIELD_DESC_COACH_LAST_NAME)
    position: str | None = Field(
        default=None,
        description="Coach's position (team roster only).",
    )
    status: str | None = Field(
        default=None,
        description="Coach's status (team roster only).",
    )
    signature: str | None = Field(
        default=None,
        description="Coach's signature (team roster only).",
    )
    created_at: datetime = Field(description="When the coach record was created.")
    updated_at: datetime = Field(description="Last time the coach record was updated.")


def parse_player(item: dict[str, Any]) -> Player:
    """Flatten a JSON:API resource object into a :class:`Player`.

    Args:
        item (dict[str, Any]): A JSON:API resource object with ``id``,
            ``attributes``, and ``relationships`` keys.

    Returns:
        Player: Parsed Player model instance.
    """
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Player(**data)


def parse_coach(item: dict[str, Any]) -> Coach:
    """Flatten a JSON:API resource object into a :class:`Coach`.

    Args:
        item (dict[str, Any]): A JSON:API resource object with ``id``,
            ``attributes``, and ``relationships`` keys.

    Returns:
        Coach: Parsed Coach model instance.
    """
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Coach(**data)
