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

The package version is derived from git tags via hatch-vcs. When running from
an unbuilt source tree, it falls back to installed metadata or ``"0+unknown"``.
"""

from __future__ import annotations

try:
    from gamesheet_sdk._version import __version__
except ImportError:  # pragma: no cover - fallback only fires uninstalled
    # _version.py is written by hatch-vcs at build time; when running from
    # a source tree that hasn't been built (or an editable install that
    # predates the latest git tag), fall back to installed metadata.
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("gamesheet-sdk-py")
    except PackageNotFoundError:
        __version__ = "0+unknown"
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
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.ipad_keys import IPadKey, list_ipad_keys
from gamesheet_sdk.leagues import League, list_leagues
from gamesheet_sdk.output import (
    ALL_FORMATS,
    DATA_FORMATS,
    DEFAULT_FORMAT,
    TABULATE_FORMATS,
    render,
)
from gamesheet_sdk.seasons import Season, SeasonDetail, get_season, list_seasons
from gamesheet_sdk.session import Session

__all__ = [
    "ALL_FORMATS",
    "Association",
    "AuthenticatedSession",
    "AuthenticationError",
    "BrowserSession",
    "Config",
    "DATA_FORMATS",
    "DEFAULT_FORMAT",
    "GameSheetError",
    "IPadKey",
    "League",
    "Season",
    "SeasonDetail",
    "Session",
    "TABULATE_FORMATS",
    "__version__",
    "get_season",
    "list_associations",
    "list_ipad_keys",
    "list_leagues",
    "list_seasons",
    "load_access_token",
    "load_refresh_token",
    "login",
    "refresh_access_token",
    "render",
    "save_tokens",
]
