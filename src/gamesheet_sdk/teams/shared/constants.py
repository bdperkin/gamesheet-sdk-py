# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams-specific constants and configuration values.

This module defines URL constants and endpoint paths specific to the GameSheet teams dashboard API gateway.

Attributes:
    TEAMS_API_GATEWAY (str): Base URL of the teams API gateway.
    FIREBASE_API_KEY (str): Firebase API key for the ``gamesheet-production`` project.
    TEAMS_TOKEN_EXCHANGE_PATH (str): Endpoint path for exchanging a Firebase ID token for app tokens.
    TEAMS_REFRESH_PATH (str): Endpoint path for refreshing an expired access token.
    TEAMS_LOOKUPS_PATH (str): Endpoint path for fetching public lookup data (no auth required).
    TEAMS_SEASONS_PATH (str): Endpoint path for fetching seasons data.
    TEAMS_TEAMS_PATH (str): Endpoint path for fetching teams data.
    TEAMS_CALENDAR_PATH (str): Endpoint path for fetching team calendar and schedule data.
    TEAMS_CALENDAR_EVENTS_PATH (str): Endpoint path for creating calendar events and practices.
    TEAMS_CALENDAR_OCCURRENCES_PATH (str): Endpoint path for fetching individual calendar event occurrences.
    TEAMS_SCHEDULE_GAME_PATH (str): Endpoint path for fetching and managing scheduled game details.
    TEAMS_AVAILABILITY_BATCH_PATH (str): Endpoint path for fetching batch availability data.
    TEAMS_IMAGES_UPLOAD_URL_PATH (str): Endpoint path for requesting direct image upload URLs.
    TEAMS_PUBLIC_CALENDAR_SERVICE (str): Host and path prefix for the public calendar subscription feed
        service.

Example:
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
FIREBASE_API_KEY: Final[str] = "AIzaSyCk5pKBFxvCMuwPchzXgvvz4XmmscJTvs8"  # notsecret
TEAMS_TOKEN_EXCHANGE_PATH: Final[str] = "/api/auth/tokens"  # noqa: S105
TEAMS_REFRESH_PATH: Final[str] = "/api/auth/refresh"
TEAMS_LOOKUPS_PATH: Final[str] = "/api/lookups"
TEAMS_SEASONS_PATH: Final[str] = "/api/seasons"
TEAMS_TEAMS_PATH: Final[str] = "/api/teams"
TEAMS_CALENDAR_PATH: Final[str] = "/api/calendar"
TEAMS_CALENDAR_EVENTS_PATH: Final[str] = "/api/calendar/events"
TEAMS_CALENDAR_OCCURRENCES_PATH: Final[str] = "/api/calendar/occurrences"
TEAMS_SCHEDULE_GAME_PATH: Final[str] = "/api/schedule-game"
TEAMS_AVAILABILITY_BATCH_PATH: Final[str] = "/api/availability/batch"
TEAMS_IMAGES_UPLOAD_URL_PATH: Final[str] = "/api/images/upload-url"
TEAMS_PUBLIC_CALENDAR_SERVICE: Final[str] = "api.teams.gamesheet.app/api/public/calendar"
