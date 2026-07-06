# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""SDK-wide constants and configuration values.

This module defines all URL constants and endpoints used throughout the GameSheet SDK.
Constants
---------
DEFAULT_BASE_URL : str
    Default GameSheet web application base URL.
APP_GAMESHEET_COM : str
    Legacy GameSheet domain (used for browser storage).
BFF_API_BASE_URL : str
    Backend-for-Frontend API base URL.
SCORESHEET_SERVICE_BASE_URL : str
    Scoresheet service base URL (for PDF downloads).
CLOUDFLARE_IMAGE_DELIVERY_BASE : str
    Cloudflare image delivery CDN base URL with account hash.
Examples
--------
Using base URLs in session configuration:
.. code-block:: python
    from gamesheet_sdk.constants import DEFAULT_BASE_URL
    from gamesheet_sdk import Session

    session = Session(base_url=DEFAULT_BASE_URL)
Using BFF API endpoints:
.. code-block:: python
    from gamesheet_sdk.constants import BFF_API_BASE_URL

    games_url = f"{BFF_API_BASE_URL}/games-list/v1"
Using image delivery:
.. code-block:: python
    from gamesheet_sdk.constants import CLOUDFLARE_IMAGE_DELIVERY_BASE

    logo_url = f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/{image_id}"
"""

from __future__ import annotations

from typing import Final

# Default base URL for the GameSheet web application
DEFAULT_BASE_URL: Final[str] = "https://gamesheet.app"
# Play subdomain for certain league operations
PLAY_GAMESHEET_APP: Final[str] = "https://play.gamesheet.app"
# Legacy domain used for browser storage state
APP_GAMESHEET_COM: Final[str] = "https://app.gamesheet.com"
# Backend-for-Frontend (BFF) API base URL
BFF_API_BASE_URL: Final[str] = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app"
# Scoresheet service base URL (for PDF downloads)
SCORESHEET_SERVICE_BASE_URL: Final[str] = "https://scoresheet-service-awy26srzoa-nn.a.run.app"
# Cloudflare image delivery CDN base URL
CLOUDFLARE_IMAGE_DELIVERY_BASE: Final[str] = "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA"

# API Endpoints
API_LOCATIONS: Final[str] = "/api/locations"
API_SEASONS_SCHEDULE: Final[str] = "/api/seasons/{season_id}/schedule"
API_SEASONS_SCHEDULE_GAME: Final[str] = "/api/seasons/{season_id}/schedule/{game_id}"
API_SEASONS_GAMES: Final[str] = "/api/seasons/{season_id}/games/{game_id}"

# BFF API Endpoints
BFF_GAMES_LIST: Final[str] = "/games-list/v1"
BFF_BROADCASTERS: Final[str] = "/get-broadcasters"
BFF_ASSETS_UPLOAD_URL: Final[str] = "/dwg/assets/upload-url"

# Scoresheet Service Endpoints
SCORESHEET_SERVICE_GAME: Final[str] = "/service.scoresheets/v4/get-game/{game_id}"

# BFF API Response Status
BFF_STATUS_SUCCESS: Final[str] = "success"

# Timezone and Localization
DEFAULT_TIMEZONE: Final[str] = "UTC"

# File and Content Type Settings
ENCODING_UTF8: Final[str] = "utf-8"
CONTENT_TYPE_JSON: Final[str] = "application/json"
FILE_EXT_PDF: Final[str] = ".pdf"

# Output Configuration
DEFAULT_OUTPUT_FORMAT: Final[str] = "simple"
SYNTAX_THEME: Final[str] = "ansi_dark"
SYNTAX_BG_COLOR: Final[str] = "default"
JSON_INDENT_SPACES: Final[int] = 2

# API Limits and Defaults
DEFAULT_GAMES_LIMIT: Final[int] = 1000

# HTTP Retry Configuration
HTTP_RETRY_STATUSES: Final[frozenset[int]] = frozenset({500, 502, 503, 504})

# Filename Patterns
SCORESHEET_FILENAME_PATTERN: Final[str] = "{date}-scoresheet-{id}-{visitor}-vs-{home}-{game_number}.pdf"

# Regex Patterns for Filename Sanitization
FILENAME_SANITIZE_PATTERN: Final[str] = r"[^\w\-]"
FILENAME_COLLAPSE_UNDERSCORES: Final[str] = r"_+"

# Valid Game Types
VALID_GAME_TYPES: Final[frozenset[str]] = frozenset(
    ["playoff", "exhibition", "tournament", "regular_season"],
)
