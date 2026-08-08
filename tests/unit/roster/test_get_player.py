# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_player function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.admin.roster import get_player
from tests.helpers import (
    CLI_TEST_SEASON_ID,
    DEFAULT_PLAYER_FIRST_NAME,
    DEFAULT_PLAYER_LAST_NAME,
    JSONAPI_CONTENT_TYPE,
    SEASON_ID,
    TEST_AUTH_HEADER,
    TEST_BASE_URL,
    TIMESTAMP_2024_01_01,
)


@responses.activate
def test_get_player_returns_single_player(config: Config) -> None:
    """Test that get_player returns a single player."""
    _player_id = CLI_TEST_SEASON_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_player_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "players",
                "id": _player_id,
                "attributes": {
                    "first_name": DEFAULT_PLAYER_FIRST_NAME,
                    "last_name": DEFAULT_PLAYER_LAST_NAME,
                    "created_at": TIMESTAMP_2024_01_01,
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_player(session, SEASON_ID, _player_id)

    assert result.id == _player_id
    assert result.season_id == SEASON_ID
    assert result.first_name == DEFAULT_PLAYER_FIRST_NAME
    assert result.last_name == DEFAULT_PLAYER_LAST_NAME


@responses.activate
def test_get_player_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_player sends correct authorization and accept headers."""
    _player_id = CLI_TEST_SEASON_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_player_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "players",
                "id": _player_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Player",
                    "created_at": TIMESTAMP_2024_01_01,
                    "updated_at": TIMESTAMP_2024_01_01,
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_player(session, SEASON_ID, _player_id)

    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == TEST_AUTH_HEADER
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_get_player_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _player_id = CLI_TEST_SEASON_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_player_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_player(session, SEASON_ID, _player_id)


@responses.activate
def test_get_player_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _player_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_player_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            get_player(session, SEASON_ID, _player_id)


@responses.activate
def test_get_player_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _player_id = CLI_TEST_SEASON_ID
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_player_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_player(session, SEASON_ID, _player_id)
