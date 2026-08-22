# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games update CLI command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.admin.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def _mock_current_game() -> MagicMock:
    """Create a mock for the current game state (returned by get).

    Returns:
        MagicMock: Mocked game object.

    """
    return MagicMock(
        data=MagicMock(
            id="game-update",
            attributes=MagicMock(
                scheduled_start_time="2026-07-15T23:00:00Z",
                scheduled_end_time="2026-07-16T01:00:00Z",
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
    )


def _mock_updated_game() -> MagicMock:
    """Create a mock for the updated game result.

    Returns:
        MagicMock: Mocked updated game result.

    """
    return MagicMock(
        model_dump=lambda **_kw: {"id": "game-update", "status": "scheduled"},
    )


def test_scheduled_update_command(runner: CliRunner) -> None:
    """Test scheduled game update command with new start time."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_get_command"),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_run.side_effect = [_mock_current_game(), _mock_updated_game()]

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
                "--start-datetime",
                "2026-07-15T22:00:00Z",
                "--location",
                "New Arena",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 2
        update_args = mock_run.call_args_list[1][0]
        assert update_args[2] == "season-update"
        assert update_args[3] == "game-update"
        assert update_args[4] == "2026-07-15T22:00:00Z"
        assert update_args[10] == "New Arena"


def test_update_with_duration_only(runner: CliRunner) -> None:
    """Test update with --duration only recomputes end from current start."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_get_command"),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_run.side_effect = [_mock_current_game(), _mock_updated_game()]

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
                "--duration",
                "90",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 2
        update_args = mock_run.call_args_list[1][0]
        assert update_args[4] == "2026-07-15T23:00:00Z"
        assert update_args[5] == "2026-07-16T00:30:00Z"


def test_update_with_split_start_inputs(runner: CliRunner) -> None:
    """Test update with --start-date + --start-time split inputs."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_get_command"),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.datetime_helpers.get_local_timezone_offset",
            return_value=-240,
        ),
    ):
        mock_run.side_effect = [_mock_current_game(), _mock_updated_game()]

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
                "--start-date",
                "2026-07-15",
                "--start-time",
                "18:00",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 2
        update_args = mock_run.call_args_list[1][0]
        assert update_args[4].endswith("Z")


def test_update_conflict_options_raises(runner: CliRunner) -> None:
    """Test error when --start-datetime and --start-date both provided."""
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
            "--start-datetime",
            "2026-07-15T19:00:00Z",
            "--start-date",
            "2026-07-15",
        ],
    )

    assert result.exit_code
    assert "Cannot combine" in result.output


def test_update_no_time_changes(runner: CliRunner) -> None:
    """Test update with only non-time fields preserves current times."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_get_command"),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_run.side_effect = [_mock_current_game(), _mock_updated_game()]

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
                "--location",
                "New Arena",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 2
        update_args = mock_run.call_args_list[1][0]
        assert update_args[4] == "2026-07-15T23:00:00Z"
        assert update_args[5] == "2026-07-16T01:00:00Z"


def test_update_end_and_duration(runner: CliRunner) -> None:
    """Test update with --end-datetime + --duration computes new start."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
        ),
        patch(
            "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
        ) as mock_run,
        patch("gamesheet_sdk.admin.cli.shared.game_runner.render_get_command"),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_run.side_effect = [_mock_current_game(), _mock_updated_game()]

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
                "--end-datetime",
                "2026-07-16T02:00:00Z",
                "--duration",
                "120",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 2
        update_args = mock_run.call_args_list[1][0]
        assert update_args[4] == "2026-07-16T00:00:00Z"
        assert update_args[5] == "2026-07-16T02:00:00Z"
