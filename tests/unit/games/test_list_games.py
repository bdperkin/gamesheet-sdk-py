"""Tests for :mod:`gamesheet_sdk.games`."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    BFF_API_BASE_URL,
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_brackets,
    list_completed,
    list_scheduled,
)

_BASE = BFF_API_BASE_URL
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/games-list/v1"


def _bff_response(games: list[dict[str, object]]) -> dict[str, object]:
    """Build a BFF API response."""
    return {"status": "success", "data": games}


@responses.activate
def test_list_completed_parses_bff_response(config: Config) -> None:
    """Test that list_completed correctly parses BFF API response format."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_bff_response(
            [
                {
                    "id": 2826460,
                    "status": "completed",
                    "date": "2026-03-08",
                    "time": "17:00",
                    "endTime": "18:21",
                    "timeZoneName": "",
                    "location": "WAKE FOREST",
                    "gameNumber": "16AA GAME 7",
                    "gameType": "playoff",
                    "visitor": {
                        "id": 383178,
                        "title": "TEAM A",
                        "divisionId": 59690,
                        "divisionTitle": "16AA",
                    },
                    "home": {
                        "id": 383176,
                        "title": "TEAM B",
                        "divisionId": 59690,
                        "divisionTitle": "16AA",
                    },
                    "visitorScore": 4,
                    "homeScore": 3,
                    "hasShootout": False,
                    "hasOvertime": False,
                    "viewed": False,
                    "flags": [],
                    "notesCount": 0,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_completed(session, _SEASON_ID)
    assert len(result) == 1
    assert result[0].id == 2826460
    assert result[0].status == "completed"
    assert result[0].date == "2026-03-08"
    assert result[0].visitor.title == "TEAM A"
    assert result[0].home.title == "TEAM B"
    assert result[0].visitor_score == 4
    assert result[0].home_score == 3


@responses.activate
def test_list_scheduled_parses_bff_response(config: Config) -> None:
    """Test that list_scheduled correctly parses BFF API response format."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_bff_response(
            [
                {
                    "id": 2437882,
                    "status": "scheduled",
                    "date": "2026-03-08",
                    "time": "09:30",
                    "endTime": None,
                    "timeZoneName": "America/New_York",
                    "location": "Test Arena",
                    "gameNumber": "4",
                    "gameType": "regular_season",
                    "visitor": {
                        "id": 383188,
                        "title": "TEAM C",
                        "divisionId": 59677,
                        "divisionTitle": "18AA",
                    },
                    "home": {
                        "id": 383186,
                        "title": "TEAM D",
                        "divisionId": 59677,
                        "divisionTitle": "18AA",
                    },
                    "visitorScore": None,
                    "homeScore": None,
                    "hasShootout": None,
                    "hasOvertime": None,
                    "viewed": False,
                    "flags": [],
                    "notesCount": 0,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_scheduled(session, _SEASON_ID)
    assert len(result) == 1
    assert result[0].id == 2437882
    assert result[0].status == "scheduled"
    assert result[0].visitor_score is None
    assert result[0].home_score is None


@responses.activate
def test_list_completed_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_completed(session, _SEASON_ID)


@responses.activate
def test_list_completed_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_completed(session, _SEASON_ID)


@responses.activate
def test_list_completed_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_completed(session, _SEASON_ID)


@responses.activate
def test_list_scheduled_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_scheduled(session, _SEASON_ID)


@responses.activate
def test_list_brackets_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_brackets(session, _SEASON_ID)


@responses.activate
def test_list_completed_handles_empty_data(config: Config) -> None:
    """Test that list_completed returns empty list when API returns no games."""
    responses.add(responses.GET, _ENDPOINT, json=_bff_response([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_completed(session, _SEASON_ID)
    assert result == []


@responses.activate
def test_bff_non_success_status_raises_error(config: Config) -> None:
    """Test that non-success BFF status raises GameSheetError."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"status": "error", "data": []},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"non-success status"):
            list_completed(session, _SEASON_ID)
