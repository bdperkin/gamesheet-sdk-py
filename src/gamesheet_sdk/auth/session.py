"""Authenticated session with automatic token refresh on 401."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import requests

from gamesheet_sdk.auth.tokens import refresh_access_token
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.session import Session

if TYPE_CHECKING:

    from gamesheet_sdk.config import Config
_LOGGER = logging.getLogger(__name__)
OnRefreshCallback = Callable[[dict[str, str]], None]


class AuthenticatedSession(Session):
    """A :class:`Session` that auto-refreshes its bearer on 401.

    Wraps :class:`Session` with the refresh-on-401 pattern that every bearer-authenticated API client ends
    up needing. Construction takes the current access + refresh tokens; the access token is attached as the
    bearer automatically. On any 401 response, the session calls :func:`refresh_access_token` against
    :data:`REFRESH_URL`, updates its bearer, optionally invokes ``on_refresh`` with the new token bundle, and
    retries the original request *once*. If the refresh itself fails the original 401 propagates to the
    caller, who can decide whether to log in again.

    Example::

        from gamesheet_sdk.auth import load_access_token, load_refresh_token, save_tokens
        from gamesheet_sdk.auth.session import AuthenticatedSession
        from gamesheet_sdk.associations import list_associations
        from gamesheet_sdk.config import Config

        config = Config()
        with AuthenticatedSession(
            config,
            access_token=load_access_token(config),
            refresh_token=load_refresh_token(config),
            on_refresh=lambda tokens: save_tokens(config, **tokens),
        ) as s:
            for assoc in list_associations(s):
                print(assoc.name)
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
            # nosemgrep: python.lang.security.audit.logging.logger-credential-leak
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
        """Send a request, refreshing the bearer and retrying once on 401.

        Performs the request using the parent :class:`~gamesheet_sdk.session.Session.request` method. If the
        response status is 401 Unauthorized, attempts to refresh the access token using the stored refresh
        token, updates the bearer token, invokes the ``on_refresh`` callback if provided, and retries the
        original request exactly once.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.).
        :param url: Target URL for the request.
        :param timeout: Request timeout in seconds. If None, uses the timeout from
            :attr:`~gamesheet_sdk.session.Session.config`.
        :param kwargs: Additional keyword arguments passed through to :meth:`requests.Session.request` (e.g.,
            headers, json, data, params).
        :returns: HTTP response object from the request. If token refresh fails, returns the original 401
            response without raising an exception.
        :raises requests.RequestException: On network or HTTP errors other than 401.
        """
        response = super().request(method, url, timeout=timeout, **kwargs)
        if response.status_code != 401:

            return response

        if not self._try_refresh():

            return response
        # nosemgrep: python.lang.security.audit.logging.logger-credential-leak
        _LOGGER.info("Refreshed access token; retrying %s %s.", method, url)
        return super().request(method, url, timeout=timeout, **kwargs)
