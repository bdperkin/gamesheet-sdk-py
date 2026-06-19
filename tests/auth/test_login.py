"""Tests for login flow and credential handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    login,
)
from gamesheet_sdk.auth.constants import LOGIN_PATH, POST_LOGIN_PATH
from tests.auth.conftest import _FIREBASE_URL, _TOKEN_URL, _make_response

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pydantic import SecretStr


# ---------- credential validation ----------------------------------------
def test_login_missing_email_raises(fake_browser_session: MagicMock) -> None:
    """Test that login raises AuthenticationError when email is missing."""
    with pytest.raises(AuthenticationError, match="requires an email"):
        login(fake_browser_session, password="hunter2")
    fake_browser_session.goto.assert_not_called()


def test_login_missing_password_raises(fake_browser_session: MagicMock) -> None:
    """Test that login raises AuthenticationError when password is missing."""
    with pytest.raises(AuthenticationError, match="requires a password"):
        login(fake_browser_session, email="alice@example.com")
    fake_browser_session.goto.assert_not_called()


def test_login_empty_string_credentials_raise(
    fake_browser_session: MagicMock,
) -> None:
    """Test that login raises AuthenticationError for empty string credentials."""
    # Empty email is rejected before the (also empty) password is ever inspected.
    with pytest.raises(AuthenticationError, match="requires an email"):
        login(fake_browser_session, email="", password="")
    fake_browser_session.goto.assert_not_called()


def test_login_reads_credentials_from_config(
    fake_browser_session: MagicMock,
) -> None:
    """Test that login reads email and password from config when not provided."""
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password=cast("SecretStr", "s3cret"),
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

    def click(__selector: str) -> None:  # noqa: U101
        for response in page.staged_responses:
            listeners["response"](response)

    page.on.side_effect = register
    page.click.side_effect = click
    login(fake_browser_session)
    page.fill.assert_any_call("#email", "bob@example.com")
    page.fill.assert_any_call("#password", "s3cret")


def test_login_args_override_config(fake_browser_session: MagicMock) -> None:
    """Test that login arguments override config credentials."""
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password=cast("SecretStr", "s3cret"),
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
    """Test that login succeeds when both Firebase and token exchange return 200."""
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
        POST_LOGIN_PATH,
        wait_until="networkidle",
        timeout=30_000,
    )
    page.click.assert_called_once_with("button[type=submit]")


def test_login_post_login_path_can_be_disabled(
    fake_browser_session: MagicMock,
) -> None:
    """Test that post_login_path=None disables post-login navigation."""
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
    """Test that custom post_login_path is used for post-login navigation."""
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
        "/dashboard",
        wait_until="networkidle",
        timeout=30_000,
    )


def test_login_post_login_navigation_timeout_is_swallowed(
    fake_browser_session: MagicMock,
) -> None:
    """Networkidle never firing should NOT fail an already-successful auth."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]

    def goto_side_effect(path: str, **kwargs: Any) -> Any:
        # The post-login navigation is the one that asks for networkidle;
        # the initial form-load navigation uses wait_until="load".
        if kwargs.get("wait_until") == "networkidle":
            _err_msg = "networkidle never fired"
            raise PlaywrightTimeoutError(_err_msg)
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
    fake_browser_session: MagicMock,
    firebase_message: str,
) -> None:
    """Test that Firebase error codes are included in raised exception."""
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
    """Test that Firebase failure without parseable body shows HTTP status."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [_make_response(_FIREBASE_URL, 500)]
    with pytest.raises(AuthenticationError) as exc_info:
        login(fake_browser_session, email="a@b.c", password="x")
    assert "HTTP 500" in str(exc_info.value)


# ---------- token-exchange failures --------------------------------------
def test_login_token_exchange_failure_raises(
    fake_browser_session: MagicMock,
) -> None:
    """Test that token exchange failure raises AuthenticationError."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 401, {}),
    ]
    with pytest.raises(AuthenticationError, match="token exchange failed"):
        login(fake_browser_session, email="a@b.c", password="x")


# ---------- timeout / silence --------------------------------------------
def test_login_no_responses_times_out(fake_browser_session: MagicMock) -> None:
    """Test that login times out when no responses arrive."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = []  # nothing arrives
    with pytest.raises(AuthenticationError, match="did not complete"):
        login(fake_browser_session, email="a@b.c", password="x", timeout=0.01)


def test_login_firebase_success_but_token_missing_times_out(
    fake_browser_session: MagicMock,
) -> None:
    """Firebase succeeds but token exchange never arrives - should timeout."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        # No token response - simulates token exchange being blocked or delayed
    ]
    with pytest.raises(AuthenticationError, match="did not complete"):
        login(fake_browser_session, email="a@b.c", password="x", timeout=0.01)


def test_login_form_detection_uses_fixed_timeout(
    fake_browser_session: MagicMock,
) -> None:
    """Test that form detection uses fixed 5s timeout regardless of login timeout."""
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
    """Test that login short-circuits when saved session already authenticates."""
    page = fake_browser_session.goto.return_value
    page.wait_for_selector.side_effect = PlaywrightTimeoutError("no #email")
    login(fake_browser_session, email="a@b.c", password="x")
    page.fill.assert_not_called()
    page.click.assert_not_called()
    # Post-login navigation still runs so the saved state gets re-flushed.
    fake_browser_session.goto.assert_any_call(
        POST_LOGIN_PATH,
        wait_until="networkidle",
        timeout=30_000,
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


def test_login_captures_token_response_separately(
    fake_browser_session: MagicMock,
) -> None:
    """The token response is captured as the second half of the auth flow."""
    page = fake_browser_session.goto.return_value
    # Stage responses in order: firebase first, then token exchange
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
    ]
    login(fake_browser_session, email="a@b.c", password="x")
    # Should succeed when both responses arrive
    assert fake_browser_session.goto.call_count == 2


def test_login_ignores_duplicate_token_responses(
    fake_browser_session: MagicMock,
) -> None:
    """Only the first token response is captured; duplicates are ignored."""
    page = fake_browser_session.goto.return_value
    # Stage duplicate token responses - only first should be captured
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
        _make_response(_TOKEN_URL, 200, {}),
        _make_response(_TOKEN_URL, 200, {}),  # duplicate, should be ignored
    ]
    login(fake_browser_session, email="a@b.c", password="x")
    # Should still succeed - duplicates don't break anything
    assert fake_browser_session.goto.call_count == 2


# ---------- firebase error without structured body (line 159) ----------------
def test_login_firebase_error_with_non_dict_error_field(
    fake_browser_session: MagicMock,
) -> None:
    """Firebase error response with non-dict error field falls back to HTTP status."""
    page = fake_browser_session.goto.return_value
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 403, {"error": "string-not-dict"}),
    ]
    with pytest.raises(AuthenticationError) as exc_info:
        login(fake_browser_session, email="a@b.c", password="x")
    assert "HTTP 403" in str(exc_info.value)


# ---------- token response arrives before firebase (line 182) ----------------
def test_login_handles_token_response_arriving_first(
    fake_browser_session: MagicMock,
) -> None:
    """Token response can arrive before firebase response; both must be present."""
    page = fake_browser_session.goto.return_value
    # Stage token first, then firebase — atypical order
    page.staged_responses = [
        _make_response(_TOKEN_URL, 200, {}),
        _make_response(_FIREBASE_URL, 200, {"idToken": "tok"}),
    ]
    login(fake_browser_session, email="a@b.c", password="x")
    # Should still succeed when both are present
    assert fake_browser_session.goto.call_count == 2


# ---------- load_refresh_token (line 348) ------------------------------------
# ---------- firebase error message edge cases (line 157->159) ---------------
def test_firebase_error_message_with_non_string_message(
    fake_browser_session: MagicMock,
) -> None:
    """Firebase error with non-string message field falls back to HTTP status."""
    page = fake_browser_session.goto.return_value
    # error.message is an int, not a string
    page.staged_responses = [
        _make_response(_FIREBASE_URL, 403, {"error": {"message": 12345}}),
    ]
    with pytest.raises(AuthenticationError) as exc_info:
        login(fake_browser_session, email="a@b.c", password="x")
    assert "HTTP 403" in str(exc_info.value)


# ---------- _origin_entry_for with multiple origins (line 367->366) ---------
