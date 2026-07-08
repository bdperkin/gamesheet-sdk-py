# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT
# pylint: disable=missing-param-doc

"""Reusable HTTP session for talking to the GameSheet WebUI.

Wraps :class:`requests.Session` with the bits every WebUI workflow
needs and nobody wants to wire up by hand:
- A pinned, version-stamped ``User-Agent``.
- Configurable base URL so callers can hand in relative paths.
- Cookie persistence to disk between process invocations.
- Retries on 5xx and connection errors for idempotent methods.
- POST is intentionally excluded from retries (no double-submission).
Direct access to the cookie jar and default headers is via
:attr:`Session.cookies` and :attr:`Session.headers`.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from importlib.metadata import PackageNotFoundError, version as _resolved_version
import json
import logging
from types import TracebackType
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry

from gamesheet_sdk.config import Config
from gamesheet_sdk.constants import HTTP_RETRY_STATUSES

if TYPE_CHECKING:
    from http.cookiejar import Cookie


def _default_user_agent() -> str:
    """Build the SDK's default ``User-Agent`` from installed metadata.

    Reads from the package's distribution metadata (which is set in `pyproject.toml` and managed by PSR)
    rather than importing ``__version__`` from the parent module, so this module stays free of cyclic imports.
    :returns: String result.
    :rtype: str
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


class Session:
    """A ``requests.Session`` wrapper configured for GameSheet WebUI access.

    Example::
        from gamesheet_sdk import Config, Session
        with Session(Config()) as s:
            resp = s.get("/api/leagues")
            resp.raise_for_status()
    The context-manager form persists cookies on exit. If you do not use
    ``with``, call :meth:`Session.close` explicitly to save state.
    """

    # -- internals --------------------------------------------------------
    def _build_http_session(self) -> requests.Session:
        """Construct and configure the underlying :class:`requests.Session`.

        Attaches a User-Agent header and mounts an HTTPAdapter with retry logic for transient server-side and
        network errors. Retries apply only to idempotent methods (GET, HEAD, OPTIONS, PUT, DELETE); POST is
        excluded to avoid double-submission.
        :returns: Return value.
        :rtype: requests.Session
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

    def _load_cookies(self) -> None:
        """Restore cookies from disk if :attr:`Config.session_path` or browser_state_path exists.

        Reads JSON-serialized cookie data from both session.json and browser-state.json (if they exist) and
        populates the underlying session's cookie jar. Browser state cookies are loaded first, then session
        cookies (which can override). If a file does not exist or cannot be parsed, the method logs a warning
        and continues. This method is called automatically during :meth:`__init__` to restore session state
        from a previous run.
        :returns: None
        :rtype: None
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

    def __init__(self, config: Config | None = None) -> None:
        """Initialize an HTTP session configured for GameSheet WebUI access.

        Constructs a :class:`requests.Session` with automatic retry logic, a version-stamped User-Agent, and
        restores any previously-saved cookies from disk. The session is ready for immediate use after
        construction.

        :param config: Optional configuration object. If ``None``, a default
            :class:`~gamesheet_sdk.config.Config` is created.
        :type config: Config | None
        """
        self.config = config or Config()
        self._http = self._build_http_session()
        self._load_cookies()

    # -- public attribute access ------------------------------------------
    @property
    def cookies(self) -> RequestsCookieJar:
        """Underlying cookie jar.

        Mutating this affects subsequent requests.
        :returns: Return value.
        :rtype: RequestsCookieJar
        """
        return self._http.cookies

    @property
    def headers(self) -> MutableMapping[str, str | bytes]:
        """Default headers attached to every request from this session.

        The underlying mapping is a case-insensitive dict (as supplied by :class:`requests.Session`), but the
        declared return type matches the stub for :attr:`requests.Session.headers`.
        :returns: Return value.
        :rtype: MutableMapping[str, str | bytes]
        """
        return self._http.headers  # pyright: ignore[reportReturnType]

    def set_bearer_token(self, token: str) -> None:
        """Attach ``Authorization: Bearer <token>`` to all subsequent requests.

        Convenience for ``s.headers["Authorization"] = f"Bearer {token}"``.
        :param token: The bearer token to attach
        :type token: str
        """
        self._http.headers["Authorization"] = f"Bearer {token}"

    def _resolve(self, url: str) -> str:
        """Resolve a relative URL against the configured base URL.

        Absolute URLs (starting with ``http://`` or ``https://``) are returned as-is. Relative paths are
        joined to :attr:`Config.base_url`.
        :param url: An absolute URL or a path relative to the base URL.
        :type url: str
        :returns: String result.
        :rtype: str
        """
        if url.startswith(("http://", "https://")):
            return url
        return urljoin(self.config.base_url.rstrip("/") + "/", url.lstrip("/"))

    # -- request methods --------------------------------------------------
    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send an HTTP request, resolving ``url`` against the configured base URL.

        :param method: HTTP verb (GET, POST, etc.).
        :type method: str
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :param timeout: Per-request timeout override; falls back to :attr:`Config.timeout` if not supplied.
        :type timeout: float | None
        :returns: Return value.
        :rtype: requests.Response
        """
        full_url = self._resolve(url)
        effective_timeout = timeout if timeout is not None else self.config.timeout
        return self._http.request(method, full_url, timeout=effective_timeout, **kwargs)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a GET request.

        See :meth:`request`.
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :returns: Return value.
        :rtype: requests.Response
        """
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a POST request.

        See :meth:`request`.
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :returns: Return value.
        :rtype: requests.Response
        """
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a PUT request.

        See :meth:`request`.
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :returns: Return value.
        :rtype: requests.Response
        """
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a PATCH request.

        See :meth:`request`.
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :returns: Return value.
        :rtype: requests.Response
        """
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a DELETE request.

        See :meth:`request`.
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :type url: str
        :returns: Return value.
        :rtype: requests.Response
        """
        return self.request("DELETE", url, **kwargs)

    # -- lifecycle --------------------------------------------------------
    def save(self) -> None:
        """Persist the current cookie state to :attr:`Config.session_path`.

        The on-disk format preserves the full cookie attribute set (``domain``, ``path``, ``secure``,
        ``expires``) so that reloaded cookies are sent against the correct scopes.
        """
        path = self.config.session_path
        path.parent.mkdir(parents=True, exist_ok=True)
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
        path.write_text(json.dumps({"cookies": cookies}, indent=2, sort_keys=True))

    def close(self) -> None:
        """Persist cookies and release the underlying HTTP connection pool."""
        try:
            self.save()
        except OSError as exc:
            _LOGGER.warning("Failed to save session cookies: %s", exc)
        self._http.close()

    def __enter__(self) -> Session:
        """Enter the context manager, returning the Session instance.

        :returns: Return value.
        :rtype: Session
        """
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context manager, persisting cookies and closing the session.

        Called automatically at the end of a ``with`` block. Delegates to :meth:`close` to save state and
        release resources.
        :returns: None
        :rtype: None
        """
        self.close()
