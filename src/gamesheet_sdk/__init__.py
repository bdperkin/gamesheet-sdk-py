"""gamesheet_sdk — unofficial Python SDK for the GameSheet Inc. platform.

This package provides both a Python API and CLI for interacting with the
GameSheet platform. GameSheet does not publish a public API, so this SDK
automates the WebUI via HTTP requests and headless browser automation.

**Core modules:**

- :mod:`~gamesheet_sdk.auth` — authentication, token management, session handling
- :mod:`~gamesheet_sdk.associations` — list associations
- :mod:`~gamesheet_sdk.leagues` — list leagues by association
- :mod:`~gamesheet_sdk.seasons` — list and retrieve season details
- :mod:`~gamesheet_sdk.ipad_keys` — retrieve iPad scoring access keys
- :mod:`~gamesheet_sdk.browser` — headless browser automation wrapper
- :mod:`~gamesheet_sdk.config` — configuration resolution (env vars + CLI args)
- :mod:`~gamesheet_sdk.output` — multi-format output rendering (JSON, YAML, CSV, tables)

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
    gamesheet-sdk-py login

    # List associations
    gamesheet-sdk-py associations list

    # Get season details
    gamesheet-sdk-py seasons get <season-id>

**Type safety:**

This package ships with a ``py.typed`` marker and enforces ``mypy --strict``.
All public APIs are fully type-annotated.

**Version resolution:**

The package version is managed in ``pyproject.toml`` by python-semantic-release
and accessible via standard importlib.metadata.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from gamesheet_sdk.associations import Association, list_associations
from gamesheet_sdk.auth import (
    AuthenticatedSession,
    load_access_token,
    load_refresh_token,
    login,
    refresh_access_token,
    save_tokens,
)
from gamesheet_sdk.browser import BrowserSession
from gamesheet_sdk.config import Config
from gamesheet_sdk.constants import (
    APP_GAMESHEET_COM,
    BFF_API_BASE_URL,
    CLOUDFLARE_IMAGE_DELIVERY_BASE,
    DEFAULT_BASE_URL,
    PLAY_GAMESHEET_APP,
)
from gamesheet_sdk.divisions import (
    Division,
    create_division,
    delete_division,
    list_division_teams,
    list_divisions,
    update_division,
)
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.games import Game, TeamInfo, list_brackets, list_completed, list_scheduled
from gamesheet_sdk.ipad_keys import IPadKey, list_ipad_keys
from gamesheet_sdk.leagues import League, list_leagues
from gamesheet_sdk.output import (
    ALL_FORMATS,
    DATA_FORMATS,
    DEFAULT_FORMAT,
    TABULATE_FORMATS,
    render,
)
from gamesheet_sdk.referees import (
    Referee,
    RefereeReport,
    create_referee,
    delete_referee,
    get_referee,
    get_referee_report,
    list_referees,
    update_referee,
)
from gamesheet_sdk.roster import Coach, Player, list_coaches, list_players
from gamesheet_sdk.seasons import Season, SeasonDetail, get_season, list_seasons
from gamesheet_sdk.session import Session
from gamesheet_sdk.teams import Team, create_team, delete_team, list_teams, update_team

try:
    __version__ = version("gamesheet-sdk-py")
except PackageNotFoundError:  # pragma: no cover - only in uninstalled source tree
    __version__ = "0+unknown"

__all__ = [
    "ALL_FORMATS",
    "APP_GAMESHEET_COM",
    "Association",
    "AuthenticatedSession",
    "AuthenticationError",
    "BFF_API_BASE_URL",
    "BrowserSession",
    "CLOUDFLARE_IMAGE_DELIVERY_BASE",
    "Coach",
    "Config",
    "DATA_FORMATS",
    "DEFAULT_BASE_URL",
    "DEFAULT_FORMAT",
    "PLAY_GAMESHEET_APP",
    "Division",
    "Game",
    "GameSheetError",
    "TeamInfo",
    "IPadKey",
    "League",
    "Player",
    "Referee",
    "RefereeReport",
    "Season",
    "SeasonDetail",
    "Session",
    "TABULATE_FORMATS",
    "Team",
    "__version__",
    "get_season",
    "list_associations",
    "list_brackets",
    "list_coaches",
    "list_completed",
    "create_division",
    "delete_division",
    "list_division_teams",
    "list_divisions",
    "update_division",
    "list_ipad_keys",
    "list_leagues",
    "list_players",
    "create_referee",
    "delete_referee",
    "get_referee",
    "get_referee_report",
    "list_referees",
    "update_referee",
    "list_scheduled",
    "list_seasons",
    "create_team",
    "delete_team",
    "list_teams",
    "update_team",
    "load_access_token",
    "load_refresh_token",
    "login",
    "refresh_access_token",
    "render",
    "save_tokens",
]
