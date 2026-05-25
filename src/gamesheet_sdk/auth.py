"""Authentication flows against the GameSheet WebUI.

The dashboard at ``https://gamesheet.app`` uses Firebase Authentication
behind a React/SPA front end. On submit the SPA POSTs credentials to
Firebase Auth's ``signInWithPassword`` endpoint and then GETs
``gamesheet.app/api/token`` to exchange the resulting ID token for a
GameSheet session cookie.

Success of the login is determined by watching *both* of those network
calls, not by waiting for the page URL to change. On failure the SPA
renders an inline error and the URL never leaves ``/users/sign_in``, so
a URL-change check would just time out instead of surfacing the actual
reason.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import Response

from .browser import BrowserSession
from .exceptions import AuthenticationError

LOGIN_PATH = "/users/sign_in"
"""Path of the login form, relative to :attr:`Config.base_url`."""

_FIREBASE_AUTH_HOST = "identitytoolkit.googleapis.com"
_FIREBASE_AUTH_PATH = ":signInWithPassword"
_TOKEN_EXCHANGE_PATH = "/api/token"  # nosec B105 - URL path, not a credential

_DEFAULT_TIMEOUT_S = 15.0
_POLL_INTERVAL_MS = 100

_LOGGER = logging.getLogger(__name__)


def login(
    session: BrowserSession,
    email: str | None = None,
    password: str | None = None,
    *,
    timeout: float | None = None,
) -> None:
    """Log into the GameSheet dashboard, leaving the session authenticated.

    Success is determined by:

    - HTTP 200 from the Firebase ``signInWithPassword`` call, **and**
    - HTTP 200 from the subsequent ``/api/token`` exchange.

    On failure the Firebase ``error.message`` (e.g. ``EMAIL_NOT_FOUND``,
    ``INVALID_LOGIN_CREDENTIALS``, ``TOO_MANY_ATTEMPTS_TRY_LATER``) is
    surfaced verbatim in the raised :class:`AuthenticationError` so
    callers know exactly what was wrong.

    :param session: An open :class:`BrowserSession`.
    :param email: Login email; falls back to ``session.config.username``.
    :param password: Login password; falls back to
        ``session.config.password.get_secret_value()``.
    :param timeout: Seconds to wait for the auth backend round-trip
        (default 15).
    :raises AuthenticationError: On missing credentials, Firebase
        rejection, ``/api/token`` failure, or backend silence past the
        timeout.
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

    timeout_s = timeout if timeout is not None else _DEFAULT_TIMEOUT_S
    timeout_ms = int(timeout_s * 1000)

    page = session.goto(LOGIN_PATH, wait_until="load")
    page.wait_for_selector("#email", timeout=timeout_ms)

    # Subscribe to the two responses we care about before triggering the
    # submit. Storing each only once protects against the SPA retrying.
    # nosec B105 - "token" is a dict key, not a credential
    captured: dict[str, Response | None] = {
        "firebase": None,
        "token": None,
    }  # nosec B105

    def on_response(response: Response) -> None:
        if _is_firebase_signin(response.url) and captured["firebase"] is None:
            captured["firebase"] = response
        elif response.url.endswith(_TOKEN_EXCHANGE_PATH) and captured["token"] is None:
            captured["token"] = response

    page.on("response", on_response)

    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit]")

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        fb = captured["firebase"]
        if fb is not None:
            if fb.status != 200:
                msg = _firebase_error_message(fb)
                raise AuthenticationError(f"Login rejected by Firebase: {msg}")
            tok = captured["token"]
            if tok is not None:
                if tok.status != 200:
                    raise AuthenticationError(
                        f"GameSheet token exchange failed (HTTP {tok.status})."
                    )
                _LOGGER.info("Login succeeded for %s.", email)
                return
        page.wait_for_timeout(_POLL_INTERVAL_MS)

    raise AuthenticationError(
        f"Login flow did not complete within {timeout_s:.0f}s. "
        "Auth backend returned no response. Try `--no-headless -vv` to debug."
    )


def _is_firebase_signin(url: str) -> bool:
    return _FIREBASE_AUTH_HOST in url and _FIREBASE_AUTH_PATH in url


def _firebase_error_message(response: Response) -> str:
    """Extract a readable error from a Firebase Auth failure response.

    Firebase returns ``{"error": {"code": N, "message": "CODE_NAME", ...}}``;
    the message is a stable identifier like ``EMAIL_NOT_FOUND`` that we
    surface verbatim so callers can react programmatically.
    """
    try:
        body: dict[str, Any] = response.json()
    except (ValueError, KeyError):
        return f"HTTP {response.status}"
    err = body.get("error", {})
    if isinstance(err, dict) and "message" in err:
        return str(err["message"])
    return f"HTTP {response.status}"
