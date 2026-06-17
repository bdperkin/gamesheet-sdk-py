"""Tests for update_division function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    update_division,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_DIVISION_ID = "80998"
_UPDATE_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/divisions/{_DIVISION_ID}"


@responses.activate
def test_update_division_updates_title(config: Config) -> None:
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Updated Division",
                    "external_id": "existing-external-id",
                    "settings": {},
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            _SEASON_ID,
            _DIVISION_ID,
            title="Updated Division",
        )
    assert result.id == _DIVISION_ID
    assert result.title == "Updated Division"
    assert result.season_id == _SEASON_ID
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
    assert payload["data"]["id"] == _DIVISION_ID
    assert payload["data"]["attributes"]["title"] == "Updated Division"
    assert payload["data"]["attributes"]["settings"] == {}
    assert payload["data"]["relationships"]["season"]["data"]["id"] == _SEASON_ID
    assert payload["data"]["relationships"]["season"]["data"]["type"] == "seasons"
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_update_division_updates_external_id(config: Config) -> None:
    # When updating only external_id, function fetches current title first
    responses.add(
        responses.GET,
        f"{_BASE}/api/divisions/{_DIVISION_ID}",
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Existing Title",
                    "external_id": "old-external-id",
                    "settings": {},
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
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "Existing Title",
                    "external_id": "new-external-id",
                    "settings": {},
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            _SEASON_ID,
            _DIVISION_ID,
            external_id="new-external-id",
        )
    assert result.id == _DIVISION_ID
    assert result.external_id == "new-external-id"
    # Verify title was fetched and included in PATCH (required by API)
    import json

    assert len(responses.calls) == 2
    # First call: GET to fetch current title
    assert responses.calls[0].request.method == "GET"
    # Second call: PATCH with existing title + new external_id
    assert responses.calls[1].request.body is not None
    patch_payload = json.loads(responses.calls[1].request.body)
    assert patch_payload["data"]["attributes"]["title"] == "Existing Title"
    assert patch_payload["data"]["attributes"]["external_id"] == "new-external-id"
    assert patch_payload["data"]["attributes"]["settings"] == {}
    assert patch_payload["data"]["relationships"]["season"]["data"]["id"] == _SEASON_ID


@responses.activate
def test_update_division_updates_both_fields(config: Config) -> None:
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "data": {
                "type": "divisions",
                "id": _DIVISION_ID,
                "attributes": {
                    "title": "New Title",
                    "external_id": "new-id",
                    "settings": {},
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2026-06-09T20:00:00Z",
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
        result = update_division(
            session,
            _SEASON_ID,
            _DIVISION_ID,
            title="New Title",
            external_id="new-id",
        )
    assert result.title == "New Title"
    assert result.external_id == "new-id"


def test_update_division_raises_value_error_if_no_fields_provided(
    config: Config,
) -> None:
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            ValueError,
            match="At least one of title or external_id must be provided",
        ):
            update_division(session, _SEASON_ID, _DIVISION_ID)


@responses.activate
def test_update_division_401_raises_authentication_error(config: Config) -> None:
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_division(session, _SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Division '.*' not found.*valid division ID.*divisions list --season-id",
        ):
            update_division(session, _SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_division(session, _SEASON_ID, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_handles_failed_title_fetch(config: Config) -> None:
    """When updating only external_id and GET fails, PATCH proceeds with empty title."""
    # GET fails with 404
    responses.add(
        responses.GET,
        f"{_BASE}/api/divisions/{_DIVISION_ID}",
        status=404,
    )
    # PATCH will fail due to missing title, which is expected
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={
            "errors": [
                {
                    "title": "is required",
                    "source": {"pointer": "/data/attributes/title"},
                },
            ],
        },
        status=400,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 400"):
            update_division(session, _SEASON_ID, _DIVISION_ID, external_id="new-id")
