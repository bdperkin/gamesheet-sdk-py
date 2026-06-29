# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_team_player function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, GameSheetError, Session
from gamesheet_sdk.roster import get_team_player
from tests.helpers import (
    PLAYER_EXTERNAL_ID,
    PLAYER_FIRST_NAME,
    PLAYER_ID,
    PLAYER_LAST_NAME,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
)


@responses.activate
def test_get_team_player_returns_player_with_roster_metadata(config: Config) -> None:
    """Test that get_team_player returns a player with team roster metadata."""
    _player_id = PLAYER_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": TEAM_ID,
                "attributes": {
                    "roster": {
                        "players": [
                            {
                                "id": _player_id,
                                "number": "42",
                                "position": "Forward",
                                "status": "Regular",
                                "duty": "captain",
                                "starting": True,
                                "added_at_game_time": False,
                                "affiliated": False,
                            },
                        ],
                    },
                },
            },
            "included": [
                {
                    "type": "players",
                    "id": _player_id,
                    "attributes": {
                        "external_id": PLAYER_EXTERNAL_ID,
                        "first_name": PLAYER_FIRST_NAME,
                        "last_name": PLAYER_LAST_NAME,
                        "created_at": "2026-05-18T23:15:08.387021Z",
                        "updated_at": "2026-06-07T15:03:25.537099Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team_player(session, SEASON_ID, TEAM_ID, _player_id)
    assert result.id == _player_id
    assert result.season_id == SEASON_ID
    assert result.first_name == PLAYER_FIRST_NAME
    assert result.last_name == PLAYER_LAST_NAME
    assert result.number == "42"
    assert result.position == "Forward"
    assert result.status == "Regular"
    assert result.designation == "Captain"
    assert result.starting is True
    assert result.added_at_game_time is False
    assert result.affiliated is False


@responses.activate
def test_get_team_player_finds_player_after_skipping_others(config: Config) -> None:
    """Test that get_team_player iterates through multiple players to find the target."""
    _player_id = PLAYER_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": TEAM_ID,
                "attributes": {
                    "roster": {
                        "players": [
                            {
                                "id": "1111111",
                                "number": "1",
                                "position": "Goalie",
                                "status": "Regular",
                            },
                            {
                                "id": "2222222",
                                "number": "2",
                                "position": "Defence",
                                "status": "Regular",
                            },
                            {
                                "id": _player_id,
                                "number": "42",
                                "position": "Forward",
                                "status": "Regular",
                                "duty": "captain",
                                "starting": True,
                                "added_at_game_time": False,
                                "affiliated": False,
                            },
                            {
                                "id": "3333333",
                                "number": "3",
                                "position": "Forward",
                                "status": "Regular",
                            },
                        ],
                    },
                },
            },
            "included": [
                {
                    "type": "players",
                    "id": "1111111",
                    "attributes": {
                        "first_name": "FIRST",
                        "last_name": "PLAYER",
                        "created_at": "2026-05-18T23:15:08.387021Z",
                        "updated_at": "2026-06-07T15:03:25.537099Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
                {
                    "type": "players",
                    "id": "2222222",
                    "attributes": {
                        "first_name": "SECOND",
                        "last_name": "PLAYER",
                        "created_at": "2026-05-18T23:15:08.387021Z",
                        "updated_at": "2026-06-07T15:03:25.537099Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
                {
                    "type": "players",
                    "id": _player_id,
                    "attributes": {
                        "external_id": PLAYER_EXTERNAL_ID,
                        "first_name": PLAYER_FIRST_NAME,
                        "last_name": PLAYER_LAST_NAME,
                        "created_at": "2026-05-18T23:15:08.387021Z",
                        "updated_at": "2026-06-07T15:03:25.537099Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
                {
                    "type": "players",
                    "id": "3333333",
                    "attributes": {
                        "first_name": "THIRD",
                        "last_name": "PLAYER",
                        "created_at": "2026-05-18T23:15:08.387021Z",
                        "updated_at": "2026-06-07T15:03:25.537099Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team_player(session, SEASON_ID, TEAM_ID, _player_id)
    assert result.id == _player_id
    assert result.first_name == PLAYER_FIRST_NAME
    assert result.last_name == PLAYER_LAST_NAME


@responses.activate
def test_get_team_player_raises_error_when_player_not_on_team(config: Config) -> None:
    """Test that get_team_player raises GameSheetError when player is not on the team."""
    _player_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": TEAM_ID,
                "attributes": {
                    "roster": {
                        "players": [],
                    },
                },
            },
            "included": [],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=f"Player {_player_id} not found on team {TEAM_ID}",
        ):
            get_team_player(session, SEASON_ID, TEAM_ID, _player_id)
