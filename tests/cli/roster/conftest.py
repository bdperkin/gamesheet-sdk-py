# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for CLI roster tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from click import Group
import pytest

from gamesheet_sdk import Config
from tests.cli.roster_helpers import run_roster_delete_test_base


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock authenticated session."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session


@pytest.fixture
def mock_config() -> Config:
    """Provide a mock config for testing."""
    return Config(base_url="https://test.example")


def run_roster_delete_test(
    group: Group,
    resource_type: str,
    resource_id: str,
    action_path: str,
    season_id: str,
    session: MagicMock,
    config: MagicMock,
    *,
    with_force: bool = True,
    input_text: str | None = None,
    should_fail: bool = False,
    error_message: str | None = None,
) -> tuple[int, str, MagicMock]:
    """Run a roster delete command test with given parameters.

    Args:
        group (Group): The click group to invoke (roster_players_group or roster_coaches_group)
        resource_type (str): Type of resource ("player" or "coach")
        resource_id (str): The resource ID to delete
        action_path (str): Full import path to the action function to patch
        season_id (str): Season ID for the test
        session (MagicMock): Mock session fixture
        config (MagicMock): Mock config fixture
        with_force (bool): Whether to include --force flag (default=True)
        input_text (str | None): Input text for confirmation prompt (default=None)
        should_fail (bool): Whether the action should raise an exception (default=False)
        error_message (str | None): Error message if should_fail is True (default=None)

    Returns:
        tuple[int, str, MagicMock]: Tuple of (exit_code, output, mock_action)
    """
    return run_roster_delete_test_base(
        group=group,
        resource_type=resource_type,
        resource_id=resource_id,
        action_path=action_path,
        build_session_path="gamesheet_sdk.admin.cli.commands.roster.build_authenticated_session",
        context_obj={
            "config": config,
            "season_id": season_id,
        },
        session=session,
        with_force=with_force,
        input_text=input_text,
        should_fail=should_fail,
        error_message=error_message,
    )
