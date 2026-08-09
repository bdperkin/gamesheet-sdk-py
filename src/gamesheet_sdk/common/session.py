# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Reusable HTTP session for talking to the GameSheet WebUI.

Wraps: class:`requests.Session` with the bits every WebUI workflow
needs and nobody wants to wire up by hand:
- A pinned, version-stamped ``User-Agent``.
- Configurable base URL so callers can hand in relative paths.
- Cookie persistence to disk between process invocations.
- Retries on 5xx and connection errors for idempotent methods.
- POST is intentionally excluded from retries (no double-submission).
Direct access to the cookie jar and default headers is via :attr:`Session.cookies` and
:attr:`Session.headers`.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from importlib.metadata import PackageNotFoundError, version as _resolved_version
import json
import logging
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.constants import HTTP_RETRY_STATUSES
from gamesheet_sdk.common.security import write_secure_text

if TYPE_CHECKING:
    from http.cookiejar import Cookie


def _default_user_agent() -> str:
    """Build the SDK's default ``User-Agent`` from installed metadata.

    Reads from the package's distribution metadata (which is set in ``pyproject.toml`` and managed by PSR)
    rather than importing ``__version__`` from the parent module, so this module stays free of cyclic imports.

    Returns:
        str: String result.
    """
    try:
        ver = _resolved_version("gamesheet-sdk-py")
    except PackageNotFoundError:
        ver = "0+unknown"

    return f"gamesheet-sdk-py/{ver} (+https://github.com/bdperkin/gamesheet-sdk-py)"


_LOGGER = logging.getLogger(__name__)
# Retry on transient server-side and gateway errors only.
_DEFAULT_RETRY_STATUSES = HTTP_RETRY_STATUSES
# Idempotent methods are safe to retry. POST is excluded so we never
# double-submit a mutation that happened to time out on the response.
_DEFAULT_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})


# pylint: disable-next=too-many-public-methods
class Session:
    """A ``requests.Session`` wrapper configured for GameSheet WebUI access.

    Example::
        from gamesheet_sdk import Config, Session
        with Session(Config()) as s:
            resp = s.get("/api/leagues")
            resp.raise_for_status()
    The context-manager form persists cookies on exit. If you do not use ``with``, call :meth:`Session.close`
    explicitly to save state.

    Constructs a :class:`requests.Session` with automatic retry logic, a version-stamped User-Agent, and
    restores any previously-saved cookies from disk. The session is ready for immediate use after
    construction.

    Args:
        config (Config | None): Optional configuration object. If ``None``, a default
            :class:`~gamesheet_sdk.common.config.Config` is created.
    """

    # -- internals --------------------------------------------------------

    def _build_http_session(self: Session) -> requests.Session:
        """Construct and configure the underlying :class:`requests.Session`.

        Attaches a User-Agent header and mounts an HTTPAdapter with retry logic for transient server-side and
        network errors. Retries apply only to idempotent methods (GET, HEAD, OPTIONS, PUT, DELETE); POST is
        excluded to avoid double-submission.

        Returns:
            requests.Session: Return value.
        """
        s = requests.Session()
        s.headers["User-Agent"] = self.config.user_agent or _default_user_agent()
        retry = Retry(
            total=self.config.request_retries,
            connect=self.config.request_retries,
            read=self.config.request_retries,
            backoff_factor=0.5,
            status_forcelist=list(_DEFAULT_RETRY_STATUSES),
            allowed_methods=list(_DEFAULT_RETRY_METHODS),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        return s

    def _load_cookies(self: Session) -> None:
        """Restore cookies from disk if :attr:`Config.session_path` or browser_state_path exists.

        Reads JSON-serialized cookie data from both session.json and browser-state.json (if they exist) and
        populates the underlying session's cookie jar. Browser state cookies are loaded first, then session
        cookies (which can override). If a file does not exist or cannot be parsed, the method logs a warning
        and continues. This method is called automatically during :meth:``__init__`` to restore session state
        from a previous run.

        Returns:
            None: None
        """
        # Load from browser state file first (from login flow)
        browser_state_path = self.config.browser_state_path
        if browser_state_path.exists():
            try:
                data = json.loads(browser_state_path.read_text())
                for raw in data.get("cookies", []):
                    cookie_dict = {
                        "name": raw["name"],
                        "value": raw["value"],
                        "domain": raw.get("domain", ""),
                        "path": raw.get("path", "/"),
                        "secure": raw.get("secure", False),
                        "expires": raw.get("expires"),
                    }
                    self._http.cookies.set(**cookie_dict)
            except (OSError, json.JSONDecodeError) as exc:
                _LOGGER.warning(
                    "Failed to load browser state cookies from %s: %s",
                    browser_state_path,
                    exc,
                )
        # Load from session file (can override browser state cookies)
        path = self.config.session_path
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Failed to load session cookies from %s: %s", path, exc)
            return

        for raw in data.get("cookies", []):
            # Create a dictionary of the cookie attributes
            cookie_dict = {
                "name": raw["name"],
                "value": raw["value"],
                "domain": raw.get("domain", ""),
                "path": raw.get("path", "/"),
                "secure": raw.get("secure", False),
                "expires": raw.get("expires"),
            }
            # Add it directly to the session jar using keyword arguments
            self._http.cookies.set(**cookie_dict)

    def __init__(self: Session, config: Config | None = None) -> None:
        self.config = config or Config()
        self._http = self._build_http_session()
        self._load_cookies()

    # -- public attribute access ------------------------------------------
    @property
    def cookies(self: Session) -> RequestsCookieJar:
        """Underlying cookie jar.

        Mutating this affects subsequent requests.

        Returns:
            RequestsCookieJar: Return value.
        """
        return self._http.cookies

    @property
    def headers(self: Session) -> MutableMapping[str, str | bytes]:
        """Default headers attached to every request from this session.

        The underlying mapping is a case-insensitive dict (as supplied by :class:`requests.Session`), but the
        declared return type matches the stub for :attr:`requests.Session.headers`.

        Returns:
            MutableMapping[str, str | bytes]: Return value.
        """
        return self._http.headers  # pyright: ignore[reportReturnType]

    def set_bearer_token(self: Session, token: str) -> None:
        """Attach ``Authorization: Bearer <token>`` to all subsequent requests.

        Convenience for ``s.headers["Authorization"] = f"Bearer {token}"``.

        Args:
            token (str): The bearer token to attach
        """
        self._http.headers["Authorization"] = f"Bearer {token}"

    def _resolve(self: Session, url: str) -> str:
        """Resolve a relative URL against the configured base URL.

        Absolute URLs (starting with ``http://`` or ``https://``) are returned as-is. Relative paths are
        joined to :attr:`Config.base_url`.

        Args:
            url (str): An absolute URL or a path relative to the base URL.

        Returns:
            str: String result.
        """
        if url.startswith(("http://", "https://")):
            return url

        return urljoin(self.config.base_url.rstrip("/") + "/", url.lstrip("/"))

    # -- request methods --------------------------------------------------
    def request(
        self: Session,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send an HTTP request, resolving ``url`` against the configured base URL.

        Args:
            method (str): HTTP verb (GET, POST, etc.).
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            timeout (float | None): Per-request timeout override; falls back to :attr:`Config.timeout` if not
                supplied.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`requests.Session.request`.

        Returns:
            requests.Response: Return value.
        """
        full_url = self._resolve(url)
        effective_timeout = timeout if timeout is not None else self.config.timeout
        return self._http.request(method, full_url, timeout=effective_timeout, **kwargs)

    def get(self: Session, url: str, **kwargs: Any) -> requests.Response:
        """Send a GET request.

        See: meth:`request`.

        Args:
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`request`.

        Returns:
            requests.Response: Return value.
        """
        return self.request("GET", url, **kwargs)

    def post(self: Session, url: str, **kwargs: Any) -> requests.Response:
        """Send a POST request.

        See: meth:`request`.

        Args:
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`request`.

        Returns:
            requests.Response: Return value.
        """
        return self.request("POST", url, **kwargs)

    def put(self: Session, url: str, **kwargs: Any) -> requests.Response:
        """Send a PUT request.

        See: meth:`request`.

        Args:
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`request`.

        Returns:
            requests.Response: Return value.
        """
        return self.request("PUT", url, **kwargs)

    def patch(self: Session, url: str, **kwargs: Any) -> requests.Response:
        """Send a PATCH request.

        See: meth:`request`.

        Args:
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`request`.

        Returns:
            requests.Response: Return value.
        """
        return self.request("PATCH", url, **kwargs)

    def delete(self: Session, url: str, **kwargs: Any) -> requests.Response:
        """Send a DELETE request.

        See: meth:`request`.

        Args:
            url (str): Absolute URL, or a path relative to :attr:`Config.base_url`.
            **kwargs (Any): Additional keyword arguments forwarded to :meth:`request`.

        Returns:
            requests.Response: Return value.
        """
        return self.request("DELETE", url, **kwargs)

    # -- lifecycle --------------------------------------------------------
    def save(self: Session) -> None:
        """Persist the current cookie state to :attr:`Config.session_path`.

        The on-disk format preserves the full cookie attribute set (``domain``, ``path``, ``secure``,
        ``expires``) so that reloaded cookies are sent against the correct scopes.
        """
        path = self.config.session_path
        session_cookies: Iterator[Cookie] = iter(self._http.cookies)
        cookies: list[dict[str, Any]] = [
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
            }
            for cookie in session_cookies
        ]
        write_secure_text(path, json.dumps({"cookies": cookies}, indent=2, sort_keys=True))

    def close(self: Session) -> None:
        """Persist cookies and release the underlying HTTP connection pool."""
        try:
            self.save()
        except OSError as exc:
            _LOGGER.warning("Failed to save session cookies: %s", exc)

        self._http.close()

    def __enter__(self: Self) -> Self:
        """Enter the context manager, returning the Session instance.

        Returns:
            Self: Return value.
        """
        return self

    def __exit__(
        self: Session,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context manager, persisting cookies and closing the session.

        Called automatically at the end of a ``with`` block. Delegates to :meth:`close` to save state and
        release resources.

        Returns:
            None: None
        """
        self.close()
