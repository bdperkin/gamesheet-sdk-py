# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_association function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.associations import get_association
from tests.fixtures.constants import TEST_ERROR_PATTERN_404_RESOURCE
from tests.helpers import (
    DEFAULT_ASSOCIATION_NAME,
    JSONAPI_CONTENT_TYPE,
    TEST_AUTH_HEADER,
    TEST_BASE_URL,
    TIMESTAMP_2024_01_01,
)


@responses.activate
def test_get_association_returns_single_association(config: Config) -> None:
    """Test that get_association returns a single association."""
    _association_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_association_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "associations",
                "id": _association_id,
                "attributes": {
                    "title": DEFAULT_ASSOCIATION_NAME,
                    "logo": "https://example.com/logo.png",
                    "created_at": TIMESTAMP_2024_01_01,
                    "updated_at": "2024-06-01T00:00:00Z",
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_association(session, _association_id)
    assert result.id == _association_id
    assert result.title == DEFAULT_ASSOCIATION_NAME
    assert result.logo == "https://example.com/logo.png"


@responses.activate
def test_get_association_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_association sends correct authorization and accept headers."""
    _association_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_association_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "associations",
                "id": _association_id,
                "attributes": {
                    "title": "Test",
                    "logo": "",
                    "created_at": TIMESTAMP_2024_01_01,
                    "updated_at": TIMESTAMP_2024_01_01,
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_association(session, _association_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == TEST_AUTH_HEADER
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_get_association_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _association_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_association_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_association(session, _association_id)


@responses.activate
def test_get_association_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _association_id = "nonexistent"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_association_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=TEST_ERROR_PATTERN_404_RESOURCE,
        ):
            get_association(session, _association_id)


@responses.activate
def test_get_association_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _association_id = "101"
    _get_endpoint = f"{TEST_BASE_URL}/api/associations/{_association_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_association(session, _association_id)
