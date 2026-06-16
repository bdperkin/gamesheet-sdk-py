"""Tests for get_division function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.divisions import get_division

_BASE = "https://test.example"


@responses.activate
def test_get_division_returns_single_division(config: Config) -> None:
    """Test that get_division returns a single division."""
    _division_id = "301"
    _season_id = "15020"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "divisions",
                "id": _division_id,
                "attributes": {
                    "title": "Test Division",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _season_id}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_division(session, _division_id, include_team_count=False)
    assert result.id == _division_id
    assert result.season_id == _season_id
    assert result.title == "Test Division"


@responses.activate
def test_get_division_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_division sends correct authorization and accept headers."""
    _division_id = "301"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "divisions",
                "id": _division_id,
                "attributes": {
                    "title": "Test",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": "1"}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_division(session, _division_id, include_team_count=False)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_division_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _division_id = "301"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_division(session, _division_id, include_team_count=False)


@responses.activate
def test_get_division_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _division_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Division '.*' not found.*valid division ID",
        ):
            get_division(session, _division_id, include_team_count=False)


@responses.activate
def test_get_division_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _division_id = "301"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_division(session, _division_id, include_team_count=False)


@responses.activate
def test_get_division_with_team_count(config: Config) -> None:
    """Test that get_division can fetch team count."""
    _division_id = "301"
    _season_id = "15020"
    _get_endpoint = f"{_BASE}/api/divisions/{_division_id}"
    _teams_endpoint = f"{_BASE}/api/divisions/{_division_id}/teams"

    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "divisions",
                "id": _division_id,
                "attributes": {
                    "title": "Test Division",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _season_id}},
                },
            },
        },
        status=200,
    )

    responses.add(
        responses.GET,
        _teams_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1",
                    "attributes": {
                        "title": "Team 1",
                        "roster": {},
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _season_id}},
                    },
                },
                {
                    "type": "teams",
                    "id": "2",
                    "attributes": {
                        "title": "Team 2",
                        "roster": {},
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _season_id}},
                    },
                },
            ],
        },
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_division(session, _division_id, include_team_count=True)

    assert result.id == _division_id
    assert result.season_id == _season_id
    assert result.title == "Test Division"
    assert result.team_count == 2
