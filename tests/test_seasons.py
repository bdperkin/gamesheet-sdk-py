"""Tests for :mod:`gamesheet_sdk.seasons`."""

# pylint: disable=too-many-lines  # Comprehensive test coverage for BFF API filtering

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    get_season,
    list_seasons,
)
from gamesheet_sdk.seasons import Season, SeasonDetail

_BASE = "https://test.example"
_LEAGUE_ID = "1148580"
_ENDPOINT = f"{_BASE}/api/seasons"
_BFF_BASE_URL = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app"
_BFF_ENDPOINT = f"{_BFF_BASE_URL}/leagues/{_LEAGUE_ID}/seasons"


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
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
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


# Tests for get_season
_SEASON_ID = "15020"
_SEASON_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}"


def _detail_payload(data: dict[str, object]) -> dict[str, object]:
    """Build a JSON:API ``{"data": {...}}`` body for a single resource."""
    return {"data": data}


@responses.activate
def test_get_season_parses_detailed_jsonapi_response(config: Config) -> None:

    responses.add(
        responses.GET,
        _SEASON_ENDPOINT,
        json=_detail_payload(
            {
                "type": "seasons",
                "id": _SEASON_ID,
                "attributes": {
                    "title": "Test Season 2026-2027",
                    "external_id": "558772B8-DAF4-4848-B7CA-1FB620F2BA52",
                    "start_date": "2026-05-15",
                    "end_date": "2027-08-15",
                    "sport": "hockey",
                    "stats_year": "2026-2027",
                    "live_scoring_mode": "public",
                    "player_of_the_game": None,
                    "flagging_criteria": {"penalty": True, "unlocked": True},
                    "flagged_penalties": ["BDG-MAJ", "CHG-MAJ"],
                    "settings": {
                        "penalty_lengths": ["2", "5", "10"],
                        "goal_value": 1,
                    },
                    "vendor_data": {},
                    "created_at": "2026-05-15T17:41:04.363363Z",
                    "updated_at": "2026-05-15T22:24:22.122544Z",
                },
                "relationships": {
                    "association": {"data": {"type": "associations", "id": "38"}},
                    "league": {"data": {"type": "leagues", "id": _LEAGUE_ID}},
                },
            },
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = get_season(session, _SEASON_ID)
    assert result.id == _SEASON_ID
    assert result.title == "Test Season 2026-2027"
    assert result.association_id == "38"
    assert result.league_id == _LEAGUE_ID
    assert result.external_id == "558772B8-DAF4-4848-B7CA-1FB620F2BA52"
    assert result.start_date == "2026-05-15"
    assert result.end_date == "2027-08-15"
    assert result.sport == "hockey"
    assert result.stats_year == "2026-2027"
    assert result.live_scoring_mode == "public"
    assert result.player_of_the_game is None
    assert result.flagging_criteria == {"penalty": True, "unlocked": True}
    assert result.flagged_penalties == ["BDG-MAJ", "CHG-MAJ"]
    assert result.settings == {"penalty_lengths": ["2", "5", "10"], "goal_value": 1}
    assert result.vendor_data == {}
    assert result.created_at == datetime(2026, 5, 15, 17, 41, 4, 363363, tzinfo=timezone.utc)
    assert result.updated_at == datetime(2026, 5, 15, 22, 24, 22, 122544, tzinfo=timezone.utc)


@responses.activate
def test_get_season_sends_bearer_and_jsonapi_accept(config: Config) -> None:

    responses.add(
        responses.GET,
        _SEASON_ENDPOINT,
        json=_detail_payload(
            {
                "type": "seasons",
                "id": _SEASON_ID,
                "attributes": {
                    "title": "Test",
                    "external_id": "uuid",
                    "start_date": "2026-01-01",
                    "end_date": "2026-12-31",
                    "sport": "hockey",
                    "stats_year": "2026",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                "relationships": {
                    "association": {"data": {"type": "associations", "id": "1"}},
                    "league": {"data": {"type": "leagues", "id": "2"}},
                },
            },
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_season(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_season_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.GET,
        _SEASON_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_season(session, _SEASON_ID)


@responses.activate
def test_get_season_404_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _SEASON_ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            get_season(session, _SEASON_ID)


@responses.activate
def test_get_season_other_failure_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _SEASON_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_season(session, _SEASON_ID)


def test_season_detail_model_ignores_unknown_attributes() -> None:

    sd = SeasonDetail(
        id="15020",
        association_id="38",
        league_id="1148580",
        title="Test",
        external_id="uuid",
        start_date="2026-01-01",
        end_date="2026-12-31",
        sport="hockey",
        stats_year="2026",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert sd.title == "Test"


# Tests for BFF API filtering


def _bff_payload(items: list[dict[str, object]]) -> dict[str, object]:
    """Build a BFF API response body."""
    return {
        "status": "success",
        "data": items,
        "meta": {
            "total_count": len(items),
            "filtered_count": len(items),
            "total_pages": 1,
            "current_page": 1,
            "page_size": 25,
        },
    }


@responses.activate
def test_list_seasons_with_status_filter_uses_bff_api(config: Config) -> None:
    """When a filter is provided, the BFF API should be used."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json=_bff_payload(
            [
                {
                    "id": 15020,
                    "title": "Active Season",
                    "start_date": "2026-05-15",
                    "end_date": "2027-08-15",
                    "stats_year": "2026-2027",
                    "is_archived": False,
                    "is_current": True,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, _LEAGUE_ID, status="active")
    assert len(result) == 1
    assert result[0].id == "15020"
    assert result[0].title == "Active Season"
    assert result[0].league_id == _LEAGUE_ID
    # Verify the BFF endpoint was called with correct parameters
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.url is not None
    assert _BFF_ENDPOINT in req.url
    assert "filter%5Bstatus%5D=active" in req.url or "filter[status]=active" in req.url


@responses.activate
def test_list_seasons_with_title_filter_uses_bff_api(config: Config) -> None:
    """Title filter should use BFF API."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json=_bff_payload(
            [
                {
                    "id": 15020,
                    "title": "Raleigh Raptors Season",
                    "start_date": "2026-05-15",
                    "end_date": "2027-08-15",
                    "stats_year": "2026-2027",
                    "is_archived": False,
                    "is_current": True,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, _LEAGUE_ID, title="Raptors")
    assert len(result) == 1
    assert "Raptors" in result[0].title
    # Verify the filter was passed
    req = responses.calls[0].request
    assert req.url is not None
    assert "filter%5Btitle%5D=Raptors" in req.url or "filter[title]=Raptors" in req.url


@responses.activate
def test_list_seasons_with_date_filters_uses_bff_api(config: Config) -> None:
    """Date range filters should use BFF API."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json=_bff_payload(
            [
                {
                    "id": 15020,
                    "title": "2026-2027 Season",
                    "start_date": "2026-05-15",
                    "end_date": "2027-08-15",
                    "stats_year": "2026-2027",
                    "is_archived": False,
                    "is_current": True,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(
            session,
            _LEAGUE_ID,
            starts_after="2026-01-01",
            ends_before="2027-12-31",
        )
    assert len(result) == 1
    # Verify the filters were passed
    req = responses.calls[0].request
    assert req.url is not None
    assert "starts_after" in req.url
    assert "ends_before" in req.url


@responses.activate
def test_list_seasons_with_stats_year_filter_uses_bff_api(config: Config) -> None:
    """Stats year filter should use BFF API."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json=_bff_payload(
            [
                {
                    "id": 15020,
                    "title": "2026-2027 Season",
                    "start_date": "2026-05-15",
                    "end_date": "2027-08-15",
                    "stats_year": "2026-2027",
                    "is_archived": False,
                    "is_current": True,
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, _LEAGUE_ID, stats_year="2026-2027")
    assert len(result) == 1
    # BFF API returns Season objects which don't have stats_year field
    # Just verify we got a result and the filter was passed
    # Verify the filter was passed
    req = responses.calls[0].request
    assert req.url is not None
    assert "stats_year" in req.url


@responses.activate
def test_list_seasons_bff_api_401_raises_authentication_error(config: Config) -> None:
    """BFF API 401 should raise AuthenticationError."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json={
            "status": "error",
            "errors": [{"code": 401, "message": "Unauthorized"}],
        },
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_seasons(session, _LEAGUE_ID, status="active")


@responses.activate
def test_list_seasons_bff_api_404_raises_gamesheet_error(config: Config) -> None:
    """BFF API 404 should raise GameSheetError with helpful message."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json={
            "status": "error",
            "errors": [{"code": 404, "message": "League not found"}],
        },
        status=404,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"League '.*' not found.*valid league ID.*leagues list",
        ):
            list_seasons(session, _LEAGUE_ID, status="active")


@responses.activate
def test_list_seasons_bff_api_other_error_raises_gamesheet_error(config: Config) -> None:
    """BFF API 500 should raise GameSheetError."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        status=500,
        body="Internal server error",
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_seasons(session, _LEAGUE_ID, status="active")


@responses.activate
def test_list_seasons_bff_api_non_success_status_raises_error(config: Config) -> None:
    """BFF API non-success status in body should raise GameSheetError."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json={"status": "error", "data": [], "errors": []},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="non-success status"):
            list_seasons(session, _LEAGUE_ID, status="active")


@responses.activate
def test_list_seasons_bff_api_empty_results(config: Config) -> None:
    """BFF API should handle empty results correctly."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json=_bff_payload([]),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, _LEAGUE_ID, status="archived")
    assert result == []


@responses.activate
def test_list_seasons_bff_api_data_as_dict_with_items(config: Config) -> None:
    """BFF API should handle data as dict with items key."""
    # pylint: disable=unexpected-keyword-arg  # list_seasons accepts keyword-only args
    responses.add(
        responses.GET,
        _BFF_ENDPOINT,
        json={
            "status": "success",
            "data": {
                "items": [
                    {
                        "id": 15020,
                        "title": "Season in dict",
                        "start_date": "2026-05-15",
                        "end_date": "2027-08-15",
                        "stats_year": "2026-2027",
                        "is_archived": False,
                        "is_current": True,
                    },
                ],
            },
            "meta": {},
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_seasons(session, _LEAGUE_ID, status="active")
    assert len(result) == 1
    assert result[0].title == "Season in dict"
