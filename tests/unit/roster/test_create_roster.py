"""Tests for create_player and create_coach functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
)
from gamesheet_sdk.roster import (
    create_coach,
    create_player,
    create_team_coach,
    create_team_player,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_TEAM_ID = "12345"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"


@responses.activate
def test_create_player_minimal_fields(config: Config) -> None:
    """Test creating a player with only required fields."""
    player_response = {
        "type": "players",
        "id": "8043169",
        "attributes": {
            "external_id": None,
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")
    assert result.id == "8043169"
    assert result.first_name == "AUSTIN"
    assert result.last_name == "ADAMSKY"
    assert result.season_id == _SEASON_ID


@responses.activate
def test_create_player_with_external_id(config: Config) -> None:
    """Test creating a player with external_id."""
    player_response = {
        "type": "players",
        "id": "8043169",
        "attributes": {
            "external_id": "BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
            external_id="BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
        )
    assert result.external_id == "BC7732F4-4993-492E-8CCB-4C2CA9C1912E"


@responses.activate
def test_create_player_with_optional_fields(config: Config) -> None:
    """Test creating a player with all optional fields."""
    player_response = {
        "type": "players",
        "id": "8043169",
        "attributes": {
            "external_id": "BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
            external_id="BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
            jersey="98",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == "8043169"


@responses.activate
def test_create_player_with_team_id(config: Config) -> None:
    """Test creating a player with team_id."""
    player_response = {
        "type": "players",
        "id": "8043169",
        "attributes": {
            "external_id": None,
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY", team_id=_TEAM_ID)
    assert result.id == "8043169"


@responses.activate
def test_create_player_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_player_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_player_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_coach_minimal_fields(config: Config) -> None:
    """Test creating a coach with only required fields."""
    coach_response = {
        "type": "coaches",
        "id": "1868550",
        "attributes": {
            "external_id": None,
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")
    assert result.id == "1868550"
    assert result.first_name == "SHAWN"
    assert result.last_name == "ALLIE"
    assert result.season_id == _SEASON_ID


@responses.activate
def test_create_coach_with_external_id(config: Config) -> None:
    """Test creating a coach with external_id."""
    coach_response = {
        "type": "coaches",
        "id": "1868550",
        "attributes": {
            "external_id": "530b7441-1db6-437e-8e5f-777ab3f6cd6c",
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(
            session,
            _SEASON_ID,
            "SHAWN",
            "ALLIE",
            external_id="530b7441-1db6-437e-8e5f-777ab3f6cd6c",
        )
    assert result.external_id == "530b7441-1db6-437e-8e5f-777ab3f6cd6c"


@responses.activate
def test_create_coach_with_position(config: Config) -> None:
    """Test creating a coach with position."""
    coach_response = {
        "type": "coaches",
        "id": "1868550",
        "attributes": {
            "external_id": None,
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(
            session,
            _SEASON_ID,
            "SHAWN",
            "ALLIE",
            position="Head Coach",
        )
    assert result.id == "1868550"


@responses.activate
def test_create_coach_with_team_id(config: Config) -> None:
    """Test creating a coach with team_id."""
    coach_response = {
        "type": "coaches",
        "id": "1868550",
        "attributes": {
            "external_id": None,
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(session, _SEASON_ID, "SHAWN", "ALLIE", team_id=_TEAM_ID)
    assert result.id == "1868550"


@responses.activate
def test_create_coach_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_coach_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_coach_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_team_player_calls_create_player_with_team_id(config: Config) -> None:
    """Test that create_team_player calls create_player with team_id."""
    player_response = {
        "type": "players",
        "id": "8043169",
        "attributes": {
            "external_id": None,
            "first_name": "AUSTIN",
            "last_name": "ADAMSKY",
            "birthdate": None,
            "photo_url": "",
            "biography": "",
            "height": "",
            "weight": "",
            "shot_hand": "",
            "province": "",
            "hometown": "",
            "country": "",
            "drafted_by": "",
            "committed_to": "",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-18T23:15:08.387021Z",
            "updated_at": "2026-06-07T15:03:25.537099Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(session, _SEASON_ID, _TEAM_ID, "AUSTIN", "ADAMSKY")
    assert result.id == "8043169"


@responses.activate
def test_create_team_coach_calls_create_coach_with_team_id(config: Config) -> None:
    """Test that create_team_coach calls create_coach with team_id."""
    coach_response = {
        "type": "coaches",
        "id": "1868550",
        "attributes": {
            "external_id": None,
            "first_name": "SHAWN",
            "last_name": "ALLIE",
            "vendor_data": {},
            "suspension": {"number": 0, "length": 0},
            "created_at": "2026-05-20T11:51:04.091798Z",
            "updated_at": "2026-05-24T19:37:46.806797Z",
        },
        "relationships": {
            "season": {
                "data": {
                    "type": "seasons",
                    "id": _SEASON_ID,
                },
            },
        },
    }
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(session, _SEASON_ID, _TEAM_ID, "SHAWN", "ALLIE")
    assert result.id == "1868550"
