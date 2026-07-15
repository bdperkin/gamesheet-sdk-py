# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test fixtures and helpers for roster delete tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from click import Group
import pytest

from gamesheet_sdk import Config
from tests.cli.roster_helpers import run_roster_delete_test_base


@pytest.fixture
def mock_session() -> MagicMock:
    """Provide a mock session for testing."""
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
    team_id: str,
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
        group: The click group to invoke (teams_roster_players_group or teams_roster_coaches_group)
        resource_type: Type of resource ("player" or "coach")
        resource_id: The resource ID to delete
        action_path: Full import path to the action function to patch
        season_id: Season ID for the test
        team_id: Team ID for the test
        session: Mock session fixture
        config: Mock config fixture
        with_force: Whether to include --force flag (default: True)
        input_text: Input text for confirmation prompt (default: None)
        should_fail: Whether the action should raise an exception (default: False)
        error_message: Error message if should_fail is True (default: None)

    Returns:
        Tuple of (exit_code, output, mock_action)
    """
    # Derive build_session_path from action_path module
    # e.g., "gamesheet_sdk.admin.cli.commands.teams_roster_players._delete..."
    #    -> "gamesheet_sdk.admin.cli.commands.teams_roster_players.build_authenticated_session"
    module_path = action_path.rsplit(".", 1)[0]
    build_session_path = f"{module_path}.build_authenticated_session"

    return run_roster_delete_test_base(
        group=group,
        resource_type=resource_type,
        resource_id=resource_id,
        action_path=action_path,
        build_session_path=build_session_path,
        context_obj={
            "config": config,
            "season_id": season_id,
            "team_id": team_id,
        },
        session=session,
        with_force=with_force,
        input_text=input_text,
        should_fail=should_fail,
        error_message=error_message,
    )
