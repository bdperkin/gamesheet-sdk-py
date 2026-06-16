"""Tests for get_referee_report function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.referees import get_referee_report

_BASE = "https://test.example"
_SEASON_ID = "15020"


@responses.activate
def test_get_referee_report_returns_complete_report(config: Config) -> None:
    """Test that get_referee_report returns a complete report."""
    _referee_id = "1146198"
    _external_id = "13340CA3-6B7D-4EC1-A183-EE281D2990A6"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _report_endpoint = f"{_BASE}/api/reports/referees/{_external_id}"

    # Mock the GET referee request
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": _external_id,
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
                    "email_address": "wes@example.com",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock the GET report request
    responses.add(
        responses.GET,
        _report_endpoint,
        json={
            "gamesRefereed": 15,
            "averagePimPerGame": 4.2,
            "mostFrequentPenalty": "Tripping",
            "majorPenaltiesCount": 3,
            "games": [
                {"id": "game1", "date": "2026-01-15"},
                {"id": "game2", "date": "2026-01-22"},
            ],
            "majorPenalties": [
                {"player": "Smith", "penalty": "Fighting"},
                {"player": "Jones", "penalty": "Checking from Behind"},
            ],
        },
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        report = get_referee_report(session, _SEASON_ID, _referee_id)

    assert report.external_id == _external_id
    assert report.first_name == "WES"
    assert report.last_name == "MCCAULEY"
    assert report.games_refereed == 15
    assert report.average_pim_per_game == 4.2
    assert report.most_frequent_penalty == "Tripping"
    assert report.major_penalties_count == 3
    assert len(report.games) == 2
    assert len(report.major_penalties) == 2


@responses.activate
def test_get_referee_report_with_minimal_data(config: Config) -> None:
    """Test that get_referee_report handles missing optional fields."""
    _referee_id = "1146199"
    _external_id = "ABC12345-6789-0DEF-ABCD-EF1234567890"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _report_endpoint = f"{_BASE}/api/reports/referees/{_external_id}"

    # Mock the GET referee request
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": _external_id,
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock the GET report request with minimal data
    responses.add(
        responses.GET,
        _report_endpoint,
        json={},  # Empty report
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        report = get_referee_report(session, _SEASON_ID, _referee_id)

    assert report.external_id == _external_id
    assert report.first_name == "Jane"
    assert report.last_name == "Doe"
    assert not report.games_refereed
    assert not report.average_pim_per_game
    assert report.most_frequent_penalty is None
    assert not report.major_penalties_count
    assert report.games == []
    assert report.major_penalties == []


@responses.activate
def test_get_referee_report_raises_error_if_no_external_id(config: Config) -> None:
    """Test that get_referee_report raises error when referee has no external_id."""
    _referee_id = "1146200"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"

    # Mock the GET referee request without external_id
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": None,  # No external_id
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
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
        with pytest.raises(
            GameSheetError,
            match=r"does not have an external_id set.*Cannot fetch report",
        ):
            get_referee_report(session, _SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_report_401_raises_authentication_error(config: Config) -> None:
    """Test that HTTP 401 on report request raises AuthenticationError."""
    _referee_id = "1146201"
    _external_id = "EXT-401-TEST"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _report_endpoint = f"{_BASE}/api/reports/referees/{_external_id}"

    # Mock the GET referee request
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": _external_id,
                    "first_name": "Auth",
                    "last_name": "Test",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock the GET report request with 401
    responses.add(
        responses.GET,
        _report_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )

    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_referee_report(session, _SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_report_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    """Test that HTTP 404 on report request raises GameSheetError with helpful message."""
    _referee_id = "1146202"
    _external_id = "EXT-404-TEST"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _report_endpoint = f"{_BASE}/api/reports/referees/{_external_id}"

    # Mock the GET referee request
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": _external_id,
                    "first_name": "Not",
                    "last_name": "Found",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock the GET report request with 404
    responses.add(responses.GET, _report_endpoint, status=404, body="Not found")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Report not found.*may not have officiated any games",
        ):
            get_referee_report(session, _SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_report_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    _referee_id = "1146203"
    _external_id = "EXT-500-TEST"
    _get_referee_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _report_endpoint = f"{_BASE}/api/reports/referees/{_external_id}"

    # Mock the GET referee request
    responses.add(
        responses.GET,
        _get_referee_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": _external_id,
                    "first_name": "Server",
                    "last_name": "Error",
                    "created_at": "2026-06-15T12:04:05Z",
                    "updated_at": "2026-06-15T12:04:05Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock the GET report request with 500
    responses.add(responses.GET, _report_endpoint, status=500, body="boom")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_referee_report(session, _SEASON_ID, _referee_id)
