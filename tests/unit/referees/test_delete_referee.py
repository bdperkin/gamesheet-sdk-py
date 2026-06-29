# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for delete_referee function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import delete_referee
from tests.helpers import JSONAPI_CONTENT_TYPE, SEASON_ID, TEST_BASE_URL

_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees"


@responses.activate
def test_delete_referee_success(config: Config) -> None:
    """Test successful referee deletion."""
    _referee_id = "1146197"
    _delete_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        # Should not raise
        delete_referee(session, SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.method == "DELETE"


@responses.activate
def test_delete_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that delete_referee sends correct Authorization and Accept headers."""
    _referee_id = "101"
    _delete_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        delete_referee(session, SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_delete_referee_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    _referee_id = "101"
    _delete_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            delete_referee(session, SEASON_ID, _referee_id)


@responses.activate
def test_delete_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    _referee_id = "nonexistent"
    _delete_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            delete_referee(session, SEASON_ID, _referee_id)


@responses.activate
def test_delete_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _referee_id = "101"
    _delete_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            delete_referee(session, SEASON_ID, _referee_id)
