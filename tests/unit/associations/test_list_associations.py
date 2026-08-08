# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for :mod:`gamesheet_sdk.associations`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_associations,
)
from tests.helpers import (
    JSONAPI_CONTENT_TYPE,
    TEST_BASE_URL,
    TIMESTAMP_2024_01_01,
    jsonapi_payload,
)

_ENDPOINT = f"{TEST_BASE_URL}/api/associations"


@responses.activate
def test_list_associations_parses_jsonapi_response(config: Config) -> None:
    """Test that list_associations correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "associations",
                    "id": "11",
                    "attributes": {
                        "title": "Hockey Time Productions",
                        "logo": "",
                        "created_at": "2023-05-01T20:29:09.30692Z",
                        "updated_at": "2023-05-01T20:29:09.30692Z",
                    },
                },
                {
                    "type": "associations",
                    "id": "40",
                    "attributes": {
                        "title": "SuperSeries AAA",
                        "logo": "https://example/logo.png",
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": "2024-06-15T12:00:00Z",
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_associations(session)

    assert [a.id for a in result] == ["11", "40"]
    assert result[0].title == "Hockey Time Productions"
    assert not result[0].logo
    assert result[0].created_at == datetime(
        2023,
        5,
        1,
        20,
        29,
        9,
        306_920,
        tzinfo=timezone.utc,
    )
    assert result[0].created_at == datetime(
        2023,
        5,
        1,
        20,
        29,
        9,
        306_920,
        tzinfo=timezone.utc,
    )
    assert result[1].logo == "https://example/logo.png"


@responses.activate
def test_list_associations_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_associations sends correct Authorization and Accept headers."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_associations(session)

    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_list_associations_empty_data_returns_empty_list(config: Config) -> None:
    """Test that list_associations returns empty list when API returns no associations."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_associations(session)


@responses.activate
def test_list_associations_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_associations(session)


@responses.activate
def test_list_associations_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_associations(session)
