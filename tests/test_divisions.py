"""Tests for :mod:`gamesheet_sdk.divisions`."""

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
    list_divisions,
)
from gamesheet_sdk.divisions import Division

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/divisions"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_divisions_parses_jsonapi_response(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "divisions",
                    "id": "701",
                    "attributes": {
                        "title": "U13 AAA",
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
                    "type": "divisions",
                    "id": "702",
                    "attributes": {
                        "title": "Bantam A",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
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
        result = list_divisions(session, _SEASON_ID)
    assert [d.id for d in result] == ["701", "702"]
    assert result[0].title == "U13 AAA"
    assert result[0].season_id == _SEASON_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "Bantam A"


@responses.activate
def test_list_divisions_sends_bearer_and_jsonapi_accept(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_divisions(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_divisions_empty_data_returns_empty_list(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_divisions(session, _SEASON_ID)


@responses.activate
def test_list_divisions_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_divisions(session, _SEASON_ID)


@responses.activate
def test_list_divisions_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            list_divisions(session, _SEASON_ID)


@responses.activate
def test_list_divisions_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_divisions(session, _SEASON_ID)


def test_division_model_ignores_unknown_attributes() -> None:

    d = Division(
        id="701",
        season_id="15020",
        title="U13 AAA",
        created_at=cast("datetime", "2024-01-01T00:00:00Z"),
        updated_at=cast("datetime", "2024-01-01T00:00:00Z"),
        unexpected_future_attr="ignored",
    )
    assert d.title == "U13 AAA"


@responses.activate
def test_list_divisions_filters_by_season_id(config: Config) -> None:
    """Verify that divisions are filtered to only include the requested season."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "divisions",
                    "id": "701",
                    "attributes": {
                        "title": "Season 15020 Division",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": "15020"}},
                    },
                },
                {
                    "type": "divisions",
                    "id": "702",
                    "attributes": {
                        "title": "Other Season Division",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": "999"}},
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_divisions(session, "15020")
    # Should only return the division for season 15020, not the one for season 999
    assert len(result) == 1
    assert result[0].id == "701"
    assert result[0].season_id == "15020"
    assert result[0].title == "Season 15020 Division"
