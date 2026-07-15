# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_game function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    BFF_API_BASE_URL,
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
)
from gamesheet_sdk.admin.games import get_game
from tests.helpers import SEASON_ID

_BFF_BASE = BFF_API_BASE_URL


@responses.activate
def test_get_game_returns_single_game(config: Config) -> None:
    """Test that get_game returns a single game."""
    _game_id = 12345
    _endpoint = f"{_BFF_BASE}/games-list/v1"
    responses.add(
        responses.GET,
        _endpoint,
        json={
            "status": "success",
            "data": [
                {
                    "id": _game_id,
                    "status": "completed",
                    "date": "2024-06-15",
                    "time": "19:00",
                    "location": "Arena A",
                    "visitor": {"id": 101, "title": "Team A"},
                    "home": {"id": 102, "title": "Team B"},
                    "visitorScore": 3,
                    "homeScore": 2,
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_game(session, SEASON_ID, _game_id)
    assert result.id == _game_id
    assert result.status == "completed"
    assert result.visitor.title == "Team A"
    assert result.home.title == "Team B"


@responses.activate
def test_get_game_finds_game_in_list(config: Config) -> None:
    """Test that get_game finds the correct game when multiple games are returned."""
    _game_id = 12346
    _endpoint = f"{_BFF_BASE}/games-list/v1"
    responses.add(
        responses.GET,
        _endpoint,
        json={
            "status": "success",
            "data": [
                {
                    "id": 12345,
                    "status": "completed",
                    "date": "2024-06-14",
                    "time": "18:00",
                    "location": "Arena B",
                    "visitor": {"id": 103, "title": "Team C"},
                    "home": {"id": 104, "title": "Team D"},
                    "visitorScore": 1,
                    "homeScore": 2,
                },
                {
                    "id": _game_id,
                    "status": "completed",
                    "date": "2024-06-15",
                    "time": "19:00",
                    "location": "Arena A",
                    "visitor": {"id": 101, "title": "Team A"},
                    "home": {"id": 102, "title": "Team B"},
                    "visitorScore": 3,
                    "homeScore": 2,
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_game(session, SEASON_ID, _game_id)
    assert result.id == _game_id
    assert result.visitor.title == "Team A"


@responses.activate
def test_get_game_404_when_game_not_found(config: Config) -> None:
    """Test that get_game raises GameSheetError when game is not found."""
    _game_id = 99999
    _endpoint = f"{_BFF_BASE}/games-list/v1"
    responses.add(
        responses.GET,
        _endpoint,
        json={"status": "success", "data": []},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Game '.*' not found.*valid game ID and season ID",
        ):
            get_game(session, SEASON_ID, _game_id)


@responses.activate
def test_get_game_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _game_id = 12345
    _endpoint = f"{_BFF_BASE}/games-list/v1"
    responses.add(
        responses.GET,
        _endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_game(session, SEASON_ID, _game_id)


@responses.activate
def test_get_game_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _game_id = 12345
    _endpoint = f"{_BFF_BASE}/games-list/v1"
    responses.add(responses.GET, _endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_game(session, SEASON_ID, _game_id)
