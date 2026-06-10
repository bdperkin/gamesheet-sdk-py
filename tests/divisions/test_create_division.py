"""Tests for create_division function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    create_division,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_CREATE_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/divisions"


@responses.activate
def test_create_division_sends_correct_payload(config: Config) -> None:

    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": "80997",
                "attributes": {
                    "external_id": "test-external-id",
                    "title": "Test Division",
                    "settings": {},
                    "created_at": "2026-06-09T19:39:56.219694Z",
                    "updated_at": "2026-06-09T19:39:56.219694Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_division(session, _SEASON_ID, "Test Division", external_id="test-external-id")
    assert result.id == "80997"
    assert result.title == "Test Division"
    assert result.season_id == _SEASON_ID
    assert result.external_id == "test-external-id"

    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"
    assert req.headers["Content-Type"] == "application/vnd.api+json"
    import json

    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["type"] == "divisions"
    assert payload["data"]["attributes"]["title"] == "Test Division"
    assert payload["data"]["attributes"]["external_id"] == "test-external-id"
    assert payload["data"]["relationships"]["season"]["data"]["id"] == _SEASON_ID


@responses.activate
def test_create_division_generates_uuid_if_external_id_not_provided(config: Config) -> None:

    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": "80998",
                "attributes": {
                    "external_id": "generated-uuid",
                    "title": "Test Division 2",
                    "settings": {},
                    "created_at": "2026-06-09T19:39:56.219694Z",
                    "updated_at": "2026-06-09T19:39:56.219694Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_division(session, _SEASON_ID, "Test Division 2")
    assert result.id == "80998"
    assert result.title == "Test Division 2"

    # Verify a UUID was generated
    import json

    assert responses.calls[0].request.body is not None
    payload = json.loads(responses.calls[0].request.body)
    external_id = payload["data"]["attributes"]["external_id"]
    assert external_id is not None
    assert len(external_id) > 0
    # Basic UUID format check
    import uuid

    try:
        uuid.UUID(external_id)
    except ValueError:
        pytest.fail(f"Generated external_id '{external_id}' is not a valid UUID")


@responses.activate
def test_create_division_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            create_division(session, _SEASON_ID, "Test Division")


@responses.activate
def test_create_division_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.POST, _CREATE_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            create_division(session, _SEASON_ID, "Test Division")


@responses.activate
def test_create_division_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.POST, _CREATE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            create_division(session, _SEASON_ID, "Test Division")
