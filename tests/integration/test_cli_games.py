# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Integration tests for games CLI commands."""

from __future__ import annotations

from unittest.mock import patch

import responses

# Explicit import for coverage tracking of dynamically-loaded Click commands
from gamesheet_sdk import BFF_API_BASE_URL
from gamesheet_sdk.cli import main
from tests.helpers import SEASON_ID

_BFF_BASE = BFF_API_BASE_URL
_SEASON_ID = SEASON_ID
_ENDPOINT = f"{_BFF_BASE}/games-list/v1"


def _bff_response(games: list[dict[str, object]]) -> dict[str, object]:
    """Build a BFF API response."""
    return {"status": "success", "data": games}


@responses.activate
def test_games_completed_list_json_format() -> None:
    """Test games completed list with JSON output."""
    with (
        patch(
            "gamesheet_sdk.cli.helpers.load_access_token",
            return_value="mock-access-token",
        ),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="mock-refresh-token",
        ),
    ):
        responses.add(
            responses.GET,
            _ENDPOINT,
            json=_bff_response([]),
            status=200,
        )
        result = main(
            ["games", "--season-id", _SEASON_ID, "completed", "list", "-F", "json"],
        )
        assert not result


@responses.activate
def test_games_scheduled_list_json_format() -> None:
    """Test games scheduled list with JSON output."""
    with (
        patch(
            "gamesheet_sdk.cli.helpers.load_access_token",
            return_value="mock-access-token",
        ),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="mock-refresh-token",
        ),
    ):
        responses.add(
            responses.GET,
            _ENDPOINT,
            json=_bff_response([]),
            status=200,
        )
        result = main(
            ["games", "--season-id", _SEASON_ID, "scheduled", "list", "-F", "json"],
        )
        assert not result


@responses.activate
def test_games_brackets_list_json_format() -> None:
    """Test games brackets list returns not implemented error."""
    with (
        patch(
            "gamesheet_sdk.cli.helpers.load_access_token",
            return_value="mock-access-token",
        ),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="mock-refresh-token",
        ),
    ):
        # Brackets list is not implemented yet - should return exit code 1
        result = main(
            ["games", "--season-id", _SEASON_ID, "brackets", "list", "-F", "json"],
        )
        assert result == 1  # Not implemented
