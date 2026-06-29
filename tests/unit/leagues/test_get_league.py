# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_league function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.leagues import get_league
from tests.helpers import JSONAPI_CONTENT_TYPE, TEST_BASE_URL

_ASSOCIATION_ID = "1001"


@responses.activate
def test_get_league_returns_single_league(config: Config) -> None:
    """Test that get_league returns a single league."""
    _league_id = "201"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_ASSOCIATION_ID}/leagues/{_league_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "leagues",
                "id": _league_id,
                "attributes": {
                    "title": "Test League",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_league(session, _ASSOCIATION_ID, _league_id)
    assert result.id == _league_id
    assert result.association_id == _ASSOCIATION_ID
    assert result.title == "Test League"


@responses.activate
def test_get_league_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_league sends correct authorization and accept headers."""
    _league_id = "201"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_ASSOCIATION_ID}/leagues/{_league_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "leagues",
                "id": _league_id,
                "attributes": {
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_league(session, _ASSOCIATION_ID, _league_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_get_league_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _league_id = "201"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_ASSOCIATION_ID}/leagues/{_league_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_league(session, _ASSOCIATION_ID, _league_id)


@responses.activate
def test_get_league_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _league_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_ASSOCIATION_ID}/leagues/{_league_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            get_league(session, _ASSOCIATION_ID, _league_id)


@responses.activate
def test_get_league_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _league_id = "201"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_ASSOCIATION_ID}/leagues/{_league_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_league(session, _ASSOCIATION_ID, _league_id)
