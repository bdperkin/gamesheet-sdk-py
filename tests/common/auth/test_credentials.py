# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for shared credential resolution helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from gamesheet_sdk import AuthenticationError, Config
from gamesheet_sdk.common.auth.credentials import resolve_email, resolve_password

if TYPE_CHECKING:
    # Imported for typing only, and referenced as a string in cast() below:
    # flake8-type-checking's TC006 requires cast() annotations to be string
    # literals, so CodeQL reports this as py/unused-import. Do not remove it.
    from pydantic import SecretStr


# ---------- resolve_email ------------------------------------------------


def test_resolve_email_explicit(config: Config) -> None:
    """Test that an explicit email is returned as-is."""
    assert resolve_email(config, "alice@example.com") == "alice@example.com"


def test_resolve_email_from_config() -> None:
    """Test that email falls back to config.username."""
    cfg = Config(base_url="https://test.example", username="bob@example.com")
    assert resolve_email(cfg, None) == "bob@example.com"


def test_resolve_email_missing_raises(config: Config) -> None:
    """Test that missing email raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match="requires an email"):
        resolve_email(config, None)


def test_resolve_email_empty_string_raises(config: Config) -> None:
    """Test that empty string email raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match="requires an email"):
        resolve_email(config, "")


# ---------- resolve_password ---------------------------------------------


def test_resolve_password_explicit(config: Config) -> None:
    """Test that an explicit password is returned as-is."""
    assert resolve_password(config, "hunter2") == "hunter2"


def test_resolve_password_from_config() -> None:
    """Test that password falls back to config.password."""
    cfg = Config(
        base_url="https://test.example",
        password=cast("SecretStr", "s3cret"),
    )
    assert resolve_password(cfg, None) == "s3cret"


def test_resolve_password_missing_raises(config: Config) -> None:
    """Test that missing password raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match="requires a password"):
        resolve_password(config, None)


def test_resolve_password_empty_string_raises(config: Config) -> None:
    """Test that empty string password raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match="requires a password"):
        resolve_password(config, "")
