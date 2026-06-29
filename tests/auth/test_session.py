# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for AuthenticatedSession auto-refresh behavior."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticatedSession, Config
from gamesheet_sdk.auth.constants import REFRESH_URL


# ---------- AuthenticatedSession -----------------------------------------
@responses.activate
def test_authenticated_session_passthrough_when_200(config: Config) -> None:
    """Test that AuthenticatedSession passes through successful 200 responses."""
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )
    with AuthenticatedSession(config, access_token="A1", refresh_token="R1") as session:
        resp = session.get("/x")
    assert resp.status_code == 200
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer A1"


@responses.activate
def test_authenticated_session_refreshes_and_retries_on_401(config: Config) -> None:
    """Test that AuthenticatedSession refreshes token and retries on 401."""
    # 1st: 401, refresh, 2nd: 200 with the new bearer.
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"access": "A2", "refresh": "R2", "roles": "Rol2"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )
    persisted: list[dict[str, str]] = []
    with AuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="R1",
        on_refresh=persisted.append,
    ) as session:
        resp = session.get("/x")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert persisted == [{"access": "A2", "refresh": "R2", "roles": "Rol2"}]
    # Three calls: original GET, refresh, retried GET.
    assert len(responses.calls) == 3
    assert responses.calls[0].request.headers["Authorization"] == "Bearer A1"
    assert responses.calls[1].request.url == REFRESH_URL
    assert responses.calls[1].request.headers["Authorization"] == "Bearer R1"
    assert responses.calls[2].request.headers["Authorization"] == "Bearer A2"


@responses.activate
def test_authenticated_session_propagates_401_when_refresh_fails(
    config: Config,
) -> None:
    """Test that 401 is propagated when token refresh fails."""
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(responses.POST, REFRESH_URL, status=401, json={"errors": [{}]})
    with AuthenticatedSession(
        config,
        access_token="A1",
        refresh_token="DEAD",
    ) as session:
        resp = session.get("/x")
    # Original 401 surfaces to the caller; no further retries.
    assert resp.status_code == 401
    assert len(responses.calls) == 2


@responses.activate
def test_authenticated_session_does_not_retry_when_refresh_returns_500(
    config: Config,
) -> None:
    """Test that request is not retried when refresh returns 500."""
    responses.add(responses.GET, "https://test.example/x", status=401)
    responses.add(responses.POST, REFRESH_URL, status=500, body="boom")
    with AuthenticatedSession(config, access_token="A1", refresh_token="R1") as session:
        resp = session.get("/x")
    assert resp.status_code == 401  # original surfaces
    assert len(responses.calls) == 2  # no retry of /x


@responses.activate
def test_authenticated_session_post_also_triggers_refresh(config: Config) -> None:
    """Test that POST requests also trigger refresh on 401."""
    responses.add(responses.POST, "https://test.example/mutate", status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"access": "A2", "refresh": "R2", "roles": "Rol2"},
        status=200,
    )
    responses.add(responses.POST, "https://test.example/mutate", status=201)
    with AuthenticatedSession(config, access_token="A1", refresh_token="R1") as session:
        resp = session.post("/mutate")
    assert resp.status_code == 201


@responses.activate
def test_authenticated_session_handles_on_refresh_oserror(
    config: Config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that OSError in on_refresh callback is logged but doesn't crash."""
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"access": "A2", "refresh": "R2", "roles": "Rol2"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://test.example/x",
        json={"ok": True},
        status=200,
    )

    def failing_callback(_tokens: dict[str, str]) -> None:
        msg = "Disk full"
        raise OSError(msg)

    with (
        caplog.at_level("WARNING"),
        AuthenticatedSession(
            config,
            access_token="A1",
            refresh_token="R1",
            on_refresh=failing_callback,
        ) as session,
    ):
        resp = session.get("/x")
    # Refresh still succeeded, request was retried despite callback failure
    assert resp.status_code == 200
    assert "on_refresh callback failed to persist" in caplog.text
    assert "Disk full" in caplog.text


# ---------- token response capture (line 131) -------------------------------
