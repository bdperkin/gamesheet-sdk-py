# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for create_team function."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import cast

import pytest
import responses

from gamesheet_sdk import (
    BFF_API_BASE_URL,
    CLOUDFLARE_IMAGE_DELIVERY_BASE,
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    create_team,
)
from tests.helpers import (
    BFF_ASSETS_UPLOAD_URL_PATH,
    DEFAULT_TEAM_NAME,
    PROTOTEAM_ID,
    SEASON_ID,
    TEST_BFF_BASE_URL,
)

_BFF_BASE = BFF_API_BASE_URL
_UPLOAD_URL_ENDPOINT = f"{TEST_BFF_BASE_URL}{BFF_ASSETS_UPLOAD_URL_PATH}"
_CREATE_ENDPOINT = f"{_BFF_BASE}/dwg/seasons/{SEASON_ID}/teams"


@responses.activate
def test_create_team_sends_correct_payload_without_logo(config: Config) -> None:
    """Test that create_team sends correct payload without logo."""
    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={
            "status": "success",
            "data": {
                "prototeam": {
                    "id": PROTOTEAM_ID,
                    "title": DEFAULT_TEAM_NAME,
                    "logo": None,
                    "sport": "hockey",
                    "ageCategory": "",
                    "province": "",
                    "createdAt": "2026-06-13T17:21:32Z",
                },
                "seasonTeam": {
                    "id": 521623,
                    "title": DEFAULT_TEAM_NAME,
                    "divisionId": 80385,
                    "seasonId": 15020,
                    "leagueId": 1148580,
                    "associationId": 38,
                    "prototeamId": PROTOTEAM_ID,
                },
                "member": None,
                "invitation": {
                    "id": 521752,
                    "code": "M9XnAHNBt5",
                    "description": "Team: Test Team",
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_team(session, SEASON_ID, DEFAULT_TEAM_NAME, "80385")

    assert result["prototeam"]["title"] == DEFAULT_TEAM_NAME
    assert result["seasonTeam"]["divisionId"] == 80385
    assert result["invitation"]["code"] == "M9XnAHNBt5"
    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    import json

    assert req.body is not None
    payload = json.loads(cast("bytes | str", req.body))
    assert payload["title"] == DEFAULT_TEAM_NAME
    assert payload["divisionId"] == 80385
    assert "externalId" not in payload
    assert "logo" not in payload


@responses.activate
def test_create_team_with_external_id(config: Config) -> None:
    """Test that create_team includes external_id in payload when provided."""
    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={
            "status": "success",
            "data": {
                "prototeam": {"id": "test-proto-id", "title": DEFAULT_TEAM_NAME},
                "seasonTeam": {"id": 123, "divisionId": 80385},
                "member": None,
                "invitation": {"id": 1, "code": "ABC123"},
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_team(
            session,
            SEASON_ID,
            DEFAULT_TEAM_NAME,
            "80385",
            external_id="custom-external-id",
        )

    assert result["prototeam"]["id"] == "test-proto-id"
    # Verify external_id in payload
    import json

    assert responses.calls[0].request.body is not None
    payload = json.loads(cast("bytes | str", responses.calls[0].request.body))
    assert payload["externalId"] == "custom-external-id"


@responses.activate
def test_create_team_with_logo(config: Config) -> None:
    """Test that create_team uploads logo and includes it in team creation."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        # Step 1: Mock upload URL request
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={
                "status": "success",
                "data": {
                    "id": "test-image-id",
                    "uploadURL": "https://upload.example/test-image-id",
                },
            },
            status=200,
        )
        # Step 2: Mock image upload
        responses.add(
            responses.POST,
            "https://upload.example/test-image-id",
            json={
                "success": True,
                "result": {
                    "id": "test-image-id",
                    "filename": "test.png",
                },
            },
            status=200,
        )
        # Step 3: Mock team creation
        responses.add(
            responses.POST,
            _CREATE_ENDPOINT,
            json={
                "status": "success",
                "data": {
                    "prototeam": {
                        "id": "proto-id",
                        "title": DEFAULT_TEAM_NAME,
                        "logo": f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/test-image-id",
                    },
                    "seasonTeam": {"id": 123, "divisionId": 80385},
                    "member": None,
                    "invitation": {"id": 1, "code": "XYZ789"},
                },
            },
            status=200,
        )
        with Session(config) as session:
            session.set_bearer_token("abc")
            result = create_team(
                session,
                SEASON_ID,
                DEFAULT_TEAM_NAME,
                "80385",
                logo_path=logo_path,
            )

        assert result["prototeam"]["logo"] == f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/test-image-id"
        # Verify all three requests were made
        assert len(responses.calls) == 3
        # Verify team creation payload includes logo
        import json

        team_req = responses.calls[2].request
        assert team_req.body is not None
        payload = json.loads(cast("bytes | str", team_req.body))
        assert payload["logo"] == f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/test-image-id"
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_create_team_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            create_team(session, SEASON_ID, DEFAULT_TEAM_NAME, "80385")


@responses.activate
def test_create_team_other_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that other HTTP errors raise GameSheetError."""
    responses.add(responses.POST, _CREATE_ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            create_team(session, SEASON_ID, DEFAULT_TEAM_NAME, "80385")


@responses.activate
def test_create_team_failed_status_raises_gamesheet_error(config: Config) -> None:
    """Test that failed status in response raises GameSheetError."""
    responses.add(
        responses.POST,
        _CREATE_ENDPOINT,
        json={"status": "error", "message": "Something went wrong"},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="Failed to create team"):
            create_team(session, SEASON_ID, DEFAULT_TEAM_NAME, "80385")


@responses.activate
def test_upload_logo_invalid_file_raises_error(config: Config) -> None:
    """Test that invalid logo file path raises GameSheetError."""
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="Logo file not found"):
            create_team(
                session,
                SEASON_ID,
                DEFAULT_TEAM_NAME,
                "80385",
                logo_path="/nonexistent/path.png",
            )


@responses.activate
def test_upload_logo_non_image_file_raises_error(config: Config) -> None:
    """Test that non-image file raises GameSheetError."""
    # Create a temporary non-image file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not an image")
        non_image_path = f.name

    try:
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(GameSheetError, match="Invalid image file"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=non_image_path,
                )
    finally:
        Path(non_image_path).unlink()


@responses.activate
def test_upload_url_request_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 on upload URL request raises AuthenticationError."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={"errors": [{"detail": "Token expired"}]},
            status=401,
        )
        with Session(config) as session:
            session.set_bearer_token("stale")
            with pytest.raises(AuthenticationError, match="HTTP 401"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=logo_path,
                )
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_upload_url_request_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that HTTP errors on upload URL request raise GameSheetError."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            status=500,
            body="Internal server error",
        )
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(GameSheetError, match="HTTP 500"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=logo_path,
                )
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_upload_url_failed_status_raises_gamesheet_error(config: Config) -> None:
    """Test that failed status on upload URL request raises GameSheetError."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={"status": "error", "message": "Upload URL generation failed"},
            status=200,
        )
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(GameSheetError, match="Failed to get upload URL"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=logo_path,
                )
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_image_upload_failure_raises_gamesheet_error(config: Config) -> None:
    """Test that HTTP errors during image upload raise GameSheetError."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={
                "status": "success",
                "data": {
                    "id": "test-image-id",
                    "uploadURL": "https://upload.example/test-image-id",
                },
            },
            status=200,
        )
        responses.add(
            responses.POST,
            "https://upload.example/test-image-id",
            status=500,
            body="Upload failed",
        )
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(GameSheetError, match="HTTP 500"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=logo_path,
                )
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_image_upload_failed_success_flag_raises_gamesheet_error(
    config: Config,
) -> None:
    """Test that failed success flag in upload response raises GameSheetError."""
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={
                "status": "success",
                "data": {
                    "id": "test-image-id",
                    "uploadURL": "https://upload.example/test-image-id",
                },
            },
            status=200,
        )
        responses.add(
            responses.POST,
            "https://upload.example/test-image-id",
            json={
                "success": False,
                "errors": ["Upload validation failed"],
            },
            status=200,
        )
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(GameSheetError, match="Failed to upload logo"):
                create_team(
                    session,
                    SEASON_ID,
                    DEFAULT_TEAM_NAME,
                    "80385",
                    logo_path=logo_path,
                )
    finally:
        Path(logo_path).unlink()
