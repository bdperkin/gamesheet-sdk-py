"""Shared fixtures for referee unit tests."""

from __future__ import annotations

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}
