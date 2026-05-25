"""Tests for :mod:`gamesheet_sdk.auth`."""

# pylint: disable=redefined-outer-name,protected-access

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk import AuthenticationError, BrowserSession, Config, login
from gamesheet_sdk.auth import LOGIN_PATH, POST_LOGIN_PATH


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

    # Two navigations: to the login form, then to the post-login destination.
    assert fake_browser_session.goto.call_count == 2
    fake_browser_session.goto.assert_any_call(LOGIN_PATH, wait_until="load")
    fake_browser_session.goto.assert_any_call(
        POST_LOGIN_PATH, wait_until="networkidle", timeout=30_000
    )
    page.click.assert_called_once_with("button[type=submit]")


def test_login_post_login_path_can_be_disabled(
    fake_browser_session: MagicMock,
) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(
        fake_browser_session,
        email="a@b.c",
        password="x",
        post_login_path=None,
    )

    # Only the navigation to the login form should have happened.
    fake_browser_session.goto.assert_called_once_with(LOGIN_PATH, wait_until="load")


def test_login_custom_post_login_path(fake_browser_session: MagicMock) -> None:
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(
        fake_browser_session,
        email="a@b.c",
        password="x",
        post_login_path="/dashboard",
    )

    fake_browser_session.goto.assert_any_call(
        "/dashboard", wait_until="networkidle", timeout=30_000
    )


def test_login_post_login_navigation_timeout_is_swallowed(
    fake_browser_session: MagicMock,
) -> None:
    """networkidle never firing should NOT fail an already-successful auth."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    def goto_side_effect(path: str, **kwargs: Any) -> Any:
        # The post-login navigation is the one that asks for networkidle;
        # the initial form-load navigation uses wait_until="load".
        if kwargs.get("wait_until") == "networkidle":
            raise PlaywrightTimeoutError("networkidle never fired")
        del path
        return page

    fake_browser_session.goto.side_effect = goto_side_effect

    # Must not raise; auth already succeeded by this point.
    login(fake_browser_session, email="a@b.c", password="x")


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


def test_login_form_detection_uses_fixed_timeout(
    fake_browser_session: MagicMock,
) -> None:
    """The probe for the login form uses a fixed short timeout (the user's
    `timeout=` parameter only governs the auth-response wait loop)."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    login(fake_browser_session, email="a@b.c", password="x", timeout=2.0)

    page.wait_for_selector.assert_called_once_with("#email", timeout=5_000)


def test_login_short_circuits_when_saved_session_already_authenticates(
    fake_browser_session: MagicMock,
) -> None:
    """If the unauth landing page renders no login form, the saved storage
    state is already authenticating this user; login() should return cleanly
    without filling or submitting anything."""
    page = fake_browser_session.goto.return_value
    page.wait_for_selector.side_effect = PlaywrightTimeoutError("no #email")

    login(fake_browser_session, email="a@b.c", password="x")

    page.fill.assert_not_called()
    page.click.assert_not_called()
    # Post-login navigation still runs so the saved state gets re-flushed.
    fake_browser_session.goto.assert_any_call(
        POST_LOGIN_PATH, wait_until="networkidle", timeout=30_000
    )


def test_login_short_circuit_respects_post_login_path_disable(
    fake_browser_session: MagicMock,
) -> None:
    """post_login_path=None still applies on the short-circuit path."""
    page = fake_browser_session.goto.return_value
    page.wait_for_selector.side_effect = PlaywrightTimeoutError("no #email")

    login(
        fake_browser_session,
        email="a@b.c",
        password="x",
        post_login_path=None,
    )

    # Only the initial form-probe navigation; no settle.
    fake_browser_session.goto.assert_called_once_with(LOGIN_PATH, wait_until="load")
