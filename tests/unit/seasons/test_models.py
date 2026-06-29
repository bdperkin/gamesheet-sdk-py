# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for Season models."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.seasons import Season, SeasonDetail


def test_season_model_ignores_unknown_attributes() -> None:
    """Season model should ignore unknown attributes for forward compatibility."""
    s = Season(
        id="501",
        league_id="1148580",
        title="2024-2025",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert s.title == "2024-2025"


def test_season_detail_model_ignores_unknown_attributes() -> None:
    """SeasonDetail model should ignore unknown attributes for forward compatibility."""
    sd = SeasonDetail(
        id="15020",
        association_id="38",
        league_id="1148580",
        title="Test",
        external_id="uuid",
        start_date="2026-01-01",
        end_date="2026-12-31",
        sport="hockey",
        stats_year="2026",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert sd.title == "Test"
