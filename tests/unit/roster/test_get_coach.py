"""Tests for get_coach function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.roster import get_coach

_BASE = "https://test.example"
_SEASON_ID = "15020"


@responses.activate
def test_get_coach_returns_single_coach(config: Config) -> None:
    """Test that get_coach returns a single coach."""
    _coach_id = "601"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches/{_coach_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "coaches",
                "id": _coach_id,
                "attributes": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
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
        result = get_coach(session, _SEASON_ID, _coach_id)
    assert result.id == _coach_id
    assert result.season_id == _SEASON_ID
    assert result.first_name == "Jane"
    assert result.last_name == "Smith"


@responses.activate
def test_get_coach_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_coach sends correct authorization and accept headers."""
    _coach_id = "601"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches/{_coach_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "coaches",
                "id": _coach_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Coach",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
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
        get_coach(session, _SEASON_ID, _coach_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_coach_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _coach_id = "601"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches/{_coach_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_coach(session, _SEASON_ID, _coach_id)


@responses.activate
def test_get_coach_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _coach_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches/{_coach_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            get_coach(session, _SEASON_ID, _coach_id)


@responses.activate
def test_get_coach_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _coach_id = "601"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches/{_coach_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_coach(session, _SEASON_ID, _coach_id)
