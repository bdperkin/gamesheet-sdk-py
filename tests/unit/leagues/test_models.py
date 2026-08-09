# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for League model."""

from __future__ import annotations

from datetime import UTC, datetime

from gamesheet_sdk.admin.leagues import League


def test_league_model_ignores_unknown_attributes() -> None:
    """League model should ignore unknown attributes for forward compatibility."""
    lg = League(
        id="101",
        association_id="38",
        title="18U AAA",
        created_at=datetime(2023, 1, 1, tzinfo=UTC),
        updated_at=datetime(2023, 1, 1, tzinfo=UTC),
        unexpected_future_attr="ignored",
    )
    assert lg.title == "18U AAA"
