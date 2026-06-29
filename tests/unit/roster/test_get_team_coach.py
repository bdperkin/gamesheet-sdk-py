# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_team_coach function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, GameSheetError, Session
from gamesheet_sdk.roster import get_team_coach
from tests.helpers import (
    COACH_EXTERNAL_ID_SECONDARY,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
)

_TEAM_ID = "12345"


@responses.activate
def test_get_team_coach_returns_coach_with_roster_metadata(config: Config) -> None:
    """Test that get_team_coach returns a coach with team roster metadata."""
    _coach_id = "1879740"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _TEAM_ID,
                "attributes": {
                    "roster": {
                        "coaches": [
                            {
                                "id": _coach_id,
                                "position": "Manager",
                                "status": "coaching",
                                "signature": "LOU_SIGNATURE",
                            },
                        ],
                    },
                },
            },
            "included": [
                {
                    "type": "coaches",
                    "id": _coach_id,
                    "attributes": {
                        "external_id": COACH_EXTERNAL_ID_SECONDARY,
                        "first_name": "LOU",
                        "last_name": "LAMORIELLO",
                        "created_at": "2026-06-25T02:48:40.059871Z",
                        "updated_at": "2026-06-25T03:40:20.968536Z",
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
        result = get_team_coach(session, SEASON_ID, _TEAM_ID, _coach_id)
    assert result.id == _coach_id
    assert result.season_id == SEASON_ID
    assert result.first_name == "LOU"
    assert result.last_name == "LAMORIELLO"
    assert result.position == "Manager"
    assert result.status == "coaching"
    assert result.signature == "LOU_SIGNATURE"


@responses.activate
def test_get_team_coach_finds_coach_after_skipping_others(config: Config) -> None:
    """Test that get_team_coach iterates through multiple coaches to find the target."""
    _coach_id = "1879740"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _TEAM_ID,
                "attributes": {
                    "roster": {
                        "coaches": [
                            {
                                "id": "1111111",
                                "position": "Assistant Coach",
                                "status": "coaching",
                            },
                            {
                                "id": "2222222",
                                "position": "Trainer",
                                "status": "coaching",
                            },
                            {
                                "id": _coach_id,
                                "position": "Manager",
                                "status": "coaching",
                                "signature": "LOU_SIGNATURE",
                            },
                        ],
                    },
                },
            },
            "included": [
                {
                    "type": "coaches",
                    "id": "1111111",
                    "attributes": {
                        "first_name": "FIRST",
                        "last_name": "COACH",
                        "created_at": "2026-06-25T02:48:40.059871Z",
                        "updated_at": "2026-06-25T03:40:20.968536Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
                {
                    "type": "coaches",
                    "id": "2222222",
                    "attributes": {
                        "first_name": "SECOND",
                        "last_name": "COACH",
                        "created_at": "2026-06-25T02:48:40.059871Z",
                        "updated_at": "2026-06-25T03:40:20.968536Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
                {
                    "type": "coaches",
                    "id": _coach_id,
                    "attributes": {
                        "external_id": COACH_EXTERNAL_ID_SECONDARY,
                        "first_name": "LOU",
                        "last_name": "LAMORIELLO",
                        "created_at": "2026-06-25T02:48:40.059871Z",
                        "updated_at": "2026-06-25T03:40:20.968536Z",
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
        result = get_team_coach(session, SEASON_ID, _TEAM_ID, _coach_id)
    assert result.id == _coach_id
    assert result.first_name == "LOU"
    assert result.last_name == "LAMORIELLO"


@responses.activate
def test_get_team_coach_raises_error_when_coach_not_on_team(config: Config) -> None:
    """Test that get_team_coach raises GameSheetError when coach is not on the team."""
    _coach_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _TEAM_ID,
                "attributes": {
                    "roster": {
                        "coaches": [],
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
            match=f"Coach {_coach_id} not found on team {_TEAM_ID}",
        ):
            get_team_coach(session, SEASON_ID, _TEAM_ID, _coach_id)
