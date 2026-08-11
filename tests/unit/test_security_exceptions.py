# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for security file utilities and exception classes."""

from __future__ import annotations

import copy
import os
from typing import TYPE_CHECKING

from gamesheet_sdk.common.exceptions import (
    AuthenticationError,
    GameSheetAPIError,
    GameSheetError,
    GameSheetNotFoundError,
    GameSheetPermissionError,
    GameSheetRateLimitError,
    GameSheetValidationError,
)
from gamesheet_sdk.common.security import write_secure_text

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_write_secure_text_creates_file_and_parent_dirs(tmp_path: Path) -> None:
    """Test that write_secure_text writes file content and creates parent dirs."""
    target_file = tmp_path / "sub_dir" / "secret.json"
    content = '{"key": "value"}'

    write_secure_text(target_file, content)

    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == content

    if os.name == "posix":
        # Verify 0600 file permissions
        file_mode = target_file.stat().st_mode & 0o777
        assert file_mode == 0o600
        # Verify 0700 dir permissions
        dir_mode = target_file.parent.stat().st_mode & 0o777
        assert dir_mode == 0o700


def test_write_secure_text_skips_chmod_on_non_posix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the directory chmod is skipped when os.name is not 'posix'."""
    # ``security`` reads ``os.name`` at call time from this same module object.
    monkeypatch.setattr(os, "name", "nt")
    target_file = tmp_path / "win_dir" / "secret.json"

    write_secure_text(target_file, "data")

    assert target_file.read_text(encoding="utf-8") == "data"


def test_exception_hierarchy() -> None:
    """Test inheritance relationship for structured exception classes."""
    api_err = GameSheetAPIError(
        "API error",
        status_code=500,
        endpoint="/api/test",
        response_body="Internal Error",
    )
    assert isinstance(api_err, GameSheetError)
    assert api_err.status_code == 500
    assert api_err.endpoint == "/api/test"
    assert api_err.response_body == "Internal Error"

    not_found = GameSheetNotFoundError(
        "Not found",
        status_code=404,
        endpoint="/api/item",
    )
    assert isinstance(not_found, GameSheetAPIError)
    assert isinstance(not_found, GameSheetError)
    assert not_found.status_code == 404

    perm_err = GameSheetPermissionError(
        "Forbidden",
        status_code=403,
        endpoint="/api/secret",
    )
    assert isinstance(perm_err, AuthenticationError)
    assert isinstance(perm_err, GameSheetAPIError)
    assert isinstance(perm_err, GameSheetError)
    assert perm_err.status_code == 403

    rate_limit = GameSheetRateLimitError(
        "Rate limited",
        status_code=429,
        endpoint="/api/fast",
    )
    assert isinstance(rate_limit, GameSheetAPIError)
    assert isinstance(rate_limit, GameSheetError)

    val_err = GameSheetValidationError("Invalid param")
    assert isinstance(val_err, GameSheetError)


def test_api_error_str_and_copy_roundtrip() -> None:
    """Structured API errors render only their message and survive ``copy.copy()``."""
    err = GameSheetAPIError(
        "API error",
        status_code=500,
        endpoint="/api/test",
        response_body="Internal Error",
    )
    assert str(err) == "API error"

    restored = copy.copy(err)
    assert str(restored) == "API error"
    assert restored.status_code == 500
    assert restored.endpoint == "/api/test"
    assert restored.response_body == "Internal Error"
