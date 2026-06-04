"""Browser-based login flow against GameSheet's Firebase Auth."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from playwright.sync_api import Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from gamesheet_sdk.auth.constants import (
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
from gamesheet_sdk.exceptions import AuthenticationError

if TYPE_CHECKING:

    from gamesheet_sdk.browser import BrowserSession
    from gamesheet_sdk.config import Config
_LOGGER = logging.getLogger(__name__)


def _resolve_email(cfg: Config, email: str | None) -> str:
    """Fall through arg → GAMESHEET_USERNAME → Config.username."""
    if email is None:

        email = cfg.username
    if not email:

        _err_msg = "Login requires an email. Pass it explicitly or set GAMESHEET_USERNAME."
        raise AuthenticationError(_err_msg)
    return email


def _resolve_password(cfg: Config, password: str | None) -> str:
    """Fall through arg → GAMESHEET_PASSWORD → Config.password.

    Kept separate from :func:`_resolve_email` so the secret never flows through a shared return value with the
    non-sensitive email — that pairing was enough to trip CodeQL's data-flow analyzer into flagging downstream
    ``email`` logging as clear-text password logging.
    """
    if password is None and cfg.password is not None:

        password = cfg.password.get_secret_value()
    if not password:

        _err_msg = "Login requires a password. Pass it explicitly or set GAMESHEET_PASSWORD."
        raise AuthenticationError(_err_msg)
    return password


def _wait_for_login_form(page: Any, cfg: Config) -> bool:
    """Return True if the form rendered, False if already authenticated."""
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

    return FIREBASE_AUTH_HOST in url and FIREBASE_AUTH_PATH in url


def _attach_response_capture(page: Any) -> dict[str, Response | None]:
    """Attach a listener that captures the first Firebase and token responses."""
    captured: dict[str, Response | None] = {"firebase": None, "token": None}  # noqa: S105 # nosec B105

    def on_response(response: Response) -> None:

        if _is_firebase_signin(response.url) and captured["firebase"] is None:

            captured["firebase"] = response
        elif response.url.endswith(TOKEN_EXCHANGE_PATH) and captured["token"] is None:
            captured["token"] = response

    page.on("response", on_response)
    return captured


def _submit_login_form(page: Any, email: str, password: str) -> None:

    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit]")


def _firebase_error_message(response: Response) -> str:
    """Extract a readable error from a Firebase Auth failure response.

    Firebase returns {"error": {"code": N, "message": "CODE_NAME", ...}}; the message is a stable identifier
    like EMAIL_NOT_FOUND that we surface verbatim so callers can react programmatically.
    """
    try:
        body: dict[str, Any] = response.json()
    except (ValueError, KeyError):
        return f"HTTP {response.status}"

    err = body.get("error")
    if isinstance(err, dict):

        message = err.get("message")  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if isinstance(message, str):

            return message

    return f"HTTP {response.status}"


def _raise_for_firebase_error(response: Response) -> None:

    if response.status != 200:

        _err_msg = f"Login rejected by Firebase: {_firebase_error_message(response)}"
        raise AuthenticationError(_err_msg)


def _raise_for_token_error(response: Response) -> None:

    if response.status != 200:

        _err_msg = f"GameSheet token exchange failed (HTTP {response.status})."
        raise AuthenticationError(_err_msg)


def _auth_round_trip_complete(captured: dict[str, Response | None], email: str) -> bool:
    """Return True once both halves have landed successfully."""
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
    """Poll until both auth responses arrive; raise on failure or timeout."""
    while time.monotonic() < deadline:

        if _auth_round_trip_complete(captured, email):

            return
        page.wait_for_timeout(POLL_INTERVAL_MS)
    _err_msg = (
        f"Login flow did not complete within {timeout_s:.0f}s. "
        "Auth backend returned no response. Try `--no-headless -vv` to debug.",
    )
    raise AuthenticationError(_err_msg)


def _settle_post_login(session: BrowserSession, path: str) -> None:
    """Navigate to ``path`` and wait for the SPA to settle.

    The auth round-trip is only the first half of a real login: the SPA needs to actually route to a real
    page (e.g. /associations) for its permissions and association data to load, which is what populates the
    cookies and localStorage that subsequent runs will reuse. Without this step the saved storage state looks
    "logged in" but the SPA's React state has never finished initializing -- subsequent loads of the same
    state surface as "Insufficient Privileges" because the permissions cache was never populated.  Failures
    here are *not* fatal: auth itself already succeeded, and long-polling endpoints can prevent
    ``networkidle`` from ever firing.
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
    - HTTP 200 from the subsequent /api/token exchange.
    On failure the Firebase error.message (e.g. EMAIL_NOT_FOUND, INVALID_LOGIN_CREDENTIALS,
    TOO_MANY_ATTEMPTS_TRY_LATER) is surfaced verbatim in the raised :class:`AuthenticationError` so callers
    know exactly what was wrong.
    :param session: An open :class:`BrowserSession`.
    :param email: Login email; falls back to ``session.config.username``.
    :param password: Login password; falls back to ``session.config.password.get_secret_value()``.
    :param timeout: Seconds to wait for the auth backend round-trip (default 15).
    :param post_login_path: Path to navigate to after the auth round-trip succeeds. The SPA performs its real
    routing and post-login data fetches when it reaches this page, so the saved storage state afterwards
    captures a fully-settled session (cookies + any SPA-cached state) rather than just the bare auth cookie.
    Pass None to skip the post-login navigation entirely. Default is :data:`POST_LOGIN_PATH`.
    :raises AuthenticationError: On missing credentials, Firebase rejection, /api/token failure, or backend
    silence past the timeout. Post-login navigation failures are logged at WARNING but do not raise -- auth
    already succeeded by that point.
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
