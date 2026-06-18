"""Tests for update_referee function."""

from __future__ import annotations

import json

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import update_referee

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


@responses.activate
def test_update_referee_sends_correct_payload_all_fields(config: Config) -> None:
    """Test that update_referee sends correct payload when updating all fields."""
    _referee_id = "1146196"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock GET request to fetch current data
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "OLD-EXTERNAL-ID",
                    "first_name": "Wes",
                    "last_name": "McCauley",
                    "email_address": "wes@old.com",
                    "created_at": "2026-06-15T12:01:41.449299Z",
                    "updated_at": "2026-06-15T12:01:41.449299Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock PATCH request with updated data
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "87487685-24B9-46EF-B8A3-D3B7ECEB1F68",
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
                    "email_address": "McCauley.Wes@example.com",
                    "created_at": "2026-06-15T12:01:41.449299Z",
                    "updated_at": "2026-06-15T12:06:46.519767Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_referee(
            session,
            _SEASON_ID,
            _referee_id,
            first_name="WES",
            last_name="MCCAULEY",
            email_address="McCauley.Wes@example.com",
            external_id="87487685-24B9-46EF-B8A3-D3B7ECEB1F68",
        )
    assert result.id == _referee_id
    assert result.first_name == "WES"
    assert result.last_name == "MCCAULEY"
    assert result.email == "McCauley.Wes@example.com"
    assert result.season_id == _SEASON_ID
    # Verify we made both GET and PATCH requests
    assert len(responses.calls) == 2
    get_req = responses.calls[0].request
    patch_req = responses.calls[1].request
    assert get_req.method == "GET"
    assert patch_req.method == "PATCH"
    # Verify the PATCH request payload includes all fields
    assert patch_req.body is not None
    payload = json.loads(patch_req.body)
    assert payload["data"]["id"] == _referee_id
    assert payload["data"]["type"] == "referees"
    assert payload["data"]["attributes"]["first_name"] == "WES"
    assert payload["data"]["attributes"]["last_name"] == "MCCAULEY"
    assert payload["data"]["attributes"]["email_address"] == "McCauley.Wes@example.com"
    assert payload["data"]["attributes"]["external_id"] == "87487685-24B9-46EF-B8A3-D3B7ECEB1F68"


@responses.activate
def test_update_referee_sends_correct_payload_partial_fields(
    config: Config,
) -> None:
    """Test that update_referee preserves unmodified fields when partially updating."""
    _referee_id = "1146197"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock GET request to fetch current data
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Original",
                    "last_name": "Name",
                    "email_address": "original@example.com",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock PATCH request
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email_address": "original@example.com",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T13:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_referee(
            session,
            _SEASON_ID,
            _referee_id,
            first_name="Updated",
        )
    assert result.id == _referee_id
    assert result.first_name == "Updated"
    assert result.last_name == "Name"
    assert result.email == "original@example.com"
    # Verify we made both GET and PATCH requests
    assert len(responses.calls) == 2
    # Verify the PATCH payload includes all required fields (from current + updates)
    patch_req = responses.calls[1].request
    assert patch_req.body is not None
    payload = json.loads(patch_req.body)
    assert payload["data"]["attributes"]["first_name"] == "Updated"
    assert payload["data"]["attributes"]["last_name"] == "Name"  # Preserved from current
    assert payload["data"]["attributes"]["email_address"] == "original@example.com"  # Preserved


@responses.activate
def test_update_referee_sends_bearer_and_jsonapi_headers(config: Config) -> None:
    """Test that update_referee sends correct Authorization and JSON:API headers."""
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock GET request
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Old",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock PATCH request
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        update_referee(session, _SEASON_ID, _referee_id, first_name="Test")
    assert len(responses.calls) == 2
    get_req = responses.calls[0].request
    patch_req = responses.calls[1].request
    assert get_req.headers["Authorization"] == "Bearer test-token"
    assert get_req.headers["Accept"] == "application/vnd.api+json"
    assert patch_req.headers["Authorization"] == "Bearer test-token"
    assert patch_req.headers["Accept"] == "application/vnd.api+json"
    assert patch_req.headers["Content-Type"] == "application/vnd.api+json"


@responses.activate
def test_update_referee_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 401
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_update_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    _referee_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 404
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_update_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 500
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_update_referee_preserves_existing_external_id(config: Config) -> None:
    """Test that update_referee preserves external_id from current attributes when not provided."""
    _referee_id = "1146300"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _existing_external_id = "EXISTING-EXT-ID-123"
    # Mock the GET request (fetch current data)
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Old",
                    "last_name": "Name",
                    "email_address": "old@example.com",
                    "external_id": _existing_external_id,  # Has existing external_id
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock the PATCH request
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "New",
                    "last_name": "Name",
                    "email_address": "old@example.com",
                    "external_id": _existing_external_id,
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T13:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        # Update only first name, should preserve existing external_id
        result = update_referee(session, _SEASON_ID, _referee_id, first_name="New")
    assert result.first_name == "New"
    assert result.last_name == "Name"
    # Verify the PATCH payload preserved the external_id
    assert len(responses.calls) == 2
    patch_req = responses.calls[1].request
    assert patch_req.body is not None
    payload = json.loads(patch_req.body)
    assert payload["data"]["attributes"]["external_id"] == _existing_external_id


@responses.activate
def test_update_referee_patch_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 on PATCH request raises AuthenticationError."""
    _referee_id = "1146301"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock the GET request (succeeds)
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock the PATCH request with 401
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Updated")


@responses.activate
def test_update_referee_patch_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 on PATCH request raises GameSheetError with helpful message."""
    _referee_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock the GET request (succeeds)
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock the PATCH request with 404
    responses.add(responses.PATCH, _patch_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Updated")


@responses.activate
def test_update_referee_patch_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors on PATCH request raise GameSheetError."""
    _referee_id = "1146302"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # Mock the GET request (succeeds)
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    # Mock the PATCH request with 500
    responses.add(responses.PATCH, _patch_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Updated")
