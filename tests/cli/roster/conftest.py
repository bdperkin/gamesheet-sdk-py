# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for CLI roster tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click import Group
from click.testing import CliRunner
import pytest

from gamesheet_sdk import Config


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
        group: The click group to invoke (roster_players_group or roster_coaches_group)
        resource_type: Type of resource ("player" or "coach")
        resource_id: The resource ID to delete
        action_path: Full import path to the action function to patch
        season_id: Season ID for the test
        session: Mock session fixture
        config: Mock config fixture
        with_force: Whether to include --force flag (default: True)
        input_text: Input text for confirmation prompt (default: None)
        should_fail: Whether the action should raise an exception (default: False)
        error_message: Error message if should_fail is True (default: None)

    Returns:
        Tuple of (exit_code, output, mock_action)
    """
    runner = CliRunner()
    patches = [
        patch(
            "gamesheet_sdk.cli.commands.roster.build_authenticated_session",
            return_value=session,
        ),
    ]

    if should_fail:
        patches.append(
            patch(
                action_path,
                side_effect=Exception(error_message or "Delete failed"),
            ),
        )
    else:
        patches.append(patch(action_path))

    with patches[0], patches[1] as mock_action:
        args = ["delete", f"--{resource_type}-id", resource_id]
        if with_force:
            args.append("--force")

        result = runner.invoke(
            group,
            args,
            obj={
                "config": config,
                "season_id": season_id,
            },
            input=input_text,
        )

        return result.exit_code, result.output, mock_action
