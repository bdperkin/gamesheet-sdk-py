# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Error message templates for the GameSheet SDK.

This module centralizes all error message templates to ensure consistency across the codebase and make future
changes (like i18n) easier.
"""

from __future__ import annotations

from gamesheet_sdk.shared.constants import HELP_USE_SEASONS_LIST

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

# Resource not found error messages (HTTP 404)
ERROR_MSG_404_RESOURCE = "Resource not found (HTTP 404) for {endpoint}"

# Generic 404 templates
ERROR_MSG_404_OBJECT_NOT_FOUND = "{object_type} '{object_id}' not found (HTTP 404). {help_text}"

ERROR_MSG_404_OBJECT_IN_PARENT = (
    "{object_type} '{object_id}' not found in {parent_type} '{parent_id}' (HTTP 404). {help_text}"
)

ERROR_MSG_404_REPORT_NOT_FOUND = (
    "Report not found for {object_type} with external_id '{external_id}' (HTTP 404). {help_text}"
)

ERROR_MSG_404_NO_ITEMS_OR_INVALID = (
    "No {item_type} found or invalid {parent_type} ID '{parent_id}' (HTTP 404). {help_text}"
)

# Specific resource 404 messages
ERROR_MSG_404_SEASON = (
    "Season '{season_id}' not found (HTTP 404). "
    "Make sure you're using a valid season ID, not a league ID. "
    f"{HELP_USE_SEASONS_LIST}"
)

ERROR_MSG_404_LEAGUE = (
    "League '{league_id}' not found (HTTP 404). "
    "Make sure you're using a valid league ID. "
    "To get valid league IDs, run: gamesheet-sdk-py leagues list"
)

ERROR_MSG_404_TEAM = (
    "Team '{team_id}' not found (HTTP 404). "
    "Make sure you're using a valid team ID. "
    "To get valid team IDs, run: gamesheet-sdk-py teams list --season-id {season_id}"
)

ERROR_MSG_404_REFEREE_IN_SEASON = (
    "Referee '{referee_id}' not found in season '{season_id}' (HTTP 404). "
    "Make sure you're using a valid referee ID and season ID."
)

ERROR_MSG_404_REFEREE_REPORT = (
    "Report not found for referee with external_id '{external_id}' (HTTP 404). "
    "The referee may not have officiated any games yet."
)

ERROR_MSG_404_IPAD_KEYS = (
    "No iPad keys found or invalid season ID '{season_id}' (HTTP 404). "
    "Make sure you're using a valid season ID, not a league ID. "
    f"{HELP_USE_SEASONS_LIST}"
)

# Generic HTTP error templates
ERROR_MSG_GENERIC_HTTP = "{context} {endpoint} returned HTTP {status_code}: {text}"

# HTTP method-specific error templates (with truncated response text)
ERROR_MSG_HTTP_GET = "GET {endpoint} returned HTTP {status_code}: {text}"
ERROR_MSG_HTTP_POST = "POST {endpoint} returned HTTP {status_code}: {text}"
ERROR_MSG_HTTP_PATCH = "PATCH {endpoint} returned HTTP {status_code}: {text}"
ERROR_MSG_HTTP_DELETE = "DELETE {endpoint} returned HTTP {status_code}: {text}"

# Domain-specific error messages
ERROR_MSG_LOCATION_NOT_FOUND = "Location '{location_id}' not found in available locations."

ERROR_MSG_BROADCASTER_INVALID = (
    "Broadcaster '{broadcaster_key}' is not valid. "
    "Use 'gamesheet-sdk-py games broadcasters list' to see valid options."
)

ERROR_MSG_GAME_TYPE_INVALID = "Game type '{game_type}' is not valid. Valid types: {valid_types}"

# BFF API error messages
ERROR_MSG_BFF_NON_SUCCESS = "BFF API returned non-success status: {status}. Response: {response}"
ERROR_MSG_BFF_NON_SUCCESS_SIMPLE = "BFF API returned non-success status: {status}"
ERROR_MSG_PENALTY_REPORT_API_STATUS = "Penalty report API returned status: {status}"

# Image upload error messages
ERROR_MSG_IMAGE_UPLOAD_FAILED = "Image upload failed: {error}"

# Validation error messages
ERROR_MSG_AT_LEAST_ONE_FIELD = "At least one field must be provided for update"
ERROR_MSG_CANNOT_UPLOAD_AND_REMOVE_PHOTO = "Cannot both upload a photo and remove it"
ERROR_MSG_CANNOT_UPLOAD_AND_REMOVE_LOGO = "Cannot both upload a logo and remove it"

# CLI-specific validation messages
ERROR_MSG_CLI_AT_LEAST_ONE_FIELD_UPDATE = "At least one field must be provided to update"
