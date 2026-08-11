# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for update_player and update_team_player functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.admin.roster import update_player, update_team_player
from tests.fixtures.constants import TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD
from tests.helpers import (
    PLAYER_ID,
    SEASON_ID,
    TEAM_ID_SECONDARY,
    TEST_BASE_URL,
    setup_update_player_mocks,
)
from tests.helpers.payloads import roster_player_payload, team_payload

_TEAM_ID = TEAM_ID_SECONDARY
_PLAYERS_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{PLAYER_ID}"


@responses.activate
def test_update_player_updates_fields(config: Config) -> None:
    """Test updating a player updates the specified fields."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=SEASON_ID)
    # Mock PATCH to update player

    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    setup_update_player_mocks(_PLAYERS_ENDPOINT, current_player, updated_player)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            SEASON_ID,
            PLAYER_ID,
            last_name="UPDATED",
        )

    assert result.last_name == "UPDATED"


@responses.activate
def test_update_player_with_photo_upload(config: Config) -> None:
    """Test updating a player with photo upload."""
    from tests.helpers import setup_photo_upload_mocks

    temp_path = setup_photo_upload_mocks()
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["photo_url"] = (
        "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/test-image-id"
    )
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            SEASON_ID,
            PLAYER_ID,
            photo_path=temp_path,
        )

    assert result.photo_url is not None
    assert result.photo_url.find("test-image-id") != -1


@responses.activate
def test_update_player_remove_photo(config: Config) -> None:
    """Test updating a player to remove photo."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=SEASON_ID)
    current_player["attributes"]["photo_url"] = "https://example.com/old-photo.jpg"
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["photo_url"] = ""
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            SEASON_ID,
            PLAYER_ID,
            remove_photo=True,
        )

    assert not result.photo_url


@responses.activate
def test_update_player_no_fields_raises_error(config: Config) -> None:
    """Test updating a player with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match=TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD):
            update_player(session, SEASON_ID, PLAYER_ID)


@responses.activate
def test_update_player_photo_and_remove_photo_raises_error(config: Config) -> None:
    """Test updating a player with both photo and remove_photo raises ValueError."""
    import tempfile

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake-image-data")
        photo_path = f.name

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(
            ValueError,
            match="Cannot both upload a photo and remove it",
        ):
            update_player(
                session,
                SEASON_ID,
                PLAYER_ID,
                photo_path=photo_path,
                remove_photo=True,
            )


@responses.activate
def test_update_team_player_updates_fields(config: Config) -> None:
    """Test updating a team player updates the specified fields."""
    # Mock GET team to fetch current team player (via list_team_players)
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [
            {
                "id": PLAYER_ID,
                "number": "99",
                "position": "centre",
                "status": "playing",
                "duty": "",
            },
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {
        "data": [{"type": "players", "id": PLAYER_ID}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/players/{PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            SEASON_ID,
            _TEAM_ID,
            PLAYER_ID,
            last_name="UPDATED",
        )

    assert result.last_name == "UPDATED"


@responses.activate
def test_update_player_with_all_profile_fields(config: Config) -> None:
    """Test updating a player with all profile fields."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["biography"] = "Test bio"
    updated_player["attributes"]["height"] = "6'2\""
    updated_player["attributes"]["weight"] = "200"
    updated_player["attributes"]["shot_hand"] = "R"
    updated_player["attributes"]["birthdate"] = "2000-01-01"
    updated_player["attributes"]["hometown"] = "Toronto"
    updated_player["attributes"]["country"] = "Canada"
    updated_player["attributes"]["province"] = "Ontario"
    updated_player["attributes"]["drafted_by"] = "Team A"
    updated_player["attributes"]["committed_to"] = "Team B"
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            SEASON_ID,
            PLAYER_ID,
            biography="Test bio",
            height="6'2\"",
            weight="200",
            shot_hand="R",
            birthdate="2000-01-01",
            hometown="Toronto",
            country="Canada",
            province="Ontario",
            drafted_by="Team A",
            committed_to="Team B",
        )

    assert result.biography == "Test bio"
    assert result.height == "6'2\""


@responses.activate
def test_update_team_player_with_all_profile_fields(config: Config) -> None:
    """Test updating a team player with all profile fields."""
    # Mock GET team to fetch current team player (via list_team_players)
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [
            {
                "id": PLAYER_ID,
                "number": "99",
                "position": "centre",
                "status": "playing",
                "duty": "",
            },
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {
        "data": [{"type": "players", "id": PLAYER_ID}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["biography"] = "Test bio"
    updated_player["attributes"]["height"] = "6'0\""
    updated_player["attributes"]["weight"] = "180"
    updated_player["attributes"]["shot_hand"] = "L"
    updated_player["attributes"]["birthdate"] = "1999-12-31"
    updated_player["attributes"]["hometown"] = "Montreal"
    updated_player["attributes"]["country"] = "Canada"
    updated_player["attributes"]["province"] = "Quebec"
    updated_player["attributes"]["drafted_by"] = "Team C"
    updated_player["attributes"]["committed_to"] = "Team D"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/players/{PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            SEASON_ID,
            _TEAM_ID,
            PLAYER_ID,
            biography="Test bio",
            height="6'0\"",
            weight="180",
            shot_hand="L",
            birthdate="1999-12-31",
            hometown="Montreal",
            country="Canada",
            province="Quebec",
            drafted_by="Team C",
            committed_to="Team D",
        )

    assert result.biography == "Test bio"


@responses.activate
def test_update_player_preserves_existing_photo_url(config: Config) -> None:
    """Test updating a player preserves existing photo_url when not uploading/removing."""
    # Mock GET to fetch current player with photo_url
    current_player = roster_player_payload(season_id=SEASON_ID)
    current_player["attributes"]["photo_url"] = "https://example.com/photo.jpg"
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    updated_player["attributes"]["photo_url"] = "https://example.com/photo.jpg"
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            SEASON_ID,
            PLAYER_ID,
            last_name="UPDATED",
        )

    assert result.last_name == "UPDATED"
    assert result.photo_url == "https://example.com/photo.jpg"


@responses.activate
def test_update_team_player_no_fields_raises_error(config: Config) -> None:
    """Test updating a team player with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match=TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD):
            update_team_player(session, SEASON_ID, _TEAM_ID, PLAYER_ID)


@responses.activate
def test_update_team_player_photo_and_remove_photo_raises_error(config: Config) -> None:
    """Test updating a team player with both photo and remove_photo raises ValueError."""
    import tempfile

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake-image-data")
        photo_path = f.name

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(
            ValueError,
            match="Cannot both upload a photo and remove it",
        ):
            update_team_player(
                session,
                SEASON_ID,
                _TEAM_ID,
                PLAYER_ID,
                photo_path=photo_path,
                remove_photo=True,
            )


@responses.activate
def test_update_team_player_with_photo_upload(config: Config) -> None:
    """Test updating a team player with photo upload."""
    from tests.helpers import setup_photo_upload_mocks

    temp_path = setup_photo_upload_mocks()
    # Mock GET team to fetch current team player
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [
            {
                "id": PLAYER_ID,
                "number": "99",
                "position": "centre",
                "status": "playing",
                "duty": "",
            },
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {
        "data": [{"type": "players", "id": PLAYER_ID}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["photo_url"] = (
        "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/test-image-id"
    )
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/players/{PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            SEASON_ID,
            _TEAM_ID,
            PLAYER_ID,
            photo_path=temp_path,
        )

    assert result.photo_url == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/test-image-id"


@responses.activate
def test_update_team_player_remove_photo(config: Config) -> None:
    """Test updating a team player with remove_photo=True."""
    # Mock GET team to fetch current team player
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=SEASON_ID)
    current_player_payload["attributes"]["photo_url"] = "https://example.com/old-photo.jpg"
    team_data["attributes"]["roster"] = {
        "players": [
            {
                "id": PLAYER_ID,
                "number": "99",
                "position": "centre",
                "status": "playing",
                "duty": "",
            },
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {
        "data": [{"type": "players", "id": PLAYER_ID}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["photo_url"] = ""
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/players/{PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            SEASON_ID,
            _TEAM_ID,
            PLAYER_ID,
            remove_photo=True,
        )

    assert not result.photo_url


@responses.activate
def test_update_team_player_preserves_existing_photo_url(config: Config) -> None:
    """Test updating a team player preserves existing photo_url when not uploading/removing."""
    # Mock GET team to fetch current team player with photo_url
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=SEASON_ID)
    current_player_payload["attributes"]["photo_url"] = "https://example.com/photo.jpg"
    team_data["attributes"]["roster"] = {
        "players": [
            {
                "id": PLAYER_ID,
                "number": "99",
                "position": "centre",
                "status": "playing",
                "duty": "",
            },
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {
        "data": [{"type": "players", "id": PLAYER_ID}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    updated_player["attributes"]["photo_url"] = "https://example.com/photo.jpg"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/players/{PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            SEASON_ID,
            _TEAM_ID,
            PLAYER_ID,
            last_name="UPDATED",
        )

    assert result.last_name == "UPDATED"
    assert result.photo_url == "https://example.com/photo.jpg"
