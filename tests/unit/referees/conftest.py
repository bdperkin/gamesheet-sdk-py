"""Shared fixtures for referee unit tests."""

from __future__ import annotations

from typing import Any

from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


def referee_response_data(referee_id: str) -> dict[str, Any]:
    """Build standard referee response payload for tests.

    Args:
        referee_id: The referee ID to use in the response

    Returns:
        A dict representing a JSON:API referee response
    """
    return {
        "data": {
            "type": "referees",
            "id": referee_id,
            "attributes": {
                "first_name": "Test",
                "last_name": "Ref",
                "created_at": "2024-09-01T10:00:00Z",
                "updated_at": "2024-09-01T10:00:00Z",
            },
            "relationships": {
                "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
            },
        },
    }


__all__ = ["jsonapi_payload", "referee_response_data", "_BASE", "_SEASON_ID", "_ENDPOINT"]
