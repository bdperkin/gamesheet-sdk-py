"""Tests for :mod:`gamesheet_sdk.ipad_keys`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_ipad_keys,
)
from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/api-keys"


@responses.activate
def test_list_ipad_keys_parses_jsonapi_response(config: Config) -> None:
    """Test that list_ipad_keys correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "api-keys",
                    "id": "3567",
                    "attributes": {
                        "value": "ipad-ncrr-kw",
                        "description": "iPad Key - Raleigh Raptors",
                        "roles": [
                            {
                                "title": "app",
                                "level": {
                                    "type": "seasons",
                                    "id": _SEASON_ID,
                                },
                            },
                        ],
                        "live_scoring_scopes": ["read", "write"],
                        "created_at": "2026-05-15T17:42:34.411627Z",
                        "updated_at": "2026-05-15T17:42:34.411627Z",
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_ipad_keys(session, _SEASON_ID)
    assert len(result) == 1
    assert result[0].id == "3567"
    assert result[0].value == "ipad-ncrr-kw"
    assert result[0].description == "iPad Key - Raleigh Raptors"
    assert result[0].roles == [
        {"title": "app", "level": {"type": "seasons", "id": _SEASON_ID}},
    ]
    assert result[0].live_scoring_scopes == ["read", "write"]
    assert result[0].created_at == datetime(
        2026,
        5,
        15,
        17,
        42,
        34,
        411627,
        tzinfo=timezone.utc,
    )
    assert result[0].updated_at == datetime(
        2026,
        5,
        15,
        17,
        42,
        34,
        411627,
        tzinfo=timezone.utc,
    )


@responses.activate
def test_list_ipad_keys_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_ipad_keys sends correct headers and season filter."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_ipad_keys(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"
    # Check that the season filter is applied
    assert req.url is not None
    assert "filter%5Bseason%5D=15020" in req.url or "filter[season]=15020" in req.url


@responses.activate
def test_list_ipad_keys_empty_data_returns_empty_list(config: Config) -> None:
    """Test that list_ipad_keys returns empty list when API returns no keys."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_ipad_keys(session, _SEASON_ID)


@responses.activate
def test_list_ipad_keys_401_raises_authentication_error(config: Config) -> None:
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
            list_ipad_keys(session, _SEASON_ID)


@responses.activate
def test_list_ipad_keys_404_raises_helpful_gamesheet_error(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"No iPad keys found or invalid season ID.*valid season ID.*seasons list --league-id",
        ):
            list_ipad_keys(session, _SEASON_ID)


@responses.activate
def test_list_ipad_keys_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_ipad_keys(session, _SEASON_ID)
