# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for Association model."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.associations import Association


def test_association_model_ignores_unknown_attributes() -> None:
    """Association model should ignore unknown attributes for forward compatibility."""
    a = Association(
        id="11",
        title="X",
        logo="",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert a.title == "X"
