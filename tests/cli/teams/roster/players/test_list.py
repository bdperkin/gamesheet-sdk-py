"""Coverage tests for teams roster players list command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams import teams_roster_players_group


def test_teams_roster_players_list_coverage() -> None:
    """Ensure teams roster players list command body is covered."""
    runner = CliRunner()
    with (
        patch("gamesheet_sdk.cli.commands.teams.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams.run_action_or_exit",
            return_value=[],
        ),
        patch("gamesheet_sdk.cli.commands.teams.render_list_command"),
    ):
        result = runner.invoke(
            teams_roster_players_group,
            ["list", "-F", "json"],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert not result.exit_code
