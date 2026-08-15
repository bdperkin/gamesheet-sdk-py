# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for Referee model."""

from __future__ import annotations

from datetime import UTC, datetime

from gamesheet_sdk.admin.referees import Referee
from tests.helpers import SEASON_ID


def test_referee_model_ignores_unknown_attributes() -> None:
    """Test that Referee model ignores unknown attributes."""
    r = Referee.model_validate(
        {
            "id": "101",
            "season_id": SEASON_ID,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "created_at": datetime(2024, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 1, tzinfo=UTC),
            "unexpected_future_attr": "ignored",
        },
    )
    assert r.first_name == "John"
    assert r.last_name == "Smith"


def test_referee_model_handles_optional_email() -> None:
    """Test that Referee model handles optional email field."""
    r = Referee(
        id="102",
        season_id=SEASON_ID,
        first_name="Jane",
        last_name="Doe",
        email=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    assert r.email is None
