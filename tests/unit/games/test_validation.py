# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for game validation functions."""

from __future__ import annotations

import pytest

from gamesheet_sdk.admin.games import validate_game_type
from gamesheet_sdk.common.exceptions import GameSheetError


def test_validate_game_type_valid() -> None:
    """Test validate_game_type with valid game types."""
    validate_game_type("playoff")
    validate_game_type("exhibition")
    validate_game_type("tournament")
    validate_game_type("regular_season")


def test_validate_game_type_invalid() -> None:
    """Test validate_game_type with invalid game type."""
    with pytest.raises(GameSheetError, match=r"Invalid game type"):
        validate_game_type("invalid_type")


# Lines 690-731: create_scheduled_game()
