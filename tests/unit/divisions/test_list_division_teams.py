"""Tests for list_division_teams function."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_division_teams,
)
from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_DIVISION_ID = "701"
_DIVISION_TEAMS_ENDPOINT = f"{_BASE}/api/divisions/{_DIVISION_ID}/teams"


@responses.activate
def test_list_division_teams_parses_jsonapi_response(config: Config) -> None:
    """Test that list_division_teams correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Raleigh Raptors",
                        "logo_url": "https://example.com/logo1.png",
                        "roster": {
                            "players": [{"id": str(i)} for i in range(15)],
                            "coaches": [{"id": str(i)} for i in range(3)],
                        },
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
                            },
                        },
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": _DIVISION_ID,
                            },
                        },
                    },
                },
                {
                    "type": "teams",
                    "id": "1002",
                    "attributes": {
                        "title": "Durham Bulls",
                        "roster": {
                            "players": [{"id": str(i)} for i in range(12)],
                            "coaches": [{"id": str(i)} for i in range(2)],
                        },
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
                            },
                        },
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": _DIVISION_ID,
                            },
                        },
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_division_teams(session, _DIVISION_ID)
    assert [t.id for t in result] == ["1001", "1002"]
    assert result[0].title == "Raleigh Raptors"
    assert result[0].season_id == _SEASON_ID
    assert result[0].division_id == _DIVISION_ID
    assert result[0].logo == "https://example.com/logo1.png"
    assert result[0].invitation_code is None  # No invitations in this response
    assert result[0].player_count == 15
    assert result[0].coach_count == 3
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "Durham Bulls"
    assert result[1].logo is None


@responses.activate
def test_list_division_teams_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_division_teams sends correct Authorization and Accept headers."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_division_teams(session, _DIVISION_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_division_teams_empty_data_returns_empty_list(config: Config) -> None:
    """Test that list_division_teams returns empty list when API returns no teams."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_with_invitation_codes(config: Config) -> None:
    """Test that invitation codes are parsed when included in the response."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Raleigh Raptors",
                        "logo_url": "https://example.com/logo1.png",
                        "roster": {
                            "players": [{"id": str(i)} for i in range(15)],
                            "coaches": [{"id": str(i)} for i in range(3)],
                        },
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
                            },
                        },
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": _DIVISION_ID,
                            },
                        },
                        "invitations": {
                            "data": [
                                {
                                    "type": "invitations",
                                    "id": "inv-123",
                                },
                            ],
                        },
                    },
                },
            ],
            "included": [
                {
                    "type": "invitations",
                    "id": "inv-123",
                    "attributes": {
                        "code": "RAPTORS2024",
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_division_teams(session, _DIVISION_ID)
    assert len(result) == 1
    assert result[0].invitation_code == "RAPTORS2024"


@responses.activate
def test_list_division_teams_sends_include_invitations_param(config: Config) -> None:
    """Test that list_division_teams requests invitations to be included."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_division_teams(session, _DIVISION_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    # Check query parameters
    assert req.url is not None
    assert "include=invitations" in req.url
    assert "fields%5Bteams%5D=title%2Clogo_url%2Croster%2Ccreated_at%2Cupdated_at" in req.url


@responses.activate
def test_list_division_teams_handles_invitation_as_single_object(config: Config) -> None:
    """Test that invitation relationship as single object (not array) is handled."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Test Team",
                        "roster": {"players": [], "coaches": []},
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": _DIVISION_ID}},
                        "invitations": {"data": {"type": "invitations", "id": "inv-456"}},
                    },
                },
            ],
            "included": [
                {"type": "invitations", "id": "inv-456", "attributes": {"code": "SINGLE2024"}},
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_division_teams(session, _DIVISION_ID)
    assert len(result) == 1
    assert result[0].invitation_code == "SINGLE2024"


@responses.activate
def test_list_division_teams_handles_missing_invitation_code_gracefully(config: Config) -> None:
    """Test that teams with invitations relationship but no matching code are handled."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Test Team",
                        "roster": {"players": [], "coaches": []},
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": _DIVISION_ID}},
                        "invitations": {"data": [{"type": "invitations", "id": "inv-999"}]},
                    },
                },
            ],
            "included": [],  # No matching invitation in included
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_division_teams(session, _DIVISION_ID)
    assert len(result) == 1
    assert result[0].invitation_code is None


@responses.activate
def test_list_division_teams_handles_malformed_invitation_data(config: Config) -> None:
    """Test that malformed invitation data in included is ignored gracefully."""
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Test Team",
                        "roster": {"players": [], "coaches": []},
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": _DIVISION_ID}},
                    },
                },
            ],
            "included": [
                {"type": "invitations", "id": "inv-123"},  # Missing code in attributes
                {"type": "invitations"},  # Missing id
                {"type": "other-type", "id": "123", "attributes": {"code": "X"}},  # Wrong type
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_division_teams(session, _DIVISION_ID)
    assert len(result) == 1
    assert result[0].invitation_code is None
