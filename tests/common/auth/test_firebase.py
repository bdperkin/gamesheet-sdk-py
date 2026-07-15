# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for shared Firebase error extraction."""

from __future__ import annotations

from gamesheet_sdk.common.auth.firebase import extract_firebase_error


def test_extract_firebase_error_standard_message() -> None:
    """Test extraction of a standard Firebase error message."""
    body = {"error": {"code": 400, "message": "EMAIL_NOT_FOUND"}}
    assert extract_firebase_error(body, 400) == "EMAIL_NOT_FOUND"


def test_extract_firebase_error_non_dict_error_field() -> None:
    """Test that non-dict error field falls back to HTTP status."""
    body = {"error": "string-not-dict"}
    assert extract_firebase_error(body, 403) == "HTTP 403"


def test_extract_firebase_error_non_string_message() -> None:
    """Test that non-string message field falls back to HTTP status."""
    body = {"error": {"message": 12345}}
    assert extract_firebase_error(body, 403) == "HTTP 403"


def test_extract_firebase_error_missing_message_key() -> None:
    """Test that missing message key falls back to HTTP status."""
    body = {"error": {"code": 400}}
    assert extract_firebase_error(body, 400) == "HTTP 400"


def test_extract_firebase_error_empty_body() -> None:
    """Test that empty body falls back to HTTP status."""
    assert extract_firebase_error({}, 500) == "HTTP 500"


def test_extract_firebase_error_missing_error_key() -> None:
    """Test that missing error key falls back to HTTP status."""
    body = {"other": "data"}
    assert extract_firebase_error(body, 422) == "HTTP 422"
