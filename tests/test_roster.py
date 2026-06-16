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

_BASE = "https://test.example"
_SEASON_ID = "15020"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_players_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=_payload(
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
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=_payload(
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
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_players_404_raises_gamesheet_error(config: Config) -> None:
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_players_500_raises_gamesheet_error(config: Config) -> None:
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_players(session, _SEASON_ID)


@responses.activate
def test_list_coaches_401_raises_authentication_error(config: Config) -> None:
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_coaches_404_raises_gamesheet_error(config: Config) -> None:
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_coaches_500_raises_gamesheet_error(config: Config) -> None:
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            list_coaches(session, _SEASON_ID)


@responses.activate
def test_list_players_handles_empty_data(config: Config) -> None:
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_players(session, _SEASON_ID)
    assert result == []


@responses.activate
def test_list_coaches_handles_empty_data(config: Config) -> None:
    responses.add(responses.GET, _COACHES_ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("valid")
        result = list_coaches(session, _SEASON_ID)
    assert result == []
