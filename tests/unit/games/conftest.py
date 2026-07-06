# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test fixtures for games unit tests."""

from __future__ import annotations

import responses

from gamesheet_sdk.constants import DEFAULT_BASE_URL


def add_mock_locations_response(location_id: str = "loc-1") -> None:
    """Add a mock locations API response.

    Helper to reduce duplicate mock setup code across test files.

    :param location_id: Location ID to use in mock data
    :type location_id: str
    """
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": location_id,
                    "location_name": "Arena A",
                    "surface_name": "Ice 1",
                    "city": "Toronto",
                    "province_state": "ON",
                    "country": "Canada",
                },
            ],
        },
        status=200,
    )
