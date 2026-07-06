# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared constants used across domain modules."""

from __future__ import annotations

#: JSON:API content type for request/response headers
JSONAPI_CONTENT_TYPE = "application/vnd.api+json"
#: Standard headers for JSON:API requests
JSONAPI_HEADERS = {
    "Accept": JSONAPI_CONTENT_TYPE,
    "Content-Type": JSONAPI_CONTENT_TYPE,
}

# Pydantic Field descriptions for common parent identifiers
FIELD_DESC_PARENT_ASSOCIATION_ID = "Parent association identifier."
FIELD_DESC_PARENT_LEAGUE_ID = "Parent league identifier."
FIELD_DESC_PARENT_SEASON_ID = "Parent season identifier."

# Pydantic Field descriptions for person name fields
FIELD_DESC_COACH_FIRST_NAME = "Coach's first name."
FIELD_DESC_COACH_LAST_NAME = "Coach's last name."
FIELD_DESC_PLAYER_FIRST_NAME = "Player's first name."
FIELD_DESC_PLAYER_LAST_NAME = "Player's last name."
FIELD_DESC_REFEREE_FIRST_NAME = "Referee's first name."
FIELD_DESC_REFEREE_LAST_NAME = "Referee's last name."

# Help text for error messages (used by both errors.py and cli.constants)
HELP_USE_SEASONS_LIST = "To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>"
