# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for list_referees function."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import list_referees
from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


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
                        "first_name": "John",
                        "last_name": "Smith",
                        "email_address": "john.smith@example.com",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
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
                {
                    "type": "referees",
                    "id": "102",
                    "attributes": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "email_address": None,
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
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
        result = list_referees(session, _SEASON_ID)
    assert [r.id for r in result] == ["101", "102"]
    assert result[0].first_name == "John"
    assert result[0].last_name == "Smith"
    assert result[0].email == "john.smith@example.com"
    assert result[0].season_id == _SEASON_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].first_name == "Jane"
    assert result[1].last_name == "Doe"
    assert result[1].email is None


@responses.activate
def test_list_referees_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_referees sends correct authorization and accept headers."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_referees_empty_data_returns_empty_list(config: Config) -> None:
    """Test that empty API response returns empty list."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_referees(session, _SEASON_ID)


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
            list_referees(session, _SEASON_ID)


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
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_uses_correct_endpoint(config: Config) -> None:
    """Test that list_referees uses the correct API endpoint."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, _SEASON_ID)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == _ENDPOINT
