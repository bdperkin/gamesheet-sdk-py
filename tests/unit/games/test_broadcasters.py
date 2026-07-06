# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for broadcaster-related functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.constants import BFF_API_BASE_URL, DEFAULT_BASE_URL
from gamesheet_sdk.exceptions import GameSheetError
from gamesheet_sdk.games import list_broadcasters, validate_broadcaster_key


@responses.activate
def test_list_broadcasters() -> None:
    """Test list_broadcasters function."""
    responses.add(
        responses.GET,
        f"{BFF_API_BASE_URL}/get-broadcasters",
        json={
            "status": "success",
            "data": [
                {"key": "hockeyTV", "title": "HockeyTV", "url": "https://hockeytv.com"},
                {
                    "key": "flosports",
                    "title": "FloSports",
                    "url": "https://flosports.tv",
                },
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token("test-token")
        broadcasters = list_broadcasters(session)
    assert len(broadcasters) == 2
    assert broadcasters[0].key == "hockeyTV"
    assert broadcasters[1].key == "flosports"


# Lines 517-526: validate_broadcaster_key()


@responses.activate
def test_validate_broadcaster_key_valid() -> None:
    """Test validate_broadcaster_key with valid broadcaster."""
    responses.add(
        responses.GET,
        f"{BFF_API_BASE_URL}/get-broadcasters",
        json={
            "status": "success",
            "data": [
                {"key": "hockeyTV", "title": "HockeyTV", "url": "https://hockeytv.com"},
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token("test-token")
        # Test case-insensitive match
        result = validate_broadcaster_key(session, "hockeytv")
    assert result == "hockeyTV"  # Returns correct casing


@responses.activate
def test_validate_broadcaster_key_empty() -> None:
    """Test validate_broadcaster_key with empty string."""
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        result = validate_broadcaster_key(session, "")
    assert not result


@responses.activate
def test_validate_broadcaster_key_invalid() -> None:
    """Test validate_broadcaster_key with invalid broadcaster."""
    responses.add(
        responses.GET,
        f"{BFF_API_BASE_URL}/get-broadcasters",
        json={
            "status": "success",
            "data": [
                {"key": "hockeyTV", "title": "HockeyTV", "url": "https://hockeytv.com"},
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token("test-token")
        with pytest.raises(GameSheetError, match=r"Invalid broadcaster.*hockeyTV"):
            validate_broadcaster_key(session, "invalid-broadcaster")


# Lines 543-547: list_locations()
