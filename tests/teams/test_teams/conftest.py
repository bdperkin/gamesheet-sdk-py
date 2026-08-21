# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures and sample data for teams tests."""

from __future__ import annotations

from typing import Any

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
from gamesheet_sdk.teams.shared.constants import (
    TEAMS_API_GATEWAY,
    TEAMS_IMAGES_UPLOAD_URL_PATH,
    TEAMS_REFRESH_PATH,
    TEAMS_TEAMS_PATH,
)

TEAMS_URL = f"{TEAMS_API_GATEWAY}{TEAMS_TEAMS_PATH}"
REFRESH_URL = f"{TEAMS_API_GATEWAY}{TEAMS_REFRESH_PATH}"
UPLOAD_ENDPOINT = f"{TEAMS_API_GATEWAY}{TEAMS_IMAGES_UPLOAD_URL_PATH}"
UPLOAD_DEST = "https://upload.imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/img-123"


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


def sample_teams_data() -> list[dict[str, Any]]:
    """Return sample teams data list.

    Returns:
        list[dict[str, Any]]: List of sample team data dictionaries.

    """
    return [
        {
            "memberId": "m-001",
            "teamId": "t-101",
            "relationship": "coach",
            "status": "active",
            "onboardingCompletedAt": "2024-09-01T10:00:00Z",
            "teamName": "Hawks 12U",
            "ageCategory": "12U",
            "clubId": "c-501",
            "joinedAt": "2024-08-15T09:00:00Z",
            "statsYear": "2024-2025",
            "extra_field": "some_extra_val",
        },
        {
            "memberId": "m-002",
            "teamId": "t-102",
            "relationship": "manager",
            "status": "pending",
            "onboardingCompletedAt": "2024-09-02T11:00:00Z",
            "teamName": "Eagles 14U",
            "ageCategory": "14U",
            "clubId": "c-502",
            "joinedAt": "2024-08-20T14:00:00Z",
            "statsYear": "2024-2025",
        },
    ]
