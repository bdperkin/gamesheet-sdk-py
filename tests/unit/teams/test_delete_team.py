# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for delete_team function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    delete_team,
)
from tests.helpers import SEASON_ID, TEST_BASE_URL

_TEAM_ID = "521623"
_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}"


@responses.activate
def test_delete_team_success(config: Config) -> None:
    """Test successful team deletion."""
    responses.add(responses.DELETE, _ENDPOINT, status=204)
    with Session(config) as session:
        session.set_bearer_token("abc")
        delete_team(session, SEASON_ID, _TEAM_ID)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == _ENDPOINT


@responses.activate
def test_delete_team_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(
        responses.DELETE,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            delete_team(session, SEASON_ID, _TEAM_ID)


@responses.activate
def test_delete_team_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError with helpful message."""
    responses.add(responses.DELETE, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Team '.*' not found.*valid team ID.*teams list --season-id",
        ):
            delete_team(session, SEASON_ID, _TEAM_ID)


@responses.activate
def test_delete_team_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.DELETE, _ENDPOINT, status=500, body="Internal error")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            delete_team(session, SEASON_ID, _TEAM_ID)
