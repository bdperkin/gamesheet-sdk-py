"""Tests for create_referee function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import create_referee

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


@responses.activate
def test_create_referee_sends_correct_payload_with_all_fields(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146197",
                "attributes": {
                    "external_id": "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
                    "first_name": "Wes",
                    "last_name": "McCauley",
                    "email_address": "Wes.McCauley@example.com",
                    "created_at": "2026-06-15T12:04:05.0325Z",
                    "updated_at": "2026-06-15T12:04:05.0325Z",
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
        result = create_referee(
            session,
            _SEASON_ID,
            "Wes",
            "McCauley",
            email_address="Wes.McCauley@example.com",
            external_id="0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
        )
    assert result.id == "1146197"
    assert result.first_name == "Wes"
    assert result.last_name == "McCauley"
    assert result.email == "Wes.McCauley@example.com"
    assert result.season_id == _SEASON_ID

    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    import json

    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Wes"
    assert payload["data"]["attributes"]["last_name"] == "McCauley"
    assert payload["data"]["attributes"]["email_address"] == "Wes.McCauley@example.com"
    assert payload["data"]["attributes"]["external_id"] == "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A"


@responses.activate
def test_create_referee_sends_correct_payload_required_fields_only(
    config: Config,
) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146198",
                "attributes": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email_address": None,
                    "created_at": "2026-06-15T13:00:00Z",
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
        result = create_referee(session, _SEASON_ID, "Jane", "Doe")
    assert result.id == "1146198"
    assert result.first_name == "Jane"
    assert result.last_name == "Doe"
    assert result.email is None

    # Verify the request payload
    import json

    req = responses.calls[0].request
    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Jane"
    assert payload["data"]["attributes"]["last_name"] == "Doe"
    assert "email_address" not in payload["data"]["attributes"]
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_create_referee_sends_bearer_and_jsonapi_headers(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "101",
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
        create_referee(session, _SEASON_ID, "Test", "Ref")
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"
    assert req.headers["Content-Type"] == "application/vnd.api+json"


@responses.activate
def test_create_referee_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            create_referee(session, _SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.POST, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            create_referee(session, _SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:

    responses.add(responses.POST, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            create_referee(session, _SEASON_ID, "Test", "Ref")
