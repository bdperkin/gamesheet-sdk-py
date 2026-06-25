"""Tests for :mod:`gamesheet_sdk.roster`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_coaches,
    list_players,
)
from gamesheet_sdk.roster import list_team_coaches, list_team_players
from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_TEAM_ID = "12345"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"
_TEAM_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}"


@responses.activate
def test_list_players_parses_jsonapi_response(config: Config) -> None:
    """Test that list_players correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=jsonapi_payload(
            [
                {
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
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_players(session, _SEASON_ID)
    assert len(result) == 1
    assert result[0].id == "8043169"
    assert result[0].first_name == "AUSTIN"
    assert result[0].last_name == "ADAMSKY"
    assert result[0].season_id == _SEASON_ID
    assert result[0].created_at == datetime(
        2026,
        5,
        18,
        23,
        15,
        8,
        387021,
        tzinfo=timezone.utc,
    )


@responses.activate
def test_list_coaches_parses_jsonapi_response(config: Config) -> None:
    """Test that list_coaches correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=jsonapi_payload(
            [
                {
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
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_coaches(session, _SEASON_ID)
    assert len(result) == 1
    assert result[0].id == "1868550"
    assert result[0].first_name == "SHAWN"
    assert result[0].last_name == "ALLIE"
    assert result[0].season_id == _SEASON_ID


@responses.activate
def test_list_players_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_players_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_players_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_coaches_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_coaches_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_coaches_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_players_handles_empty_data(config: Config) -> None:
    """Test that list_players returns empty list when API returns no data."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_players(session, _SEASON_ID)
    assert result == []


@responses.activate
def test_list_coaches_handles_empty_data(config: Config) -> None:
    """Test that list_coaches returns empty list when API returns no data."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_coaches(session, _SEASON_ID)
    assert result == []


@responses.activate
def test_list_team_players_parses_jsonapi_response(config: Config) -> None:
    """Test that list_team_players correctly parses JSON:API response format."""
    player_data = {
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
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {
            "title": "Test Team",
            "roster": {
                "players": [
                    {
                        "id": "8043169",
                        "number": "98",
                        "duty": "",
                        "position": "forward",
                        "status": "",
                        "starting": False,
                        "added_at_game_time": False,
                        "affiliated": False,
                    },
                ],
            },
        },
        "relationships": {
            "players": {"data": [{"type": "players", "id": "8043169"}]},
        },
    }
    response_body = {"data": team_data, "included": [player_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_players(session, _SEASON_ID, _TEAM_ID)
    assert len(result) == 1
    assert result[0].id == "8043169"
    assert result[0].first_name == "AUSTIN"
    assert result[0].last_name == "ADAMSKY"
    assert result[0].season_id == _SEASON_ID
    assert result[0].number == "98"
    assert result[0].position == "forward"
    assert result[0].starting is False


@responses.activate
def test_list_team_coaches_parses_jsonapi_response(config: Config) -> None:
    """Test that list_team_coaches correctly parses JSON:API response format."""
    coach_data = {
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
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {
            "title": "Test Team",
            "roster": {
                "coaches": [
                    {
                        "id": "1868550",
                        "position": "assistant_coach",
                        "status": "",
                        "signature": "",
                    },
                ],
            },
        },
        "relationships": {
            "coaches": {"data": [{"type": "coaches", "id": "1868550"}]},
        },
    }
    response_body = {"data": team_data, "included": [coach_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_coaches(session, _SEASON_ID, _TEAM_ID)
    assert len(result) == 1
    assert result[0].id == "1868550"
    assert result[0].first_name == "SHAWN"
    assert result[0].last_name == "ALLIE"
    assert result[0].season_id == _SEASON_ID
    assert result[0].position == "assistant_coach"


@responses.activate
def test_list_team_players_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_team_players(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_players_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_team_players(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_players_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_team_players(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_coaches_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_team_coaches(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_coaches_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_team_coaches(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_coaches_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_team_coaches(session, _SEASON_ID, _TEAM_ID)


@responses.activate
def test_list_team_players_handles_empty_data(config: Config) -> None:
    """Test that list_team_players returns empty list when API returns no data."""
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {"title": "Test Team"},
        "relationships": {"players": {"data": []}},
    }
    response_body = {"data": team_data, "included": []}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_team_players(session, _SEASON_ID, _TEAM_ID)
    assert not result


@responses.activate
def test_list_team_coaches_handles_empty_data(config: Config) -> None:
    """Test that list_team_coaches returns empty list when API returns no data."""
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {"title": "Test Team"},
        "relationships": {"coaches": {"data": []}},
    }
    response_body = {"data": team_data, "included": []}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_team_coaches(session, _SEASON_ID, _TEAM_ID)
    assert not result


@responses.activate
def test_list_team_players_without_roster_metadata(config: Config) -> None:
    """Test that list_team_players handles missing roster metadata gracefully."""
    player_data = {
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
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {"title": "Test Team"},
        "relationships": {
            "players": {"data": [{"type": "players", "id": "8043169"}]},
        },
    }
    response_body = {"data": team_data, "included": [player_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_players(session, _SEASON_ID, _TEAM_ID)
    assert len(result) == 1
    assert result[0].id == "8043169"
    assert result[0].first_name == "AUSTIN"
    assert result[0].position is None


@responses.activate
def test_list_team_coaches_without_roster_metadata(config: Config) -> None:
    """Test that list_team_coaches handles missing roster metadata gracefully."""
    coach_data = {
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
    team_data = {
        "type": "teams",
        "id": _TEAM_ID,
        "attributes": {"title": "Test Team"},
        "relationships": {
            "coaches": {"data": [{"type": "coaches", "id": "1868550"}]},
        },
    }
    response_body = {"data": team_data, "included": [coach_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_coaches(session, _SEASON_ID, _TEAM_ID)
    assert len(result) == 1
    assert result[0].id == "1868550"
    assert result[0].first_name == "SHAWN"
    assert result[0].position is None
