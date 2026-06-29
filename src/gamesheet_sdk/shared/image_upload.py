# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared image upload functionality for GameSheet resources."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from gamesheet_sdk.constants import BFF_API_BASE_URL, CLOUDFLARE_IMAGE_DELIVERY_BASE
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.session import Session


def upload_image(session: Session, image_path: str, image_type: str = "image") -> str:
    """Upload an image file and return its Cloudflare CDN URL.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param image_path: Path to a local image file.
    :type image_path: str
    :param image_type: Type of image for error messages (e.g., "photo", "logo").
    :type image_type: str
    :returns: The Cloudflare CDN URL for the uploaded image.
    :rtype: str
    :raises GameSheetError: If the file is not found, is not a valid image, or the upload fails.
    :raises AuthenticationError: If the server returns 401.
    """
    image_file_path = Path(image_path)
    if not image_file_path.exists():
        _err_msg = f"{image_type.capitalize()} file not found: {image_path}"
        raise GameSheetError(_err_msg)
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        _err_msg = f"Invalid image file: {image_path}"
        raise GameSheetError(_err_msg)
    upload_url_endpoint = f"{BFF_API_BASE_URL}/dwg/assets/upload-url"
    upload_url_response = session.post(upload_url_endpoint)
    if upload_url_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again."
        )
        raise AuthenticationError(_err_msg)
    if upload_url_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url_endpoint} returned HTTP {upload_url_response.status_code}: "
            f"{upload_url_response.text[:200]!r}"
        )
        raise GameSheetError(_err_msg)
    upload_data: dict[str, Any] = upload_url_response.json()
    if upload_data.get("status") != "success":
        _err_msg = f"Failed to get upload URL: {upload_data}"
        raise GameSheetError(_err_msg)
    upload_url: str = upload_data["data"]["uploadURL"]
    image_id: str = upload_data["data"]["id"]
    with image_file_path.open("rb") as f:
        upload_response = session.post(
            upload_url,
            files={"file": (image_file_path.name, f, mime_type)},
        )
    if upload_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url} returned HTTP {upload_response.status_code}: "
            f"{upload_response.text[:200]!r}"
        )
        raise GameSheetError(_err_msg)
    upload_result: dict[str, Any] = upload_response.json()
    if not upload_result.get("success"):
        _err_msg = f"Failed to upload {image_type}: {upload_result}"
        raise GameSheetError(_err_msg)
    return f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/{image_id}"
