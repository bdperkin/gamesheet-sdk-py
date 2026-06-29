# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for CLI teams roster tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock config."""
    return MagicMock()


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock authenticated session."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session
