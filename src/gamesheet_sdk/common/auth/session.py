# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Authenticated sessions with automatic token refresh on 401/403."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
import logging
from typing import Any

import requests

from gamesheet_sdk.common.auth.tokens import refresh_access_token
from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import GameSheetError
from gamesheet_sdk.common.session import Session

_LOGGER = logging.getLogger(__name__)
OnRefreshCallback = Callable[[dict[str, str]], None]


class BaseAuthenticatedSession(Session, ABC):
    """Abstract base for sessions that auto-refresh their bearer on 401 or 403.

    Subclasses provide :meth:`_do_refresh` to perform the actual token refresh HTTP call against their
    pillar's endpoint. Everything else — constructor, retry logic, callback notification — is shared.

    On any 401 or 403 response the session calls :meth:`_do_refresh`, updates its bearer, optionally invokes
    ``on_refresh`` with the new token bundle, and retries the original request *once*. Both 401 and 403 are
    treated as authentication failures because different GameSheet API endpoints use different status codes
    for expired tokens. If the refresh itself fails the original response propagates to the caller.
    """

    def __init__(
        self: BaseAuthenticatedSession,
        config: Config | None = None,
        *,
        access_token: str,
        refresh_token: str,
        on_refresh: OnRefreshCallback | None = None,
    ) -> None:
        """Initialize an authenticated session with token auto-refresh on 401/403.

        :param config: Optional configuration object. If ``None``, a default
            :class:`~gamesheet_sdk.common.config.Config` is created.
        :type config: Config | None
        :param access_token: Current access token to use as the bearer in the ``Authorization`` header.
        :type access_token: str
        :param refresh_token: Refresh token used to renew the access token on 401/403 responses.
        :type refresh_token: str
        :param on_refresh: Optional callback invoked with a token dict after a successful token refresh. Use
            this to persist the new tokens to disk (e.g. via
            :func:`~gamesheet_sdk.common.auth.tokens.save_tokens`).
        :type on_refresh: OnRefreshCallback | None
        """
        super().__init__(config)
        self._refresh_token = refresh_token
        self._on_refresh = on_refresh
        self.set_bearer_token(access_token)

    @abstractmethod
    def _do_refresh(self: BaseAuthenticatedSession) -> dict[str, str]:
        """Perform the pillar-specific token refresh HTTP call.

        Subclasses call their own ``refresh_access_token()`` variant here and return the resulting token dict.

        :returns: Dictionary with at least ``access`` and ``refresh`` keys.
        :rtype: dict[str, str]
        :raises GameSheetError: On any refresh failure (propagated to :meth:`_try_refresh`).
        """

    def _notify_refresh(
        self: BaseAuthenticatedSession,
        new_tokens: dict[str, str],
    ) -> None:
        """Invoke the optional persistence callback, swallowing disk errors."""
        if self._on_refresh is None:
            return
        try:
            self._on_refresh(new_tokens)
        except OSError as exc:
            _LOGGER.warning("on_refresh callback failed to persist: %s", exc)

    def _try_refresh(self: BaseAuthenticatedSession) -> bool:
        """Run a single refresh round-trip; return whether the retry should happen."""
        try:
            new_tokens = self._do_refresh()
        except GameSheetError as exc:
            # nosemgrep
            _LOGGER.warning(
                "Token refresh failed: %s; surfacing original response.",
                exc,
            )
            return False
        self.set_bearer_token(new_tokens["access"])
        self._refresh_token = new_tokens["refresh"]
        self._notify_refresh(new_tokens)
        return True

    def request(
        self: BaseAuthenticatedSession,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send a request, refreshing the bearer and retrying once on 401 or 403.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.).
        :type method: str
        :param url: Target URL for the request.
        :type url: str
        :param timeout: Request timeout in seconds. If None, uses the timeout from
            :attr:`~gamesheet_sdk.common.session.Session.config`.
        :type timeout: float | None
        :param kwargs: Additional keyword arguments forwarded to the parent :meth:`request`.
        :type kwargs: Any
        :returns: HTTP response object from the request. If token refresh fails, returns the original 401/403
            response without raising an exception.
        :rtype: requests.Response
        """
        response = super().request(method, url, timeout=timeout, **kwargs)
        if response.status_code not in (401, 403):
            return response
        if not self._try_refresh():
            return response
        # nosemgrep
        _LOGGER.info("Refreshed access token; retrying %s %s.", method, url)
        return super().request(method, url, timeout=timeout, **kwargs)


class AuthenticatedSession(BaseAuthenticatedSession):
    """Admin-pillar session that refreshes via the admin token endpoint.

    Delegates to :func:`~gamesheet_sdk.common.auth.tokens.refresh_access_token`, forwarding the
    session's ``User-Agent`` header so the admin gateway can log the calling client.

    Example::

        from gamesheet_sdk.common.auth import load_access_token, load_refresh_token, save_tokens
        from gamesheet_sdk.common.auth.session import AuthenticatedSession
        from gamesheet_sdk.admin.associations import list_associations
        from gamesheet_sdk.common.config import Config
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

    def _do_refresh(self: AuthenticatedSession) -> dict[str, str]:
        """Refresh via the admin token endpoint, forwarding the session User-Agent."""
        return refresh_access_token(
            self._refresh_token,
            user_agent=str(self._http.headers.get("User-Agent", "")) or None,
            timeout=self.config.timeout,
        )
