# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for update_division function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    update_division,
)
from tests.helpers import (
    JSONAPI_CONTENT_TYPE,
    SEASON_ID,
    TEST_BASE_URL,
    TIMESTAMP_2024_09_01,
)

_DIVISION_ID = "80998"
_UPDATE_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/divisions/{_DIVISION_ID}"


def _verify_update_payload(request_body: bytes | str, expected_title: str) -> None:
    """Verify the structure of an update division request payload."""
    import json

    payload = json.loads(request_body)
    assert payload["data"]["type"] == "divisions"
    assert payload["data"]["id"] == _DIVISION_ID
    assert payload["data"]["attributes"]["title"] == expected_title
    assert payload["data"]["attributes"]["settings"] == {}
    assert payload["data"]["relationships"]["season"]["data"]["id"] == SEASON_ID
    assert payload["data"]["relationships"]["season"]["data"]["type"] == "seasons"


@responses.activate
def test_update_division_updates_title(config: Config) -> None:
    """Test that update_division successfully updates division title."""
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Updated Division",
                    "external_id": "existing-external-id",
                    "settings": {},
                    "created_at": TIMESTAMP_2024_09_01,
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            SEASON_ID,
            _DIVISION_ID,
            title="Updated Division",
        )
    assert result.id == _DIVISION_ID
    assert result.title == "Updated Division"
    assert result.season_id == SEASON_ID
    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE
    assert req.headers["Content-Type"] == JSONAPI_CONTENT_TYPE
    assert req.body is not None
    _verify_update_payload(req.body, "Updated Division")
    import json

    payload = json.loads(req.body)
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_update_division_updates_external_id(config: Config) -> None:
    """Test that update_division fetches current title when updating only external_id."""
    # When updating only external_id, function fetches current title first
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/divisions/{_DIVISION_ID}",
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Existing Title",
                    "external_id": "old-external-id",
                    "settings": {},
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
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Existing Title",
                    "external_id": "new-external-id",
                    "settings": {},
                    "created_at": TIMESTAMP_2024_09_01,
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            SEASON_ID,
            _DIVISION_ID,
            external_id="new-external-id",
        )
    assert result.id == _DIVISION_ID
    assert result.external_id == "new-external-id"
    # Verify title was fetched and included in PATCH (required by API)
    import json

    assert len(responses.calls) == 2
    # First call: GET to fetch current title
    assert responses.calls[0].request.method == "GET"
    # Second call: PATCH with existing title + new external_id
    assert responses.calls[1].request.body is not None
    patch_payload = json.loads(responses.calls[1].request.body)
    assert patch_payload["data"]["attributes"]["title"] == "Existing Title"
    assert patch_payload["data"]["attributes"]["external_id"] == "new-external-id"
    assert patch_payload["data"]["attributes"]["settings"] == {}
    assert patch_payload["data"]["relationships"]["season"]["data"]["id"] == SEASON_ID


@responses.activate
def test_update_division_updates_both_fields(config: Config) -> None:
    """Test that update_division successfully updates both title and external_id."""
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "New Title",
                    "external_id": "new-id",
                    "settings": {},
                    "created_at": TIMESTAMP_2024_09_01,
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            SEASON_ID,
            _DIVISION_ID,
            title="New Title",
            external_id="new-id",
        )
    assert result.title == "New Title"
    assert result.external_id == "new-id"


def test_update_division_raises_value_error_if_no_fields_provided(
    config: Config,
) -> None:
    """Test that update_division raises ValueError when no fields are provided."""
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            ValueError,
            match="At least one of title or external_id must be provided",
        ):
            update_division(session, SEASON_ID, _DIVISION_ID)


@responses.activate
def test_update_division_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_division(session, SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            update_division(session, SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_division(session, SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_handles_failed_title_fetch(config: Config) -> None:
    """When updating only external_id and GET fails, PATCH proceeds with empty title."""
    # GET fails with 404
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/divisions/{_DIVISION_ID}",
        status=404,
    )
    # PATCH will fail due to missing title, which is expected
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "errors": [
                {
                    "title": "is required",
                    "source": {"pointer": "/data/attributes/title"},
                },
            ],
        },
        status=400,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 400"):
            update_division(session, SEASON_ID, _DIVISION_ID, external_id="new-id")
