# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test-specific constants for consistent test data across test files."""

from __future__ import annotations

# Authentication test tokens
TEST_BEARER_TOKEN = "test-token"
TEST_ACCESS_TOKEN = "bearer-tok"
TEST_REFRESH_TOKEN = "refresh-tok"

# Test IDs
TEST_SEASON_ID = "test-season-123"
TEST_GAME_ID = "test-game-456"
TEST_TEAM_ID = "test-team-789"
TEST_DIVISION_ID = "test-division-101"
TEST_LOCATION_ID = "test-location-202"

# Test user data
TEST_SCOREKEEPER_NAME = "John Doe"
TEST_SCOREKEEPER_PHONE = "555-1234"

# Test location data
TEST_LOCATION_NAME = "Arena A"
TEST_SURFACE_NAME = "Ice 1"
TEST_CITY = "Toronto"
TEST_PROVINCE_STATE = "ON"
TEST_COUNTRY = "Canada"

# Test timezone data
TEST_TIMEZONE_NAME = "America/Toronto"
TEST_TIMEZONE_OFFSET = -240  # EDT offset in minutes

# Test error messages
TEST_ERROR_DISK_FULL = "Disk full"
TEST_ERROR_PERMISSION_DENIED = "Permission denied"
TEST_ERROR_GENERIC = "Test error"
TEST_ERROR_VALIDATION = "Test validation error"

# Test error message regex patterns (for pytest.raises match=)
TEST_ERROR_PATTERN_404_RESOURCE = r"Resource not found \(HTTP 404\)"
TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD = "At least one field must be provided"

# Test file content
TEST_FAKE_IMAGE_CONTENT = "fake image content"
