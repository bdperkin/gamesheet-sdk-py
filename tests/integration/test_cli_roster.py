# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Integration tests for roster CLI commands."""

from __future__ import annotations

from pathlib import Path
import tempfile

import responses

from gamesheet_sdk import DEFAULT_BASE_URL
from gamesheet_sdk.cli import main

# Explicit import for coverage tracking of dynamically-loaded Click commands
from tests.helpers import (
    SEASON_ID,
    jsonapi_payload,
)

_BASE = DEFAULT_BASE_URL
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{SEASON_ID}/coaches"
_TOKEN_DIR = Path(tempfile.gettempdir()) / ".gamesheet"
_ACCESS_TOKEN_PATH = _TOKEN_DIR / "access_token"
_REFRESH_TOKEN_PATH = _TOKEN_DIR / "refresh_token"


def _mock_tokens() -> None:
    """Create mock access and refresh token files."""
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    _ACCESS_TOKEN_PATH.write_text("mock-access-token")
    _REFRESH_TOKEN_PATH.write_text("mock-refresh-token")


def _cleanup_tokens() -> None:
    """Remove mock token files."""
    if _ACCESS_TOKEN_PATH.exists():
        _ACCESS_TOKEN_PATH.unlink()
    if _REFRESH_TOKEN_PATH.exists():
        _REFRESH_TOKEN_PATH.unlink()


@responses.activate
def test_roster_players_list_json_format() -> None:
    """Test roster players list with JSON output."""
    _mock_tokens()
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    result = main(
        ["roster", "--season-id", SEASON_ID, "players", "list", "-F", "json"],
    )
    assert not result
    _cleanup_tokens()


@responses.activate
def test_roster_coaches_list_json_format() -> None:
    """Test roster coaches list with JSON output."""
    _mock_tokens()
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    result = main(
        ["roster", "--season-id", SEASON_ID, "coaches", "list", "-F", "json"],
    )
    assert not result
    _cleanup_tokens()
