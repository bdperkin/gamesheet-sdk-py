# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_referee function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import get_referee
from tests.unit.referees.conftest import SEASON_ID, TEST_BASE_URL, referee_response_data


@responses.activate
def test_get_referee_returns_single_referee(config: Config) -> None:
    """Test that get_referee returns a single referee."""
    _referee_id = "1146197"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
                    "email_address": "Wes.McCauley@example.com",
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
        result = get_referee(session, SEASON_ID, _referee_id)
    assert result.id == _referee_id
    assert result.first_name == "WES"
    assert result.last_name == "MCCAULEY"
    assert result.email == "Wes.McCauley@example.com"
    assert result.season_id == SEASON_ID


@responses.activate
def test_get_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_referee sends correct authorization and accept headers."""
    _referee_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json=referee_response_data(_referee_id),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_referee(session, SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_referee_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _referee_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_referee(session, SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _referee_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            get_referee(session, SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _referee_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_referee(session, SEASON_ID, _referee_id)
