# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Browser-based login flow against GameSheet's Firebase Auth."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from playwright.sync_api import Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk.common.auth.constants import (
    DEFAULT_TIMEOUT_S,
    FIREBASE_AUTH_HOST,
    FIREBASE_AUTH_PATH,
    FORM_DETECTION_TIMEOUT_MS,
    LOGIN_PATH,
    POLL_INTERVAL_MS,
    POST_LOGIN_NAVIGATION_TIMEOUT_MS,
    POST_LOGIN_PATH,
    TOKEN_EXCHANGE_PATH,
)
from gamesheet_sdk.common.auth.credentials import resolve_email, resolve_password
from gamesheet_sdk.common.auth.firebase import extract_firebase_error
from gamesheet_sdk.common.auth.tokens import load_access_token, load_refresh_token
from gamesheet_sdk.common.browser import BrowserSession
from gamesheet_sdk.common.exceptions import AuthenticationError

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config

_LOGGER = logging.getLogger(__name__)


def _resolve_email(cfg: Config, email: str | None) -> str:
    """Resolve the login email from explicit argument, environment variable, or config.

    Delegates to :func:`~gamesheet_sdk.common.auth.credentials.resolve_email`.

    Args:
        cfg (Config): Configuration object containing username from env/defaults.
        email (str | None): Explicit email address, or None to fall back to config.

    Returns:
        str: The resolved email address.

    Raises:
        AuthenticationError: If no email is available from any source.
    """
    return resolve_email(cfg, email)


def _resolve_password(cfg: Config, password: str | None) -> str:
    """Resolve the login password from explicit argument, environment variable, or config.

    Delegates to :func:`~gamesheet_sdk.common.auth.credentials.resolve_password`.

    Args:
        cfg (Config): Configuration object containing password from env/defaults.
        password (str | None): Explicit password, or None to fall back to config.

    Returns:
        str: The resolved password string.

    Raises:
        AuthenticationError: If no password is available from any source.
    """
    return resolve_password(cfg, password)


def _wait_for_login_form(page: Any, cfg: Config) -> bool:
    """Wait for the login form to appear, or detect an already-authenticated session.

    Waits up to :data:`FORM_DETECTION_TIMEOUT_MS` for the ``#email`` input field. If the timeout fires, the
    saved browser state at ``cfg.browser_state_path`` already authenticates this user, so no login form is
    needed.

    Args:
        page (Any): Playwright page object currently at the login URL.
        cfg (Config): Configuration object containing browser state path for logging.

    Returns:
        bool: Boolean result.
    """
    try:
        page.wait_for_selector("#email", timeout=FORM_DETECTION_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        _LOGGER.warning(
            "No login form at %s within %.0fs; assuming the saved session at "
            "%s already authenticates this user. Delete that file to force "
            "a fresh login (e.g. to switch accounts).",
            LOGIN_PATH,
            FORM_DETECTION_TIMEOUT_MS / 1000,
            cfg.browser_state_path,
        )
        return False

    return True


def _is_firebase_signin(url: str) -> bool:
    """Check whether a URL is a Firebase Auth signInWithPassword endpoint.

    Args:
        url (str): The URL to test.

    Returns:
        bool: Boolean result.
    """
    return FIREBASE_AUTH_HOST in url and FIREBASE_AUTH_PATH in url


def _attach_response_capture(page: Any) -> dict[str, Response | None]:
    """Attach a Playwright response listener to capture Firebase and token exchange responses.

    Registers a ``page.on("response", ...)`` handler that saves the first Firebase signInWithPassword response
    and the first GameSheet token exchange response into a shared dict. The handler stays active for the life
    of the page, but only the first match for each key is stored.

    Args:
        page (Any): Playwright page object on which to register the response listener.

    Returns:
        dict[str, Response | None]: None. The registered handler populates them as matching responses arrive.
    """
    captured: dict[str, Response | None] = {"firebase": None, "token": None}

    def on_response(response: Response) -> None:
        """Capture Firebase Auth and token exchange responses as they arrive.

        Populates the ``captured`` dict with the first Firebase signInWithPassword response and the first
        GameSheet token exchange response encountered. Subsequent responses of the same type are ignored. Side
        effect: mutates the enclosing ``captured`` dict.

        Args:
            response (Response): A Playwright Response object intercepted by the page listener.
        """
        if _is_firebase_signin(response.url) and captured["firebase"] is None:
            captured["firebase"] = response
        elif response.url.endswith(TOKEN_EXCHANGE_PATH) and captured["token"] is None:
            captured["token"] = response

    page.on("response", on_response)
    return captured


def _submit_login_form(page: Any, email: str, password: str) -> None:
    """Fill in the login form and submit it.

    Args:
        page (Any): Playwright page object showing the login form.
        email (str): Email address to enter into the ``#email`` input.
        password (str): Password to enter into the ``#password`` input.

    Returns:
        None: None. The form submission triggers background network calls captured by
            :func:`_attach_response_capture`.
    """
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit]")


def _firebase_error_message(response: Response) -> str:
    """Extract a readable error from a Firebase Auth failure response.

    Parses the Playwright response JSON and delegates to
    :func:`~gamesheet_sdk.common.auth.firebase.extract_firebase_error`.

    Args:
        response (Response): Playwright Response object from Firebase Auth endpoint.

    Returns:
        str: Extracted error message or HTTP status fallback.
    """
    try:
        body: dict[str, Any] = response.json()
    except (ValueError, KeyError):
        return f"HTTP {response.status}"

    return extract_firebase_error(body, response.status)


def _raise_for_firebase_error(response: Response) -> None:
    """Raise AuthenticationError if the Firebase Auth response indicates failure.

    Args:
        response (Response): Playwright Response object from the Firebase signInWithPassword call.

    Returns:
        None: None on success (HTTP 200).

    Raises:
        AuthenticationError: If the response status is not 200. The exception message includes the Firebase
            error code extracted by :func:`_firebase_error_message`.
    """
    if response.status != 200:
        _err_msg = f"Login rejected by Firebase: {_firebase_error_message(response)}"
        raise AuthenticationError(_err_msg)


def _raise_for_token_error(response: Response) -> None:
    """Raise AuthenticationError if the GameSheet token exchange response indicates failure.

    Args:
        response (Response): Playwright Response object from the /api/token exchange call.

    Returns:
        None: None on success (HTTP 200).

    Raises:
        AuthenticationError: If the response status is not 200.
    """
    if response.status != 200:
        _err_msg = f"GameSheet token exchange failed (HTTP {response.status})."
        raise AuthenticationError(_err_msg)


def _auth_round_trip_complete(captured: dict[str, Response | None], email: str) -> bool:
    """Check whether both Firebase Auth and token exchange have completed successfully.

    Args:
        captured (dict[str, Response | None]): Dict populated by :func:`_attach_response_capture` containing
            ``"firebase"`` and ``"token"`` response objects.
        email (str): Email address being logged in, used for success logging.

    Returns:
        bool: Boolean result.

    Raises:
        AuthenticationError: If Firebase Auth or token exchange responses indicate failure (via
            :func:`_raise_for_firebase_error` or :func:`_raise_for_token_error`).
    """
    fb = captured["firebase"]
    if fb is None:
        return False

    _raise_for_firebase_error(fb)
    tok = captured["token"]
    if tok is None:
        return False

    _raise_for_token_error(tok)
    _LOGGER.info("Login succeeded for %s.", email)
    return True


def _await_auth_outcome(
    page: Any,
    captured: dict[str, Response | None],
    *,
    deadline: float,
    email: str,
    timeout_s: float,
) -> None:
    """Poll until both Firebase Auth and token exchange responses arrive, or timeout expires.

    Checks: func:`_auth_round_trip_complete` in a loop with :data:`POLL_INTERVAL_MS` sleeps. Raises on
    explicit auth failure (via ``_auth_round_trip_complete``) or if the deadline passes with no response.

    Args:
        page (Any): Playwright page object used for polling waits.
        captured (dict[str, Response | None]): Dict populated by :func:`_attach_response_capture`, checked
            each iteration.
        deadline (float): Absolute time (from ``time.monotonic()``) at which to give up.
        email (str): Email address being logged in, passed through to :func:`_auth_round_trip_complete` for
            logging.
        timeout_s (float): Total timeout in seconds, used only in the timeout error message.

    Returns:
        None: None on success (both responses landed with HTTP 200).

    Raises:
        AuthenticationError: If auth responses indicate failure (via :func:`_auth_round_trip_complete`), or if
            the deadline passes with no responses.
    """
    while time.monotonic() < deadline:
        if _auth_round_trip_complete(captured, email):
            return

        page.wait_for_timeout(POLL_INTERVAL_MS)

    _err_msg = (
        f"Login flow did not complete within {timeout_s:.0f}s. "
        "Auth backend returned no response. Try `--no-headless -vv` to debug."
    )
    raise AuthenticationError(_err_msg)


def _settle_post_login(session: BrowserSession, path: str) -> None:
    """Navigate to ``path`` and wait for the SPA to settle.

    The auth round-trip is only the first half of a real login: the SPA needs to actually route to a real page
    (e.g. ``/associations``) for its permissions and association data to load, which is what populates the
    cookies and localStorage that subsequent runs will reuse. Without this step the saved storage state looks
    "logged in" but the SPA's React state has never finished initializing -- subsequent loads of the same
    state surface as "Insufficient Privileges" because the permissions cache was never populated.

    Failures here are *not* fatal: auth itself already succeeded, and long-polling endpoints can prevent
    ``networkidle`` from ever firing.

    Args:
        session (BrowserSession): Active browser session to navigate.
        path (str): Destination path to navigate to for SPA settlement.

    Returns:
        None: None
    """
    try:
        session.goto(
            path,
            wait_until="networkidle",
            timeout=POST_LOGIN_NAVIGATION_TIMEOUT_MS,
        )
    except PlaywrightTimeoutError:
        _LOGGER.debug(
            "Post-login navigation to %s did not reach networkidle in %ds; "
            "auth succeeded so proceeding anyway.",
            path,
            POST_LOGIN_NAVIGATION_TIMEOUT_MS // 1000,
        )


def login(
    session: BrowserSession,
    email: str | None = None,
    password: str | None = None,
    *,
    timeout: float | None = None,
    post_login_path: str | None = POST_LOGIN_PATH,
) -> None:
    """Log into the GameSheet dashboard, leaving the session authenticated.

    Success is determined by:

    - HTTP 200 from the Firebase signInWithPassword call, **and**
    - HTTP 200 from the subsequent ``/api/token`` exchange.

    On failure the Firebase error.message (e.g. ``EMAIL_NOT_FOUND``, ``INVALID_LOGIN_CREDENTIALS``,
    ``TOO_MANY_ATTEMPTS_TRY_LATER``) is surfaced verbatim in the raised :exc:`AuthenticationError` so callers
    know exactly what was wrong.

    Args:
        session (BrowserSession): An open :class:`BrowserSession`.
        email (str | None): Login email; falls back to ``session.config.username``.
        password (str | None): Login password; falls back to ``session.config.password.get_secret_value()``.
        timeout (float | None): Seconds to wait for the auth backend round-trip (default 15).
        post_login_path (str | None): Path to navigate to after the auth round-trip succeeds. The SPA performs
            its real routing and post-login data fetches when it reaches this page, so the saved storage state
            afterwards captures a fully-settled session (cookies + any SPA-cached state) rather than just the
            bare auth cookie. Pass ``None`` to skip the post-login navigation entirely. Default is
            :data:`POST_LOGIN_PATH`.

    Raises:
        AuthenticationError: If authentication fails (missing credentials, Firebase rejection, token exchange
            failure, or timeout).
    """
    email = _resolve_email(session.config, email)
    password = _resolve_password(session.config, password)
    timeout_s = timeout if timeout is not None else DEFAULT_TIMEOUT_S
    page = session.goto(LOGIN_PATH, wait_until="load")
    if not _wait_for_login_form(page, session.config):
        # Saved storage state already authenticates; just settle and return.
        if post_login_path is not None:
            _settle_post_login(session, post_login_path)

        return

    captured = _attach_response_capture(page)
    _submit_login_form(page, email, password)
    _await_auth_outcome(
        page,
        captured,
        deadline=time.monotonic() + timeout_s,
        email=email,
        timeout_s=timeout_s,
    )
    if post_login_path is not None:
        _settle_post_login(session, post_login_path)


class AdminLoginFlow:
    """Browser-based: class:`~gamesheet_sdk.common.auth.flow.LoginFlow` for the admin dashboard.

    Wraps the headless-browser :func:`login` flow in a class that conforms to the
    :class:`~gamesheet_sdk.common.auth.flow.LoginFlow` protocol.  After the browser session closes (persisting
    localStorage to disk), the access and refresh tokens are read back and returned so callers can use them
    without touching the state file directly.

    **Example: **

    .. code-block:: python

        from gamesheet_sdk.common.auth.login import AdminLoginFlow
        from gamesheet_sdk.common.config import Config

        config = Config()
        flow = AdminLoginFlow(config)
        tokens = flow.authenticate(email="user@example.com")
        print(tokens["access"])

    Store the configuration for later browser-session creation.

    Args:
        config (Config): SDK configuration (credentials, URLs, storage paths).
    """

    def __init__(self: AdminLoginFlow, config: Config) -> None:
        self._config = config

    def authenticate(
        self: AdminLoginFlow,
        email: str | None = None,
        password: str | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, str]:
        """Run the browser-based admin login and return tokens.

        Opens a :class:`~gamesheet_sdk.common.browser.BrowserSession`, drives the Firebase login form via
        :func:`login`, and reads the persisted tokens from the saved browser state file.

        Args:
            email (str | None): Login email, or ``None`` to resolve from config/env.
            password (str | None): Login password, or ``None`` to resolve from config/env.
            timeout (float | None): Auth round-trip timeout in seconds, or ``None`` for the default.

        Returns:
            dict[str, str]: Token bundle with ``"access"`` and ``"refresh"`` keys.

        Raises:
            ~gamesheet_sdk.common.exceptions.AuthenticationError: If credentials are missing, the auth backend
                rejects them, or tokens are not found in the saved state after login.
        """
        with BrowserSession(self._config) as session:
            login(session, email=email, password=password, timeout=timeout)

        access = load_access_token(self._config)
        refresh = load_refresh_token(self._config)
        if access is None or refresh is None:
            _err_msg = "Login completed but tokens were not found in saved state."
            raise AuthenticationError(_err_msg)

        return {"access": access, "refresh": refresh}
