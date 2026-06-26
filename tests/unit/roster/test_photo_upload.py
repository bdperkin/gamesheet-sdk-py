"""Tests for photo upload functionality."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session


def test_upload_photo_file_not_found(config: Config) -> None:
    """Test photo upload with non-existent file."""
    from gamesheet_sdk.roster.players import _upload_photo

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Photo file not found"):
            _upload_photo(session, "/nonexistent/path/photo.jpg")


def test_upload_photo_invalid_mime_type(config: Config) -> None:
    """Test photo upload with invalid file type."""
    import tempfile

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary non-image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
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

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request with 401
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
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

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request with 500
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
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

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request with failure status
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
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
    import tempfile

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request (success)
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
        json={
            "status": "success",
            "data": {"uploadURL": "https://upload.example.com/test", "id": "test-image-id"},
        },
        status=200,
    )
    # Mock upload request with 500 error
    responses.add(
        responses.POST,
        "https://upload.example.com/test",
        json={"error": "upload failed"},
        status=500,
    )

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="returned HTTP 500"):
            _upload_photo(session, temp_path)


@responses.activate
def test_upload_photo_upload_not_successful(config: Config) -> None:
    """Test photo upload when upload result is not successful."""
    import tempfile

    from gamesheet_sdk.roster.players import _upload_photo

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request (success)
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
        json={
            "status": "success",
            "data": {"uploadURL": "https://upload.example.com/test", "id": "test-image-id"},
        },
        status=200,
    )
    # Mock upload request with success=false
    responses.add(
        responses.POST,
        "https://upload.example.com/test",
        json={"success": False, "error": "virus detected"},
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match="Failed to upload photo"):
            _upload_photo(session, temp_path)
