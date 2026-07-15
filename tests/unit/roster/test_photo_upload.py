# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for photo upload functionality."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from tests.fixtures.constants import TEST_FAKE_IMAGE_CONTENT
from tests.helpers import BFF_ASSETS_UPLOAD_URL_PATH, TEST_BFF_BASE_URL


def test_upload_photo_file_not_found(config: Config) -> None:
    """Test photo upload with non-existent file."""
    from gamesheet_sdk.admin.roster.players import _upload_photo

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Photo file not found"):
            _upload_photo(session, "/nonexistent/path/photo.jpg")


def test_upload_photo_invalid_mime_type(config: Config) -> None:
    """Test photo upload with invalid file type."""
    import tempfile

    from gamesheet_sdk.admin.roster.players import _upload_photo

    # Create a temporary non-image file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
    ) as temp_file:
        temp_file.write("not an image")
        temp_path = temp_file.name
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Invalid image file"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_auth_error(config: Config) -> None:
    """Test photo upload with 401 authentication error."""
    import tempfile

    from gamesheet_sdk.admin.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jpg",
        delete=False,
    ) as temp_file:
        temp_file.write(TEST_FAKE_IMAGE_CONTENT)
        temp_path = temp_file.name
    # Mock upload URL request with 401
    responses.add(
        responses.POST,
        f"{TEST_BFF_BASE_URL}{BFF_ASSETS_UPLOAD_URL_PATH}",
        json={"error": "unauthorized"},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(AuthenticationError, match="Access token rejected"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_server_error(config: Config) -> None:
    """Test photo upload with server error."""
    import tempfile

    from gamesheet_sdk.admin.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jpg",
        delete=False,
    ) as temp_file:
        temp_file.write(TEST_FAKE_IMAGE_CONTENT)
        temp_path = temp_file.name
    # Mock upload URL request with 500
    responses.add(
        responses.POST,
        f"{TEST_BFF_BASE_URL}{BFF_ASSETS_UPLOAD_URL_PATH}",
        json={"error": "server error"},
        status=500,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="returned HTTP 500"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_failed_status(config: Config) -> None:
    """Test photo upload with failed status in response."""
    import tempfile

    from gamesheet_sdk.admin.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jpg",
        delete=False,
    ) as temp_file:
        temp_file.write(TEST_FAKE_IMAGE_CONTENT)
        temp_path = temp_file.name
    # Mock upload URL request with failure status
    responses.add(
        responses.POST,
        f"{TEST_BFF_BASE_URL}{BFF_ASSETS_UPLOAD_URL_PATH}",
        json={"status": "failed", "error": "could not generate URL"},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Failed to get upload URL"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_upload_failed(config: Config) -> None:
    """Test photo upload when actual upload fails."""
    from gamesheet_sdk.admin.roster.players import _upload_photo
    from tests.helpers import setup_photo_upload_mocks

    temp_path = setup_photo_upload_mocks(
        upload_status=500,
        upload_response={"error": "upload failed"},
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="returned HTTP 500"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_upload_not_successful(config: Config) -> None:
    """Test photo upload when upload result is not successful."""
    from gamesheet_sdk.admin.roster.players import _upload_photo
    from tests.helpers import setup_photo_upload_mocks

    temp_path = setup_photo_upload_mocks(
        upload_response={"success": False, "error": "virus detected"},
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Failed to upload photo"):
            _upload_photo(session, temp_path)
