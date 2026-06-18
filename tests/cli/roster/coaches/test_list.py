"""Coverage tests for roster coaches list command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.roster import coaches_group


def test_roster_coaches_list_coverage() -> None:
    """Ensure coaches list command body is covered."""
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
            coaches_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020"},
        )
        assert not result.exit_code
