# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for get_team function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.teams import get_team
from tests.helpers import (
    DEFAULT_TEAM_NAME,
    JSONAPI_CONTENT_TYPE,
    SEASON_ID,
    TEST_AUTH_HEADER,
    TEST_BASE_URL,
    TIMESTAMP_2024_01_01,
)


@responses.activate
def test_get_team_returns_single_team(config: Config) -> None:
    """Test that get_team returns a single team."""
    _team_id = "401"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": _team_id,
                    "attributes": {
                        "title": DEFAULT_TEAM_NAME,
                        "logo_url": "https://example.com/logo.png",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": "2024-06-01T00:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team(session, SEASON_ID, _team_id)
    assert result.id == _team_id
    assert result.season_id == SEASON_ID
    assert result.title == DEFAULT_TEAM_NAME


@responses.activate
def test_get_team_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that get_team sends correct authorization and accept headers."""
    _team_id = "401"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": _team_id,
                    "attributes": {
                        "title": "Test",
                        "logo_url": "",
                        "roster": {},
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": TIMESTAMP_2024_01_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_team(session, SEASON_ID, _team_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == TEST_AUTH_HEADER
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE


@responses.activate
def test_get_team_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 raises AuthenticationError."""
    _team_id = "401"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_team(session, SEASON_ID, _team_id)


@responses.activate
def test_get_team_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that team not found raises GameSheetError with helpful message."""
    _team_id = "nonexistent"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "other-team",
                    "attributes": {
                        "title": "Other Team",
                        "logo_url": "",
                        "roster": {},
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": TIMESTAMP_2024_01_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Team '.*' not found.*valid team ID and season ID",
        ):
            get_team(session, SEASON_ID, _team_id)


@responses.activate
def test_get_team_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _team_id = "401"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(responses.GET, _list_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_team(session, SEASON_ID, _team_id)


@responses.activate
def test_get_team_with_invitation_code(config: Config) -> None:
    """Test that get_team extracts invitation code from included resources."""
    _team_id = "401"
    _invitation_code = "ABC123"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": _team_id,
                    "attributes": {
                        "title": DEFAULT_TEAM_NAME,
                        "logo_url": "",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": "2024-06-01T00:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                        "invitations": {
                            "data": [{"type": "invitations", "id": "inv-1"}],
                        },
                    },
                },
            ],
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
        result = get_team(session, SEASON_ID, _team_id)
    assert result.id == _team_id
    assert result.season_id == SEASON_ID
    assert result.title == DEFAULT_TEAM_NAME
    assert result.invitation_code == _invitation_code


@responses.activate
def test_get_team_without_invitation_code(config: Config) -> None:
    """Test that get_team handles missing invitation code gracefully."""
    _team_id = "402"
    _list_endpoint = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"
    responses.add(
        responses.GET,
        _list_endpoint,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": _team_id,
                    "attributes": {
                        "title": "Test Team Without Code",
                        "logo_url": "",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_01_01,
                        "updated_at": "2024-06-01T00:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                    },
                },
            ],
            "included": [],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team(session, SEASON_ID, _team_id)
    assert result.id == _team_id
    assert result.season_id == SEASON_ID
    assert result.title == "Test Team Without Code"
    assert result.invitation_code is None
