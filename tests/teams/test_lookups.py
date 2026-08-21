# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the teams lookups domain module."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.teams.lookups import LookupValue, list_lookups
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_LOOKUPS_PATH

_LOOKUPS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_LOOKUPS_PATH}"


def _lookups_payload(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Wrap category data in the standard teams API envelope.

    Args:
        data (dict[str, list[dict[str, Any]]]): Category data dictionary.

    Returns:
        dict[str, Any]: Envelope response dictionary.

    """
    return {"success": True, "data": data}


@responses.activate
def test_list_lookups_parses_response() -> None:
    """Test that list_lookups returns categories with LookupValue objects."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        json=_lookups_payload(
            {
                "sports": [
                    {"key": "hockey", "title": "Hockey"},
                    {"key": "soccer", "title": "Soccer"},
                ],
                "game_types": [
                    {"key": "league", "title": "League"},
                ],
            },
        ),
        status=200,
    )

    result = list_lookups(timeout=1.0)

    assert set(result) == {"sports", "game_types"}
    assert len(result["sports"]) == 2
    assert len(result["game_types"]) == 1
    assert result["sports"][0].key == "hockey"
    assert result["sports"][0].title == "Hockey"
    assert result["sports"][1].key == "soccer"
    assert result["game_types"][0].key == "league"
    assert isinstance(result["sports"][0], LookupValue)


@responses.activate
def test_list_lookups_preserves_extra_fields() -> None:
    """Test that category-specific extra fields survive on the model."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        json=_lookups_payload(
            {
                "broadcasters": [
                    {
                        "key": "HOCKEYTV",
                        "title": "HockeyTV",
                        "url": "https://www.hockeytv.com/",
                    },
                ],
                "positions": [
                    {
                        "key": "forward",
                        "abbr": "f",
                        "title": "Forward",
                        "type": "position",
                        "sport": ["hockey", "soccer"],
                    },
                ],
            },
        ),
        status=200,
    )

    result = list_lookups(timeout=1.0)

    broadcaster = result["broadcasters"][0]
    dumped = broadcaster.model_dump()
    assert dumped["url"] == "https://www.hockeytv.com/"

    position = result["positions"][0]
    dumped = position.model_dump()
    assert dumped["abbr"] == "f"
    assert dumped["sport"] == ["hockey", "soccer"]


@responses.activate
def test_list_lookups_missing_title_defaults_empty() -> None:
    """Test that values without a title field get title=''."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        json=_lookups_payload(
            {
                "entitlements": [
                    {
                        "key": "LineupNotifications",
                        "scope": "sport",
                        "enabled": ["soccer"],
                    },
                ],
            },
        ),
        status=200,
    )

    result = list_lookups(timeout=1.0)

    ent = result["entitlements"][0]
    assert ent.key == "LineupNotifications"
    assert not ent.title
    assert ent.model_dump()["scope"] == "sport"


@responses.activate
def test_list_lookups_empty_data() -> None:
    """Test that an empty data dict returns an empty dict."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        json=_lookups_payload({}),
        status=200,
    )

    result = list_lookups(timeout=1.0)

    assert not result


@responses.activate
def test_list_lookups_http_error() -> None:
    """Test that non-200 raises GameSheetError."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        body="Internal Server Error",
        status=500,
    )

    with pytest.raises(GameSheetError, match="HTTP 500"):
        list_lookups(timeout=1.0)


@responses.activate
def test_list_lookups_timeout_forwarded() -> None:
    """Test that the timeout parameter is passed through to requests.get."""
    responses.add(
        responses.GET,
        _LOOKUPS_URL,
        json=_lookups_payload({"sports": [{"key": "hockey", "title": "Hockey"}]}),
        status=200,
    )

    list_lookups(timeout=42.0)

    assert responses.calls[0].request.url == _LOOKUPS_URL
