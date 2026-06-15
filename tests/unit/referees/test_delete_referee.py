"""Tests for delete_referee function."""

from __future__ import annotations

import json

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import delete_referee

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"



@responses.activate
def test_delete_referee_success(config: Config) -> None:
    _referee_id = "1146197"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        # Should not raise
        delete_referee(session, _SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.method == "DELETE"



@responses.activate
def test_delete_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        delete_referee(session, _SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"



@responses.activate
def test_delete_referee_401_raises_authentication_error(config: Config) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            delete_referee(session, _SEASON_ID, _referee_id)



@responses.activate
def test_delete_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    _referee_id = "nonexistent"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            delete_referee(session, _SEASON_ID, _referee_id)



@responses.activate
def test_delete_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            delete_referee(session, _SEASON_ID, _referee_id)
