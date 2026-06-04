"""Authentication-related constants and configuration values."""

from __future__ import annotations

# Path on which the SDK drives the login form, relative to Config.base_url.
# GameSheet's SPA renders the login form inline at the same route that becomes
# the authenticated dashboard, rather than at a dedicated /users/sign_in route.
# Driving the form here lets the same SPA instance handle the unauthenticated
# to authenticated transition in place, so its post-login data fetches happen
# with context preserved and the saved storage state captures a fully-settled
# session.
LOGIN_PATH = "/associations"
# Default destination after a successful login.
# Navigating here after the auth round-trip lets the SPA fetch the user's
# permissions, association list, and any other post-login state that the
# dashboard caches in cookies / localStorage. Without this navigation the
# saved browser state captures only "authenticated, pre-routing", which
# makes subsequent runs look unprivileged to the SPA.
POST_LOGIN_PATH = "/associations"
# Firebase Auth host and endpoint
FIREBASE_AUTH_HOST = "identitytoolkit.googleapis.com"
FIREBASE_AUTH_PATH = ":signInWithPassword"
# GameSheet token exchange endpoint
TOKEN_EXCHANGE_PATH = "/api/token"  # noqa: S105 # nosec B105
# Endpoint that mints a fresh access token from a valid refresh token.
REFRESH_URL = "https://gateway-authserver-awy26srzoa-nn.a.run.app/auth/v4/refresh"
# Timeouts
REFRESH_TIMEOUT_S = 30.0
DEFAULT_TIMEOUT_S = 15.0
POLL_INTERVAL_MS = 100
POST_LOGIN_NAVIGATION_TIMEOUT_MS = 30_000
# Generous window for the unauthenticated landing page to render the form
# if it's going to. If a saved storage state already authenticates the user,
# the SPA renders the dashboard instead and no #email ever appears.
FORM_DETECTION_TIMEOUT_MS = 5_000
