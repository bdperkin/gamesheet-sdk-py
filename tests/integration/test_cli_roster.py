# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Integration tests for roster CLI commands."""

from __future__ import annotations

from pathlib import Path
import tempfile

import responses

# Explicit import for coverage tracking of dynamically-loaded Click commands
from gamesheet_sdk import DEFAULT_BASE_URL
from gamesheet_sdk.cli import main
from tests.helpers import (
    SEASON_ID,
    jsonapi_payload,
)

_BASE = DEFAULT_BASE_URL
_SEASON_ID = "15020"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"
_TOKEN_PATH = Path(tempfile.gettempdir()) / ".gamesheet" / "access_token"


def _mock_token() -> None:
    """Create a mock access token file."""
    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_PATH.write_text("mock-token")


def _cleanup_token() -> None:
    """Remove mock token file."""
    if _TOKEN_PATH.exists():
        _TOKEN_PATH.unlink()


@responses.activate
def test_roster_players_list_json_format() -> None:
    """Test roster players list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    result = main(
        ["roster", "--season-id", _SEASON_ID, "players", "list", "-F", "json"],
    )
    assert not result
    _cleanup_token()


@responses.activate
def test_roster_coaches_list_json_format() -> None:
    """Test roster coaches list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=jsonapi_payload([]),
        status=200,
    )
    result = main(
        ["roster", "--season-id", _SEASON_ID, "coaches", "list", "-F", "json"],
    )
    assert not result
    _cleanup_token()
