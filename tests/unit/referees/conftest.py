"""Shared fixtures for referee unit tests."""

from __future__ import annotations

from tests.helpers import jsonapi_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"

__all__ = ["jsonapi_payload", "_BASE", "_SEASON_ID", "_ENDPOINT"]
