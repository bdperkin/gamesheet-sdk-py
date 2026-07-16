# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for :mod:`gamesheet_sdk.admin.teams`."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    list_teams,
)
from gamesheet_sdk.admin.teams import Team
from tests.helpers import (
    JSONAPI_CONTENT_TYPE,
    SEASON_ID,
    TEST_BASE_URL,
    TIMESTAMP_2024_09_01,
    jsonapi_payload,
)

_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams"


@responses.activate
def test_list_teams_parses_jsonapi_response(config: Config) -> None:
    """Test that list_teams correctly parses JSON:API response format."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Raleigh Raptors",
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": SEASON_ID,
                            },
                        },
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": "5001",
                            },
                        },
                    },
                },
                {
                    "type": "teams",
                    "id": "1002",
                    "attributes": {
                        "title": "Durham Bulls",
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": SEASON_ID,
                            },
                        },
                        "division": {
                            "data": None,
                        },
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_teams(session, SEASON_ID)
    assert [t.id for t in result] == ["1001", "1002"]
    assert result[0].title == "Raleigh Raptors"
    assert result[0].season_id == SEASON_ID
    assert result[0].division_id == "5001"
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].title == "Durham Bulls"
    assert result[1].division_id is None


@responses.activate
def test_list_teams_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    """Test that list_teams sends correct headers and query parameters."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_teams(session, SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == JSONAPI_CONTENT_TYPE
    # Verify sparse fieldset is requested to get logo_url and roster
    # URL-encoded: fields[teams] = fields%5Bteams%5D, include = invitations
    url = req.url or ""
    assert "fields%5Bteams%5D" in url
    assert "logo_url" in url
    assert "roster" in url
    assert "include=invitations" in url


@responses.activate
def test_list_teams_empty_data_returns_empty_list(config: Config) -> None:
    """Test that list_teams returns empty list when API returns no teams."""
    responses.add(responses.GET, _ENDPOINT, json=jsonapi_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_teams(session, SEASON_ID)


@responses.activate
def test_list_teams_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_teams(session, SEASON_ID)


@responses.activate
def test_list_teams_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            list_teams(session, SEASON_ID)


@responses.activate
def test_list_teams_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_teams(session, SEASON_ID)


def test_team_model_handles_optional_division_id() -> None:
    """Test that Team model correctly handles optional division_id field."""
    t = Team(
        id="1002",
        season_id=SEASON_ID,
        title="Durham Bulls",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert t.title == "Durham Bulls"
    assert t.division_id is None


@responses.activate
def test_list_teams_includes_optional_fields(config: Config) -> None:
    """Verify that optional fields (logo_url, roster counts, invitation) are parsed when present."""
    from tests.helpers.payloads import invitation_relationship_and_included

    invitation_rel, invitation_inc = invitation_relationship_and_included()
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Raleigh Raptors",
                        "logo_url": "https://example.com/logo.png",
                        "roster": {
                            "players": [
                                {"id": "1", "number": "1"},
                                {"id": "2", "number": "2"},
                                {"id": "3", "number": "3"},
                            ],
                            "coaches": [
                                {"id": "10", "position": "head_coach"},
                                {"id": "11", "position": "assistant_coach"},
                            ],
                        },
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": SEASON_ID,
                            },
                        },
                        "division": {
                            "data": {
                                "type": "divisions",
                                "id": "5001",
                            },
                        },
                    }
                    | invitation_rel,
                },
            ],
            "included": invitation_inc,
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        result = list_teams(session, SEASON_ID)
    assert len(result) == 1
    team = result[0]
    assert team.logo == "https://example.com/logo.png"
    assert team.invitation_code == "RAPTORS2024"
    assert team.player_count == 3
    assert team.coach_count == 2


@responses.activate
def test_list_teams_without_invitations(config: Config) -> None:
    """Verify teams without invitation relationship have None invitation_code."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Team Without Invitation",
                        "logo_url": "https://example.com/logo.png",
                        "roster": {
                            "players": [{"id": "1"}],
                            "coaches": [{"id": "10"}],
                        },
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {
                            "data": {"type": "seasons", "id": SEASON_ID},
                        },
                        "division": {"data": None},
                        # No invitations relationship
                    },
                },
            ],
            # No included section
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        result = list_teams(session, SEASON_ID)
    assert len(result) == 1
    assert result[0].invitation_code is None


@responses.activate
def test_list_teams_with_invitation_as_single_object(config: Config) -> None:
    """Verify invitation relationship as single object (not array) is handled."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Team",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                        "division": {"data": None},
                        "invitations": {
                            "data": {"type": "invitations", "id": "inv-456"},
                        },
                    },
                },
            ],
            "included": [
                {
                    "type": "invitations",
                    "id": "inv-456",
                    "attributes": {"code": "SINGLE2024"},
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        result = list_teams(session, SEASON_ID)
    assert len(result) == 1
    assert result[0].invitation_code == "SINGLE2024"


@responses.activate
def test_list_teams_with_malformed_invitation_data(config: Config) -> None:
    """Verify malformed invitation data is ignored gracefully."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json={
            "data": [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Team with orphan invitation",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                        "division": {"data": None},
                        "invitations": {
                            # Invitation ID not in included - orphaned reference
                            "data": [{"type": "invitations", "id": "inv-orphan"}],
                        },
                    },
                },
                {
                    "type": "teams",
                    "id": "1002",
                    "attributes": {
                        "title": "Team with empty invitation ID",
                        "roster": {"players": [], "coaches": []},
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                        "division": {"data": None},
                        "invitations": {
                            # Empty/null ID
                            "data": [{"type": "invitations", "id": ""}],
                        },
                    },
                },
            ],
            "included": [
                # Invitation missing ID (skipped in loop)
                {"type": "invitations", "attributes": {"code": "NOCODE"}},
                # Invitation missing code (skipped in loop)
                {"type": "invitations", "id": "inv-nocode"},
                # Non-invitation type (skipped by type check)
                {"type": "divisions", "id": "div-1", "attributes": {"name": "A"}},
                # Valid invitation but not referenced by any team
                {
                    "type": "invitations",
                    "id": "inv-unused",
                    "attributes": {"code": "UNUSED"},
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        result = list_teams(session, SEASON_ID)
    assert len(result) == 2
    # No valid invitation matched for either team
    assert result[0].invitation_code is None
    assert result[1].invitation_code is None


@responses.activate
def test_list_teams_uses_correct_endpoint(config: Config) -> None:
    """Verify that teams endpoint includes season_id in the path."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=jsonapi_payload(
            [
                {
                    "type": "teams",
                    "id": "1001",
                    "attributes": {
                        "title": "Season 15020 Team",
                        "created_at": TIMESTAMP_2024_09_01,
                        "updated_at": TIMESTAMP_2024_09_01,
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": SEASON_ID}},
                        "division": {"data": None},
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_teams(session, SEASON_ID)
    # API filters by season_id in URL path, so all results are for that season
    assert len(result) == 1
    assert result[0].id == "1001"
    assert result[0].season_id == SEASON_ID
    assert result[0].title == "Season 15020 Team"
