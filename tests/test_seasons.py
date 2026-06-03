"""Tests for :mod:`gamesheet_sdk.seasons`."""

# pylint: disable=redefined-outer-name,protected-access

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
    list_seasons,
)
from gamesheet_sdk.seasons import Season

_BASE = "https://test.example"
_LEAGUE_ID = "1148580"
_ENDPOINT = f"{_BASE}/api/seasons"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_seasons_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "seasons",
                    "id": "501",
                    "attributes": {
                        "title": "2024-2025",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "league": {
                            "data": {
                                "type": "leagues",
                                "id": _LEAGUE_ID,
                            },
                        },
                    },
                },
                {
                    "type": "seasons",
                    "id": "502",
                    "attributes": {
                        "title": "2023-2024",
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "league": {
                            "data": {
                                "type": "leagues",
                                "id": _LEAGUE_ID,
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
        result = list_seasons(session, _LEAGUE_ID)

    assert [s.id for s in result] == ["501", "502"]
    assert result[0].title == "2024-2025"
    assert result[0].league_id == _LEAGUE_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "2023-2024"


@responses.activate
def test_list_seasons_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_seasons(session, _LEAGUE_ID)

    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_seasons_empty_data_returns_empty_list(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_seasons(session, _LEAGUE_ID)


@responses.activate
def test_list_seasons_401_raises_authentication_error(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_seasons(session, _LEAGUE_ID)


@responses.activate
def test_list_seasons_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_seasons(session, _LEAGUE_ID)


def test_season_model_ignores_unknown_attributes() -> None:
    s = Season(
        id="501",
        league_id="1148580",
        title="2024-2025",
        created_at=cast("datetime", "2024-01-01T00:00:00Z"),
        updated_at=cast("datetime", "2024-01-01T00:00:00Z"),
        unexpected_future_attr="ignored",  # type: ignore[call-arg]
    )
    assert s.title == "2024-2025"


@responses.activate
def test_list_seasons_filters_by_league_id(config: Config) -> None:
    """Verify that seasons are filtered to only include the requested league."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "seasons",
                    "id": "501",
                    "attributes": {
                        "title": "League 1148580 Season",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "league": {"data": {"type": "leagues", "id": "1148580"}},
                    },
                },
                {
                    "type": "seasons",
                    "id": "502",
                    "attributes": {
                        "title": "Other League Season",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "league": {"data": {"type": "leagues", "id": "999"}},
                    },
                },
            ],
        ),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, "1148580")

    # Should only return the season for league 1148580, not the one for league 999
    assert len(result) == 1
    assert result[0].id == "501"
    assert result[0].league_id == "1148580"
    assert result[0].title == "League 1148580 Season"
