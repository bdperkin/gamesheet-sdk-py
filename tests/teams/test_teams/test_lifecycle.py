# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for team lifecycle management (archive, restore, delete)."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.teams import (
    archive_team,
    delete_team,
    restore_team,
    unarchive_team,
)
from tests.teams.test_teams.conftest import (
    REFRESH_URL,
    TEAMS_URL,
    make_session,
)


@responses.activate
def test_archive_team_success() -> None:
    """Test archive_team sends PATCH with isArchived=True and returns TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
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

    session = make_session()
    result = archive_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.teamName == "Peterborough Petes 2"
    assert result.isArchived is True


@responses.activate
def test_archive_team_auth_error() -> None:
    """Test archive_team raises AuthenticationError on 401."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
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
        archive_team(session, team_id, timeout=1.0)


@responses.activate
def test_archive_team_server_error() -> None:
    """Test archive_team raises GameSheetError on non-2xx status."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Server error")

    session = make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/.* returned HTTP 500"):
        archive_team(session, team_id, timeout=1.0)


@responses.activate
def test_restore_team_success() -> None:
    """Test restore_team sends PATCH with isArchived=False and returns TeamDetail."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
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

    session = make_session()
    result = restore_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.teamName == "Peterborough Petes 2"
    assert result.isArchived is False


@responses.activate
def test_unarchive_team_alias() -> None:
    """Test unarchive_team alias functions identically to restore_team."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
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

    session = make_session()
    result = unarchive_team(session, team_id, timeout=1.0)
    assert result.teamId == team_id
    assert result.isArchived is False


@responses.activate
def test_restore_team_auth_error() -> None:
    """Test restore_team raises AuthenticationError on 401."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
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
        restore_team(session, team_id, timeout=1.0)


@responses.activate
def test_restore_team_server_error() -> None:
    """Test restore_team raises GameSheetError on non-2xx status."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    patch_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.PATCH, patch_url, status=500, body="Server error")

    session = make_session()
    with pytest.raises(GameSheetError, match=r"PATCH /api/teams/.* returned HTTP 500"):
        restore_team(session, team_id, timeout=1.0)


@responses.activate
def test_delete_team_success() -> None:
    """Test delete_team sends DELETE and succeeds on 200/204."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    delete_url = f"{TEAMS_URL}/{team_id}"
    responses.add(
        responses.DELETE,
        delete_url,
        status=204,
    )

    session = make_session()
    delete_team(session, team_id, timeout=1.0)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.method == "DELETE"


@responses.activate
def test_delete_team_auth_error() -> None:
    """Test delete_team raises AuthenticationError on 401."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    delete_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.DELETE, delete_url, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )

    session = make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        delete_team(session, team_id, timeout=1.0)


@responses.activate
def test_delete_team_server_error() -> None:
    """Test delete_team raises GameSheetError on non-2xx status."""
    team_id = "eb20a094-5c3c-47bc-918f-c8f69cfe0719"
    delete_url = f"{TEAMS_URL}/{team_id}"
    responses.add(responses.DELETE, delete_url, status=500, body="Server error")

    session = make_session()
    with pytest.raises(GameSheetError, match=r"DELETE /api/teams/.* returned HTTP 500"):
        delete_team(session, team_id, timeout=1.0)
