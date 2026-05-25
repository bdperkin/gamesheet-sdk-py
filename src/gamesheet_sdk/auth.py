"""Authentication flows against the GameSheet WebUI.

The dashboard at https://gamesheet.app is a Devise-style Rails app
served behind a React/SPA front end. The login form is rendered
client-side and submitted via JavaScript, so a plain
:class:`requests.Session` POST is not enough. This module drives the
form through Playwright (see :class:`gamesheet_sdk.BrowserSession`).
"""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .browser import BrowserSession
from .exceptions import AuthenticationError

LOGIN_PATH = "/users/sign_in"
"""Path of the login form, relative to :attr:`Config.base_url`."""

_DEFAULT_TIMEOUT_S = 15.0


def login(
    session: BrowserSession,
    email: str | None = None,
    password: str | None = None,
    *,
    timeout: float | None = None,
) -> None:
    """Log into the GameSheet dashboard, leaving the session authenticated.

    On success the session cookie and any localStorage tokens are now
    in ``session.context``; the next call to ``session.save()`` (or
    context-manager exit) persists them to
    :attr:`Config.browser_state_path` so subsequent processes pick them
    back up.

    If ``email`` or ``password`` are not supplied here they are read
    from :attr:`Config.username` and :attr:`Config.password`
    respectively (typically populated from the ``GAMESHEET_USERNAME``
    and ``GAMESHEET_PASSWORD`` environment variables).

    :param session: An open :class:`BrowserSession`. The browser will
        be started lazily on first navigation if it has not been
        already.
    :param email: Email/username for the GameSheet account.
    :param password: Password for the GameSheet account.
    :param timeout: Seconds to wait for the post-submit redirect off
        the sign-in page. Defaults to 15.
    :raises AuthenticationError: If credentials are missing or the
        server rejects the submission (the page does not redirect off
        :data:`LOGIN_PATH` within the timeout).
    """
    cfg = session.config
    if email is None:
        email = cfg.username
    if password is None and cfg.password is not None:
        # pylint: disable-next=no-member  # pylint mis-types SecretStr as FieldInfo
        password = cfg.password.get_secret_value()
    if not email or not password:
        raise AuthenticationError(
            "Login requires an email and password. Pass them explicitly or "
            "set GAMESHEET_USERNAME and GAMESHEET_PASSWORD."
        )

    timeout_ms = int((timeout if timeout is not None else _DEFAULT_TIMEOUT_S) * 1000)
    page = session.goto(LOGIN_PATH, wait_until="load")
    page.wait_for_selector("#email", timeout=timeout_ms)
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit]")
    try:
        page.wait_for_url(
            lambda url: LOGIN_PATH not in url,
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError as exc:
        raise AuthenticationError(
            "Login rejected: server did not redirect off the sign-in page "
            f"within {timeout_ms / 1000:.0f}s. Check credentials or rate limits."
        ) from exc
