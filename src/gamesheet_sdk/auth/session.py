# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Authenticated session with automatic token refresh on 401."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

import requests

from gamesheet_sdk.auth.tokens import refresh_access_token
from gamesheet_sdk.config import Config
from gamesheet_sdk.exceptions import GameSheetError
from gamesheet_sdk.session import Session

_LOGGER = logging.getLogger(__name__)
OnRefreshCallback = Callable[[dict[str, str]], None]


class AuthenticatedSession(Session):
    """A :class:`Session` that auto-refreshes its bearer on 401 or 403.

    Wraps :class:`Session` with the refresh-on-auth-failure pattern that every bearer-authenticated API
    client ends up needing. Construction takes the current access + refresh tokens; the access token is
    attached as the bearer automatically. On any 401 or 403 response, the session calls
    :func:`refresh_access_token` against :data:`REFRESH_URL`, updates its bearer, optionally invokes
    ``on_refresh`` with the new token bundle, and retries the original request *once*. Both 401 and 403 are
    treated as authentication failures because different GameSheet API endpoints use different status codes
    for expired tokens. If the refresh itself fails the original response propagates to the caller, who can
    decide whether to log in again.

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
        """Initialize an authenticated session with token auto-refresh on 401/403.

        Constructs a :class:`~gamesheet_sdk.session.Session` with the given configuration, stores the refresh
        token for automatic renewal, and attaches the access token as the bearer. Optionally registers a
        callback to persist updated tokens after a successful refresh.

        :param config: Optional configuration object. If ``None``, a default
            :class:`~gamesheet_sdk.config.Config` is created.
        :type config: Config | None
        :param access_token: Current access token to use as the bearer in the ``Authorization`` header.
        :type access_token: str
        :param refresh_token: Refresh token used to renew the access token on 401/403 responses.
        :type refresh_token: str
        :param on_refresh: Optional callback invoked with a ``{"access": ..., "refresh": ...}`` dict after a
            successful token refresh. Use this to persist the new tokens to disk (e.g. via
            :func:`~gamesheet_sdk.auth.tokens.save_tokens`).
        :type on_refresh: OnRefreshCallback | None
        """
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
        except OSError as exc:
            _LOGGER.warning("on_refresh callback failed to persist: %s", exc)

    def _try_refresh(self) -> bool:
        """Run a single refresh round-trip; return whether the retry should happen."""
        try:
            new_tokens = refresh_access_token(
                self._refresh_token,
                user_agent=str(self._http.headers.get("User-Agent", "")) or None,
                timeout=self.config.timeout,
            )
        except GameSheetError as exc:
            # nosemgrep: python.lang.security.audit.logging.logger-credential-leak
            _LOGGER.warning("Token refresh failed: %s; surfacing 401.", exc)
            return False
        self.set_bearer_token(new_tokens["access"])
        self._refresh_token = new_tokens["refresh"]
        self._notify_refresh(new_tokens)
        return True

    # pylint: disable-next=missing-param-doc
    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send a request, refreshing the bearer and retrying once on 401 or 403.

        Performs the request using the parent :class:`~gamesheet_sdk.session.Session.request` method. If the
        response status is 401 Unauthorized or 403 Forbidden, attempts to refresh the access token using the
        stored refresh token, updates the bearer token, invokes the ``on_refresh`` callback if provided, and
        retries the original request exactly once. Both 401 and 403 are treated as authentication failures
        because different GameSheet API endpoints use different status codes for expired tokens.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.).
        :type method: str
        :param url: Target URL for the request.
        :type url: str
        :param timeout: Request timeout in seconds. If None, uses the timeout from
            :attr:`~gamesheet_sdk.session.Session.config`.
        :type timeout: float | None
        :returns: HTTP response object from the request. If token refresh fails, returns the original 401/403
            response without raising an exception.
        :rtype: requests.Response
        """
        response = super().request(method, url, timeout=timeout, **kwargs)
        if response.status_code not in (401, 403):
            return response
        if not self._try_refresh():
            return response
        # nosemgrep: python.lang.security.audit.logging.logger-credential-leak
        _LOGGER.info("Refreshed access token; retrying %s %s.", method, url)
        return super().request(method, url, timeout=timeout, **kwargs)
