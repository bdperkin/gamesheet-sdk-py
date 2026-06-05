"""Tests for :mod:`gamesheet_sdk.referees`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
)
from gamesheet_sdk.referees import Referee, list_referees

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_referees_parses_jsonapi_response(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "referees",
                    "id": "101",
                    "attributes": {
                        "first_name": "John",
                        "last_name": "Smith",
                        "email": "john.smith@example.com",
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
                    },
                },
                {
                    "type": "referees",
                    "id": "102",
                    "attributes": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "email": None,
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
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
        result = list_referees(session, _SEASON_ID)
    assert [r.id for r in result] == ["101", "102"]
    assert result[0].first_name == "John"
    assert result[0].last_name == "Smith"
    assert result[0].email == "john.smith@example.com"
    assert result[0].season_id == _SEASON_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].first_name == "Jane"
    assert result[1].last_name == "Doe"
    assert result[1].email is None


@responses.activate
def test_list_referees_sends_bearer_and_jsonapi_accept(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_referees_empty_data_returns_empty_list(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_referees(session, _SEASON_ID)


def test_referee_model_ignores_unknown_attributes() -> None:

    r = Referee(
        id="101",
        season_id="15020",
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        created_at=cast("datetime", "2024-01-01T00:00:00Z"),
        updated_at=cast("datetime", "2024-01-01T00:00:00Z"),
        unexpected_future_attr="ignored",
    )
    assert r.first_name == "John"
    assert r.last_name == "Smith"


def test_referee_model_handles_optional_email() -> None:

    r = Referee(
        id="102",
        season_id="15020",
        first_name="Jane",
        last_name="Doe",
        email=None,
        created_at=cast("datetime", "2024-01-01T00:00:00Z"),
        updated_at=cast("datetime", "2024-01-01T00:00:00Z"),
    )
    assert r.email is None


@responses.activate
def test_list_referees_uses_correct_endpoint(config: Config) -> None:
    """Verify that referees endpoint includes season_id in the path."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "referees",
                    "id": "101",
                    "attributes": {
                        "first_name": "John",
                        "last_name": "Smith",
                        "email": "john.smith@example.com",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": "15020"}},
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_referees(session, "15020")
    # API filters by season_id in URL path, so all results are for that season
    assert len(result) == 1
    assert result[0].id == "101"
    assert result[0].season_id == "15020"
    assert result[0].first_name == "John"
    assert result[0].last_name == "Smith"
