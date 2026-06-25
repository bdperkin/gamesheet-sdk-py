"""Coverage tests for teams roster coaches get command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.teams_roster import teams_roster_coaches_group


def test_teams_roster_coaches_get_coverage() -> None:
    """Ensure teams roster coaches get command body is covered."""
    runner = CliRunner()
    mock_coach = MagicMock()
    mock_coach.id = "1868550"
    with (
        patch("gamesheet_sdk.cli.commands.teams_roster.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.teams_roster._get_team_coach_action",
            return_value=mock_coach,
        ),
        patch("gamesheet_sdk.cli.commands.teams_roster.render_get_command"),
    ):
        result = runner.invoke(
            teams_roster_coaches_group,
            [
                "get",
                "--coach-id",
                "1868550",
                "-F",
                "json",
            ],
            obj={"config": MagicMock(), "season_id": "15020", "team_id": "12345"},
        )
        assert not result.exit_code
