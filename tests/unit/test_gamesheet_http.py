# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for gamesheet_sdk.shared.gamesheet_http module."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import Mock

import pytest

from gamesheet_sdk.common.exceptions import (
    AuthenticationError,
    GameSheetError,
    GameSheetPermissionError,
    GameSheetRateLimitError,
)
from gamesheet_sdk.common.shared.gamesheet_http import (
    handle_response,
    handle_season_scoped_response,
)


def test_handle_response_passes_on_200() -> None:
    """Test that handle_response does nothing for successful 200 responses."""
    response = Mock()
    response.status_code = 200
    # Should not raise any exception
    handle_response(response, "/api/test", "GET test")


def test_handle_response_raises_on_401() -> None:
    """Test that handle_response raises AuthenticationError for 401."""
    response = Mock()
    response.status_code = 401
    with pytest.raises(
        AuthenticationError,
        match=(
            r"Access token rejected \(HTTP 401\) for GET test\. "
            r"Use `gamesheet-admin login` to authenticate\."
        ),
    ):
        handle_response(response, "/api/test", "GET test")


def test_handle_response_raises_on_403() -> None:
    """Test that handle_response raises AuthenticationError for 403."""
    response = Mock()
    response.status_code = 403
    with pytest.raises(
        AuthenticationError,
        match=(
            r"Access forbidden \(HTTP 403\) for GET test\. "
            r"Your session cookies may have expired\. "
            r"Use `gamesheet-admin login` to re-authenticate\."
        ),
    ):
        handle_response(response, "/api/test", "GET test")


def test_handle_response_raises_on_404() -> None:
    """Test that handle_response raises GameSheetError for 404."""
    response = Mock()
    response.status_code = 404
    with pytest.raises(
        GameSheetError,
        match=r"Resource not found \(HTTP 404\) for /api/test",
    ):
        handle_response(response, "/api/test", "GET test")


def test_handle_response_raises_on_500() -> None:
    """Test that handle_response raises GameSheetError for 500."""
    response = Mock()
    response.status_code = 500
    response.text = "Internal Server Error"
    with pytest.raises(
        GameSheetError,
        match=r"GET TEST /api/test returned HTTP 500: Internal Server Error",
    ):
        handle_response(response, "/api/test", "GET test")


def test_handle_response_uses_default_context_msg() -> None:
    """Test that handle_response uses default context_msg when not provided."""
    response = Mock()
    response.status_code = 401
    with pytest.raises(
        AuthenticationError,
        match=r"Access token rejected \(HTTP 401\) for request\.",
    ):
        handle_response(response, "/api/test")


def test_handle_response_403_includes_cookie_expiry_message() -> None:
    """Test that 403 error message mentions cookie expiry."""
    response = Mock()
    response.status_code = 403
    with pytest.raises(
        AuthenticationError,
        match=r"session cookies may have expired",
    ):
        handle_response(response, "/api/test", "POST data")


def test_handle_response_raises_on_429() -> None:
    """Test that handle_response raises GameSheetRateLimitError for 429."""
    response = Mock()
    response.status_code = 429
    response.text = "Too Many Requests"
    with pytest.raises(
        GameSheetRateLimitError,
        match=r"Rate limit exceeded \(HTTP 429\) for /api/test",
    ) as exc_info:
        handle_response(response, "/api/test", "GET test")

    assert exc_info.value.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert exc_info.value.endpoint == "/api/test"
    assert exc_info.value.response_body == "Too Many Requests"


def test_handle_season_scoped_response_raises_on_403() -> None:
    """Test that handle_season_scoped_response raises GameSheetPermissionError for 403."""
    response = Mock()
    response.status_code = 403
    response.text = "Forbidden"
    with pytest.raises(
        GameSheetPermissionError,
        match=r"Access forbidden \(HTTP 403\) for POST referee",
    ) as exc_info:
        handle_season_scoped_response(
            response,
            "/api/seasons/1/referees",
            "1",
            method="POST",
            resource_type="referee",
        )

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.endpoint == "/api/seasons/1/referees"
