# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for referee unit tests."""

from __future__ import annotations

from typing import Any

from tests.helpers import (
    SEASON_ID,
    TEST_BASE_URL,
    TIMESTAMP_2024_09_01,
    jsonapi_payload,
    referees_endpoint,
)

_ENDPOINT = referees_endpoint(SEASON_ID)


def referee_response_data(referee_id: str) -> dict[str, Any]:
    """Build standard referee response payload for tests.

    :param referee_id: The referee ID to use in the response
    :returns: A dict representing a JSON:API referee response
    """
    return {
        "data": {
            "type": "referees",
            "id": referee_id,
            "attributes": {
                "first_name": "Test",
                "last_name": "Ref",
                "created_at": TIMESTAMP_2024_09_01,
                "updated_at": TIMESTAMP_2024_09_01,
            },
            "relationships": {
                "season": {"data": {"type": "seasons", "id": SEASON_ID}},
            },
        },
    }


__all__ = [
    "jsonapi_payload",
    "referee_response_data",
    "TEST_BASE_URL",
    "SEASON_ID",
    "_ENDPOINT",
]
