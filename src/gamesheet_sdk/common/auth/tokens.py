# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Token loading, saving, and refreshing.

This module provides functions for managing GameSheet authentication tokens:

- Loading access and refresh tokens from browser storage state
- Saving updated tokens back to persistent storage
- Refreshing expired access tokens using refresh tokens

The token storage mechanism uses a browser storage state file (JSON) that
mirrors the structure of Playwright's persistent context storage. This allows
tokens to be shared between headless browser sessions and direct HTTP sessions.

**Example:**

Load existing tokens and refresh if needed:

.. code-block:: python
        from gamesheet_sdk.common.config import Config
        from gamesheet_sdk.common.auth.tokens import (
            load_access_token,
            load_refresh_token,
            refresh_access_token,
            save_tokens,
        )

        config = Config()
        access = load_access_token(config)
        refresh = load_refresh_token(config)
        if access is None and refresh is not None:
            # Refresh the access token
            tokens = refresh_access_token(refresh)
            save_tokens(
                config,
                access=tokens["access"],
                refresh=tokens["refresh"],
                roles=tokens["roles"],
            )
"""

from __future__ import annotations

import json

import requests

from gamesheet_sdk.common.auth.constants import REFRESH_TIMEOUT_S, REFRESH_URL
from gamesheet_sdk.common.auth.storage import (
    apply_local_storage_updates,
    load_local_storage_value,
    origin_entry_for,
    read_state_or_empty,
)
from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError


def load_access_token(config: Config) -> str | None:
    """Read the SPA's access token from the saved browser storage state.

    Returns the value of the ``accessToken`` localStorage entry for the SPA's
    origin (``Config.base_url``), or ``None`` if the storage state file is missing,
    unreadable, or does not contain a token. The access token is used for
    authenticating API requests and typically has a short lifetime (10 minutes).

    **Example:**

    .. code-block:: python

        from gamesheet_sdk.common.auth.tokens import load_access_token
        from gamesheet_sdk.common.config import Config

        config = Config()
        token = load_access_token(config)
        if token:
            print("Access token loaded successfully")

    Args:
        config (Config): Configuration object containing the base URL
            and browser state path.

    Returns:
        str | None: The access token string if found, otherwise
        ``None``.
    """
    return load_local_storage_value(config, "accessToken")


def load_refresh_token(config: Config) -> str | None:
    """Read the SPA's refresh token from the saved browser storage state.

    Companion to :func:`load_access_token`. Returns the value of the ``refreshToken``
    localStorage entry. Used to drive :func:`refresh_access_token` and
    :class:`~gamesheet_sdk.common.auth.session.AuthenticatedSession`.

    Args:
        config (Config): Configuration object containing the base URL
            and browser state path.

    Returns:
        str | None: The refresh token string if found, otherwise
        ``None``.
    """
    return load_local_storage_value(config, "refreshToken")


def build_token_updates(
    *,
    access: str,
    refresh: str | None,
    roles: str | None,
) -> dict[str, str]:
    """Build a localStorage-update dict from the present keyword arguments.

    Creates a dictionary mapping localStorage keys to token values, including
    only the tokens that were provided (non-``None``). This is used internally by
    :func:`save_tokens` to prepare the updates for browser storage.

    **Example:**

    .. code-block:: python

        updates = build_token_updates(
            access="access_token_value",
            refresh="refresh_token_value",
            roles=None,
        )
        sorted(updates.keys())
        # ['accessToken', 'refreshToken']

    Args:
        access (str): The access token to store (required).
        refresh (str | None): The refresh token to store, or ``None`` to
            skip.
        roles (str | None): The roles token to store, or ``None`` to
            skip.

    Returns:
        dict[str, str]: Dictionary mapping localStorage keys
        (``accessToken``, ``refreshToken``, ``rolesToken``) to their
        values.
    """
    updates: dict[str, str] = {"accessToken": access}
    if refresh is not None:
        updates["refreshToken"] = refresh

    if roles is not None:
        updates["rolesToken"] = roles

    return updates


def save_tokens(
    config: Config,
    *,
    access: str,
    refresh: str | None = None,
    roles: str | None = None,
) -> None:
    """Persist new token values back into the saved browser storage state.

    Reads :attr:`Config.browser_state_path` (or starts with an empty state if
    it is missing or malformed), updates the localStorage entries for
    ``config.base_url`` in place, and writes the file back. Only the keys
    that were passed are written; unspecified ones are left alone. Both
    :class:`~gamesheet_sdk.common.browser.BrowserSession` and direct token loading
    use this same storage format, making them mutually compatible.

    **Example:**

    Save tokens after a successful refresh:

    .. code-block:: python

        from gamesheet_sdk.common.config import Config
        from gamesheet_sdk.common.auth.tokens import save_tokens

        config = Config()
        save_tokens(
            config,
            access="new_access_token",
            refresh="new_refresh_token",
            roles="roles_token",
        )

    Args:
        config (Config): Configuration object containing the base URL
            and browser state path where tokens will be saved.
        access (str): The access token to save (required).
        refresh (str | None): The refresh token to save, or ``None`` to
            leave unchanged.
        roles (str | None): The roles token to save, or ``None`` to
            leave unchanged.
    """
    path = config.browser_state_path
    state = read_state_or_empty(path)
    origin_entry = origin_entry_for(state, config.base_url)
    apply_local_storage_updates(
        origin_entry.setdefault("localStorage", []),
        build_token_updates(access=access, refresh=refresh, roles=roles),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def refresh_access_token(
    refresh_token: str,
    *,
    user_agent: str | None = None,
    timeout: float = REFRESH_TIMEOUT_S,
) -> dict[str, str]:
    """Exchange refresh_token for a fresh {access, refresh, roles} bundle.

    POSTs to :data:`~gamesheet_sdk.common.auth.constants.REFRESH_URL` with
    ``Authorization: Bearer <refresh_token>`` and an empty JSON body. The gateway
    returns a new access token (10-min TTL), a new refresh token (long TTL,
    replaces the one you sent), and a roles token.

    This is a standalone HTTP call that does not use a :class:`~requests.Session`,
    so it can be used from inside
    :class:`~gamesheet_sdk.common.auth.session.AuthenticatedSession`'s retry path without
    recursing.

    **Example:**

    Refresh an expired access token:

    .. code-block:: python

        from gamesheet_sdk.common.auth.tokens import (
            load_refresh_token,
            refresh_access_token,
            save_tokens,
        )
        from gamesheet_sdk.common.config import Config

        config = Config()
        refresh = load_refresh_token(config)
        if refresh:
            try:
                tokens = refresh_access_token(refresh)
                save_tokens(
                    config,
                    access=tokens["access"],
                    refresh=tokens["refresh"],
                    roles=tokens["roles"],
                )
            except AuthenticationError:
                print("Refresh token expired, please log in again")

    Args:
        refresh_token (str): The refresh token to exchange for new
            tokens.
        user_agent (str | None): Optional User-Agent header value for
            the request.
        timeout (float): Request timeout in seconds. Defaults to
            :data:`~gamesheet_sdk.common.auth.constants.REFRESH_TIMEOUT_
            S`.

    Returns:
        dict[str, str]: Dictionary with keys ``access``, ``refresh``,
        and ``roles``, each containing the corresponding token string.

    Raises:
        AuthenticationError: If the refresh token is rejected (HTTP
            401). This typically means the token has expired and the
            user needs to re-authenticate via ``gamesheet-admin login``.
        GameSheetError: For any other non-2xx HTTP response from the
            token refresh endpoint.
    """
    headers = {
        "Authorization": f"Bearer {refresh_token}",
        "Content-Type": "application/json",
    }
    if user_agent is not None:
        headers["User-Agent"] = user_agent

    response = requests.post(REFRESH_URL, json={}, headers=headers, timeout=timeout)
    if response.status_code == 401:
        _err_msg = "Refresh token rejected. Run `gamesheet-admin login` to re-authenticate."
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
