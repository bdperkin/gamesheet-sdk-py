# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared pytest fixtures for auth tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from gamesheet_sdk import BrowserSession, Config
from gamesheet_sdk.common.auth.constants import FIREBASE_AUTH_URL, TOKEN_EXCHANGE_URL

__all__ = ["_make_response", "_FIREBASE_URL", "_TOKEN_URL", "fake_browser_session"]


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
_TOKEN_URL = TOKEN_EXCHANGE_URL


@pytest.fixture
def fake_browser_session(config: Config) -> MagicMock:
    """Build a BrowserSession-spec'd mock whose page captures a response listener.

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

    def click(*__args: Any, **__kwargs: Any) -> None:
        for response in page.staged_responses:
            listeners["response"](response)

    page.click.side_effect = click
    # Make wait_for_timeout actually advance the clock a little so loops
    # don't spin entirely in zero real time.
    page.wait_for_timeout.side_effect = lambda __ms__: None
    return sess
