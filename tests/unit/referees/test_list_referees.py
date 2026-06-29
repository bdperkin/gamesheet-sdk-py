# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for list_referees function."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import list_referees
from tests.helpers import (
    DEFAULT_COACH_LAST_NAME,
    DEFAULT_PLAYER_FIRST_NAME,
    DEFAULT_PLAYER_LAST_NAME,
    JSONAPI_CONTENT_TYPE,
    SEASON_ID,
    TEST_BASE_URL,
    jsonapi_payload,
)

_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees"


@responses.activate
def test_list_referees_parses_jsonapi_response(config: Config) -> None:
    """Test that list_referees correctly parses JSON:API response."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "referees",
                    "id": "101",
                    "attributes": {
                        "first_name": DEFAULT_PLAYER_FIRST_NAME,
                        "last_name": DEFAULT_COACH_LAST_NAME,
                        "email_address": "john.smith@example.com",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": SEASON_ID,
                            },
                        },
                    },
                },
                {
                    "type": "referees",
                    "id": "102",
                    "attributes": {
                        "first_name": "Jane",
                        "last_name": DEFAULT_PLAYER_LAST_NAME,
                        "email_address": None,
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": SEASON_ID,
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
        result = list_referees(session, SEASON_ID)
    assert [r.id for r in result] == ["101", "102"]
    assert result[0].first_name == DEFAULT_PLAYER_FIRST_NAME
    assert result[0].last_name == DEFAULT_COACH_LAST_NAME
    assert result[0].email == "john.smith@example.com"
    assert result[0].season_id == SEASON_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].first_name == "Jane"
    assert result[1].last_name == DEFAULT_PLAYER_LAST_NAME
    assert result[1].email is None


@responses.activate
def test_list_referees_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_referees sends correct authorization and accept headers."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_list_referees_empty_data_returns_empty_list(config: Config) -> None:
    """Test that empty API response returns empty list."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_referees(session, SEASON_ID)


@responses.activate
def test_list_referees_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_referees(session, SEASON_ID)


@responses.activate
def test_list_referees_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            list_referees(session, SEASON_ID)


@responses.activate
def test_list_referees_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_referees(session, SEASON_ID)


@responses.activate
def test_list_referees_uses_correct_endpoint(config: Config) -> None:
    """Test that list_referees uses the correct API endpoint."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, SEASON_ID)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == _ENDPOINT
