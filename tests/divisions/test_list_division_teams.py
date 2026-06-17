"""Tests for list_division_teams function."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_division_teams,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_DIVISION_ID = "701"
_DIVISION_TEAMS_ENDPOINT = f"{_BASE}/api/divisions/{_DIVISION_ID}/teams"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_division_teams_parses_jsonapi_response(config: Config) -> None:
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=_payload(
            [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Raleigh Raptors",
                        "logo_url": "https://example.com/logo1.png",
                        "roster": {
                            "players": [{"id": str(i)} for i in range(15)],
                            "coaches": [{"id": str(i)} for i in range(3)],
                        },
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
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": _DIVISION_ID,
                            },
                        },
                    },
                },
                {
                    "type": "teams",
                    "id": "1002",
                    "attributes": {
                        "title": "Durham Bulls",
                        "roster": {
                            "players": [{"id": str(i)} for i in range(12)],
                            "coaches": [{"id": str(i)} for i in range(2)],
                        },
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
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": _DIVISION_ID,
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
        result = list_division_teams(session, _DIVISION_ID)
    assert [t.id for t in result] == ["1001", "1002"]
    assert result[0].title == "Raleigh Raptors"
    assert result[0].season_id == _SEASON_ID
    assert result[0].division_id == _DIVISION_ID
    assert result[0].logo == "https://example.com/logo1.png"
    assert result[0].invitation_code is None  # No invitations in this response
    assert result[0].player_count == 15
    assert result[0].coach_count == 3
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "Durham Bulls"
    assert result[1].logo is None


@responses.activate
def test_list_division_teams_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_division_teams(session, _DIVISION_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_division_teams_empty_data_returns_empty_list(config: Config) -> None:
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json=_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_401_raises_authentication_error(config: Config) -> None:
    responses.add(
        responses.GET,
        _DIVISION_TEAMS_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Resource not found \(HTTP 404\)",
        ):
            list_division_teams(session, _DIVISION_ID)


@responses.activate
def test_list_division_teams_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_division_teams(session, _DIVISION_ID)
