"""Tests for get_team function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.teams import get_team

_BASE = "https://test.example"
_SEASON_ID = "15020"


@responses.activate
def test_get_team_returns_single_team(config: Config) -> None:
    """Test that get_team returns a single team."""
    _team_id = "401"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_team_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _team_id,
                "attributes": {
                    "title": "Test Team",
                    "roster": {"players": [], "coaches": []},
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
        result = get_team(session, _SEASON_ID, _team_id)
    assert result.id == _team_id
    assert result.season_id == _SEASON_ID
    assert result.title == "Test Team"


@responses.activate
def test_get_team_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_team sends correct authorization and accept headers."""
    _team_id = "401"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_team_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _team_id,
                "attributes": {
                    "title": "Test",
                    "roster": {},
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
        get_team(session, _SEASON_ID, _team_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_team_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _team_id = "401"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_team_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_team(session, _SEASON_ID, _team_id)


@responses.activate
def test_get_team_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 raises GameSheetError with helpful message."""
    _team_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_team_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Team '.*' not found.*valid team ID and season ID",
        ):
            get_team(session, _SEASON_ID, _team_id)


@responses.activate
def test_get_team_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _team_id = "401"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_team_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_team(session, _SEASON_ID, _team_id)


@responses.activate
def test_get_team_with_invitation_code(config: Config) -> None:
    """Test that get_team extracts invitation code from included resources."""
    _team_id = "401"
    _season_id = "15020"
    _invitation_code = "ABC123"
    _get_endpoint = f"{_BASE}/api/seasons/{_season_id}/teams/{_team_id}"
    
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _team_id,
                "attributes": {
                    "title": "Test Team",
                    "roster": {"players": [], "coaches": []},
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _season_id}},
                    "invitations": {"data": {"type": "invitations", "id": "inv-1"}},
                },
            },
            "included": [
                {
                    "type": "invitations",
                    "id": "inv-1",
                    "attributes": {
                        "code": _invitation_code,
                    },
                },
            ],
        },
        status=200,
    )
    
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team(session, _season_id, _team_id)
    
    assert result.id == _team_id
    assert result.season_id == _season_id
    assert result.title == "Test Team"
    assert result.invitation_code == _invitation_code


@responses.activate
def test_get_team_without_invitation_code(config: Config) -> None:
    """Test that get_team handles missing invitation code gracefully."""
    _team_id = "402"
    _season_id = "15020"
    _get_endpoint = f"{_BASE}/api/seasons/{_season_id}/teams/{_team_id}"
    
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _team_id,
                "attributes": {
                    "title": "Test Team Without Code",
                    "roster": {"players": [], "coaches": []},
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _season_id}},
                },
            },
            "included": [],
        },
        status=200,
    )
    
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team(session, _season_id, _team_id)
    
    assert result.id == _team_id
    assert result.season_id == _season_id
    assert result.title == "Test Team Without Code"
    assert result.invitation_code is None


@responses.activate
def test_get_team_with_non_invitation_included(config: Config) -> None:
    """Test that get_team skips non-invitation included resources."""
    _team_id = "403"
    _season_id = "15020"
    _get_endpoint = f"{_BASE}/api/seasons/{_season_id}/teams/{_team_id}"
    
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _team_id,
                "attributes": {
                    "title": "Test Team",
                    "roster": {"players": [], "coaches": []},
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-06-01T00:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _season_id}},
                },
            },
            "included": [
                {
                    "type": "other_resource",
                    "id": "other-1",
                    "attributes": {},
                },
            ],
        },
        status=200,
    )
    
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team(session, _season_id, _team_id)
    
    assert result.id == _team_id
    assert result.invitation_code is None
