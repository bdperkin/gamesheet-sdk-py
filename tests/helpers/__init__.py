# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test helper utilities."""

from __future__ import annotations

from tests.helpers.constants import (
    ASSOCIATION_ID,
    COACH_EXTERNAL_ID,
    COACH_FIRST_NAME,
    COACH_ID_PRIMARY,
    COACH_ID_SECONDARY,
    COACH_LAST_NAME,
    DEFAULT_COACH_FIRST_NAME,
    DEFAULT_COACH_LAST_NAME,
    DEFAULT_PLAYER_FIRST_NAME,
    DEFAULT_PLAYER_LAST_NAME,
    DIVISION_ID,
    INVITATION_CODE,
    INVITATION_ID,
    LEAGUE_ID,
    PLAYER_EXTERNAL_ID,
    PLAYER_FIRST_NAME,
    PLAYER_ID,
    PLAYER_LAST_NAME,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
)
from tests.helpers.mocks import (
    setup_get_team_roster_mocks,
    setup_photo_upload_mocks,
    setup_team_roster_update_mocks,
    setup_update_coach_mocks,
    setup_update_player_mocks,
)
from tests.helpers.payloads import (
    association_payload,
    invitation_relationship_and_included,
    jsonapi_detail_payload,
    jsonapi_payload,
    league_payload,
    roster_coach_payload,
    roster_player_payload,
    team_payload,
)

__all__ = [
    "ASSOCIATION_ID",
    "COACH_EXTERNAL_ID",
    "COACH_FIRST_NAME",
    "COACH_ID_PRIMARY",
    "COACH_ID_SECONDARY",
    "COACH_LAST_NAME",
    "DEFAULT_COACH_FIRST_NAME",
    "DEFAULT_COACH_LAST_NAME",
    "DEFAULT_PLAYER_FIRST_NAME",
    "DEFAULT_PLAYER_LAST_NAME",
    "DIVISION_ID",
    "INVITATION_CODE",
    "INVITATION_ID",
    "LEAGUE_ID",
    "PLAYER_EXTERNAL_ID",
    "PLAYER_FIRST_NAME",
    "PLAYER_ID",
    "PLAYER_LAST_NAME",
    "SEASON_ID",
    "TEAM_ID",
    "TEST_BASE_URL",
    "association_payload",
    "invitation_relationship_and_included",
    "jsonapi_detail_payload",
    "jsonapi_payload",
    "league_payload",
    "roster_coach_payload",
    "roster_player_payload",
    "setup_get_team_roster_mocks",
    "setup_photo_upload_mocks",
    "setup_team_roster_update_mocks",
    "setup_update_coach_mocks",
    "setup_update_player_mocks",
    "team_payload",
]
