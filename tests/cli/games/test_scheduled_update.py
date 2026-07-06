# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games update CLI command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli


def test_scheduled_update_command(runner: CliRunner) -> None:
    """Test scheduled game update command."""
    with (
        patch("gamesheet_sdk.cli.commands.games_scheduled.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games_scheduled.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.cli.commands.games_scheduled.render_get_command"),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        # Mock returns: first call is get (current state), second is update
        mock_run.side_effect = [
            # First call: get current game
            MagicMock(
                data=MagicMock(
                    id="game-update",
                    attributes=MagicMock(
                        scheduled_start_time="2026-07-15T19:00:00-04:00",
                        scheduled_end_time="2026-07-15T21:00:00-04:00",
                        location="Old Arena",
                        scorekeeper=MagicMock(name="Old Name", phone="555-0000"),
                        game_type="regular_season",
                        time_zone_name="America/Toronto",
                        time_zone_offset=-240,
                        number="100",
                        status="scheduled",
                        data=MagicMock(
                            broadcaster="",
                            home_label="HOME",
                            visitor_label="AWAY",
                        ),
                    ),
                    relationships=MagicMock(
                        home_team=MagicMock(data=MagicMock(id="team-old-1")),
                        home_division=MagicMock(data=MagicMock(id="div-old-1")),
                        visitor_team=MagicMock(data=MagicMock(id="team-old-2")),
                        visitor_division=MagicMock(data=MagicMock(id="div-old-2")),
                    ),
                ),
            ),
            # Second call: update result
            MagicMock(
                model_dump=lambda **_kw: {
                    "id": "game-update",
                    "status": "scheduled",
                },
            ),
        ]

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-update",
                "scheduled",
                "update",
                "--game-id",
                "game-update",
                "--scheduled-start-time",
                "2026-07-16T20:00:00-04:00",
                "--location",
                "New Arena",
            ],
        )

        assert not result.exit_code
        assert mock_run.call_count == 2  # get + update
        # Verify update call (second call)
        update_args = mock_run.call_args_list[1][0]
        assert update_args[2] == "season-update"  # season_id (index 2)
        assert update_args[3] == "game-update"  # game_id (index 3)
        assert update_args[4] == "2026-07-16T20:00:00-04:00"  # New start time (index 4)
        assert update_args[10] == "New Arena"  # New location (index 10)
