"""Reusable HTTP session for talking to the GameSheet WebUI.

Wraps :class:`requests.Session` with the bits every WebUI workflow.

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

import json
import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _resolved_version
from typing import TYPE_CHECKING, Any, Iterator
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from gamesheet_sdk.config import Config

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from http.cookiejar import Cookie
    from types import TracebackType

    from requests.cookies import RequestsCookieJar


def _default_user_agent() -> str:
    """Build the SDK's default ``User-Agent`` from installed metadata.

    Reads from the package's distribution metadata (which is set in `pyproject.toml` and managed by PSR)
    rather than importing ``__version__`` from the parent module, so this module stays free of cyclic imports.
    """
    try:
        ver = _resolved_version("gamesheet-sdk-py")
    except PackageNotFoundError:  # pragma: no cover
        ver = "0+unknown"
    return f"gamesheet-sdk-py/{ver} (+https://github.com/bdperkin/gamesheet-sdk-py)"


_LOGGER = logging.getLogger(__name__)
# Retry on transient server-side and gateway errors only.
_DEFAULT_RETRY_STATUSES = frozenset({500, 502, 503, 504})
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
    The context-manager form persists cookies on exit. If you do not use
    ``with``, call :meth:`Session.close` explicitly to save state.
    """

    # -- internals --------------------------------------------------------
    def _build_http_session(self) -> requests.Session:
        """Construct and configure the underlying :class:`requests.Session`.

        Attaches a User-Agent header and mounts an HTTPAdapter with retry logic for transient server-side and
        network errors. Retries apply only to idempotent methods (GET, HEAD, OPTIONS, PUT, DELETE); POST is
        excluded to avoid double-submission.
        :returns: A configured :class:`requests.Session` instance.
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
        """Restore cookies from disk if :attr:`Config.session_path` exists.

        Reads JSON-serialized cookie data and populates the underlying session's cookie jar. If the file does
        not exist or cannot be parsed, the method logs a warning and continues with an empty jar. This method
        is called automatically during :meth:`__init__` to restore session state from a previous run.
        """
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
        self.config = config or Config()
        self._http = self._build_http_session()
        self._load_cookies()

    # -- public attribute access ------------------------------------------
    @property
    def cookies(self) -> RequestsCookieJar:
        """Underlying cookie jar.

        Mutating this affects subsequent requests.
        """
        return self._http.cookies

    @property
    def headers(self) -> MutableMapping[str, str | bytes]:
        """Default headers attached to every request from this session.

        The underlying mapping is a case-insensitive dict (as supplied by :class:`requests.Session`), but the
        declared return type matches the stub for :attr:`requests.Session.headers`.
        """
        return self._http.headers  # pyright: ignore[reportReturnType]

    def set_bearer_token(self, token: str) -> None:
        """Attach ``Authorization: Bearer <token>`` to all subsequent requests.

        Convenience for ``s.headers["Authorization"] = f"Bearer {token}"``.
        """
        self._http.headers["Authorization"] = f"Bearer {token}"

    def _resolve(self, url: str) -> str:
        """Resolve a relative URL against the configured base URL.

        Absolute URLs (starting with ``http://`` or ``https://``) are returned as-is. Relative paths are
        joined to :attr:`Config.base_url`.
        :param url: An absolute URL or a path relative to the base URL.
        :returns: The fully-qualified URL.
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
        :param url: Absolute URL, or a path relative to :attr:`Config.base_url`.
        :param timeout: Per-request timeout override; falls back to :attr:`Config.timeout` if not supplied.
        :param kwargs: Forwarded to :meth:`requests.Session.request`.
        :returns: The :class:`requests.Response` returned by the server.
        """
        full_url = self._resolve(url)
        effective_timeout = timeout if timeout is not None else self.config.timeout
        return self._http.request(method, full_url, timeout=effective_timeout, **kwargs)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a GET request.

        See :meth:`request`.
        """
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a POST request.

        See :meth:`request`.
        """
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a PUT request.

        See :meth:`request`.
        """
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a PATCH request.

        See :meth:`request`.
        """
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        """Send a DELETE request.

        See :meth:`request`.
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
        except OSError as exc:  # pragma: no cover
            _LOGGER.warning("Failed to save session cookies: %s", exc)
        self._http.close()

    def __enter__(self) -> Session:
        """Enter the context manager, returning the Session instance.

        :returns: This Session instance for use in the ``with`` block.
        """
        return self

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_val: BaseException | None,
        __exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context manager, persisting cookies and closing the session.

        Called automatically at the end of a ``with`` block. Delegates to :meth:`close` to save state and
        release resources.
        """
        self.close()
