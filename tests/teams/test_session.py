# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for TeamsAuthenticatedSession auto-refresh behavior."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import responses

from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import TEAMS_API_GATEWAY, TEAMS_REFRESH_PATH
from tests.fixtures.constants import TEST_ERROR_DISK_FULL

if TYPE_CHECKING:
    import pytest

    from gamesheet_sdk import Config

TEAMS_REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"


@responses.activate
def test_teams_session_passthrough_when_200(config: Config) -> None:
    """Test that TeamsAuthenticatedSession passes through successful 200 responses."""
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
    ) as session:
        resp = session.get("/x")

    assert resp.status_code == HTTPStatus.OK
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer A1"


@responses.activate
def test_teams_session_refreshes_and_retries_on_401(config: Config) -> None:
    """Test that TeamsAuthenticatedSession refreshes token and retries on 401."""
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(
        responses.POST,
        TEAMS_REFRESH_URL,
        json={"access": "A2", "refresh": "R2"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )
    persisted: list[dict[str, str]] = []
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
        on_refresh=persisted.append,
    ) as session:
        resp = session.get("/x")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"ok": True}
    assert persisted == [{"access": "A2", "refresh": "R2"}]
    assert len(responses.calls) == 3
    assert responses.calls[0].request.headers["Authorization"] == "Bearer A1"
    assert responses.calls[1].request.url == TEAMS_REFRESH_URL
    assert responses.calls[1].request.headers["Authorization"] == "Bearer R1"
    assert responses.calls[2].request.headers["Authorization"] == "Bearer A2"


@responses.activate
def test_teams_session_propagates_401_when_refresh_fails(config: Config) -> None:
    """Test that 401 is propagated when token refresh fails."""
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(responses.POST, TEAMS_REFRESH_URL, status=401, json={"errors": [{}]})
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="DEAD",
    ) as session:
        resp = session.get("/x")

    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert len(responses.calls) == 2


@responses.activate
def test_teams_session_does_not_retry_when_refresh_returns_500(
    config: Config,
) -> None:
    """Test that request is not retried when refresh returns 500."""
    responses.add(responses.GET, "https://test.example/x", status=401)
    responses.add(responses.POST, TEAMS_REFRESH_URL, status=500, body="boom")
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
    ) as session:
        resp = session.get("/x")

    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert len(responses.calls) == 2


@responses.activate
def test_teams_session_post_also_triggers_refresh(config: Config) -> None:
    """Test that POST requests also trigger refresh on 401."""
    responses.add(responses.POST, "https://test.example/mutate", status=401)
    responses.add(
        responses.POST,
        TEAMS_REFRESH_URL,
        json={"access": "A2", "refresh": "R2"},
        status=200,
    )
    responses.add(responses.POST, "https://test.example/mutate", status=201)
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
    ) as session:
        resp = session.post("/mutate")

    assert resp.status_code == HTTPStatus.CREATED


@responses.activate
def test_teams_session_handles_on_refresh_oserror(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that OSError in on_refresh callback is logged but doesn't crash."""
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(
        responses.POST,
        TEAMS_REFRESH_URL,
        json={"access": "A2", "refresh": "R2"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )

    def failing_callback(_tokens: dict[str, str]) -> None:
        raise OSError(TEST_ERROR_DISK_FULL)

    with (
        caplog.at_level("WARNING"),
        TeamsAuthenticatedSession(
            config,
            access_token="A1",
            refresh_token="R1",
            on_refresh=failing_callback,
        ) as session,
    ):
        resp = session.get("/x")

    assert resp.status_code == HTTPStatus.OK
    assert "on_refresh callback failed to persist" in caplog.text
    assert TEST_ERROR_DISK_FULL in caplog.text


@responses.activate
def test_teams_session_refreshes_and_retries_on_403(config: Config) -> None:
    """Test that TeamsAuthenticatedSession refreshes token and retries on 403."""
    responses.add(responses.GET, "https://test.example/y", json={"err": 1}, status=403)
    responses.add(
        responses.POST,
        TEAMS_REFRESH_URL,
        json={"access": "A2", "refresh": "R2"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://test.example/y",
        json={"ok": True},
        status=200,
    )
    persisted: list[dict[str, str]] = []
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
        on_refresh=persisted.append,
    ) as session:
        resp = session.get("/y")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"ok": True}
    assert persisted == [{"access": "A2", "refresh": "R2"}]
    assert len(responses.calls) == 3
    assert responses.calls[0].request.headers["Authorization"] == "Bearer A1"
    assert responses.calls[1].request.url == TEAMS_REFRESH_URL
    assert responses.calls[1].request.headers["Authorization"] == "Bearer R1"
    assert responses.calls[2].request.headers["Authorization"] == "Bearer A2"


@responses.activate
def test_teams_session_propagates_403_when_refresh_fails(config: Config) -> None:
    """Test that 403 is propagated when token refresh fails."""
    responses.add(responses.GET, "https://test.example/z", json={"err": 1}, status=403)
    responses.add(responses.POST, TEAMS_REFRESH_URL, status=401, json={"errors": [{}]})
    with TeamsAuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="DEAD",
    ) as session:
        resp = session.get("/z")

    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert len(responses.calls) == 2
