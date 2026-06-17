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
from gamesheet_sdk.ipad_keys import IPadKey

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/api-keys"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_ipad_keys_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
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
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
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
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_ipad_keys(session, _SEASON_ID)


@responses.activate
def test_list_ipad_keys_401_raises_authentication_error(config: Config) -> None:
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
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_ipad_keys(session, _SEASON_ID)


def test_ipad_key_model_ignores_unknown_attributes() -> None:
    key = IPadKey(
        id="3567",
        value="ipad-test-key",
        description="Test Key",
        roles=[],
        live_scoring_scopes=["read"],
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert key.value == "ipad-test-key"
