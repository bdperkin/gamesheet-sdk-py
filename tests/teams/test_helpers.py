# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for teams CLI helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import Exit

from gamesheet_sdk.common.config import Config
from gamesheet_sdk.common.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.session import TeamsAuthenticatedSession


def test_build_authenticated_session_success() -> None:
    """build_authenticated_session returns TeamsAuthenticatedSession when tokens exist."""
    config = Config()
    with (
        patch("gamesheet_sdk.teams.cli.helpers.load_access_token", return_value="access-123"),
        patch("gamesheet_sdk.teams.cli.helpers.load_refresh_token", return_value="refresh-123"),
    ):
        session = build_authenticated_session(config)

    assert isinstance(session, TeamsAuthenticatedSession)
    assert session._refresh_token == "refresh-123"  # noqa: S105


def test_build_authenticated_session_missing_tokens() -> None:
    """build_authenticated_session raises Exit(1) when tokens are missing."""
    config = Config()
    with (
        patch("gamesheet_sdk.teams.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.teams.cli.helpers.load_refresh_token", return_value=None),
        pytest.raises(Exit) as exc_info,
    ):
        build_authenticated_session(config)

    assert exc_info.value.exit_code == 1


def test_run_action_or_exit_success() -> None:
    """run_action_or_exit executes action in context manager and returns result."""
    session = MagicMock()
    action = MagicMock(return_value="success_result")

    result = run_action_or_exit(session, action, "arg1", kwarg="val")

    assert result == "success_result"
    action.assert_called_once_with(session, "arg1", kwarg="val")


def test_run_action_or_exit_auth_error() -> None:
    """run_action_or_exit catches AuthenticationError and raises Exit(1)."""
    session = MagicMock()
    action = MagicMock(side_effect=AuthenticationError("Invalid token"))

    with pytest.raises(Exit) as exc_info:
        run_action_or_exit(session, action)

    assert exc_info.value.exit_code == 1


def test_run_action_or_exit_gamesheet_error() -> None:
    """run_action_or_exit catches GameSheetError and raises Exit(1)."""
    session = MagicMock()
    action = MagicMock(side_effect=GameSheetError("Resource not found"))

    with pytest.raises(Exit) as exc_info:
        run_action_or_exit(session, action)

    assert exc_info.value.exit_code == 1
