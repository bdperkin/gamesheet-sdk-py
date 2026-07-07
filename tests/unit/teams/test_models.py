# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for Team model."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.teams import Team
from tests.helpers import SEASON_ID


def test_team_model_ignores_unknown_attributes() -> None:
    """Team model should ignore unknown attributes for forward compatibility."""
    t = Team(
        id="1001",
        season_id=SEASON_ID,
        title="Raleigh Raptors",
        division_id="5001",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert t.title == "Raleigh Raptors"
