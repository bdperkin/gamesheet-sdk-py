"""Authentication flows against the GameSheet WebUI.

The dashboard at ``https://gamesheet.app`` uses Firebase Authentication
behind a React/SPA front end. On submit the SPA POSTs credentials to
Firebase Auth's ``signInWithPassword`` endpoint and then GETs
``gamesheet.app/api/token`` to exchange the resulting ID token for a
GameSheet session cookie.

Success of the login is determined by watching *both* of those network
calls, not by waiting for the page URL to change. On failure the SPA
renders an inline error and the URL never leaves ``/associations``, so
a URL-change check would just time out instead of surfacing the actual
reason.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from playwright.sync_api import Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .browser import BrowserSession
from .config import Config
from .exceptions import AuthenticationError

LOGIN_PATH = "/associations"
"""Path on which the SDK drives the login form, relative to
:attr:`Config.base_url`.

GameSheet's SPA renders the login form inline at the same route that
becomes the authenticated dashboard, rather than at a dedicated
``/users/sign_in`` route. Driving the form here -- instead of at
``/users/sign_in``, which is also valid HTML but is a *separate* React
app instance -- lets the same SPA instance handle the unauthenticated
to authenticated transition in place, so its post-login data fetches
happen with context preserved and the saved storage state captures a
fully-settled session.
"""

POST_LOGIN_PATH = "/associations"
"""Default destination after a successful login.

Navigating here after the auth round-trip lets the SPA fetch the user's
permissions, association list, and any other post-login state that the
dashboard caches in cookies / localStorage. Without this navigation the
saved browser state captures only "authenticated, pre-routing", which
makes subsequent runs look unprivileged to the SPA.
"""

_FIREBASE_AUTH_HOST = "identitytoolkit.googleapis.com"
_FIREBASE_AUTH_PATH = ":signInWithPassword"
_TOKEN_EXCHANGE_PATH = "/api/token"  # nosec B105 - URL path, not a credential

_DEFAULT_TIMEOUT_S = 15.0
_POLL_INTERVAL_MS = 100
_POST_LOGIN_NAVIGATION_TIMEOUT_MS = 30_000
# Generous window for the unauthenticated landing page to render the form
# if it's going to. If a saved storage state already authenticates the
# user, the SPA renders the dashboard instead and no #email ever appears.
_FORM_DETECTION_TIMEOUT_MS = 5_000

_LOGGER = logging.getLogger(__name__)


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
    :param post_login_path: Path to navigate to after the auth round-trip
        succeeds. The SPA performs its real routing and post-login data
        fetches when it reaches this page, so the saved storage state
        afterwards captures a fully-settled session (cookies + any
        SPA-cached state) rather than just the bare auth cookie. Pass
        ``None`` to skip the post-login navigation entirely. Default is
        :data:`POST_LOGIN_PATH`.
    :raises AuthenticationError: On missing credentials, Firebase
        rejection, ``/api/token`` failure, or backend silence past the
        timeout. Post-login navigation failures are logged at WARNING
        but do not raise -- auth already succeeded by that point.
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

    page = session.goto(LOGIN_PATH, wait_until="load")

    # The SPA renders the login form when unauthenticated and the dashboard
    # when authenticated. Probe briefly for the form: if it does not show
    # up, a saved storage state has already authenticated this session and
    # there is nothing for us to do but the post-login settle step.
    try:
        page.wait_for_selector("#email", timeout=_FORM_DETECTION_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        _LOGGER.warning(
            "No login form at %s within %.0fs; assuming the saved session at "
            "%s already authenticates this user. Delete that file to force "
            "a fresh login (e.g. to switch accounts).",
            LOGIN_PATH,
            _FORM_DETECTION_TIMEOUT_MS / 1000,
            cfg.browser_state_path,
        )
        if post_login_path is not None:
            _settle_post_login(session, post_login_path)
        return

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
                if post_login_path is not None:
                    _settle_post_login(session, post_login_path)
                return
        page.wait_for_timeout(_POLL_INTERVAL_MS)

    raise AuthenticationError(
        f"Login flow did not complete within {timeout_s:.0f}s. "
        "Auth backend returned no response. Try `--no-headless -vv` to debug."
    )


def _is_firebase_signin(url: str) -> bool:
    return _FIREBASE_AUTH_HOST in url and _FIREBASE_AUTH_PATH in url


def _settle_post_login(session: BrowserSession, path: str) -> None:
    """Navigate to ``path`` and wait for the SPA to settle.

    The auth round-trip is only the first half of a real login: the SPA
    needs to actually route to a real page (e.g. /associations) for its
    permissions and association data to load, which is what populates the
    cookies and localStorage that subsequent runs will reuse. Without
    this step the saved storage state looks "logged in" but the SPA's
    React state has never finished initializing -- subsequent loads of
    the same state surface as "Insufficient Privileges" because the
    permissions cache was never populated.

    Failures here are *not* fatal: auth itself already succeeded, and
    long-polling endpoints can prevent ``networkidle`` from ever firing.
    """
    try:
        session.goto(
            path,
            wait_until="networkidle",
            timeout=_POST_LOGIN_NAVIGATION_TIMEOUT_MS,
        )
    except PlaywrightTimeoutError:
        _LOGGER.debug(
            "Post-login navigation to %s did not reach networkidle in %ds; "
            "auth succeeded so proceeding anyway.",
            path,
            _POST_LOGIN_NAVIGATION_TIMEOUT_MS // 1000,
        )


def load_access_token(config: Config) -> str | None:
    """Read the SPA's access token from the saved browser storage state.

    Returns the value of the ``accessToken`` localStorage entry for the
    SPA's origin (``Config.base_url``), or ``None`` if the storage state
    file is missing, unreadable, or does not contain a token. The
    returned string is the raw JWT and is intended to be attached to
    HTTP requests as ``Authorization: Bearer <token>`` via
    :meth:`Session.set_bearer_token`.
    """
    path = config.browser_state_path
    if not path.exists():
        return None
    try:
        state: dict[str, Any] = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        _LOGGER.warning("Failed to read browser storage state from %s.", path)
        return None
    for origin in state.get("origins", []):
        if origin.get("origin") != config.base_url:
            continue
        for kv in origin.get("localStorage", []):
            if kv.get("name") == "accessToken":  # nosec B105 - localStorage key
                value = kv.get("value")
                return value if isinstance(value, str) and value else None
    return None


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
