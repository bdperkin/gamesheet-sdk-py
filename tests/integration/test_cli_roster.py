# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Integration tests for roster CLI commands."""

from __future__ import annotations

from unittest.mock import patch

import responses

from gamesheet_sdk import DEFAULT_BASE_URL
from gamesheet_sdk.cli import main

# Explicit import for coverage tracking of dynamically-loaded Click commands
from tests.helpers import SEASON_ID, jsonapi_payload

_BASE = DEFAULT_BASE_URL
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{SEASON_ID}/coaches"


@responses.activate
def test_roster_players_list_json_format() -> None:
    """Test roster players list with JSON output."""
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
            _PLAYERS_ENDPOINT,
            json=jsonapi_payload([]),
            status=200,
        )
        result = main(
            ["roster", "--season-id", SEASON_ID, "players", "list", "-F", "json"],
        )
        assert not result


@responses.activate
def test_roster_coaches_list_json_format() -> None:
    """Test roster coaches list with JSON output."""
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
            _COACHES_ENDPOINT,
            json=jsonapi_payload([]),
            status=200,
        )
        result = main(
            ["roster", "--season-id", SEASON_ID, "coaches", "list", "-F", "json"],
        )
        assert not result
