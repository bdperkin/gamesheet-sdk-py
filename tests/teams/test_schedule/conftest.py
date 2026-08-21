# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures and sample data for teams schedule tests."""

from __future__ import annotations

from typing import Any

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_AVAILABILITY_BATCH_PATH,
    TEAMS_CALENDAR_EVENTS_PATH,
    TEAMS_CALENDAR_OCCURRENCES_PATH,
    TEAMS_CALENDAR_PATH,
    TEAMS_REFRESH_PATH,
    TEAMS_SCHEDULE_GAME_PATH,
)

CALENDAR_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_PATH}"
CALENDAR_EVENTS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_EVENTS_PATH}"
OCCURRENCE_URL = f"{TEAMS_API_GATEWAY}{TEAMS_CALENDAR_OCCURRENCES_PATH}"
SCHEDULE_GAME_URL = f"{TEAMS_API_GATEWAY}{TEAMS_SCHEDULE_GAME_PATH}"
AVAILABILITY_URL = f"{TEAMS_API_GATEWAY}{TEAMS_AVAILABILITY_BATCH_PATH}"
REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"


def make_session() -> TeamsAuthenticatedSession:
    """Create a test TeamsAuthenticatedSession.

    Returns:
        TeamsAuthenticatedSession: Test authenticated session instance.

    """
    config = Config()
    return TeamsAuthenticatedSession(
        config,
        access_token="test-access",
        refresh_token="test-refresh",
    )


def sample_calendar_data() -> list[dict[str, Any]]:
    """Return sample calendar event data list.

    Returns:
        list[dict[str, Any]]: List of sample event data dictionaries.

    """
    return [
        {
            "id": "evt-101",
            "type": "event",
            "eventDate": "2026-08-20",
            "eventTime": "17:00",
            "eventTitle": "Team Pizza Party",
            "eventLocation": "Clubhouse",
            "eventData": {"notes": "Bring drinks"},
            "customField": "extra",
        },
        {
            "id": 202,
            "type": "game",
            "eventDate": "2026-08-22",
            "eventTime": "19:00",
            "eventTitle": "Hawks vs Eagles",
            "eventLocation": "Arena A",
            "eventData": {"homeTeam": "Hawks", "awayTeam": "Eagles"},
        },
        {
            "id": "prac-303",
            "type": "practice",
            "eventDate": "2026-08-24",
            "eventTime": "06:00",
            "eventTitle": "Morning Skate",
            "eventLocation": "Rink 2",
            "eventData": {"drills": ["skating", "passing"]},
        },
    ]
