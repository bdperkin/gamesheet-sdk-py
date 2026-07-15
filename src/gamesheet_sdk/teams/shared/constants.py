# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams-specific constants and configuration values.

This module defines URL constants and endpoint paths specific to the
GameSheet teams dashboard API gateway.

Constants
---------
TEAMS_API_GATEWAY : str
    Base URL of the teams API gateway.
FIREBASE_API_KEY : str
    Firebase API key for the ``gamesheet-production`` project.
TEAMS_TOKEN_EXCHANGE_PATH : str
    Endpoint path for exchanging a Firebase ID token for app tokens.
TEAMS_REFRESH_PATH : str
    Endpoint path for refreshing an expired access token.

Examples
--------
Building a token exchange URL:

.. code-block:: python

    from gamesheet_sdk.teams.shared.constants import (
        TEAMS_API_GATEWAY,
        TEAMS_TOKEN_EXCHANGE_PATH,
    )

    url = f"{TEAMS_API_GATEWAY}{TEAMS_TOKEN_EXCHANGE_PATH}"
"""

from __future__ import annotations

from typing import Final

TEAMS_API_GATEWAY: Final[str] = "https://api.teams.gamesheet.app"
FIREBASE_API_KEY: Final[str] = "AIzaSyCk5pKBFxvCMuwPchzXgvvz4XmmscJTvs8"
TEAMS_TOKEN_EXCHANGE_PATH: Final[str] = "/api/auth/tokens"
TEAMS_REFRESH_PATH: Final[str] = "/api/auth/refresh"
