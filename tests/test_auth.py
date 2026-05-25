"""Tests for :mod:`gamesheet_sdk.auth`."""

# pylint: disable=redefined-outer-name,protected-access

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from gamesheet_sdk import AuthenticationError, BrowserSession, Config, login
from gamesheet_sdk.auth import LOGIN_PATH


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


_FIREBASE_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=X"
)
_TOKEN_URL = "https://gamesheet.app/api/token"


@pytest.fixture
def fake_browser_session(config: Config) -> MagicMock:
    """A BrowserSession-spec'd mock whose page captures a response listener.

    The page's ``click`` is wired to fire whatever responses the test
    has staged via the ``staged_responses`` attribute; the test sets
    that list to control what arrives after submit.
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
    page.wait_for_timeout.side_effect = lambda ms: None
    return sess


# ---------- credential validation ----------------------------------------


def test_login_missing_email_raises(fake_browser_session: MagicMock) -> None:
    with pytest.raises(AuthenticationError, match="email and password"):
        login(fake_browser_session, password="hunter2")
    fake_browser_session.goto.assert_not_called()


def test_login_missing_password_raises(fake_browser_session: MagicMock) -> None:
    with pytest.raises(AuthenticationError, match="email and password"):
        login(fake_browser_session, email="alice@example.com")
    fake_browser_session.goto.assert_not_called()


def test_login_empty_string_credentials_raise(
    fake_browser_session: MagicMock,
) -> None:
    with pytest.raises(AuthenticationError, match="email and password"):
        login(fake_browser_session, email="", password="")
    fake_browser_session.goto.assert_not_called()


def test_login_reads_credentials_from_config(
    fake_browser_session: MagicMock,
) -> None:
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password="s3cret",
    )
    fake_browser_session.goto.return_value.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]
    # Re-wire the click side effect to use the new page mock.
    page = fake_browser_session.goto.return_value
    listeners: dict[str, Any] = {}

    def register(ev: str, cb: Any) -> None:
        listeners[ev] = cb

    def click(_selector: str) -> None:
        for response in page.staged_responses:
            listeners["response"](response)

    page.on.side_effect = register
    page.click.side_effect = click

    login(fake_browser_session)

    page.fill.assert_any_call("#email", "bob@example.com")
    page.fill.assert_any_call("#password", "s3cret")


def test_login_args_override_config(fake_browser_session: MagicMock) -> None:
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password="s3cret",
    )
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(fake_browser_session, email="alice@example.com", password="other")

    page.fill.assert_any_call("#email", "alice@example.com")
    page.fill.assert_any_call("#password", "other")


# ---------- happy path ---------------------------------------------------


def test_login_succeeds_when_firebase_and_token_both_200(
    fake_browser_session: MagicMock,
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(fake_browser_session, email="a@b.c", password="x")

    fake_browser_session.goto.assert_called_once_with(LOGIN_PATH, wait_until="load")
    page.click.assert_called_once_with("button[type=submit]")


# ---------- firebase failures --------------------------------------------


@pytest.mark.parametrize(
    "firebase_message",
    [
        "EMAIL_NOT_FOUND",
        "INVALID_LOGIN_CREDENTIALS",
        "USER_DISABLED",
        "TOO_MANY_ATTEMPTS_TRY_LATER",
    ],
)
def test_login_surfaces_firebase_error_code(
    fake_browser_session: MagicMock, firebase_message: str
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(
            _FIREBASE_URL,
            400,
            {"error": {"code": 400, "message": firebase_message}},
        ),
    ]

    with pytest.raises(AuthenticationError) as exc_info:
        login(fake_browser_session, email="a@b.c", password="bad")

    assert firebase_message in str(exc_info.value)
    assert "Firebase" in str(exc_info.value)


def test_login_firebase_failure_without_parseable_body(
    fake_browser_session: MagicMock,
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [_make_response(_FIREBASE_URL, 500, body=None)]

    with pytest.raises(AuthenticationError) as exc_info:
        login(fake_browser_session, email="a@b.c", password="x")

    assert "HTTP 500" in str(exc_info.value)


# ---------- token-exchange failures --------------------------------------


def test_login_token_exchange_failure_raises(
    fake_browser_session: MagicMock,
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 401, {}),
    ]

    with pytest.raises(AuthenticationError, match="token exchange failed"):
        login(fake_browser_session, email="a@b.c", password="x")


# ---------- timeout / silence --------------------------------------------


def test_login_no_responses_times_out(fake_browser_session: MagicMock) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = []  # nothing arrives

    with pytest.raises(AuthenticationError, match="did not complete"):
        login(fake_browser_session, email="a@b.c", password="x", timeout=0.01)


def test_login_custom_timeout_applies_to_wait_for_selector(
    fake_browser_session: MagicMock,
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(fake_browser_session, email="a@b.c", password="x", timeout=2.0)

    page.wait_for_selector.assert_called_once_with("#email", timeout=2000)
