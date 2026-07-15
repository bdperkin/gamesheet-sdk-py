# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Authentication-related constants and configuration values.

This module defines all authentication constants used throughout the
:mod:`gamesheet_sdk.common.auth` package, including URL paths, endpoints, and timing
parameters for login flows and token operations.
Constants
---------
LOGIN_PATH : str
    Path for the login form relative to the base URL.
POST_LOGIN_PATH : str
    Default destination after successful authentication.
FIREBASE_AUTH_HOST : str
    Firebase Authentication service hostname.
FIREBASE_AUTH_PATH : str
    Firebase Authentication endpoint path.
TOKEN_EXCHANGE_PATH : str
    GameSheet token exchange API endpoint.
REFRESH_URL : str
    Full URL for refreshing access tokens.
REFRESH_TIMEOUT_S : float
    Timeout in seconds for token refresh operations.
DEFAULT_TIMEOUT_S : float
    Default timeout in seconds for HTTP requests.
POLL_INTERVAL_MS : int
    Polling interval in milliseconds for browser state checks.
POST_LOGIN_NAVIGATION_TIMEOUT_MS : int
    Timeout in milliseconds for post-login navigation.
FORM_DETECTION_TIMEOUT_MS : int
    Timeout in milliseconds for detecting the login form.
Examples
--------
Using authentication constants in login flows:
.. code-block:: python
    from gamesheet_sdk.common.auth.constants import (
        LOGIN_PATH,
        POST_LOGIN_PATH,
        DEFAULT_TIMEOUT_S,
    )

    # Construct login URL
    login_url = f"{base_url}{LOGIN_PATH}"
    # Use timeout in HTTP request
    response = session.get(login_url, timeout=DEFAULT_TIMEOUT_S)
Using timeout constants with Playwright:
.. code-block:: python
    from gamesheet_sdk.common.auth.constants import (
        FORM_DETECTION_TIMEOUT_MS,
        POST_LOGIN_NAVIGATION_TIMEOUT_MS,
    )

    # Wait for login form to appear
    page.wait_for_selector("#email", timeout=FORM_DETECTION_TIMEOUT_MS)
    # Wait for post-login navigation
    page.wait_for_url(pattern, timeout=POST_LOGIN_NAVIGATION_TIMEOUT_MS)
Using Firebase and token exchange constants:
.. code-block:: python
    from gamesheet_sdk.common.auth.constants import (
        FIREBASE_AUTH_HOST,
        FIREBASE_AUTH_PATH,
        TOKEN_EXCHANGE_PATH,
    )

    # Build Firebase auth URL
    firebase_url = f"https://{FIREBASE_AUTH_HOST}{FIREBASE_AUTH_PATH}"
    # Build token exchange URL
    token_url = f"{base_url}{TOKEN_EXCHANGE_PATH}"
"""

from __future__ import annotations

from typing import Final

from gamesheet_sdk.common.constants import DEFAULT_BASE_URL

# Path on which the SDK drives the login form, relative to Config.base_url.
# GameSheet's SPA renders the login form inline at the same route that becomes
# the authenticated dashboard, rather than at a dedicated /users/sign_in route.
# Driving the form here lets the same SPA instance handle the unauthenticated
# to authenticated transition in place, so its post-login data fetches happen
# with context preserved and the saved storage state captures a fully-settled
# session.
LOGIN_PATH: Final[str] = "/associations"
# Default destination after a successful login.
# Navigating here after the auth round-trip lets the SPA fetch the user's
# permissions, association list, and any other post-login state that the
# dashboard caches in cookies / localStorage. Without this navigation the
# saved browser state captures only "authenticated, pre-routing", which
# makes subsequent runs look unprivileged to the SPA.
POST_LOGIN_PATH: Final[str] = "/associations"
# Firebase Auth host and endpoint
FIREBASE_AUTH_HOST: Final[str] = "identitytoolkit.googleapis.com"
FIREBASE_AUTH_PATH: Final[str] = ":signInWithPassword"
FIREBASE_AUTH_URL: Final[str] = f"https://{FIREBASE_AUTH_HOST}/v1/accounts{FIREBASE_AUTH_PATH}"
# GameSheet token exchange endpoint
TOKEN_EXCHANGE_PATH: Final[str] = "/api/token"
TOKEN_EXCHANGE_URL: Final[str] = f"{DEFAULT_BASE_URL}{TOKEN_EXCHANGE_PATH}"
# Endpoint that mints a fresh access token from a valid refresh token.
REFRESH_URL: Final[str] = "https://gateway-authserver-awy26srzoa-nn.a.run.app/auth/v4/refresh"
# Timeouts
REFRESH_TIMEOUT_S: Final[float] = 30.0
DEFAULT_TIMEOUT_S: Final[float] = 15.0
POLL_INTERVAL_MS: Final[int] = 100
POST_LOGIN_NAVIGATION_TIMEOUT_MS: Final[int] = 30_000
# Generous window for the unauthenticated landing page to render the form
# if it's going to. If a saved storage state already authenticates the user,
# the SPA renders the dashboard instead and no #email ever appears.
FORM_DETECTION_TIMEOUT_MS: Final[int] = 5_000
