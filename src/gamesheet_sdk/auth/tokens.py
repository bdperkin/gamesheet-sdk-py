"""Token loading, saving, and refreshing."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import requests

from gamesheet_sdk.auth.constants import REFRESH_TIMEOUT_S, REFRESH_URL
from gamesheet_sdk.auth.storage import (
    apply_local_storage_updates,
    load_local_storage_value,
    origin_entry_for,
    read_state_or_empty,
)
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:

    from gamesheet_sdk.config import Config
_LOGGER = logging.getLogger(__name__)


def load_access_token(config: Config) -> str | None:
    """Read the SPA's access token from the saved browser storage state.

    Returns the value of the ``accessToken`` localStorage entry for the SPA's origin (``Config.base_url``), or
    None if the storage state file is missing, unreadable, or does not contain a token. Intended to be
    attached
    """
    return load_local_storage_value(config, "accessToken")


def load_refresh_token(config: Config) -> str | None:
    """Read the SPA's refresh token from the saved browser storage state.

    Companion to :func:`load_access_token`. Used to drive :func:`refresh_access_token` and
    :class:`AuthenticatedSession`.
    """
    return load_local_storage_value(config, "refreshToken")


def build_token_updates(
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


def save_tokens(
    config: Config,
    *,
    access: str,
    refresh: str | None = None,
    roles: str | None = None,
) -> None:
    """Persist new token values back into the saved browser storage state.

    Reads :attr:`Config.browser_state_path` (or starts with an empty state if it is missing or malformed),
    updates the localStorage entries for ``config.base_url`` in place, and writes the file back. Only the keys
    that were passed are written; unspecified ones are left alone. The companion ``BrowserSession`` either
    path are mutually compatible.
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

    POSTs to :data:`REFRESH_URL` with ``Authorization: Bearer <refresh_token>`` and an empty JSON body. The
    gateway returns a new access token (10-min TTL), a new refresh token (long TTL, replaces the one you
    sent), Standalone HTTP call -- no :class:`Session` needed, so it can be used from inside
    :class:`AuthenticatedSession`'s retry path without recursing.
    :raises AuthenticationError: If the refresh token is rejected (401).
    :raises GameSheetError: For any other non-2xx response.
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
