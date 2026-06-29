# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for roster players list command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster_players import players_group
from tests.helpers import SEASON_ID


def test_roster_players_list_coverage() -> None:
    """Ensure players list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.roster.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.roster.render_list_command"),
    ):
        result = runner.invoke(
            players_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": SEASON_ID},
        )
        assert not result.exit_code
