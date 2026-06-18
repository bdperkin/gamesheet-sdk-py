"""Test coverage for teams roster group context setup."""

from __future__ import annotations

from unittest.mock import MagicMock

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams import teams_group


def test_teams_roster_group_context_setup() -> None:
    """Ensure teams roster group context is properly set up."""
    # Invoke the roster group with required options to trigger context setup
    result = CliRunner().invoke(
        teams_group,
        ["roster", "--season-id", "100", "--team-id", "50", "players", "--help"],
        obj=MagicMock(),
    )
    # We just care that the context gets set up, not the command output
    # The --help will show the help for players, confirming context passed through
    assert not result.exit_code
