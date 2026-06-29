# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for :mod:`gamesheet_sdk.roster`."""

from __future__ import annotations

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
from tests.helpers import (
    COACH_FIRST_NAME,
    COACH_ID_PRIMARY,
    COACH_LAST_NAME,
    DEFAULT_TEAM_NAME,
    PLAYER_FIRST_NAME,
    PLAYER_ID,
    PLAYER_LAST_NAME,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
    jsonapi_payload,
    roster_coach_payload,
    roster_player_payload,
)

_PLAYERS_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players"
_COACHES_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/coaches"
_TEAM_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{TEAM_ID}"


@responses.activate
def test_list_players_parses_jsonapi_response(config: Config) -> None:
    """Test that list_players correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=jsonapi_payload(
            [
                roster_player_payload(
                    season_id=SEASON_ID,
                    first_name=PLAYER_FIRST_NAME,
                    last_name=PLAYER_LAST_NAME,
                ),
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_players(session, SEASON_ID)
    assert len(result) == 1
    assert result[0].id == PLAYER_ID
    assert result[0].first_name == PLAYER_FIRST_NAME
    assert result[0].last_name == PLAYER_LAST_NAME
    assert result[0].season_id == SEASON_ID
    assert result[0].created_at is not None
    assert result[0].updated_at is not None


@responses.activate
def test_list_coaches_parses_jsonapi_response(config: Config) -> None:
    """Test that list_coaches correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=jsonapi_payload(
            [
                roster_coach_payload(
                    season_id=SEASON_ID,
                    first_name=COACH_FIRST_NAME,
                    last_name=COACH_LAST_NAME,
                ),
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_coaches(session, SEASON_ID)
    assert len(result) == 1
    assert result[0].id == COACH_ID_PRIMARY
    assert result[0].first_name == COACH_FIRST_NAME
    assert result[0].last_name == COACH_LAST_NAME
    assert result[0].season_id == SEASON_ID


@responses.activate
def test_list_players_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_players(session, SEASON_ID)


@responses.activate
def test_list_players_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_players(session, SEASON_ID)


@responses.activate
def test_list_players_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_players(session, SEASON_ID)


@responses.activate
def test_list_coaches_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_coaches(session, SEASON_ID)


@responses.activate
def test_list_coaches_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_coaches(session, SEASON_ID)


@responses.activate
def test_list_coaches_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_coaches(session, SEASON_ID)


@responses.activate
def test_list_players_handles_empty_data(config: Config) -> None:
    """Test that list_players returns empty list when API returns no data."""
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_players(session, SEASON_ID)
    assert result == []


@responses.activate
def test_list_coaches_handles_empty_data(config: Config) -> None:
    """Test that list_coaches returns empty list when API returns no data."""
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_coaches(session, SEASON_ID)
    assert result == []


@responses.activate
def test_list_team_players_parses_jsonapi_response(config: Config) -> None:
    """Test that list_team_players correctly parses JSON:API response format."""
    player_data = roster_player_payload(
        season_id=SEASON_ID,
        first_name=PLAYER_FIRST_NAME,
        last_name=PLAYER_LAST_NAME,
    )
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {
            "title": DEFAULT_TEAM_NAME,
            "roster": {
                "players": [
                    {
                        "id": PLAYER_ID,
                        "number": "98",
                        "duty": "captain",
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
            "players": {"data": [{"type": "players", "id": PLAYER_ID}]},
        },
    }
    response_body = {"data": team_data, "included": [player_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_players(session, SEASON_ID, TEAM_ID)
    assert len(result) == 1
    assert result[0].id == PLAYER_ID
    assert result[0].first_name == PLAYER_FIRST_NAME
    assert result[0].last_name == PLAYER_LAST_NAME
    assert result[0].season_id == SEASON_ID
    assert result[0].number == "98"
    assert result[0].position == "forward"
    assert result[0].designation == "Captain"
    assert result[0].starting is False


@responses.activate
def test_list_team_coaches_parses_jsonapi_response(config: Config) -> None:
    """Test that list_team_coaches correctly parses JSON:API response format."""
    coach_data = roster_coach_payload(
        season_id=SEASON_ID,
        first_name=COACH_FIRST_NAME,
        last_name=COACH_LAST_NAME,
    )
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {
            "title": DEFAULT_TEAM_NAME,
            "roster": {
                "coaches": [
                    {
                        "id": COACH_ID_PRIMARY,
                        "position": "assistant_coach",
                        "status": "",
                        "signature": "",
                    },
                ],
            },
        },
        "relationships": {
            "coaches": {"data": [{"type": "coaches", "id": COACH_ID_PRIMARY}]},
        },
    }
    response_body = {"data": team_data, "included": [coach_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_coaches(session, SEASON_ID, TEAM_ID)
    assert len(result) == 1
    assert result[0].id == COACH_ID_PRIMARY
    assert result[0].first_name == COACH_FIRST_NAME
    assert result[0].last_name == COACH_LAST_NAME
    assert result[0].season_id == SEASON_ID
    assert result[0].position == "assistant_coach"


@responses.activate
def test_list_team_players_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_team_players(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_players_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_team_players(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_players_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_team_players(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_coaches_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_team_coaches(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_coaches_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_team_coaches(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_coaches_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _TEAM_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_team_coaches(session, SEASON_ID, TEAM_ID)


@responses.activate
def test_list_team_players_handles_empty_data(config: Config) -> None:
    """Test that list_team_players returns empty list when API returns no data."""
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {"title": DEFAULT_TEAM_NAME},
        "relationships": {"players": {"data": []}},
    }
    response_body = {"data": team_data, "included": []}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_team_players(session, SEASON_ID, TEAM_ID)
    assert not result


@responses.activate
def test_list_team_coaches_handles_empty_data(config: Config) -> None:
    """Test that list_team_coaches returns empty list when API returns no data."""
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {"title": DEFAULT_TEAM_NAME},
        "relationships": {"coaches": {"data": []}},
    }
    response_body = {"data": team_data, "included": []}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_team_coaches(session, SEASON_ID, TEAM_ID)
    assert not result


@responses.activate
def test_list_team_players_with_empty_duty(config: Config) -> None:
    """Test that list_team_players handles empty duty field."""
    player_data = roster_player_payload(
        season_id=SEASON_ID,
        first_name=PLAYER_FIRST_NAME,
        last_name=PLAYER_LAST_NAME,
    )
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {
            "title": DEFAULT_TEAM_NAME,
            "roster": {
                "players": [
                    {
                        "id": PLAYER_ID,
                        "number": "98",
                        "duty": "",
                        "position": "forward",
                        "status": "playing",
                    },
                ],
            },
        },
        "relationships": {
            "players": {"data": [{"type": "players", "id": PLAYER_ID}]},
        },
    }
    response_body = {"data": team_data, "included": [player_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_players(session, SEASON_ID, TEAM_ID)
    assert len(result) == 1
    # Empty duty string results in empty designation, not None
    assert not result[0].designation


@responses.activate
def test_list_team_players_without_roster_metadata(config: Config) -> None:
    """Test that list_team_players handles missing roster metadata gracefully."""
    player_data = roster_player_payload(
        season_id=SEASON_ID,
        first_name=PLAYER_FIRST_NAME,
        last_name=PLAYER_LAST_NAME,
    )
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {"title": DEFAULT_TEAM_NAME},
        "relationships": {
            "players": {"data": [{"type": "players", "id": PLAYER_ID}]},
        },
    }
    response_body = {"data": team_data, "included": [player_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_players(session, SEASON_ID, TEAM_ID)
    assert len(result) == 1
    assert result[0].id == PLAYER_ID
    assert result[0].first_name == PLAYER_FIRST_NAME
    # Position comes from player payload, not roster metadata
    assert result[0].position == "centre"


@responses.activate
def test_list_team_coaches_without_roster_metadata(config: Config) -> None:
    """Test that list_team_coaches handles missing roster metadata gracefully."""
    coach_data = roster_coach_payload(
        season_id=SEASON_ID,
        first_name=COACH_FIRST_NAME,
        last_name=COACH_LAST_NAME,
    )
    team_data = {
        "type": "teams",
        "id": TEAM_ID,
        "attributes": {"title": DEFAULT_TEAM_NAME},
        "relationships": {
            "coaches": {"data": [{"type": "coaches", "id": COACH_ID_PRIMARY}]},
        },
    }
    response_body = {"data": team_data, "included": [coach_data]}
    responses.add(responses.GET, _TEAM_ENDPOINT, json=response_body, status=200)
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_team_coaches(session, SEASON_ID, TEAM_ID)
    assert len(result) == 1
    assert result[0].id == COACH_ID_PRIMARY
    assert result[0].first_name == COACH_FIRST_NAME
    # Position comes from coach payload, not roster metadata
    assert result[0].position == "head_coach"
