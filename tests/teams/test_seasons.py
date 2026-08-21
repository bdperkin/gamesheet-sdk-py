# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the teams seasons domain module."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.seasons import (
    PenaltyCode,
    SeasonDetail,
    SeasonSummary,
    SeasonTeam,
    fetch_seasons_raw,
    get_season,
    get_season_penalty_codes,
    get_season_teams,
    list_seasons,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_REFRESH_PATH,
    TEAMS_SEASONS_PATH,
)

_SEASONS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_SEASONS_PATH}"
_REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"


def _make_session() -> TeamsAuthenticatedSession:
    """Create a test TeamsAuthenticatedSession.

    Returns:
        TeamsAuthenticatedSession: Test authenticated session instance.

    """
    config = Config()
    return TeamsAuthenticatedSession(
        config,
        access_token="test-access",
        refresh_token="test-refresh",
    )


def _sample_seasons_data() -> list[dict[str, Any]]:
    """Return sample seasons data list.

    Returns:
        list[dict[str, Any]]: List of sample season data dictionaries.

    """
    return [
        {
            "id": 101,
            "title": "2024-2025 Regular Season",
            "stats_year": "2024-2025",
            "leagueId": 201,
            "league": {
                "id": 201,
                "title": "Great Lakes League",
            },
            "association": {
                "id": 301,
                "title": "USA Hockey",
            },
            "sport": "hockey",
            "start_date": "2024-09-01",
            "end_date": "2025-04-30",
            "penaltyCodes": [
                {
                    "code": "TRIP",
                    "name": "Tripping",
                    "severity": "minor",
                },
                {
                    "code": "SLASH",
                    "name": "Slashing",
                    "severity": "minor",
                },
            ],
            "teams": [
                {
                    "id": 1001,
                    "title": "Hawks",
                    "division": "Varsity",
                },
                {
                    "id": 1002,
                    "title": "Eagles",
                    "division": "Varsity",
                },
            ],
        },
        {
            "id": 102,
            "title": "2023-2024 Season",
            "stats_year": "2023-2024",
            "leagueId": 202,
            "league": {
                "id": 202,
                "title": "Midwest League",
            },
            "association": None,
            "penaltyCodes": [],
            "teams": [],
        },
    ]


@responses.activate
def test_list_seasons_parses_response() -> None:
    """Test that list_seasons returns parsed SeasonSummary objects."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = list_seasons(session, timeout=1.0)

    assert len(result) == 2
    s1 = result[0]
    assert isinstance(s1, SeasonSummary)
    assert s1.id == "101"
    assert s1.title == "2024-2025 Regular Season"
    assert s1.stats_year == "2024-2025"
    assert s1.leagueId == "201"
    assert s1.league_id == "201"
    assert s1.league_title == "Great Lakes League"
    assert s1.association_id == "301"
    assert s1.association_title == "USA Hockey"

    s2 = result[1]
    assert s2.id == "102"
    assert not s2.association_id
    assert not s2.association_title


@responses.activate
def test_list_seasons_with_data_envelope() -> None:
    """Test that list_seasons handles nested data envelope."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "data": {"seasons": _sample_seasons_data()}},
        status=200,
    )

    session = _make_session()
    result = list_seasons(session, timeout=1.0)

    assert len(result) == 2
    assert result[0].id == "101"


@responses.activate
def test_list_seasons_with_data_list() -> None:
    """Test that list_seasons handles data as a direct list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "data": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = list_seasons(session, timeout=1.0)

    assert len(result) == 2
    assert result[0].id == "101"


@responses.activate
def test_list_seasons_with_raw_list() -> None:
    """Test that list_seasons handles top-level JSON list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json=_sample_seasons_data(),
        status=200,
    )

    session = _make_session()
    result = list_seasons(session, timeout=1.0)

    assert len(result) == 2
    assert result[0].id == "101"


@responses.activate
def test_list_seasons_empty() -> None:
    """Test that list_seasons returns empty list when no seasons are present."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": []},
        status=200,
    )

    session = _make_session()
    result = list_seasons(session, timeout=1.0)

    assert result == []


@responses.activate
def test_get_season_excludes_penalty_codes_and_teams() -> None:
    """Test that get_season returns SeasonDetail without penaltyCodes and teams."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = get_season(session, "101", timeout=1.0)

    assert isinstance(result, SeasonDetail)
    assert result.id == "101"
    assert result.title == "2024-2025 Regular Season"
    dumped = result.model_dump()
    assert "penaltyCodes" not in dumped
    assert "teams" not in dumped
    assert dumped["sport"] == "hockey"
    assert dumped["start_date"] == "2024-09-01"


@responses.activate
def test_get_season_without_optional_fields() -> None:
    """Test get_season when id or leagueId are None or absent in the response."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={
            "seasons": [
                {"id": 105, "title": "Minimal Season"},
                {"id": None, "leagueId": None, "title": "None ID Season"},
                {"title": "No ID Key Season"},
            ],
        },
        status=200,
    )

    session = _make_session()
    result = get_season(session, "105", timeout=1.0)
    assert result.id == "105"
    assert result.title == "Minimal Season"

    result_none = get_season(session, "None", timeout=1.0)
    assert not result_none.id
    assert not result_none.leagueId

    result_no_id = get_season(session, "", timeout=1.0)
    assert result_no_id.id is None
    assert result_no_id.title == "No ID Key Season"


@responses.activate
def test_get_season_not_found() -> None:
    """Test that get_season raises GameSheetError if season ID does not exist."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match="Season '999' not found"):
        get_season(session, "999", timeout=1.0)


@responses.activate
def test_get_season_penalty_codes() -> None:
    """Test that get_season_penalty_codes returns penalty codes for a season."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = get_season_penalty_codes(session, "101", timeout=1.0)

    assert len(result) == 2
    assert isinstance(result[0], PenaltyCode)
    assert result[0].code == "TRIP"
    assert result[0].name == "Tripping"
    assert result[0].model_dump()["severity"] == "minor"
    assert result[1].code == "SLASH"


@responses.activate
def test_get_season_penalty_codes_empty() -> None:
    """Test get_season_penalty_codes when season has no penalty codes."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = get_season_penalty_codes(session, "102", timeout=1.0)

    assert not result


@responses.activate
def test_get_season_penalty_codes_not_a_list() -> None:
    """Test get_season_penalty_codes when penaltyCodes is not a list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": [{"id": "104", "penaltyCodes": None}]},
        status=200,
    )

    session = _make_session()
    result = get_season_penalty_codes(session, "104", timeout=1.0)

    assert not result


@responses.activate
def test_get_season_penalty_codes_dict_without_code() -> None:
    """Test get_season_penalty_codes when dict item has no code field."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": [{"id": "104", "penaltyCodes": [{"name": "Penalty Without Code"}]}]},
        status=200,
    )

    session = _make_session()
    result = get_season_penalty_codes(session, "104", timeout=1.0)

    assert len(result) == 1
    assert result[0].name == "Penalty Without Code"


@responses.activate
def test_get_season_penalty_codes_string_items() -> None:
    """Test get_season_penalty_codes when items are strings instead of dicts."""
    seasons = [
        {
            "id": "103",
            "title": "Season 103",
            "penaltyCodes": ["ROUGH", "HOOK"],
        },
    ]
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": seasons},
        status=200,
    )

    session = _make_session()
    result = get_season_penalty_codes(session, "103", timeout=1.0)

    assert len(result) == 2
    assert result[0].code == "ROUGH"
    assert result[1].code == "HOOK"


@responses.activate
def test_get_season_penalty_codes_not_found() -> None:
    """Test get_season_penalty_codes raises GameSheetError if season not found."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": []},
        status=200,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match="Season '101' not found"):
        get_season_penalty_codes(session, "101", timeout=1.0)


@responses.activate
def test_get_season_teams() -> None:
    """Test that get_season_teams returns teams for a season."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = get_season_teams(session, "101", timeout=1.0)

    assert len(result) == 2
    assert isinstance(result[0], SeasonTeam)
    assert result[0].id == "1001"
    assert result[0].title == "Hawks"
    assert result[0].model_dump()["division"] == "Varsity"
    assert result[1].id == "1002"
    assert result[1].title == "Eagles"


@responses.activate
def test_get_season_teams_empty() -> None:
    """Test get_season_teams when season has no teams."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": _sample_seasons_data()},
        status=200,
    )

    session = _make_session()
    result = get_season_teams(session, "102", timeout=1.0)

    assert not result


@responses.activate
def test_get_season_teams_not_a_list() -> None:
    """Test get_season_teams when teams is not a list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": [{"id": "104", "teams": None}]},
        status=200,
    )

    session = _make_session()
    result = get_season_teams(session, "104", timeout=1.0)

    assert not result


@responses.activate
def test_get_season_teams_dict_without_id() -> None:
    """Test get_season_teams when dict item has no id field."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": [{"id": "104", "teams": [{"title": "No ID Team"}]}]},
        status=200,
    )

    session = _make_session()
    result = get_season_teams(session, "104", timeout=1.0)

    assert len(result) == 1
    assert result[0].title == "No ID Team"


@responses.activate
def test_get_season_teams_string_items() -> None:
    """Test get_season_teams when items are strings instead of dicts."""
    seasons = [
        {
            "id": "103",
            "title": "Season 103",
            "teams": ["501", "502"],
        },
    ]
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"seasons": seasons},
        status=200,
    )

    session = _make_session()
    result = get_season_teams(session, "103", timeout=1.0)

    assert len(result) == 2
    assert result[0].id == "501"
    assert result[1].id == "502"


@responses.activate
def test_get_season_teams_not_found() -> None:
    """Test get_season_teams raises GameSheetError if season not found."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"success": True, "seasons": []},
        status=200,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match="Season '101' not found"):
        get_season_teams(session, "101", timeout=1.0)


@responses.activate
def test_fetch_seasons_raw_unauthorized() -> None:
    """Test that 401 raises AuthenticationError."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        body="Unauthorized",
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        status=401,
        json={"errors": [{}]},
    )

    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_seasons_raw(session, timeout=1.0)


@responses.activate
def test_fetch_seasons_raw_http_error() -> None:
    """Test that 500 raises GameSheetError."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        body="Internal Server Error",
        status=500,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match="HTTP 500"):
        fetch_seasons_raw(session, timeout=1.0)


@responses.activate
def test_fetch_seasons_raw_empty_json() -> None:
    """Test that an unexpected JSON response structure returns empty list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json={"unexpected": "structure"},
        status=200,
    )

    session = _make_session()
    result = fetch_seasons_raw(session, timeout=1.0)

    assert result == []


@responses.activate
def test_fetch_seasons_raw_primitive_json() -> None:
    """Test that primitive JSON response returns empty list."""
    responses.add(
        responses.GET,
        _SEASONS_URL,
        json="plain string",
        status=200,
    )

    session = _make_session()
    result = fetch_seasons_raw(session, timeout=1.0)

    assert result == []
