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
COACH_EXTERNAL_ID = "530b7441-1db6-437e-8e5f-777ab3f6cd6c"

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
