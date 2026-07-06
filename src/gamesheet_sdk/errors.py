# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Error message templates for the GameSheet SDK.

This module centralizes all error message templates to ensure consistency across the codebase and make future
changes (like i18n) easier.
"""

from __future__ import annotations

# Authentication error messages
ERROR_MSG_401_GENERIC = (
    "Access token rejected (HTTP 401) for {context}. Use `gamesheet-sdk-py login` to authenticate."
)

ERROR_MSG_401_EXPIRED = (
    "Access token rejected (HTTP 401). Likely expired; "
    "re-run `gamesheet-sdk-py login` to refresh and try again."
)

ERROR_MSG_403_GENERIC = (
    "Access forbidden (HTTP 403) for {context}. "
    "Your session cookies may have expired. "
    "Use `gamesheet-sdk-py login` to re-authenticate."
)

ERROR_MSG_NO_SESSION = "No saved session found. Run `gamesheet-sdk-py login` first."

ERROR_MSG_REFRESH_REJECTED = "Refresh token rejected. Run `gamesheet-sdk-py login` to re-authenticate."

# Resource not found error messages
ERROR_MSG_404_RESOURCE = "Resource not found (HTTP 404) for {endpoint}"

ERROR_MSG_404_SEASON = (
    "Season '{season_id}' not found (HTTP 404). "
    "Make sure you're using a valid season ID. "
    "To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>"
)

# Generic HTTP error template
ERROR_MSG_GENERIC_HTTP = "{context} {endpoint} returned HTTP {status_code}: {text}"

# Domain-specific error messages
ERROR_MSG_LOCATION_NOT_FOUND = "Location '{location_id}' not found in available locations."

ERROR_MSG_BROADCASTER_INVALID = (
    "Broadcaster '{broadcaster_key}' is not valid. "
    "Use 'gamesheet-sdk-py games broadcasters list' to see valid options."
)

ERROR_MSG_GAME_TYPE_INVALID = "Game type '{game_type}' is not valid. Valid types: {valid_types}"

# BFF API error messages
ERROR_MSG_BFF_NON_SUCCESS = "BFF API returned non-success status: {status}. Response: {response}"

# Image upload error messages
ERROR_MSG_IMAGE_UPLOAD_FAILED = "Image upload failed: {error}"
