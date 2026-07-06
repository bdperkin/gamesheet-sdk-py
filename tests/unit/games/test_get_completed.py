# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_completed_game function."""

from __future__ import annotations

import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.constants import DEFAULT_BASE_URL, SCORESHEET_SERVICE_BASE_URL
from gamesheet_sdk.games import get_completed_game


@responses.activate
def test_get_completed_game() -> None:
    """Test get_completed_game function."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/seasons/123/games/game-1",
        json={
            "data": {
                "id": "game-1",
                "status": "completed",
                "home_score": 3,
                "visitor_score": 2,
            },
        },
        status=200,
        match=[
            responses.matchers.query_param_matcher(
                {"include": "players,coaches,referees,teams,season,association,league"},
            ),
        ],
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token("test-token")
        game = get_completed_game(session, "123", "game-1")
    assert game["data"]["id"] == "game-1"
    assert game["data"]["status"] == "completed"


# Lines 952-955: download_completed_game_pdf()
