# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""gamesheet_sdk — unofficial Python SDK for the GameSheet Inc. platform.

This package provides both a Python API and CLI for interacting with the GameSheet platform. GameSheet does
not publish a public API, so this SDK automates the WebUI via HTTP requests and headless browser automation.

**Core modules:**

- :mod:`~gamesheet_sdk.common.auth` — authentication, token management, session handling
- :mod:`~gamesheet_sdk.admin.associations` — list associations
- :mod:`~gamesheet_sdk.admin.leagues` — list leagues by association
- :mod:`~gamesheet_sdk.admin.seasons` — list and retrieve season details
- :mod:`~gamesheet_sdk.admin.ipad_keys` — retrieve iPad scoring access keys
- :mod:`~gamesheet_sdk.common.browser` — headless browser automation wrapper
- :mod:`~gamesheet_sdk.common.config` — configuration resolution (env vars + CLI args)
- :mod:`~gamesheet_sdk.common.output` — multi-format output rendering (JSON, YAML, CSV, tables)

**Quick start (API):**

.. code-block:: python
    from gamesheet_sdk import login, list_associations

    # Authenticate and get session
    session = login(email="user@example.com", password="secret")
    # List associations
    associations = list_associations(session)
    for assoc in associations:
        print(f"{assoc.name} (ID: {assoc.id})")

**Quick start (CLI):**

.. code-block:: bash
    # Login (stores tokens for subsequent commands)
    gamesheet-admin login
    # List associations
    gamesheet-admin associations list
    # Get season details
    gamesheet-admin seasons get <season-id>

**Type safety:**

This package ships with a ``py.typed`` marker and enforces type checking via Astral ``ty``.
All public APIs are fully type-annotated.
**Version resolution:** The package version is managed in ``pyproject.toml`` by
python-semantic-release and accessible via standard importlib.metadata.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from gamesheet_sdk.admin.associations import Association, list_associations
from gamesheet_sdk.admin.divisions import (
    Division,
    create_division,
    delete_division,
    list_division_teams,
    list_divisions,
    update_division,
)
from gamesheet_sdk.admin.games import (
    Game,
    TeamInfo,
    list_brackets,
    list_completed,
    list_scheduled,
)
from gamesheet_sdk.admin.ipad_keys import IPadKey, list_ipad_keys
from gamesheet_sdk.admin.leagues import League, list_leagues
from gamesheet_sdk.admin.referees import (
    Referee,
    RefereeReport,
    create_referee,
    delete_referee,
    get_referee,
    get_referee_report,
    list_referees,
    update_referee,
)
from gamesheet_sdk.admin.roster import Coach, Player, list_coaches, list_players
from gamesheet_sdk.admin.seasons import Season, SeasonDetail, get_season, list_seasons
from gamesheet_sdk.admin.teams import (
    Team,
    create_team,
    delete_team,
    list_teams,
    update_team,
)
from gamesheet_sdk.common.auth import (
    AuthenticatedSession,
    load_access_token,
    load_refresh_token,
    login,
    refresh_access_token,
    save_tokens,
)
from gamesheet_sdk.common.browser import BrowserSession
from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.constants import (
    APP_GAMESHEET_COM,
    BFF_API_BASE_URL,
    CLOUDFLARE_IMAGE_DELIVERY_BASE,
    DEFAULT_BASE_URL,
    PLAY_GAMESHEET_APP,
)
from gamesheet_sdk.common.exceptions import (
    AuthenticationError,
    GameSheetAPIError,
    GameSheetError,
    GameSheetNotFoundError,
    GameSheetPermissionError,
    GameSheetRateLimitError,
    GameSheetValidationError,
)
from gamesheet_sdk.common.output import (
    ALL_FORMATS,
    DATA_FORMATS,
    DEFAULT_FORMAT,
    TABULATE_FORMATS,
    render,
)
from gamesheet_sdk.common.session import Session

try:
    __version__ = version("gamesheet-sdk-py")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "ALL_FORMATS",
    "APP_GAMESHEET_COM",
    "BFF_API_BASE_URL",
    "CLOUDFLARE_IMAGE_DELIVERY_BASE",
    "DATA_FORMATS",
    "DEFAULT_BASE_URL",
    "DEFAULT_FORMAT",
    "PLAY_GAMESHEET_APP",
    "TABULATE_FORMATS",
    "Association",
    "AuthenticatedSession",
    "AuthenticationError",
    "BrowserSession",
    "Coach",
    "Config",
    "Division",
    "Game",
    "GameSheetAPIError",
    "GameSheetError",
    "GameSheetNotFoundError",
    "GameSheetPermissionError",
    "GameSheetRateLimitError",
    "GameSheetValidationError",
    "IPadKey",
    "League",
    "Player",
    "Referee",
    "RefereeReport",
    "Season",
    "SeasonDetail",
    "Session",
    "Team",
    "TeamInfo",
    "__version__",
    "create_division",
    "create_referee",
    "create_team",
    "delete_division",
    "delete_referee",
    "delete_team",
    "get_referee",
    "get_referee_report",
    "get_season",
    "list_associations",
    "list_brackets",
    "list_coaches",
    "list_completed",
    "list_division_teams",
    "list_divisions",
    "list_ipad_keys",
    "list_leagues",
    "list_players",
    "list_referees",
    "list_scheduled",
    "list_seasons",
    "list_teams",
    "load_access_token",
    "load_refresh_token",
    "login",
    "refresh_access_token",
    "render",
    "save_tokens",
    "update_division",
    "update_referee",
    "update_team",
]
