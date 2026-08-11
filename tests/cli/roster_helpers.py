# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared test helpers for roster CLI tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

if TYPE_CHECKING:
    from click import Group


def run_roster_delete_test_base(
    group: Group,
    resource_type: str,
    resource_id: str,
    action_path: str,
    build_session_path: str,
    context_obj: dict[str, Any],
    session: MagicMock,
    *,
    with_force: bool = True,
    input_text: str | None = None,
    should_fail: bool = False,
    error_message: str | None = None,
) -> tuple[int, str, MagicMock]:
    """Run a roster delete command test with given parameters.

    Base implementation shared between roster and teams_roster tests.

    Args:
        group (Group): The click group to invoke
        resource_type (str): Type of resource ("player" or "coach")
        resource_id (str): The resource ID to delete
        action_path (str): Full import path to the action function to patch
        build_session_path (str): Path to build_authenticated_session to patch
        context_obj (dict[str, Any]): Click context obj dict (must include config, season_id, optionally
            team_id)
        session (MagicMock): Mock session fixture
        with_force (bool): Whether to include --force flag (default=True)
        input_text (str | None): Input text for confirmation prompt (default=None)
        should_fail (bool): Whether the action should raise an exception (default=False)
        error_message (str | None): Error message if should_fail is True (default=None)

    Returns:
        tuple[int, str, MagicMock]: Tuple of (exit_code, output, mock_action)
    """
    runner = CliRunner()
    patches = [
        patch(
            build_session_path,
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
            obj=context_obj,
            input=input_text,
        )

        return result.exit_code, result.output, mock_action
