"""Tests for :mod:`gamesheet_sdk.auth`.

The login flow is exercised against a ``MagicMock(spec=BrowserSession)``
so unit tests run without spinning up a real Chromium. A future
``@pytest.mark.browser`` integration suite will drive the real form
end-to-end once we have a test account or a recorded fixture.
"""

# pylint: disable=redefined-outer-name,protected-access

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk import AuthenticationError, BrowserSession, Config, login
from gamesheet_sdk.auth import LOGIN_PATH


@pytest.fixture
def fake_browser_session(config: Config) -> MagicMock:
    """A BrowserSession spec'd mock whose .goto returns a fresh page mock."""
    sess = MagicMock(spec=BrowserSession)
    sess.config = config
    sess.goto.return_value = MagicMock(name="page")
    return sess


# ---------- happy path ----------------------------------------------------


def test_login_with_explicit_credentials(fake_browser_session: MagicMock) -> None:
    login(fake_browser_session, email="alice@example.com", password="hunter2")

    fake_browser_session.goto.assert_called_once_with(LOGIN_PATH, wait_until="load")
    page = fake_browser_session.goto.return_value
    page.wait_for_selector.assert_called_once_with("#email", timeout=15_000)
    page.fill.assert_any_call("#email", "alice@example.com")
    page.fill.assert_any_call("#password", "hunter2")
    page.click.assert_called_once_with("button[type=submit]")
    page.wait_for_url.assert_called_once()


def test_login_reads_credentials_from_config(
    fake_browser_session: MagicMock,
) -> None:
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password="s3cret",
    )

    login(fake_browser_session)

    page = fake_browser_session.goto.return_value
    page.fill.assert_any_call("#email", "bob@example.com")
    page.fill.assert_any_call("#password", "s3cret")


def test_login_args_override_config(fake_browser_session: MagicMock) -> None:
    fake_browser_session.config = Config(
        base_url="https://test.example",
        username="bob@example.com",
        password="s3cret",
    )

    login(fake_browser_session, email="alice@example.com", password="other")

    page = fake_browser_session.goto.return_value
    page.fill.assert_any_call("#email", "alice@example.com")
    page.fill.assert_any_call("#password", "other")


# ---------- credential validation -----------------------------------------


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


# ---------- post-submit redirect failure ---------------------------------


def test_login_failed_redirect_raises(fake_browser_session: MagicMock) -> None:
    page = fake_browser_session.goto.return_value
    page.wait_for_url.side_effect = PlaywrightTimeoutError("timeout")

    with pytest.raises(AuthenticationError, match="server did not redirect"):
        login(fake_browser_session, email="alice@example.com", password="bad")

    # The submit click still happened before the failure was detected.
    page.click.assert_called_once_with("button[type=submit]")


def test_login_custom_timeout_passes_through(
    fake_browser_session: MagicMock,
) -> None:
    login(
        fake_browser_session,
        email="alice@example.com",
        password="hunter2",
        timeout=2.0,
    )
    page = fake_browser_session.goto.return_value
    page.wait_for_selector.assert_called_once_with("#email", timeout=2000)
    _, kwargs = page.wait_for_url.call_args
    assert kwargs["timeout"] == 2000


def test_login_url_predicate_recognizes_sign_in_path(
    fake_browser_session: MagicMock,
) -> None:
    """The wait_for_url predicate should keep waiting while the URL contains
    /users/sign_in, and resolve once we're off it."""
    login(fake_browser_session, email="a@b.c", password="x")
    page = fake_browser_session.goto.return_value
    predicate, _ = page.wait_for_url.call_args
    fn = predicate[0]
    assert fn("https://gamesheet.app/users/sign_in") is False
    assert fn("https://gamesheet.app/associations") is True
