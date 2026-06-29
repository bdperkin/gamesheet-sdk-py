# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for create_referee function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import create_referee
from tests.helpers import (
    DEFAULT_PLAYER_LAST_NAME,
    JSONAPI_CONTENT_TYPE,
    REFEREE_EXTERNAL_ID_PRIMARY,
    SEASON_ID,
    TEST_AUTH_HEADER,
    TEST_BASE_URL,
    TEST_EMAIL_REFEREE,
    TIMESTAMP_2024_09_01,
)

_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees"


@responses.activate
def test_create_referee_sends_correct_payload_with_all_fields(config: Config) -> None:
    """Test that create_referee sends correct payload with all optional fields."""
    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146197",
                "attributes": {
                    "external_id": REFEREE_EXTERNAL_ID_PRIMARY,
                    "first_name": "Wes",
                    "last_name": "McCauley",
                    "email_address": TEST_EMAIL_REFEREE,
                    "created_at": "2026-06-15T12:04:05.0325Z",
                    "updated_at": "2026-06-15T12:04:05.0325Z",
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
        result = create_referee(
            session,
            SEASON_ID,
            "Wes",
            "McCauley",
            email_address=TEST_EMAIL_REFEREE,
            external_id=REFEREE_EXTERNAL_ID_PRIMARY,
        )
    assert result.id == "1146197"
    assert result.first_name == "Wes"
    assert result.last_name == "McCauley"
    assert result.email == TEST_EMAIL_REFEREE
    assert result.season_id == SEASON_ID
    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    import json

    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Wes"
    assert payload["data"]["attributes"]["last_name"] == "McCauley"
    assert payload["data"]["attributes"]["email_address"] == TEST_EMAIL_REFEREE
    assert payload["data"]["attributes"]["external_id"] == REFEREE_EXTERNAL_ID_PRIMARY


@responses.activate
def test_create_referee_sends_correct_payload_required_fields_only(
    config: Config,
) -> None:
    """Test that create_referee sends correct payload with only required fields."""
    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146198",
                "attributes": {
                    "first_name": "Jane",
                    "last_name": DEFAULT_PLAYER_LAST_NAME,
                    "email_address": None,
                    "created_at": "2026-06-15T13:00:00Z",
                    "updated_at": "2026-06-15T13:00:00Z",
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
        result = create_referee(session, SEASON_ID, "Jane", DEFAULT_PLAYER_LAST_NAME)
    assert result.id == "1146198"
    assert result.first_name == "Jane"
    assert result.last_name == DEFAULT_PLAYER_LAST_NAME
    assert result.email is None
    # Verify the request payload
    import json

    req = responses.calls[0].request
    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Jane"
    assert payload["data"]["attributes"]["last_name"] == DEFAULT_PLAYER_LAST_NAME
    assert "email_address" not in payload["data"]["attributes"]
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_create_referee_sends_bearer_and_jsonapi_headers(config: Config) -> None:
    """Test that create_referee sends correct Authorization and JSON:API headers."""
    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "101",
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": TIMESTAMP_2024_09_01,
                    "updated_at": TIMESTAMP_2024_09_01,
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
        create_referee(session, SEASON_ID, "Test", "Ref")
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == TEST_AUTH_HEADER
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE
    assert req.headers["Content-Type"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_create_referee_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.POST,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            create_referee(session, SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.POST, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            create_referee(session, SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.POST, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            create_referee(session, SEASON_ID, "Test", "Ref")
