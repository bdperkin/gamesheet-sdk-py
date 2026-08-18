# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the teams domain module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import responses

if TYPE_CHECKING:
    from pathlib import Path

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_REFRESH_PATH,
    TEAMS_TEAMS_PATH,
)
from gamesheet_sdk.teams.teams import (
    TeamDetail,
    TeamSummary,
    _find_team,
    _parse_team_summary,
    archive_team,
    fetch_team_raw,
    fetch_teams_raw,
    get_team,
    list_teams,
    restore_team,
    unarchive_team,
    update_team,
    upload_team_image,
)

_TEAMS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}"
_REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"


def _make_session() -> TeamsAuthenticatedSession:
    """Create a test TeamsAuthenticatedSession."""
    config = Config()
    return TeamsAuthenticatedSession(
        config,
        access_token="test-access",
        refresh_token="test-refresh",
    )


def _sample_teams_data() -> list[dict[str, Any]]:
    """Return sample teams data list."""
    return [
        {
            "memberId": "m-001",
            "teamId": "t-101",
            "relationship": "coach",
            "status": "active",
            "onboardingCompletedAt": "2024-09-01T10:00:00Z",
            "teamName": "Hawks 12U",
            "ageCategory": "12U",
            "clubId": "c-501",
            "joinedAt": "2024-08-15T09:00:00Z",
            "statsYear": "2024-2025",
            "extra_field": "some_extra_val",
        },
        {
            "memberId": "m-002",
            "teamId": "t-102",
            "relationship": "manager",
            "status": "pending",
            "onboardingCompletedAt": "2024-09-02T11:00:00Z",
            "teamName": "Eagles 14U",
            "ageCategory": "14U",
            "clubId": "c-502",
            "joinedAt": "2024-08-20T14:00:00Z",
            "statsYear": "2024-2025",
        },
    ]


@responses.activate
def test_list_teams_parses_response() -> None:
    """Test that list_teams returns parsed TeamSummary objects."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"success": True, "teams": _sample_teams_data()},
        status=200,
    )

    session = _make_session()
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
        _TEAMS_URL,
        json={"teams": []},
        status=200,
    )

    session = _make_session()
    result = list_teams(session, timeout=1.0)
    assert result == []


@responses.activate
def test_fetch_teams_raw_data_envelope_dict() -> None:
    """Test fetch_teams_raw when API wraps in data.teams dictionary."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"data": {"teams": _sample_teams_data()}},
        status=200,
    )

    session = _make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2
    assert result[0]["teamName"] == "Hawks 12U"


@responses.activate
def test_fetch_teams_raw_data_envelope_list() -> None:
    """Test fetch_teams_raw when API returns data as a list."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"data": _sample_teams_data()},
        status=200,
    )

    session = _make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2


@responses.activate
def test_fetch_teams_raw_direct_list() -> None:
    """Test fetch_teams_raw when API returns a top-level list."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json=_sample_teams_data(),
        status=200,
    )

    session = _make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert len(result) == 2


@responses.activate
def test_fetch_teams_raw_unexpected_shape() -> None:
    """Test fetch_teams_raw when API returns an unrecognized structure."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"unknown_key": "some_value"},
        status=200,
    )

    session = _make_session()
    result = fetch_teams_raw(session, timeout=1.0)
    assert result == []


@responses.activate
def test_fetch_teams_raw_non_dict_non_list_body() -> None:
    """Test fetch_teams_raw when response JSON is neither dict nor list."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json=123,
        status=200,
    )

    session = _make_session()
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
        _TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = _make_session()
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
        _TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = _make_session()
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
        _TEAMS_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = _make_session()
    with pytest.raises(AuthenticationError, match="Authentication required"):
        fetch_teams_raw(session, timeout=1.0)


@responses.activate
def test_fetch_teams_raw_server_error() -> None:
    """Test that 500 raises GameSheetError."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        body="Internal Server Error",
        status=500,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match="HTTP 500"):
        fetch_teams_raw(session, timeout=1.0)


@responses.activate
def test_get_team_success() -> None:
    """Test get_team returns detailed TeamDetail model."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"teams": _sample_teams_data()},
        status=200,
    )

    session = _make_session()
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
        _TEAMS_URL,
        json={"teams": raw_data},
        status=200,
    )

    session = _make_session()
    detail = get_team(session, "999", timeout=1.0)

    assert detail.teamId == "999"


@responses.activate
def test_get_team_not_found() -> None:
    """Test get_team raises GameSheetError when ID does not exist."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"teams": _sample_teams_data()},
        status=200,
    )

    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Team 't-999' not found\."):
        get_team(session, "t-999", timeout=1.0)


@responses.activate
def test_get_team_401() -> None:
    """Test get_team 401 error propagates AuthenticationError."""
    responses.add(
        responses.GET,
        _TEAMS_URL,
        json={"error": "Unauthorized"},
        status=401,
    )
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = _make_session()
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
    assert summary.memberId == ""
    assert summary.teamId == ""
    assert summary.relationship == ""
    assert summary.status == ""
    assert summary.onboardingCompletedAt == ""
    assert summary.teamName == ""
    assert summary.ageCategory == ""
    assert summary.clubId == ""
    assert summary.joinedAt == ""
    assert summary.statsYear == ""


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


_UPLOAD_ENDPOINT = f"{TEAMS_API_GATEWAY}/api/images/upload-url"
_UPLOAD_DEST = "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123"


@responses.activate
def test_fetch_team_raw_single_endpoint_success() -> None:
    """Test fetch_team_raw retrieves team directly from GET /api/teams/{id}."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"team": {"teamId": "t-101", "teamName": "Hawks 12U"}},
        status=200,
    )
    session = _make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"
    assert result["teamName"] == "Hawks 12U"


@responses.activate
def test_fetch_team_raw_data_envelope_success() -> None:
    """Test fetch_team_raw unwraps data envelope from GET /api/teams/{id}."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"data": {"teamId": "t-101", "teamName": "Hawks 12U"}},
        status=200,
    )
    session = _make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"


@responses.activate
def test_fetch_team_raw_bare_dict_success() -> None:
    """Test fetch_team_raw handles bare dict from GET /api/teams/{id}."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(
        responses.GET,
        url,
        json={"teamId": "t-101", "teamName": "Hawks 12U"},
        status=200,
    )
    session = _make_session()
    result = fetch_team_raw(session, "t-101", timeout=1.0)
    assert result["teamId"] == "t-101"


@responses.activate
def test_fetch_team_raw_server_error() -> None:
    """Test fetch_team_raw raises GameSheetError on HTTP 500."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(responses.GET, url, status=500, body="Server error")
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/teams/t-101 returned HTTP 500"):
        fetch_team_raw(session, "t-101", timeout=1.0)


@responses.activate
def test_fetch_team_raw_unexpected_body() -> None:
    """Test fetch_team_raw raises GameSheetError when body is not a dict."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(responses.GET, url, json=123, status=200)
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Unexpected response format"):
        fetch_team_raw(session, "t-101", timeout=1.0)


@responses.activate
def test_fetch_team_raw_auth_error() -> None:
    """Test fetch_team_raw raises AuthenticationError on 401."""
    url = f"{_TEAMS_URL}/t-101"
    responses.add(responses.GET, url, status=401)
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        fetch_team_raw(session, "t-101", timeout=1.0)


@responses.activate
def test_upload_team_image_success(tmp_path: Path) -> None:
    """Test upload_team_image performs get upload-url and post file successfully."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        _UPLOAD_ENDPOINT,
        json={"uploadURL": _UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(
        responses.POST,
        _UPLOAD_DEST,
        json={"success": True},
        status=200,
    )

    session = _make_session()
    result = upload_team_image(session, str(image_file), "logo", timeout=1.0)
    assert result == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123"


@responses.activate
def test_upload_team_image_extracts_id_from_url(tmp_path: Path) -> None:
    """Test upload_team_image extracts id from uploadURL when id field is omitted."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        _UPLOAD_ENDPOINT,
        json={"data": {"uploadURL": "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id"}},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id",
        json={"success": True},
        status=200,
    )

    session = _make_session()
    result = upload_team_image(session, str(image_file), "logo", timeout=1.0)
    assert result == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id"


def test_upload_team_image_nonexistent_file() -> None:
    """Test upload_team_image raises GameSheetError if file does not exist."""
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Logo file not found"):
        upload_team_image(session, "/nonexistent/path/logo.png", "logo")


def test_upload_team_image_invalid_mime_type(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if file is not an image."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("not an image")
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Invalid image file"):
        upload_team_image(session, str(text_file), "logo")


@responses.activate
def test_upload_team_image_auth_error(tmp_path: Path) -> None:
    """Test upload_team_image raises AuthenticationError on 401."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, _UPLOAD_ENDPOINT, status=401)
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_endpoint_error(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError on upload-url endpoint error."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, _UPLOAD_ENDPOINT, status=500, body="Server error")
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/images/upload-url returned HTTP 500"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_missing_upload_url_field(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if response has no uploadURL."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, _UPLOAD_ENDPOINT, json={"status": "ok"}, status=200)
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Failed to get upload URL"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_upload_post_error(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if POSTing file fails."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(
        responses.GET,
        _UPLOAD_ENDPOINT,
        json={"uploadURL": _UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(responses.POST, _UPLOAD_DEST, status=500, body="Upload failed")
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"Failed to upload logo"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_update_team_success() -> None:
    """Test update_team sends PATCH and returns refreshed TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(
        responses.PATCH,
        patch_url,
        json={
            "success": True,
            "team": {
                "teamId": team_id,
                "teamName": "Peterborough Petes 2",
                "skill": "rec",
                "ageCategory": "U18",
                "province": "VA",
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamName": "Peterborough Petes 2",
                "skill": "rec",
                "ageCategory": "U18",
                "province": "VA",
                "seasonTeamsUpdated": 1,
                "isArchived": False,
            },
        },
        status=200,
    )

    session = _make_session()
    updated = update_team(
        session,
        team_id,
        team_name="Peterborough Petes 2",
        skill="rec",
        age_category="U18",
        province="VA",
        timeout=1.0,
    )

    assert isinstance(updated, TeamDetail)
    assert updated.teamId == team_id
    assert updated.teamName == "Peterborough Petes 2"
    assert updated.skill == "rec"
    assert updated.ageCategory == "U18"
    assert updated.province == "VA"
    assert updated.seasonTeamsUpdated == 1
    assert updated.isArchived is False


@responses.activate
def test_update_team_with_local_logo_upload(tmp_path: Path) -> None:
    """Test update_team uploads logo when local file path is provided."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        _UPLOAD_ENDPOINT,
        json={"uploadURL": _UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(responses.POST, _UPLOAD_DEST, json={"success": True}, status=200)
    responses.add(
        responses.PATCH,
        patch_url,
        json={"success": True},
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamName": "Hawks",
                "teamLogo": "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123",
            },
        },
        status=200,
    )

    session = _make_session()
    updated = update_team(
        session,
        team_id,
        team_name="Hawks",
        team_logo=str(image_file),
        timeout=1.0,
    )
    assert updated.teamLogo == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123"


@responses.activate
def test_update_team_with_direct_url_logo() -> None:
    """Test update_team uses direct image URL without calling upload endpoint."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    logo_url = "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/735bf689-4e29-41c0-e3ad-e4eec779f100"

    responses.add(
        responses.PATCH,
        patch_url,
        json={"success": True},
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamLogo": logo_url,
            },
        },
        status=200,
    )

    session = _make_session()
    updated = update_team(
        session,
        team_id,
        team_logo=logo_url,
        extra_note="custom",
        timeout=1.0,
    )
    assert updated.teamLogo == logo_url


def test_update_team_no_fields_raises_error() -> None:
    """Test update_team raises GameSheetError if no fields are provided."""
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"At least one field must be provided for update"):
        update_team(session, "t-101")


@responses.activate
def test_update_team_auth_error() -> None:
    """Test update_team raises AuthenticationError on 401."""
    team_id = "t-101"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=401)
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = _make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        update_team(session, team_id, team_name="New Name", timeout=1.0)


@responses.activate
def test_update_team_server_error() -> None:
    """Test update_team raises GameSheetError on PATCH non-2xx status."""
    team_id = "t-101"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Internal error")
    session = _make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/t-101 returned HTTP 500"):
        update_team(session, team_id, team_name="New Name", timeout=1.0)


@responses.activate
def test_update_team_with_id_field_and_none_extra_fields() -> None:
    """Test update_team handles fallback id field and skips None in extra_fields."""
    team_id = "t-555"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, json={"success": True}, status=200)
    responses.add(
        responses.GET,
        patch_url,
        json={"id": "t-555", "teamName": "Updated Via ID"},
        status=200,
    )

    session = _make_session()
    result = update_team(
        session,
        team_id,
        team_name="Updated Via ID",
        custom_null=None,
        custom_valid="yes",
        timeout=1.0,
    )
    assert result.teamId == "t-555"
    assert result.teamName == "Updated Via ID"


@responses.activate
def test_update_team_with_neither_team_id_nor_id() -> None:
    """Test update_team when refreshed team payload contains neither teamId nor id."""
    team_id = "t-999"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, json={"success": True}, status=200)
    responses.add(
        responses.GET,
        patch_url,
        json={"teamName": "No ID Team"},
        status=200,
    )

    session = _make_session()
    result = update_team(
        session,
        team_id,
        team_name="No ID Team",
        timeout=1.0,
    )
    assert result.teamId is None
    assert result.teamName == "No ID Team"


@responses.activate
def test_archive_team_success() -> None:
    """Test archive_team sends PATCH with isArchived=True and returns TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(
        responses.PATCH,
        patch_url,
        json={"success": True},
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamName": "Peterborough Petes 2",
                "teamLogo": "https://imagedelivery.net/test/logo-123",
                "skill": "rec",
                "ageCategory": "U18",
                "province": "VA",
                "isArchived": True,
            },
        },
        status=200,
    )

    session = _make_session()
    result = archive_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.teamName == "Peterborough Petes 2"
    assert result.isArchived is True


@responses.activate
def test_archive_team_auth_error() -> None:
    """Test archive_team raises AuthenticationError on 401."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=401)
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = _make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        archive_team(session, team_id, timeout=1.0)


@responses.activate
def test_archive_team_server_error() -> None:
    """Test archive_team raises GameSheetError on non-2xx status."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Server error")

    session = _make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/.* returned HTTP 500"):
        archive_team(session, team_id, timeout=1.0)


@responses.activate
def test_restore_team_success() -> None:
    """Test restore_team sends PATCH with isArchived=False and returns TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(
        responses.PATCH,
        patch_url,
        json={"success": True},
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamName": "Peterborough Petes 2",
                "teamLogo": "https://imagedelivery.net/test/logo-123",
                "skill": "rec",
                "ageCategory": "U18",
                "province": "VA",
                "isArchived": False,
            },
        },
        status=200,
    )

    session = _make_session()
    result = restore_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.teamName == "Peterborough Petes 2"
    assert result.isArchived is False


@responses.activate
def test_unarchive_team_alias() -> None:
    """Test unarchive_team alias functions identically to restore_team."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(
        responses.PATCH,
        patch_url,
        json={"success": True},
        status=200,
    )
    responses.add(
        responses.GET,
        patch_url,
        json={
            "team": {
                "teamId": team_id,
                "teamName": "Peterborough Petes 2",
                "isArchived": False,
            },
        },
        status=200,
    )

    session = _make_session()
    result = unarchive_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.isArchived is False


@responses.activate
def test_restore_team_auth_error() -> None:
    """Test restore_team raises AuthenticationError on 401."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=401)
    responses.add(
        responses.POST,
        _REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = _make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        restore_team(session, team_id, timeout=1.0)


@responses.activate
def test_restore_team_server_error() -> None:
    """Test restore_team raises GameSheetError on non-2xx status."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{_TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Server error")

    session = _make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/.* returned HTTP 500"):
        restore_team(session, team_id, timeout=1.0)
