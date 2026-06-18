"""Tests for delete_division function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    delete_division,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_DELETE_DIVISION_ID = "80999"
_DELETE_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/divisions/{_DELETE_DIVISION_ID}"


@responses.activate
def test_delete_division_sends_delete_request(config: Config) -> None:
    """Test successful division deletion."""
    responses.add(
        responses.DELETE,
        _DELETE_ENDPOINT,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        delete_division(session, _SEASON_ID, _DELETE_DIVISION_ID)
    # Verify the request
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.method == "DELETE"
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_delete_division_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.DELETE,
        _DELETE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            delete_division(session, _SEASON_ID, _DELETE_DIVISION_ID)


@responses.activate
def test_delete_division_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.DELETE, _DELETE_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            delete_division(session, _SEASON_ID, _DELETE_DIVISION_ID)


@responses.activate
def test_delete_division_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.DELETE, _DELETE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            delete_division(session, _SEASON_ID, _DELETE_DIVISION_ID)
