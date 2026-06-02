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
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

# pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from gamesheet_sdk.browser import BrowserSession
    from gamesheet_sdk.config import Config

import requests
from playwright.sync_api import Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# pylint: disable=ungrouped-imports
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.session import Session

# Path on which the SDK drives the login form, relative to
# :attr:`Config.base_url`.
# GameSheet's SPA renders the login form inline at the same route that
# becomes the authenticated dashboard, rather than at a dedicated
# ``/users/sign_in`` route. Driving the form here -- instead of at
# ``/users/sign_in``, which is also valid HTML but is a *separate* React
# app instance -- lets the same SPA instance handle the unauthenticated
# to authenticated transition in place, so its post-login data fetches
# happen with context preserved and the saved storage state captures a
# fully-settled session.
LOGIN_PATH = "/associations"

# Default destination after a successful login.
# Navigating here after the auth round-trip lets the SPA fetch the user's
# permissions, association list, and any other post-login state that the
# dashboard caches in cookies / localStorage. Without this navigation the
# saved browser state captures only "authenticated, pre-routing", which
# makes subsequent runs look unprivileged to the SPA.
POST_LOGIN_PATH = "/associations"

_FIREBASE_AUTH_HOST = "identitytoolkit.googleapis.com"
_FIREBASE_AUTH_PATH = ":signInWithPassword"
_TOKEN_EXCHANGE_PATH = "/api/token"  # noqa: S105 # nosec B105

# Endpoint that mints a fresh access token from a valid refresh token.
REFRESH_URL = "https://gateway-authserver-awy26srzoa-nn.a.run.app/auth/v4/refresh"

_REFRESH_TIMEOUT_S = 30.0

_DEFAULT_TIMEOUT_S = 15.0
_POLL_INTERVAL_MS = 100
_POST_LOGIN_NAVIGATION_TIMEOUT_MS = 30_000
# Generous window for the unauthenticated landing page to render the form
# if it's going to. If a saved storage state already authenticates the
# user, the SPA renders the dashboard instead and no #email ever appears.
_FORM_DETECTION_TIMEOUT_MS = 5_000

_LOGGER = logging.getLogger(__name__)


def _resolve_email(cfg: Config, email: str | None) -> str:
    """Fall through arg → ``GAMESHEET_USERNAME`` → :attr:`Config.username`."""
    if email is None:
        email = cfg.username
    if not email:
        _err_msg = "Login requires an email. Pass it explicitly or set GAMESHEET_USERNAME."
        raise AuthenticationError(_err_msg)
    return email


def _resolve_password(cfg: Config, password: str | None) -> str:
    """Fall through arg → ``GAMESHEET_PASSWORD`` → :attr:`Config.password`.

    Kept separate from :func:`_resolve_email` so the secret never flows through a shared return value with the
    non-sensitive email — that pairing was enough to trip CodeQL's data-flow analyzer into flagging downstream
    ``email`` logging as clear-text password logging.
    """
    if password is None and cfg.password is not None:
        # pylint: disable-next=no-member  # pylint mis-types SecretStr as FieldInfo
        password = cfg.password.get_secret_value()
    if not password:
        _err_msg = "Login requires a password. Pass it explicitly or set GAMESHEET_PASSWORD."
        raise AuthenticationError(_err_msg)
    return password


def _wait_for_login_form(page: Any, cfg: Config) -> bool:
    """Return ``True`` if the form rendered, ``False`` if already authenticated."""
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
        return False
    return True


def _is_firebase_signin(url: str) -> bool:
    return _FIREBASE_AUTH_HOST in url and _FIREBASE_AUTH_PATH in url


def _attach_response_capture(page: Any) -> dict[str, Response | None]:
    """Attach a listener that captures the first Firebase and token responses."""
    captured: dict[str, Response | None] = {"firebase": None, "token": None}  # noqa: S105 # nosec B105

    def on_response(response: Response) -> None:
        if _is_firebase_signin(response.url) and captured["firebase"] is None:
            captured["firebase"] = response
        elif response.url.endswith(_TOKEN_EXCHANGE_PATH) and captured["token"] is None:
            captured["token"] = response

    page.on("response", on_response)
    return captured


def _submit_login_form(page: Any, email: str, password: str) -> None:
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit]")


def _firebase_error_message(response: Response) -> str:
    """Extract a readable error from a Firebase Auth failure response.

    Firebase returns ``{"error": {"code": N, "message": "CODE_NAME", ...}}``; the message is a stable
    identifier like ``EMAIL_NOT_FOUND`` that we surface verbatim so callers can react programmatically.
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
    """Return ``True`` once both halves have landed successfully."""
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
        page.wait_for_timeout(_POLL_INTERVAL_MS)
    _err_msg = (
        f"Login flow did not complete within {timeout_s:.0f}s. "
        "Auth backend returned no response. Try `--no-headless -vv` to debug.",
    )
    raise AuthenticationError(_err_msg)


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
    email = _resolve_email(session.config, email)
    password = _resolve_password(session.config, password)
    timeout_s = timeout if timeout is not None else _DEFAULT_TIMEOUT_S

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


def _read_state_file(path: Any) -> dict[str, Any] | None:
    """Parse the browser storage state JSON, or return ``None`` on miss/error."""
    if not path.exists():
        return None
    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        _LOGGER.warning("Failed to read browser storage state from %s.", path)
        return None
    return loaded


def _lookup_local_storage(state: dict[str, Any], base_url: str, name: str) -> Any:
    """Return the named localStorage value for ``base_url``, or ``None``."""
    for origin in state.get("origins", []):
        if origin.get("origin") != base_url:
            continue
        for kv in origin.get("localStorage", []):
            if kv.get("name") == name:
                return kv.get("value")
    return None


def _load_local_storage_value(config: Config, name: str) -> str | None:
    """Read one localStorage entry for ``config.base_url`` from the saved state."""
    state = _read_state_file(config.browser_state_path)
    if state is None:
        return None
    value = _lookup_local_storage(state, config.base_url, name)
    return value if isinstance(value, str) and value else None


def load_access_token(config: Config) -> str | None:
    """Read the SPA's access token from the saved browser storage state.

    Returns the value of the ``accessToken`` localStorage entry for the SPA's origin (``Config.base_url``), or
    ``None`` if the storage state file is missing, unreadable, or does not contain a token. Intended to be
    attached to HTTP requests via :meth:`Session.set_bearer_token`.
    """
    return _load_local_storage_value(config, "accessToken")


def load_refresh_token(config: Config) -> str | None:
    """Read the SPA's refresh token from the saved browser storage state.

    Companion to :func:`load_access_token`. Used to drive :func:`refresh_access_token` and
    :class:`AuthenticatedSession`.
    """
    return _load_local_storage_value(config, "refreshToken")


def _read_state_or_empty(path: Any) -> dict[str, Any]:
    """Like :func:`_read_state_file` but returns an empty skeleton on miss/error."""
    empty: dict[str, Any] = {"cookies": [], "origins": []}
    if not path.exists():
        return empty
    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError:
        return empty
    return loaded


def _origin_entry_for(state: dict[str, Any], base_url: str) -> dict[str, Any]:
    """Return the origin entry for ``base_url``, creating it if absent."""
    origins: list[dict[str, Any]] = state.setdefault("origins", [])
    for origin in origins:
        if origin.get("origin") == base_url:
            return origin
    new_entry: dict[str, Any] = {"origin": base_url, "localStorage": []}
    origins.append(new_entry)
    return new_entry


def _build_token_updates(
    *,
    access: str,
    refresh: str | None,
    roles: str | None,
) -> dict[str, str]:
    """Build a localStorage-update dict from the present keyword arguments."""
    updates: dict[str, str] = {"accessToken": access}
    if refresh is not None:
        updates["refreshToken"] = refresh
    if roles is not None:
        updates["rolesToken"] = roles
    return updates


def _apply_local_storage_updates(ls: list[dict[str, str]], updates: dict[str, str]) -> None:
    """Upsert each ``name → value`` pair into the localStorage list."""
    by_name = {kv.get("name"): kv for kv in ls}
    for name, value in updates.items():
        existing = by_name.get(name)
        if existing is not None:
            existing["value"] = value
        else:
            ls.append({"name": name, "value": value})


def save_tokens(
    config: Config,
    *,
    access: str,
    refresh: str | None = None,
    roles: str | None = None,
) -> None:
    """Persist new token values back into the saved browser storage state.

    Reads :attr:`Config.browser_state_path` (or starts with an empty state if it is missing or malformed),
    updates the localStorage entries for ``config.base_url`` in place, and writes the file back.

    Only the keys that were passed are written; unspecified ones are left alone. The companion
    ``BrowserSession`` saves the same file structurally, so updates from either path are mutually compatible.
    """
    path = config.browser_state_path
    state = _read_state_or_empty(path)
    origin_entry = _origin_entry_for(state, config.base_url)
    _apply_local_storage_updates(
        origin_entry.setdefault("localStorage", []),
        _build_token_updates(access=access, refresh=refresh, roles=roles),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def refresh_access_token(
    refresh_token: str,
    *,
    user_agent: str | None = None,
    timeout: float = _REFRESH_TIMEOUT_S,
) -> dict[str, str]:
    """Exchange ``refresh_token`` for a fresh ``{access, refresh, roles}`` bundle.

    POSTs to :data:`REFRESH_URL` with ``Authorization: Bearer <refresh_token>`` and an
    empty JSON body. The gateway returns a new access token (10-min TTL), a new refresh
    token (long TTL, replaces the one you sent), and a roles token.

    Standalone HTTP call -- no :class:`Session` needed, so it can be used from inside
    :class:`AuthenticatedSession`'s retry path without recursing.

    :raises AuthenticationError: If the refresh token is rejected (401). :raises
    GameSheetError: For any other non-2xx response.
    """
    headers = {
        "Authorization": f"Bearer {refresh_token}",
        "Content-Type": "application/json",
    }
    if user_agent is not None:
        headers["User-Agent"] = user_agent
    response = requests.post(REFRESH_URL, json={}, headers=headers, timeout=timeout)
    if response.status_code == 401:
        _err_msg = "Refresh token rejected. Run `gamesheet-sdk-py login` to re-authenticate."
        raise AuthenticationError(_err_msg)
    if response.status_code >= 400:
        _err_msg = f"Token refresh failed: HTTP {response.status_code}: {response.text[:200]!r}"
        raise GameSheetError(_err_msg)
    body = response.json()
    return {
        "access": body["access"],
        "refresh": body["refresh"],
        "roles": body["roles"],
    }


OnRefreshCallback = Callable[[dict[str, str]], None]


class AuthenticatedSession(Session):
    """A :class:`Session` that auto-refreshes its bearer on 401.

    Wraps :class:`Session` with the refresh-on-401 pattern that every
    bearer-authenticated API client ends up needing. Construction takes
    the current access + refresh tokens; the access token is attached as
    the bearer automatically. On any 401 response, the session calls
    :func:`refresh_access_token` against :data:`REFRESH_URL`, updates
    its bearer, optionally invokes ``on_refresh`` with the new token
    bundle, and retries the original request *once*. If the refresh
    itself fails the original 401 propagates to the caller, who can
    decide whether to log in again.

    Example::

        with AuthenticatedSession(
            config,
            access_token=load_access_token(config),
            refresh_token=load_refresh_token(config),
            on_refresh=lambda tokens: save_tokens(config, **tokens),
        ) as s:
            for assoc in list_associations(s):
                ...
    """

    def __init__(
        self,
        config: Config | None = None,
        *,
        access_token: str,
        refresh_token: str,
        on_refresh: OnRefreshCallback | None = None,
    ) -> None:
        super().__init__(config)
        self._refresh_token = refresh_token
        self._on_refresh = on_refresh
        self.set_bearer_token(access_token)

    def _notify_refresh(self, new_tokens: dict[str, str]) -> None:
        """Invoke the optional persistence callback, swallowing disk errors."""
        if self._on_refresh is None:
            return
        try:
            self._on_refresh(new_tokens)
        except OSError as exc:  # pragma: no cover - disk failure path
            _LOGGER.warning("on_refresh callback failed to persist: %s", exc)

    def _try_refresh(self) -> bool:
        """Run a single refresh round-trip; return whether the retry should happen."""
        try:
            new_tokens = refresh_access_token(
                self._refresh_token,
                user_agent=str(self._http.headers.get("User-Agent", "")) or None,
                timeout=self.config.timeout,
            )
        except (AuthenticationError, GameSheetError) as exc:
            _LOGGER.warning("Token refresh failed: %s; surfacing 401.", exc)
            return False
        self.set_bearer_token(new_tokens["access"])
        self._refresh_token = new_tokens["refresh"]
        self._notify_refresh(new_tokens)
        return True

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send a request, refreshing the bearer and retrying once on 401."""
        response = super().request(method, url, timeout=timeout, **kwargs)
        if response.status_code != 401:
            return response
        if not self._try_refresh():
            return response
        _LOGGER.info("Refreshed access token; retrying %s %s.", method, url)
        return super().request(method, url, timeout=timeout, **kwargs)
