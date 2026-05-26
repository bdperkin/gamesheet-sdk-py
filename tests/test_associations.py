"""Tests for :mod:`gamesheet_sdk.associations`."""

# pylint: disable=redefined-outer-name,protected-access

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_associations,
)
from gamesheet_sdk.associations import Association

_BASE = "https://test.example"
_ENDPOINT = f"{_BASE}/api/associations"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_associations_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "associations",
                    "id": "11",
                    "attributes": {
                        "title": "Hockey Time Productions",
                        "logo": "",
                        "created_at": "2023-05-01T20:29:09.30692Z",
                        "updated_at": "2023-05-01T20:29:09.30692Z",
                    },
                },
                {
                    "type": "associations",
                    "id": "40",
                    "attributes": {
                        "title": "SuperSeries AAA",
                        "logo": "https://example/logo.png",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-06-15T12:00:00Z",
                    },
                },
            ]
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_associations(session)

    assert [a.id for a in result] == ["11", "40"]
    assert result[0].title == "Hockey Time Productions"
    assert result[0].logo == ""
    assert result[0].created_at == datetime(2023, 5, 1, 20, 29, 9, 306_920, tzinfo=timezone.utc)
    assert result[1].logo == "https://example/logo.png"


@responses.activate
def test_list_associations_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_associations(session)

    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_associations_empty_data_returns_empty_list(config: Config) -> None:
    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert list_associations(session) == []


@responses.activate
def test_list_associations_401_raises_authentication_error(config: Config) -> None:
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_associations(session)


@responses.activate
def test_list_associations_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_associations(session)


def test_association_model_ignores_unknown_attributes() -> None:
    a = Association(
        id="11",
        title="X",
        logo="",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
        unexpected_future_attr="ignored",
    )
    assert a.title == "X"
