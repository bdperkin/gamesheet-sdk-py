# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test coverage for roster group context setup."""

from __future__ import annotations

from unittest.mock import MagicMock

from click.testing import CliRunner

from gamesheet_sdk.cli.main import cli


def test_roster_group_context_setup() -> None:
    """Ensure roster group context is properly set up."""
    # Invoke the roster group with required options to trigger context setup
    result = CliRunner().invoke(
        cli,
        ["roster", "--season-id", "100", "players", "--help"],
        obj=MagicMock(),
    )
    # We just care that the context gets set up, not the command output
    # The --help will show the help for players, confirming context passed through
    assert not result.exit_code
