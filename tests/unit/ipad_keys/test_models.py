# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for IPadKey model."""

from __future__ import annotations

from datetime import datetime, timezone

from gamesheet_sdk.ipad_keys import IPadKey


def test_ipad_key_model_ignores_unknown_attributes() -> None:
    """IPadKey model should ignore unknown attributes for forward compatibility."""
    key = IPadKey(
        id="3567",
        value="ipad-test-key",
        description="Test Key",
        roles=[],
        live_scoring_scopes=["read"],
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert key.value == "ipad-test-key"
