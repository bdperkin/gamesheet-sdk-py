"""Tests for Division and Team model validation."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.divisions import Division
from gamesheet_sdk.teams import Team


def test_division_model_ignores_unknown_attributes() -> None:
    """Verify that Division model ignores unknown attributes."""
    d = Division(
        id="701",
        season_id="15020",
        title="U13 AAA",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert d.id == "701"
    assert d.season_id == "15020"
    assert d.title == "U13 AAA"
    assert d.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert d.updated_at == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_team_model_accepts_optional_fields() -> None:
    """Verify that Team model accepts optional fields like logo, player_count, etc."""
    t = Team(
        id="1001",
        season_id="15020",
        title="Raleigh Raptors",
        division_id="701",
        logo="https://example.com/logo.png",
        invitation_code="ABC123",
        player_count=15,
        coach_count=3,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert t.id == "1001"
    assert t.season_id == "15020"
    assert t.division_id == "701"
    assert t.title == "Raleigh Raptors"
    assert t.logo == "https://example.com/logo.png"
    assert t.invitation_code == "ABC123"
    assert t.player_count == 15
    assert t.coach_count == 3
    assert t.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert t.updated_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
