# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for Division and Team model validation."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.divisions import Division
from gamesheet_sdk.teams import Team
from tests.helpers import DIVISION_ID, SEASON_ID


def test_division_model_ignores_unknown_attributes() -> None:
    """Verify that Division model ignores unknown attributes."""
    d = Division(
        id=DIVISION_ID,
        season_id=SEASON_ID,
        title="U13 AAA",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert d.id == DIVISION_ID
    assert d.season_id == SEASON_ID
    assert d.title == "U13 AAA"
    assert d.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert d.updated_at == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_team_model_accepts_optional_fields() -> None:
    """Verify that Team model accepts optional fields like logo, player_count, etc."""
    t = Team(
        id="1001",
        season_id=SEASON_ID,
        title="Raleigh Raptors",
        division_id=DIVISION_ID,
        logo="https://example.com/logo.png",
        invitation_code="ABC123",
        player_count=15,
        coach_count=3,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert t.id == "1001"
    assert t.season_id == SEASON_ID
    assert t.division_id == DIVISION_ID
    assert t.title == "Raleigh Raptors"
    assert t.logo == "https://example.com/logo.png"
    assert t.invitation_code == "ABC123"
    assert t.player_count == 15
    assert t.coach_count == 3
    assert t.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert t.updated_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
