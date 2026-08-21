# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_referee function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.admin.referees import get_referee
from tests.helpers import (
    REFEREE_EXTERNAL_ID_PRIMARY,
    TEST_AUTH_HEADER,
    TEST_EMAIL_REFEREE,
)
from tests.unit.referees.conftest import SEASON_ID, TEST_BASE_URL, referee_response_data


@responses.activate
def test_get_referee_returns_single_referee(config: Config) -> None:
    """Test that get_referee returns a single referee."""
    referee_id = "1146197"
    get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{referee_id}"
    responses.add(
        responses.GET,
        get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": referee_id,
                "attributes": {
                    "external_id": REFEREE_EXTERNAL_ID_PRIMARY,
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
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
        result = get_referee(session, SEASON_ID, referee_id)

    assert result.id == referee_id
    assert result.first_name == "WES"
    assert result.last_name == "MCCAULEY"
    assert result.email == TEST_EMAIL_REFEREE
    assert result.season_id == SEASON_ID


@responses.activate
def test_get_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_referee sends correct authorization and accept headers."""
    referee_id = "101"
    get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{referee_id}"
    responses.add(
        responses.GET,
        get_endpoint,
        json=referee_response_data(referee_id),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_referee(session, SEASON_ID, referee_id)

    from tests.helpers import JSONAPI_CONTENT_TYPE

    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == TEST_AUTH_HEADER
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_get_referee_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    referee_id = "101"
    get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{referee_id}"
    responses.add(
        responses.GET,
        get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_referee(session, SEASON_ID, referee_id)


@responses.activate
def test_get_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    referee_id = "nonexistent"
    get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{referee_id}"
    responses.add(responses.GET, get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            get_referee(session, SEASON_ID, referee_id)


@responses.activate
def test_get_referee_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    referee_id = "101"
    get_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/referees/{referee_id}"
    responses.add(responses.GET, get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_referee(session, SEASON_ID, referee_id)
