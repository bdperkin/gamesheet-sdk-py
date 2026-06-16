"""Tests for AuthenticatedSession auto-refresh behavior."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import responses

from gamesheet_sdk import (
    AuthenticatedSession,
    BrowserSession,
    Config,
)
from gamesheet_sdk.auth.constants import FIREBASE_AUTH_URL, REFRESH_URL, TOKEN_EXCHANGE_URL


def _make_response(url: str, status: int, body: Any = None) -> MagicMock:
    """Build a MagicMock that quacks like a playwright Response."""
    r = MagicMock(name=f"response[{url}]")
    r.url = url
    r.status = status
    if body is not None:

        r.json.return_value = body
    else:
        r.json.side_effect = ValueError("no body")
    return r


_FIREBASE_URL = f"{FIREBASE_AUTH_URL}?key=X"
_TOKEN_URL = TOKEN_EXCHANGE_URL  # nosec B105


@pytest.fixture
def fake_browser_session(config: Config) -> MagicMock:
    """A BrowserSession-spec'd mock whose page captures a response listener.

    The page's ``click`` is wired to fire whatever responses the test has staged via the ``staged_responses``
    attribute; the test sets that list to control what arrives after submit.
    """
    sess = MagicMock(spec=BrowserSession)
    sess.config = config
    page = MagicMock(name="page")
    sess.goto.return_value = page
    # Capture the response callback the production code registers.
    listeners: dict[str, Any] = {}

    def register(event: str, callback: Any) -> None:

        listeners[event] = callback

    page.on.side_effect = register
    # Default: no staged responses (simulates timeout).
    page.staged_responses = []

    def click(_selector: str) -> None:

        for response in page.staged_responses:

            listeners["response"](response)

    page.click.side_effect = click
    # Make wait_for_timeout actually advance the clock a little so loops
    # don't spin entirely in zero real time.
    page.wait_for_timeout.side_effect = lambda _ms: None
    return sess


# ---------- AuthenticatedSession -----------------------------------------


@responses.activate
def test_authenticated_session_passthrough_when_200(config: Config) -> None:

    responses.add(responses.GET, "https://test.example/x", json={"ok": True}, status=200)
    with AuthenticatedSession(config, access_token="A1", refresh_token="R1") as session:
        resp = session.get("/x")
    assert resp.status_code == 200
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer A1"


@responses.activate
def test_authenticated_session_refreshes_and_retries_on_401(config: Config) -> None:

    # 1st: 401, refresh, 2nd: 200 with the new bearer.
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(
        responses.POST,
        REFRESH_URL,
        json={"access": "A2", "refresh": "R2", "roles": "Rol2"},
        status=200,
    )
    responses.add(responses.GET, "https://test.example/x", json={"ok": True}, status=200)
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
    responses.add(responses.GET, "https://test.example/x", json={"err": 1}, status=401)
    responses.add(responses.POST, REFRESH_URL, status=401, json={"errors": [{}]})
    with AuthenticatedSession(config, access_token="A1", refresh_token="DEAD") as session:
        resp = session.get("/x")
    # Original 401 surfaces to the caller; no further retries.
    assert resp.status_code == 401
    assert len(responses.calls) == 2


@responses.activate
def test_authenticated_session_does_not_retry_when_refresh_returns_500(
    config: Config,
) -> None:
    responses.add(responses.GET, "https://test.example/x", status=401)
    responses.add(responses.POST, REFRESH_URL, status=500, body="boom")
    with AuthenticatedSession(config, access_token="A1", refresh_token="R1") as session:
        resp = session.get("/x")
    assert resp.status_code == 401  # original surfaces
    assert len(responses.calls) == 2  # no retry of /x


@responses.activate
def test_authenticated_session_post_also_triggers_refresh(config: Config) -> None:
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


# ---------- token response capture (line 131) -------------------------------
