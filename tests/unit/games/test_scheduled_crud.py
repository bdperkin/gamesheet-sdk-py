# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled game CRUD functions."""

from __future__ import annotations

from unittest.mock import patch

import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.admin.games import (
    create_scheduled_game,
    delete_scheduled_game,
    get_scheduled_game,
    update_scheduled_game,
)
from gamesheet_sdk.common.constants import BFF_API_BASE_URL, DEFAULT_BASE_URL
from tests.fixtures.constants import (
    TEST_BEARER_TOKEN,
    TEST_LOCATION_NAME,
    TEST_SCOREKEEPER_NAME,
    TEST_SCOREKEEPER_PHONE,
    TEST_SURFACE_NAME,
    TEST_TIMEZONE_NAME,
    TEST_TIMEZONE_OFFSET,
)
from tests.unit.games.conftest import add_mock_locations_response


@responses.activate
def test_create_scheduled_game() -> None:
    """Test create_scheduled_game function."""
    # Mock locations for validation
    add_mock_locations_response()
    # Mock broadcasters for validation
    responses.add(
        responses.GET,
        f"{BFF_API_BASE_URL}/get-broadcasters",
        json={
            "status": "success",
            "data": [
                {"key": "hockeyTV", "title": "HockeyTV", "url": "https://hockeytv.com"},
            ],
        },
        status=200,
    )
    # Mock create request
    responses.add(
        responses.POST,
        f"{DEFAULT_BASE_URL}/api/seasons/123/schedule",
        json={
            "data": {
                "type": "scheduled-games",
                "id": "game-1",
                "attributes": {
                    "scheduled_start_time": "2026-07-04T10:00:00-04:00",
                    "scheduled_end_time": "2026-07-04T12:00:00-04:00",
                    "number": "G1",
                    "location": f"{TEST_LOCATION_NAME} {TEST_SURFACE_NAME}",
                    "scorekeeper": {
                        "name": TEST_SCOREKEEPER_NAME,
                        "phone": TEST_SCOREKEEPER_PHONE,
                    },
                    "game_type": "regular_season",
                    "time_zone_offset": TEST_TIMEZONE_OFFSET,
                    "time_zone_name": TEST_TIMEZONE_NAME,
                    "data": {
                        "broadcaster": "hockeyTV",
                        "home_label": "",
                        "visitor_label": "",
                    },
                    "status": "",
                },
                "relationships": {
                    "home_team": {"data": {"id": "1", "type": "teams"}},
                    "home_division": {"data": {"id": "10", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "2", "type": "teams"}},
                    "visitor_division": {"data": {"id": "20", "type": "divisions"}},
                },
            },
        },
        status=201,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        game = create_scheduled_game(
            session,
            season_id="123",
            scheduled_start_time="2026-07-04T10:00:00-04:00",
            scheduled_end_time="2026-07-04T12:00:00-04:00",
            home_team_id="1",
            home_division_id="10",
            visitor_team_id="2",
            visitor_division_id="20",
            number="G1",
            location="arena a ice 1",
            scorekeeper_name=TEST_SCOREKEEPER_NAME,
            scorekeeper_phone=TEST_SCOREKEEPER_PHONE,
            game_type="regular_season",
            time_zone_offset=TEST_TIMEZONE_OFFSET,
            time_zone_name=TEST_TIMEZONE_NAME,
            broadcaster="hockeytv",
            home_label="",
            visitor_label="",
        )
    assert game.data.id == "game-1"


# Lines 751-755: get_scheduled_game()


@responses.activate
def test_get_scheduled_game() -> None:
    """Test get_scheduled_game function."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/seasons/123/schedule/game-1",
        json={
            "data": {
                "type": "scheduled-games",
                "id": "game-1",
                "attributes": {
                    "scheduled_start_time": "2026-07-04T10:00:00-04:00",
                    "scheduled_end_time": "2026-07-04T12:00:00-04:00",
                    "number": "G1",
                    "location": f"{TEST_LOCATION_NAME} {TEST_SURFACE_NAME}",
                    "scorekeeper": {
                        "name": TEST_SCOREKEEPER_NAME,
                        "phone": TEST_SCOREKEEPER_PHONE,
                    },
                    "game_type": "regular_season",
                    "time_zone_offset": TEST_TIMEZONE_OFFSET,
                    "time_zone_name": TEST_TIMEZONE_NAME,
                    "data": {"broadcaster": "", "home_label": "", "visitor_label": ""},
                    "status": "scheduled",
                },
                "relationships": {
                    "home_team": {"data": {"id": "1", "type": "teams"}},
                    "home_division": {"data": {"id": "10", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "2", "type": "teams"}},
                    "visitor_division": {"data": {"id": "20", "type": "divisions"}},
                },
            },
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        game = get_scheduled_game(session, "123", "game-1")
    assert game.data.id == "game-1"


# Lines 835-880: update_scheduled_game()


@responses.activate
def test_update_scheduled_game() -> None:
    """Test update_scheduled_game function."""
    # Mock locations for validation
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": "loc-1",
                    "location_name": "Arena B",
                    "surface_name": "Ice 2",
                    "city": "Toronto",
                    "province_state": "ON",
                    "country": "Canada",
                },
            ],
        },
        status=200,
    )
    # Mock broadcasters for validation
    responses.add(
        responses.GET,
        f"{BFF_API_BASE_URL}/get-broadcasters",
        json={
            "status": "success",
            "data": [
                {
                    "key": "flosports",
                    "title": "FloSports",
                    "url": "https://flosports.tv",
                },
            ],
        },
        status=200,
    )
    # Mock update request
    responses.add(
        responses.PATCH,
        f"{DEFAULT_BASE_URL}/api/seasons/123/schedule/game-1",
        json={
            "data": {
                "type": "scheduled-games",
                "id": "game-1",
                "attributes": {
                    "scheduled_start_time": "2026-07-04T11:00:00-04:00",
                    "scheduled_end_time": "2026-07-04T13:00:00-04:00",
                    "number": "G2",
                    "location": "Arena B Ice 2",
                    "scorekeeper": {"name": "Jane", "phone": "555-5678"},
                    "game_type": "playoff",
                    "time_zone_offset": TEST_TIMEZONE_OFFSET,
                    "time_zone_name": TEST_TIMEZONE_NAME,
                    "data": {
                        "vendors": {},
                        "is_valid": False,
                        "broadcaster": "flosports",
                        "location_id": 0,
                        "broadcaster_id": 0,
                        "home_label": "Home",
                        "visitor_label": "Away",
                    },
                    "status": "scheduled",
                },
                "relationships": {
                    "home_team": {"data": {"id": "3", "type": "teams"}},
                    "home_division": {"data": {"id": "30", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "4", "type": "teams"}},
                    "visitor_division": {"data": {"id": "40", "type": "divisions"}},
                },
            },
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        game = update_scheduled_game(
            session,
            season_id="123",
            game_id="game-1",
            scheduled_start_time="2026-07-04T11:00:00-04:00",
            scheduled_end_time="2026-07-04T13:00:00-04:00",
            home_team_id="3",
            home_division_id="30",
            visitor_team_id="4",
            visitor_division_id="40",
            number="G2",
            location="arena b ice 2",
            scorekeeper_name="Jane",
            scorekeeper_phone="555-5678",
            game_type="playoff",
            time_zone_offset=TEST_TIMEZONE_OFFSET,
            time_zone_name=TEST_TIMEZONE_NAME,
            broadcaster="flosports",
            home_label="Home",
            visitor_label="Away",
            status="scheduled",
        )
    assert game.data.id == "game-1"
    assert game.data.attributes.number == "G2"


# Lines 898-900: delete_scheduled_game()


@responses.activate
def test_delete_scheduled_game() -> None:
    """Test delete_scheduled_game function."""
    responses.add(
        responses.DELETE,
        f"{DEFAULT_BASE_URL}/api/seasons/123/schedule/game-1",
        status=204,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        delete_scheduled_game(session, "123", "game-1")
    # Should complete without error


# Lines 925-930: get_completed_game()


def test_create_scheduled_game_empty_location_skips_validation() -> None:
    """Test that empty location skips validation in create_scheduled_game."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    with (
        patch("gamesheet_sdk.admin.games.locations.validate_location") as mock_validate_loc,
        patch.object(session, "post") as mock_post,
    ):
        # Mock a minimal successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "data": {
                "type": "scheduled-games",
                "id": "game-1",
                "attributes": {
                    "scheduled_start_time": "2026-07-15T19:00:00-04:00",
                    "scheduled_end_time": "2026-07-15T21:00:00-04:00",
                    "location": "",
                    "scorekeeper": {
                        "name": TEST_SCOREKEEPER_NAME,
                        "phone": TEST_SCOREKEEPER_PHONE,
                    },
                    "game_type": "regular_season",
                    "time_zone_name": "UTC",
                    "time_zone_offset": 0,
                    "number": "101",
                    "status": "scheduled",
                    "data": {"broadcaster": "", "home_label": "", "visitor_label": ""},
                },
                "relationships": {
                    "home_team": {"data": {"id": "team-1", "type": "teams"}},
                    "home_division": {"data": {"id": "div-1", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "team-2", "type": "teams"}},
                    "visitor_division": {"data": {"id": "div-2", "type": "divisions"}},
                },
            },
        }

        game = create_scheduled_game(
            session,
            season_id="season-1",
            scheduled_start_time="2026-07-15T19:00:00-04:00",
            scheduled_end_time="2026-07-15T21:00:00-04:00",
            home_team_id="team-1",
            home_division_id="div-1",
            visitor_team_id="team-2",
            visitor_division_id="div-2",
            location="",  # Empty location - should skip validation
            scorekeeper_name=TEST_SCOREKEEPER_NAME,
            scorekeeper_phone=TEST_SCOREKEEPER_PHONE,
            game_type="regular_season",
            time_zone_name="UTC",
            time_zone_offset=0,
            number="101",
            broadcaster="",  # Empty broadcaster - should skip validation
        )

        # Verify validate_location was NOT called (empty string skips validation)
        mock_validate_loc.assert_not_called()
        assert game.data.id == "game-1"


def test_create_scheduled_game_empty_broadcaster_skips_validation() -> None:
    """Test that empty broadcaster skips validation in create_scheduled_game."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    with (
        patch(
            "gamesheet_sdk.admin.games.locations.validate_location",
            return_value="Arena A Ice 1",
        ),
        patch(
            "gamesheet_sdk.admin.games.broadcasters.validate_broadcaster_key",
        ) as mock_validate_bc,
        patch.object(session, "post") as mock_post,
    ):
        # Mock a minimal successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "data": {
                "type": "scheduled-games",
                "id": "game-2",
                "attributes": {
                    "scheduled_start_time": "2026-07-20T14:00:00-07:00",
                    "scheduled_end_time": "2026-07-20T16:00:00-07:00",
                    "location": f"{TEST_LOCATION_NAME} {TEST_SURFACE_NAME}",
                    "scorekeeper": {"name": "Jane", "phone": "555-5678"},
                    "game_type": "playoff",
                    "time_zone_name": "America/Vancouver",
                    "time_zone_offset": -420,
                    "number": "202",
                    "status": "scheduled",
                    "data": {"broadcaster": "", "home_label": "", "visitor_label": ""},
                },
                "relationships": {
                    "home_team": {"data": {"id": "team-3", "type": "teams"}},
                    "home_division": {"data": {"id": "div-3", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "team-4", "type": "teams"}},
                    "visitor_division": {"data": {"id": "div-4", "type": "divisions"}},
                },
            },
        }

        game = create_scheduled_game(
            session,
            season_id="season-2",
            scheduled_start_time="2026-07-20T14:00:00-07:00",
            scheduled_end_time="2026-07-20T16:00:00-07:00",
            home_team_id="team-3",
            home_division_id="div-3",
            visitor_team_id="team-4",
            visitor_division_id="div-4",
            location=f"{TEST_LOCATION_NAME} {TEST_SURFACE_NAME}",
            scorekeeper_name="Jane",
            scorekeeper_phone="555-5678",
            game_type="playoff",
            time_zone_name="America/Vancouver",
            time_zone_offset=-420,
            number="202",
            broadcaster="",  # Empty broadcaster - should skip validation
        )

        # Verify validate_broadcaster_key was NOT called (empty string skips validation)
        mock_validate_bc.assert_not_called()
        assert game.data.id == "game-2"


def test_update_scheduled_game_empty_location_skips_validation() -> None:
    """Test that empty location skips validation in update_scheduled_game."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    with (
        patch("gamesheet_sdk.admin.games.locations.validate_location") as mock_validate_loc,
        patch.object(session, "patch") as mock_patch,
    ):
        # Mock a minimal successful response
        mock_patch.return_value.status_code = 200
        mock_patch.return_value.json.return_value = {
            "data": {
                "type": "scheduled-games",
                "id": "game-3",
                "attributes": {
                    "scheduled_start_time": "2026-07-25T10:00:00-04:00",
                    "scheduled_end_time": "2026-07-25T12:00:00-04:00",
                    "location": "",
                    "scorekeeper": {"name": "Bob", "phone": "555-9999"},
                    "game_type": "exhibition",
                    "time_zone_name": "America/Toronto",
                    "time_zone_offset": -240,
                    "number": "303",
                    "status": "scheduled",
                    "data": {"broadcaster": "", "home_label": "", "visitor_label": ""},
                },
                "relationships": {
                    "home_team": {"data": {"id": "team-5", "type": "teams"}},
                    "home_division": {"data": {"id": "div-5", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "team-6", "type": "teams"}},
                    "visitor_division": {"data": {"id": "div-6", "type": "divisions"}},
                },
            },
        }

        game = update_scheduled_game(
            session,
            season_id="season-3",
            game_id="game-3",
            scheduled_start_time="2026-07-25T10:00:00-04:00",
            scheduled_end_time="2026-07-25T12:00:00-04:00",
            home_team_id="team-5",
            home_division_id="div-5",
            visitor_team_id="team-6",
            visitor_division_id="div-6",
            location="",  # Empty location - should skip validation
            scorekeeper_name="Bob",
            scorekeeper_phone="555-9999",
            game_type="exhibition",
            time_zone_name="America/Toronto",
            time_zone_offset=-240,
            number="303",
            status="scheduled",
            broadcaster="",  # Empty broadcaster - should skip validation
        )

        # Verify validate_location was NOT called (empty string skips validation)
        mock_validate_loc.assert_not_called()
        assert game.data.id == "game-3"


def test_update_scheduled_game_empty_broadcaster_skips_validation() -> None:
    """Test that empty broadcaster skips validation in update_scheduled_game."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    with (
        patch(
            "gamesheet_sdk.admin.games.locations.validate_location",
            return_value="Arena B Rink 2",
        ),
        patch(
            "gamesheet_sdk.admin.games.broadcasters.validate_broadcaster_key",
        ) as mock_validate_bc,
        patch.object(session, "patch") as mock_patch,
    ):
        # Mock a minimal successful response
        mock_patch.return_value.status_code = 200
        mock_patch.return_value.json.return_value = {
            "data": {
                "type": "scheduled-games",
                "id": "game-4",
                "attributes": {
                    "scheduled_start_time": "2026-07-30T15:00:00-05:00",
                    "scheduled_end_time": "2026-07-30T17:00:00-05:00",
                    "location": "Arena B Rink 2",
                    "scorekeeper": {"name": "Alice", "phone": "555-7777"},
                    "game_type": "tournament",
                    "time_zone_name": "America/Montreal",
                    "time_zone_offset": -300,
                    "number": "404",
                    "status": "scheduled",
                    "data": {"broadcaster": "", "home_label": "", "visitor_label": ""},
                },
                "relationships": {
                    "home_team": {"data": {"id": "team-7", "type": "teams"}},
                    "home_division": {"data": {"id": "div-7", "type": "divisions"}},
                    "visitor_team": {"data": {"id": "team-8", "type": "teams"}},
                    "visitor_division": {"data": {"id": "div-8", "type": "divisions"}},
                },
            },
        }

        game = update_scheduled_game(
            session,
            season_id="season-4",
            game_id="game-4",
            scheduled_start_time="2026-07-30T15:00:00-05:00",
            scheduled_end_time="2026-07-30T17:00:00-05:00",
            home_team_id="team-7",
            home_division_id="div-7",
            visitor_team_id="team-8",
            visitor_division_id="div-8",
            location="Arena B Rink 2",
            scorekeeper_name="Alice",
            scorekeeper_phone="555-7777",
            game_type="tournament",
            time_zone_name="America/Montreal",
            time_zone_offset=-300,
            number="404",
            status="scheduled",
            broadcaster="",  # Empty broadcaster - should skip validation
        )

        # Verify validate_broadcaster_key was NOT called (empty string skips validation)
        mock_validate_bc.assert_not_called()
        assert game.data.id == "game-4"
