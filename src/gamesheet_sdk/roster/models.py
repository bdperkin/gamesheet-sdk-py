# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster data models for players and coaches."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamesheet_sdk.shared import parse_jsonapi_resource
from gamesheet_sdk.shared.constants import (
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

    :var id: Player identifier (string in JSON:API).
    :var season_id: Parent season identifier.
    :var external_id: External identifier.
    :var first_name: Player's first name.
    :var last_name: Player's last name.
    :var birthdate: Player's birthdate.
    :var photo_url: URL to player photo.
    :var biography: Player biography.
    :var height: Player height.
    :var weight: Player weight.
    :var shot_hand: Player's shooting hand.
    :var province: Player's province.
    :var hometown: Player's hometown.
    :var country: Player's country.
    :var drafted_by: Team that drafted the player.
    :var committed_to: School/team player committed to.
    :var number: Player's jersey number (team roster only).
    :var position: Player's position (team roster only).
    :var duty: Player's duty (team roster only).
    :var designation: Player's designation (team roster only).
    :var status: Player's status (team roster only).
    :var starting: Whether player is starting (team roster only).
    :var added_at_game_time: Whether player was added at game time (team roster only).
    :var affiliated: Whether player is affiliated (team roster only).
    :var created_at: When the player record was created.
    :var updated_at: Last time the player record was updated.
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

    :var id: Coach identifier (string in JSON:API).
    :var season_id: Parent season identifier.
    :var external_id: External identifier.
    :var first_name: Coach's first name.
    :var last_name: Coach's last name.
    :var position: Coach's position (team roster only).
    :var status: Coach's status (team roster only).
    :var signature: Coach's signature (team roster only).
    :var created_at: When the coach record was created.
    :var updated_at: Last time the coach record was updated.
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

    :param item: A JSON:API resource object with ``id``, ``attributes``, and ``relationships`` keys.
    :type item: dict[str, Any]
    :returns: Parsed Player model instance.
    :rtype: Player
    """
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Player(**data)


def parse_coach(item: dict[str, Any]) -> Coach:
    """Flatten a JSON:API resource object into a :class:`Coach`.

    :param item: A JSON:API resource object with ``id``, ``attributes``, and ``relationships`` keys.
    :type item: dict[str, Any]
    :returns: Parsed Coach model instance.
    :rtype: Coach
    """
    data = parse_jsonapi_resource(item, relationship_map={"season": "season_id"})
    return Coach(**data)
