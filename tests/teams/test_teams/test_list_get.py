# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for listing and fetching teams."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.teams import (
    TeamDetail,
    TeamSummary,
    _find_team,
    _parse_team_summary,
    fetch_team_raw,
    fetch_teams_raw,
    get_team,
    list_teams,
)
from tests.teams.test_teams.conftest import (
    REFRESH_URL,
    TEAMS_URL,
    make_session,
    sample_teams_data,
)


@responses.activate
def test_list_teams_parses_response() -> None:
    """Test that list_teams returns parsed TeamSummary objects."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"success": True, "teams": sample_teams_data()},
        status=200,
    )

    session = make_session()
    result = list_teams(session, timeout=1.0)

    assert len(result) == 2
    assert isinstance(result[0], TeamSummary)
    assert result[0].memberId == "m-001"
    assert result[0].teamId == "t-101"
    assert result[0].relationship == "coach"
    assert result[0].status == "active"
    assert result[0].onboardingCompletedAt == "2024-09-01T10:00:00Z"
    assert result[0].teamName == "Hawks 12U"
    assert result[0].ageCategory == "12U"
    assert result[0].clubId == "c-501"
    assert result[0].joinedAt == "2024-08-15T09:00:00Z"
    assert result[0].statsYear == "2024-2025"

    assert result[1].memberId == "m-002"
    assert result[1].teamId == "t-102"
    assert result[1].teamName == "Eagles 14U"


@responses.activate
def test_list_teams_empty() -> None:
    """Test list_teams with empty array in response."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": []},
        status=200,
    )

    session = make_session()
    result = list_teams(session, timeout=1.0)
    assert result == []


@responses.activate
def test_fetch_teams_raw_data_envelope_dict() -> None:
    """Test fetch_teams_raw when API wraps in data.teams dictionary."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"data": {"teams": sample_teams_data()}},
        status=200,
    )

    session = make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2
    assert result[0]["teamName"] == "Hawks 12U"


@responses.activate
def test_fetch_teams_raw_data_envelope_list() -> None:
    """Test fetch_teams_raw when API returns data as a list."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"data": sample_teams_data()},
        status=200,
    )

    session = make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2


@responses.activate
def test_fetch_teams_raw_direct_list() -> None:
    """Test fetch_teams_raw when API returns a top-level list."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json=sample_teams_data(),
        status=200,
    )

    session = make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2


@responses.activate
def test_fetch_teams_raw_unexpected_shape() -> None:
    """Test fetch_teams_raw when API returns an unrecognized structure."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"unknown_key": "some_value"},
        status=200,
    )

    session = make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert result == []


@responses.activate
def test_fetch_teams_raw_non_dict_non_list_body() -> None:
    """Test fetch_teams_raw when response JSON is neither dict nor list."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json=123,
        status=200,
    )

    session = make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert result == []


@responses.activate
def test_get_team_no_id_or_team_id() -> None:
    """Test get_team when neither teamId nor id are in the team dict."""
    raw_data = [
        {
            "teamName": "Nameless Team",
            "status": "inactive",
        },
    ]
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = make_session()
    detail = get_team(session, "", timeout=1.0)
    assert detail.teamName == "Nameless Team"
    assert detail.teamId is None


@responses.activate
def test_get_team_with_integer_member_id_and_null_club_id() -> None:
    """Test get_team when memberId is int and clubId is None (matching live API behavior)."""
    raw_data = [
        {
            "teamId": "eb20a094-5c3c-47bc-918f-c8f69cfe0719",
            "teamName": "Warriors 14U",
            "memberId": 134466,
            "clubId": None,
            "statsYear": 2024,
            "status": "active",
            "relationship": "coach",
            "ageCategory": "14U",
            "joinedAt": None,
            "onboardingCompletedAt": None,
        },
    ]
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = make_session()
    detail = get_team(session, "eb20a094-5c3c-47bc-918f-c8f69cfe0719", timeout=1.0)
    assert detail.teamId == "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    assert detail.memberId == 134466
    assert detail.clubId is None
    assert detail.statsYear == 2024
    assert detail.teamName == "Warriors 14U"


@responses.activate
def test_fetch_teams_raw_unauthorized() -> None:
    """Test that 401 raises AuthenticationError."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_teams_raw(session, timeout=1.0)


@responses.activate
def test_fetch_teams_raw_server_error() -> None:
    """Test that 500 raises GameSheetError."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        body="Internal Server Error",
        status=500,
    )

    session = make_session()
    with pytest.raises(GameSheetError, match="HTTP 500"):
        fetch_teams_raw(session, timeout=1.0)


@responses.activate
def test_get_team_success() -> None:
    """Test get_team returns detailed TeamDetail model."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": sample_teams_data()},
        status=200,
    )

    session = make_session()
    detail = get_team(session, "t-101", timeout=1.0)

    assert isinstance(detail, TeamDetail)
    assert detail.teamId == "t-101"
    assert detail.teamName == "Hawks 12U"
    assert detail.relationship == "coach"
    assert detail.status == "active"
    assert detail.onboardingCompletedAt == "2024-09-01T10:00:00Z"
    assert detail.memberId == "m-001"
    assert detail.clubId == "c-501"
    assert detail.ageCategory == "12U"
    assert detail.statsYear == "2024-2025"
    assert detail.joinedAt == "2024-08-15T09:00:00Z"


@responses.activate
def test_get_team_fallback_id_field() -> None:
    """Test get_team fallback when only 'id' is present in raw dictionary."""
    raw_data = [
        {
            "id": 999,
            "title": "Fallback Team",
            "status": "active",
        },
    ]
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = make_session()
    detail = get_team(session, "999", timeout=1.0)

    assert detail.teamId == "999"


@responses.activate
def test_get_team_not_found() -> None:
    """Test get_team raises GameSheetError when ID does not exist."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"teams": sample_teams_data()},
        status=200,
    )

    session = make_session()
    with pytest.raises(GameSheetError, match=r"Team 't-999' not found\."):
        get_team(session, "t-999", timeout=1.0)


@responses.activate
def test_get_team_401() -> None:
    """Test get_team 401 error propagates AuthenticationError."""
    responses.add(
        responses.GET,
        TEAMS_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = make_session()
    with pytest.raises(AuthenticationError):
        get_team(session, "t-101", timeout=1.0)


def test_parse_team_summary_empty_and_null_values() -> None:
    """Test _parse_team_summary with empty dictionary and null fields."""
    raw: dict[str, Any] = {
        "memberId": None,
        "teamId": None,
        "relationship": None,
        "status": None,
        "onboardingCompletedAt": None,
        "teamName": None,
        "ageCategory": None,
        "clubId": None,
        "joinedAt": None,
        "statsYear": None,
    }
    summary = _parse_team_summary(raw)
    assert not summary.memberId
    assert not summary.teamId
    assert not summary.relationship
    assert not summary.status
    assert not summary.onboardingCompletedAt
    assert not summary.teamName
    assert not summary.ageCategory
    assert not summary.clubId
    assert not summary.joinedAt
    assert not summary.statsYear


def test_parse_team_summary_snake_case_keys() -> None:
    """Test _parse_team_summary when payload uses snake_case keys."""
    raw: dict[str, Any] = {
        "member_id": "m-123",
        "team_id": "t-456",
        "relationship": "parent",
        "status": "active",
        "onboarding_completed_at": "2024-09-01T00:00:00Z",
        "team_name": "Panthers",
        "age_category": "10U",
        "club_id": "c-789",
        "joined_at": "2024-08-01T00:00:00Z",
        "stats_year": "2024-2025",
    }
    summary = _parse_team_summary(raw)
    assert summary.memberId == "m-123"
    assert summary.teamId == "t-456"
    assert summary.teamName == "Panthers"
    assert summary.onboardingCompletedAt == "2024-09-01T00:00:00Z"
    assert summary.statsYear == "2024-2025"


def test_find_team_not_found() -> None:
    """Test _find_team raises GameSheetError if team is missing."""
    with pytest.raises(GameSheetError, match=r"Team 't-nonexistent' not found\."):
        _find_team([], "t-nonexistent")


def test_team_detail_model_defaults() -> None:
    """Test TeamDetail model instantiation with default values."""
    detail = TeamDetail()
    assert detail.teamId is None
    assert detail.teamName is None
    assert detail.status is None
    assert detail.relationship is None
    assert detail.memberId is None
    assert detail.clubId is None
    assert detail.ageCategory is None
    assert detail.statsYear is None
    assert detail.joinedAt is None
    assert detail.onboardingCompletedAt is None
    assert detail.teamLogo is None
    assert detail.skill is None
    assert detail.province is None
    assert detail.isArchived is None
    assert detail.seasonTeamsUpdated is None


@responses.activate
def test_fetch_team_raw_single_endpoint_success() -> None:
    """Test fetch_team_raw retrieves team directly from GET /api/teams/{id}."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"team": {"teamId": "t-101", "teamName": "Hawks 12U"}},
        status=200,
    )
    session = make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"
    assert result["teamName"] == "Hawks 12U"


@responses.activate
def test_fetch_team_raw_data_envelope_success() -> None:
    """Test fetch_team_raw unwraps data envelope from GET /api/teams/{id}."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"data": {"teamId": "t-101", "teamName": "Hawks 12U"}},
        status=200,
    )
    session = make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"


@responses.activate
def test_fetch_team_raw_bare_dict_success() -> None:
    """Test fetch_team_raw handles bare dict from GET /api/teams/{id}."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"teamId": "t-101", "teamName": "Hawks 12U"},
        status=200,
    )
    session = make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"


@responses.activate
def test_fetch_team_raw_server_error() -> None:
    """Test fetch_team_raw raises GameSheetError on HTTP 500."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(responses.GET, url, status=500, body="Server error")
    session = make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/teams/t-101 returned HTTP 500"):
        fetch_team_raw(session, "t-101", timeout=1.0)


@responses.activate
def test_fetch_team_raw_unexpected_body() -> None:
    """Test fetch_team_raw raises GameSheetError when body is not a dict."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(responses.GET, url, json=123, status=200)
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Unexpected response format"):
        fetch_team_raw(session, "t-101", timeout=1.0)


@responses.activate
def test_fetch_team_raw_auth_error() -> None:
    """Test fetch_team_raw raises AuthenticationError on 401."""
    url = f"{TEAMS_URL}/t-101"
    responses.add(responses.GET, url, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        fetch_team_raw(session, "t-101", timeout=1.0)
