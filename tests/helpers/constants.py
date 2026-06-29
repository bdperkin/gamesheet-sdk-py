# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test constants for GameSheet SDK tests.

This module provides a single source of truth for commonly-used test data values (IDs, names, UUIDs) that
appear across multiple test files. Using named constants instead of magic strings improves readability,
catches typos at import time, and makes it easier to maintain consistent test data.
"""

from __future__ import annotations

# Resource IDs (from actual GameSheet responses observed during test recording)
PLAYER_ID = "8043169"
COACH_ID_PRIMARY = "1868550"
COACH_ID_SECONDARY = "1879938"
SEASON_ID = "15020"
TEAM_ID = "12345"
DIVISION_ID = "701"
ASSOCIATION_ID = "123"
LEAGUE_ID = "456"

# External IDs (UUIDs used for integration with external systems)
PLAYER_EXTERNAL_ID = "BC7732F4-4993-492E-8CCB-4C2CA9C1912E"
PLAYER_EXTERNAL_ID_SECONDARY = "C9B37D2D-77DD-4C2D-BF47-D2B8175ECB47"
COACH_EXTERNAL_ID = "530b7441-1db6-437e-8e5f-777ab3f6cd6c"
COACH_EXTERNAL_ID_SECONDARY = "FB031B8B-2AB4-4682-817F-6E6076315241"
COACH_EXTERNAL_ID_TERTIARY = "35B8EC31-2221-48FB-9C5A-06AA1ED7134D"
REFEREE_EXTERNAL_ID_PRIMARY = "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A"
REFEREE_EXTERNAL_ID_SECONDARY = "87487685-24B9-46EF-B8A3-D3B7ECEB1F68"
REFEREE_EXTERNAL_ID_TERTIARY = "13340CA3-6B7D-4EC1-A183-EE281D2990A6"
REFEREE_EXTERNAL_ID_TEST = "ABC12345-6789-0DEF-ABCD-EF1234567890"
SEASON_EXTERNAL_ID = "558772B8-DAF4-4848-B7CA-1FB620F2BA52"
PROTOTEAM_ID = "a86f6c21-9894-46c7-a73c-c3ed509002e9"

# Real person names (from actual test recordings - GameSheet returns uppercase)
PLAYER_FIRST_NAME = "AUSTIN"
PLAYER_LAST_NAME = "ADAMSKY"
COACH_FIRST_NAME = "SHAWN"
COACH_LAST_NAME = "ALLIE"

# Default/placeholder names for payload builders
DEFAULT_PLAYER_FIRST_NAME = "John"
DEFAULT_PLAYER_LAST_NAME = "Doe"
DEFAULT_COACH_FIRST_NAME = "Coach"
DEFAULT_COACH_LAST_NAME = "Smith"

# Invitation/team codes
INVITATION_ID = "inv-123"
INVITATION_CODE = "RAPTORS2024"

# Base URLs for test endpoints
TEST_BASE_URL = "https://test.example"

# JSON:API content type (used in header assertions)
JSONAPI_CONTENT_TYPE = "application/vnd.api+json"
