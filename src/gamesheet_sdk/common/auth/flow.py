# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Login flow protocol for pluggable authentication strategies.

Defines: class:`LoginFlow`, the structural interface that both admin (browser-based) and teams (HTTP-only)
authentication implement. Downstream code that needs to authenticate — CLI commands, session construction
helpers — depends on this protocol rather than on a concrete login function, so the auth mechanism can vary
per pillar without changing the consumer.

**Example — using a LoginFlow implementation:**

.. code-block:: python

    from gamesheet_sdk.common.auth.flow import LoginFlow
    from gamesheet_sdk.common.auth.tokens import save_tokens
    from gamesheet_sdk.common.config import Config


    def run_login(flow: LoginFlow, config: Config) -> None:
        tokens = flow.authenticate(email="user@example.com")
        save_tokens(config, **tokens)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LoginFlow(Protocol):
    """Structural interface for authentication flows.

    Any class that exposes an ``authenticate`` method with the signature below is a valid :class:`LoginFlow` —
    no explicit inheritance needed (structural subtyping via :class:`typing.Protocol`).

    Implementations hold whatever state they need (a :class:`~gamesheet_sdk.common.config.Config`, a
    :class:`~gamesheet_sdk.common.browser.BrowserSession`, HTTP clients, etc.) and expose only the common
    ``authenticate`` entry point.

    The returned dict contains at minimum ``"access"`` and ``"refresh"`` keys.  Admin flows may also include
    ``"roles"``.  The shape matches :func:`~gamesheet_sdk.common.auth.tokens.refresh_access_token`'s return
    value and can be unpacked directly into :func:`~gamesheet_sdk.common.auth.tokens.save_tokens`.
    """

    def authenticate(
        self: LoginFlow,
        email: str | None = None,
        password: str | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, str]:
        """Authenticate with the GameSheet platform and return tokens.

        Credential resolution follows a standard fallback chain: explicit arguments → ``GAMESHEET_USERNAME`` /
        ``GAMESHEET_PASSWORD`` env vars → :class:`~gamesheet_sdk.common.config.Config` fields. Implementations
        raise :class:`~gamesheet_sdk.common.exceptions.AuthenticationError` when credentials are missing or
        authentication is rejected.

        Args:
            email (str | None): Login email, or ``None`` to resolve from config/env.
            password (str | None): Login password, or ``None`` to resolve from config/env.
            timeout (float | None): Auth round-trip timeout in seconds, or ``None`` for the implementation's
                default.

        Returns:
            dict[str, str]: Token bundle with at least ``"access"`` and ``"refresh"`` keys.

        Raises:
            ~gamesheet_sdk.common.exceptions.AuthenticationError: If credentials are missing or the auth
                backend rejects them.

        """
        _ = (email, password, timeout)
        return {}
