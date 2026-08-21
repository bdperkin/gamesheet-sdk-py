# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for uploading team image."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import responses

from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.teams import upload_team_image
from tests.teams.test_teams.conftest import (
    REFRESH_URL,
    UPLOAD_DEST,
    UPLOAD_ENDPOINT,
    make_session,
)

if TYPE_CHECKING:
    from pathlib import Path


@responses.activate
def test_upload_team_image_success(tmp_path: Path) -> None:
    """Test upload_team_image performs get upload-url and post file successfully."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        UPLOAD_ENDPOINT,
        json={"uploadURL": UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(
        responses.POST,
        UPLOAD_DEST,
        json={"success": True},
        status=200,
    )

    session = make_session()
    result = upload_team_image(session, str(image_file), "logo", timeout=1.0)
    assert result == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123"


@responses.activate
def test_upload_team_image_extracts_id_from_url(tmp_path: Path) -> None:
    """Test upload_team_image extracts id from uploadURL when id field is omitted."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    responses.add(
        responses.GET,
        UPLOAD_ENDPOINT,
        json={"data": {"uploadURL": "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id"}},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id",
        json={"success": True},
        status=200,
    )

    session = make_session()
    result = upload_team_image(session, str(image_file), "logo", timeout=1.0)
    assert result == "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/extracted-id"


def test_upload_team_image_nonexistent_file() -> None:
    """Test upload_team_image raises GameSheetError if file does not exist."""
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Logo file not found"):
        upload_team_image(session, "/nonexistent/path/logo.png", "logo")


def test_upload_team_image_invalid_mime_type(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if file is not an image."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("not an image")
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Invalid image file"):
        upload_team_image(session, str(text_file), "logo")


@responses.activate
def test_upload_team_image_auth_error(tmp_path: Path) -> None:
    """Test upload_team_image raises AuthenticationError on 401."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, UPLOAD_ENDPOINT, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"error": "invalid_grant"},
        status=401,
    )
    session = make_session()
    with pytest.raises(AuthenticationError, match=r"Authentication required"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_endpoint_error(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError on upload-url endpoint error."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, UPLOAD_ENDPOINT, status=500, body="Server error")
    session = make_session()
    with pytest.raises(GameSheetError, match=r"GET /api/images/upload-url returned HTTP 500"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_missing_upload_url_field(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if response has no uploadURL."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(responses.GET, UPLOAD_ENDPOINT, json={"status": "ok"}, status=200)
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Failed to get upload URL"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)


@responses.activate
def test_upload_team_image_upload_post_error(tmp_path: Path) -> None:
    """Test upload_team_image raises GameSheetError if POSTing file fails."""
    image_file = tmp_path / "test_logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    responses.add(
        responses.GET,
        UPLOAD_ENDPOINT,
        json={"uploadURL": UPLOAD_DEST, "id": "img-123"},
        status=200,
    )
    responses.add(responses.POST, UPLOAD_DEST, status=500, body="Upload failed")
    session = make_session()
    with pytest.raises(GameSheetError, match=r"Failed to upload logo"):
        upload_team_image(session, str(image_file), "logo", timeout=1.0)
