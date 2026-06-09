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
    create_division,
    list_division_teams,
    list_divisions,
    update_division,
)
from gamesheet_sdk.divisions import Division
from gamesheet_sdk.teams import Team

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


@responses.activate
def test_list_divisions_includes_team_counts_when_requested(config: Config) -> None:
    """Verify that team counts are fetched and populated when include_team_counts=True."""
    # Mock the divisions list response
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
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
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
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                    },
                },
            ],
        ),
        status=200,
    )
    # Mock the teams responses for each division
    responses.add(
        responses.GET,
        f"{_BASE}/api/divisions/701/teams",
        json=_payload(
            [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Team A",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": "701"}},
                    },
                },
                {
                    "type": "teams",
                    "id": "1002",
                    "attributes": {
                        "title": "Team B",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": "701"}},
                    },
                },
                {
                    "type": "teams",
                    "id": "1003",
                    "attributes": {
                        "title": "Team C",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": "701"}},
                    },
                },
            ],
        ),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_BASE}/api/divisions/702/teams",
        json=_payload(
            [
                {
                    "type": "teams",
                    "id": "2001",
                    "attributes": {
                        "title": "Team D",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                        "division": {"data": {"type": "divisions", "id": "702"}},
                    },
                },
            ],
        ),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_divisions(session, _SEASON_ID, include_team_counts=True)

    assert len(result) == 2
    assert result[0].id == "701"
    assert result[0].team_count == 3
    assert result[1].id == "702"
    assert result[1].team_count == 1


@responses.activate
def test_list_divisions_without_team_counts_leaves_field_none(config: Config) -> None:
    """Verify that team_count is None when include_team_counts=False."""
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
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_divisions(session, _SEASON_ID, include_team_counts=False)
    assert len(result) == 1
    assert result[0].team_count is None


_DIVISION_ID = "701"
_DIVISION_TEAMS_ENDPOINT = f"{_BASE}/api/divisions/{_DIVISION_ID}/teams"


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
                        "logo": "https://example.com/logo1.png",
                        "invitation_code": "ABC123",
                        "player_count": 15,
                        "coach_count": 3,
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
                        "logo": None,
                        "invitation_code": "XYZ789",
                        "player_count": 12,
                        "coach_count": 2,
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
    assert result[0].invitation_code == "ABC123"
    assert result[0].player_count == 15
    assert result[0].coach_count == 3
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "Durham Bulls"
    assert result[1].logo is None


@responses.activate
def test_list_division_teams_sends_bearer_and_jsonapi_accept(config: Config) -> None:

    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_division_teams(session, _DIVISION_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_division_teams_empty_data_returns_empty_list(config: Config) -> None:

    responses.add(responses.GET, _DIVISION_TEAMS_ENDPOINT, json=_payload([]), status=200)
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
            match=r"Division '.*' not found.*valid division ID.*divisions list --season-id",
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


def test_team_model_accepts_optional_fields() -> None:

    t = Team(
        id="1001",
        season_id="15020",
        title="Raleigh Raptors",
        division_id="701",
        logo="https://example.com/logo.png",
        invitation_code="ABC123",
        player_count=15,
        coach_count=3,
        created_at=cast("datetime", "2024-01-01T00:00:00Z"),
        updated_at=cast("datetime", "2024-01-01T00:00:00Z"),
    )
    assert t.title == "Raleigh Raptors"
    assert t.logo == "https://example.com/logo.png"
    assert t.player_count == 15


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


_UPDATE_ENDPOINT = f"{_BASE}/api/divisions/{_DIVISION_ID}"


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
        result = update_division(session, _DIVISION_ID, title="Updated Division")
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

    payload = json.loads(req.body)
    assert payload["data"]["type"] == "divisions"
    assert payload["data"]["id"] == _DIVISION_ID
    assert payload["data"]["attributes"]["title"] == "Updated Division"
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_update_division_updates_external_id(config: Config) -> None:

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
        result = update_division(session, _DIVISION_ID, external_id="new-external-id")
    assert result.id == _DIVISION_ID
    assert result.external_id == "new-external-id"

    # Verify only external_id was sent
    import json

    payload = json.loads(responses.calls[0].request.body)
    assert "title" not in payload["data"]["attributes"]
    assert payload["data"]["attributes"]["external_id"] == "new-external-id"


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
        result = update_division(session, _DIVISION_ID, title="New Title", external_id="new-id")
    assert result.title == "New Title"
    assert result.external_id == "new-id"


def test_update_division_raises_value_error_if_no_fields_provided(config: Config) -> None:

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(ValueError, match="At least one of title or external_id must be provided"):
            update_division(session, _DIVISION_ID)


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
            update_division(session, _DIVISION_ID, title="Test")


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
            update_division(session, _DIVISION_ID, title="Test")


@responses.activate
def test_update_division_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_division(session, _DIVISION_ID, title="Test")
