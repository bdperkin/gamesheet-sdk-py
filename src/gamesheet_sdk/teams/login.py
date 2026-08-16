# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""HTTP-only login flow for the GameSheet teams dashboard.

Authenticates against the same Firebase project as the admin dashboard (``gamesheet-production``) but uses
pure HTTP calls instead of headless browser automation:

1. ``POST`` Firebase REST ``signInWithPassword`` with the project's API key.
2. ``GET /api/auth/tokens`` on the teams API gateway, exchanging the Firebase ID token for application-level
    access and refresh tokens.

The resulting tokens are persisted via :func:`~gamesheet_sdk.common.auth.tokens.save_tokens` so that
subsequent CLI commands can authenticate without repeating the login flow.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import requests

from gamesheet_sdk.common.auth.constants import DEFAULT_TIMEOUT_S, FIREBASE_AUTH_URL
from gamesheet_sdk.common.auth.credentials import resolve_email, resolve_password
from gamesheet_sdk.common.auth.firebase import extract_firebase_error
from gamesheet_sdk.common.auth.tokens import save_tokens
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.shared.constants import (
    FIREBASE_API_KEY,
    TEAMS_API_GATEWAY,
    TEAMS_REFRESH_PATH,
    TEAMS_TOKEN_EXCHANGE_PATH,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config

_LOGGER = logging.getLogger(__name__)


def _firebase_error_message(response: requests.Response) -> str:
    """Extract a readable error from a Firebase Auth failure response.

    Parses the ``requests`` response JSON and delegates to
    :func:`~gamesheet_sdk.common.auth.firebase.extract_firebase_error`.

    Args:
        response (requests.Response): HTTP response from Firebase Auth endpoint.

    Returns:
        str: Extracted error message or HTTP status fallback.

    """
    try:
        body: dict[str, Any] = response.json()
    except (ValueError, KeyError):
        return f"HTTP {response.status_code}"

    return extract_firebase_error(body, response.status_code)


def _firebase_sign_in(email: str, password: str, *, timeout: float) -> str:
    """Authenticate with Firebase REST API and return the ID token.

    Args:
        email (str): User email address.
        password (str): User password.
        timeout (float): Request timeout in seconds.

    Returns:
        str: Firebase ID token string.

    Raises:
        AuthenticationError: If Firebase rejects the credentials.

    """
    url = f"{FIREBASE_AUTH_URL}?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload, timeout=timeout)
    if response.status_code != HTTPStatus.OK:
        _err_msg = f"Login rejected by Firebase: {_firebase_error_message(response)}"
        raise AuthenticationError(_err_msg)

    return str(response.json()["idToken"])


def _exchange_id_token(id_token: str, *, timeout: float) -> dict[str, str]:
    """Exchange a Firebase ID token for teams application tokens.

    Args:
        id_token (str): Firebase ID token from :func:`_firebase_sign_in`.
        timeout (float): Request timeout in seconds.

    Returns:
        dict[str, str]: Dictionary with ``"access"`` and ``"refresh"`` keys.

    Raises:
        AuthenticationError: If the token exchange fails.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_TOKEN_EXCHANGE_PATH}"
    headers = {"Authorization": f"Bearer {id_token}"}
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code != HTTPStatus.OK:
        _err_msg = f"Teams token exchange failed (HTTP {response.status_code})."
        raise AuthenticationError(_err_msg)

    tokens = response.json()["tokens"]
    return {"access": tokens["access"], "refresh": tokens["refresh"]}


def refresh_access_token(
    refresh_token: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, str]:
    """Exchange a refresh token for a fresh ``{access, refresh}`` pair via the teams API gateway.

    POSTs to :data:`~gamesheet_sdk.teams.shared.constants.TEAMS_REFRESH_PATH` with ``Authorization: Bearer
    <refresh_token>`` and an empty JSON body. The gateway returns a new access token and a replacement refresh
    token.

    This is a standalone HTTP call that does not use a :class:`~requests.Session`, so it can be called from
    inside an auto-refresh retry path without recursing.

    Args:
        refresh_token (str): The refresh token to exchange for new tokens.
        timeout (float): Request timeout in seconds. Defaults to
            :data:`~gamesheet_sdk.common.auth.constants.DEFAULT_TIMEOUT_S`.

    Returns:
        dict[str, str]: Dictionary with keys ``access`` and ``refresh``, each containing the corresponding
            token string.

    Raises:
        AuthenticationError: If the refresh token is rejected (HTTP 401). This typically means the token has
            expired and the user needs to re-authenticate via ``gamesheet-teams login``.
        GameSheetError: For any other non-2xx HTTP response from the token refresh endpoint.

    """
    url = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"
    headers = {
        "Authorization": f"Bearer {refresh_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json={}, headers=headers, timeout=timeout)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        _err_msg = "Refresh token rejected. Run `gamesheet-teams login` to re-authenticate."
        raise AuthenticationError(_err_msg)

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        _err_msg = f"Token refresh failed: HTTP {response.status_code}: {response.text[:200]!r}"
        raise GameSheetError(_err_msg)

    body = response.json()
    return {"access": body["access"], "refresh": body["refresh"]}


class TeamsLoginFlow:
    """HTTP-based :class:`~gamesheet_sdk.common.auth.flow.LoginFlow` for the teams dashboard.

    Authenticates via two sequential HTTP calls — Firebase REST ``signInWithPassword`` followed by a token
    exchange against the teams API gateway — without requiring a headless browser.

    Example:
        Authenticating with the teams dashboard:

        .. code-block:: python

            from gamesheet_sdk.common.config import Config
            from gamesheet_sdk.teams.login import TeamsLoginFlow

            config = Config(base_url="https://teams.gamesheet.app")
            flow = TeamsLoginFlow(config)
            tokens = flow.authenticate(email="user@example.com", password="secret")
            print(tokens["access"])

    Args:
        config (Config): SDK configuration (credentials, URLs, storage paths).

    """

    def __init__(self: TeamsLoginFlow, config: Config) -> None:
        """Initialize TeamsLoginFlow with SDK config.

        Args:
            config (Config): SDK configuration (credentials, URLs, storage paths).

        """
        self._config = config

    def authenticate(
        self: TeamsLoginFlow,
        email: str | None = None,
        password: str | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, str]:
        """Run the HTTP-only teams login and return tokens.

        Resolves credentials from the arguments or :class:`~gamesheet_sdk.common.config.Config`, authenticates
        with Firebase, exchanges the ID token for application tokens, and persists them to disk.

        Args:
            email (str | None): Login email, or ``None`` to resolve from config/env.
            password (str | None): Login password, or ``None`` to resolve from config/env.
            timeout (float | None): HTTP request timeout in seconds, or ``None`` for the default.

        Returns:
            dict[str, str]: Token bundle with ``"access"`` and ``"refresh"`` keys.

        Raises:
            ~gamesheet_sdk.common.exceptions.AuthenticationError: If credentials are missing, Firebase rejects
                them, or the token exchange fails.

        """
        resolved_email = resolve_email(self._config, email)
        resolved_password = resolve_password(self._config, password)
        timeout_s = timeout if timeout is not None else DEFAULT_TIMEOUT_S
        id_token = _firebase_sign_in(
            resolved_email,
            resolved_password,
            timeout=timeout_s,
        )
        tokens = _exchange_id_token(id_token, timeout=timeout_s)
        save_tokens(self._config, access=tokens["access"], refresh=tokens["refresh"])
        _LOGGER.info("Teams login succeeded for %s.", resolved_email)
        return tokens
