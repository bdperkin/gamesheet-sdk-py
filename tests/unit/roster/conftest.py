# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for roster unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gamesheet_sdk.common.session import Session


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock session."""
    session = MagicMock(spec=Session)
    mock_response = MagicMock()
    mock_response.status_code = 204
    session.delete.return_value = mock_response
    return session
