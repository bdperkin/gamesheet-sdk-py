# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test fixtures for games unit tests."""

from __future__ import annotations

import responses

from gamesheet_sdk.common.constants import DEFAULT_BASE_URL
from tests.fixtures.constants import (
    TEST_CITY,
    TEST_COUNTRY,
    TEST_LOCATION_NAME,
    TEST_PROVINCE_STATE,
    TEST_SURFACE_NAME,
)


def add_mock_locations_response(location_id: str = "loc-1") -> None:
    """Add a mock locations API response.

    Helper to reduce duplicate mock setup code across test files.

    Args:
        location_id (str): Location ID to use in mock data
    """
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": location_id,
                    "location_name": TEST_LOCATION_NAME,
                    "surface_name": TEST_SURFACE_NAME,
                    "city": TEST_CITY,
                    "province_state": TEST_PROVINCE_STATE,
                    "country": TEST_COUNTRY,
                },
            ],
        },
        status=200,
    )
