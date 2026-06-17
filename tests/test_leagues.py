"""Tests for :mod:`gamesheet_sdk.leagues`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_leagues,
)
from gamesheet_sdk.leagues import League

_BASE = "https://test.example"
_ASSOCIATION_ID = "38"
_ENDPOINT = f"{_BASE}/api/associations/{_ASSOCIATION_ID}/leagues"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_leagues_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "leagues",
                    "id": "101",
                    "attributes": {
                        "title": "18U AAA",
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2024-01-15T14:30:00Z",
                    },
                },
                {
                    "type": "leagues",
                    "id": "102",
                    "attributes": {
                        "title": "16U AA",
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_leagues(session, _ASSOCIATION_ID)
    assert [lg.id for lg in result] == ["101", "102"]
    assert result[0].title == "18U AAA"
    assert result[0].association_id == _ASSOCIATION_ID
    assert result[0].created_at == datetime(2023, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 1, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "16U AA"


@responses.activate
def test_list_leagues_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_leagues(session, _ASSOCIATION_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_leagues_empty_data_returns_empty_list(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_leagues(session, _ASSOCIATION_ID)


@responses.activate
def test_list_leagues_401_raises_authentication_error(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_leagues(session, _ASSOCIATION_ID)


@responses.activate
def test_list_leagues_404_raises_helpful_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            list_leagues(session, _ASSOCIATION_ID)


@responses.activate
def test_list_leagues_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_leagues(session, _ASSOCIATION_ID)


def test_league_model_ignores_unknown_attributes() -> None:
    lg = League(
        id="101",
        association_id="38",
        title="18U AAA",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert lg.title == "18U AAA"


@responses.activate
def test_list_leagues_constructs_correct_endpoint_for_association(
    config: Config,
) -> None:
    """Verify that different association IDs result in correct endpoint paths."""
    association_id = "42"
    endpoint = f"{_BASE}/api/associations/{association_id}/leagues"
    responses.add(responses.GET, endpoint, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_leagues(session, association_id)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == endpoint
