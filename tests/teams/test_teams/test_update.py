# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for updating team details."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.teams import (
    TeamDetail,
    update_team,
)
from tests.teams.test_teams.conftest import (
    REFRESH_URL,
    TEAMS_URL,
    UPLOAD_DEST,
    UPLOAD_ENDPOINT,
    make_session,
)

if TYPE_CHECKING:
    from pathlib import Path


@responses.activate
def test_update_team_success() -> None:
    """Test update_team sends PATCH and returns refreshed TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
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

    session = make_session()
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
    patch_url = f"{TEAMS_URL}/{team_id}"
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        UPLOAD_ENDPOINT,
        json={"uploadURL": UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(responses.POST, UPLOAD_DEST, json={"success": True}, status=200)
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

    session = make_session()
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
    patch_url = f"{TEAMS_URL}/{team_id}"
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

    session = make_session()
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
    session = make_session()
    with pytest.raises(GameSheetError, match=r"At least one field must be provided for update"):
        update_team(session, "t-101")


@responses.activate
def test_update_team_auth_error() -> None:
    """Test update_team raises AuthenticationError on 401."""
    team_id = "t-101"
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        update_team(session, team_id, team_name="New Name", timeout=1.0)


@responses.activate
def test_update_team_server_error() -> None:
    """Test update_team raises GameSheetError on PATCH non-2xx status."""
    team_id = "t-101"
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Internal error")
    session = make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/t-101 returned HTTP 500"):
        update_team(session, team_id, team_name="New Name", timeout=1.0)


@responses.activate
def test_update_team_with_id_field_and_none_extra_fields() -> None:
    """Test update_team handles fallback id field and skips None in extra_fields."""
    team_id = "t-555"
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, json={"success": True}, status=200)
    responses.add(
        responses.GET,
        patch_url,
        json={"id": "t-555", "teamName": "Updated Via ID"},
        status=200,
    )

    session = make_session()
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
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, json={"success": True}, status=200)
    responses.add(
        responses.GET,
        patch_url,
        json={"teamName": "No ID Team"},
        status=200,
    )

    session = make_session()
    result = update_team(
        session,
        team_id,
        team_name="No ID Team",
        timeout=1.0,
    )
    assert result.teamId is None
    assert result.teamName == "No ID Team"
