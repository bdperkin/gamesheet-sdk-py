# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for schedule games CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import (
    CreatedGameResult,
    ScheduleDeleteResult,
    UpdatedGameResult,
)
from gamesheet_sdk.teams.seasons import SeasonOwnership

#: ``schedule games create`` derives --association-id / --league-id from the season, so every create makes
#: one lookup call before the create call itself.
OWNERSHIP = SeasonOwnership(association_id="38", league_id="1148580")

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_games_create_help(runner: CliRunner) -> None:
    """Test `gamesheet-teams schedule games create --help`."""
    result = runner.invoke(
        cli,
        ["schedule", "games", "create", "--help"],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 0
    assert "game" in result.output.lower()
    assert "--opposing-team-id" in result.output
    assert "--home" in result.output
    assert "--game-number" in result.output


def test_games_create_home_and_aliases(runner: CliRunner) -> None:
    """Test `schedule games create`, `add`, `new` as home team."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
        home_flag=True,
    )
    for subcmd in ["create", "add", "new"]:
        with (
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
                return_value=MagicMock(),
            ),
            patch(
                "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
                side_effect=[OWNERSHIP, mock_created],
            ) as mock_action,
        ):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "games",
                    subcmd,
                    "-t",
                    "525015",
                    "--opposing-team-id",
                    "523675",
                    "--season-id",
                    "15020",
                    "--division-id",
                    "81419",
                    "--opposing-division-id",
                    "81419",
                    "--game-number",
                    "TEST-123",
                    "--game-type",
                    "regular_season",
                    "--home",
                    "--start",
                    "2026-08-20 12:00",
                    "--end",
                    "2026-08-20 13:15",
                ],
            )
            assert result.exit_code == 0
            assert "TEST-123" in result.output
            args = mock_action.call_args[0]
            kwargs = mock_action.call_args[1]
            assert args[2] == "525015"
            assert args[3] == "15020"
            assert args[4] == "81419"
            assert args[5] == "523675"
            assert args[6] == "2026-08-20T12:00"
            assert args[7] == "13:15"
            assert kwargs["home_flag"] is True
            assert kwargs["game_number"] == "TEST-123"


def test_games_create_visitor(runner: CliRunner) -> None:
    """Test `schedule games create --visitor`."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
        home_flag=False,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[OWNERSHIP, mock_created],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--opposing-division-id",
                "81419",
                "--game-number",
                "TEST-123",
                "--game-type",
                "regular_season",
                "--visitor",
                "--start",
                "2026-08-20 12:00",
                "--duration",
                "75",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["home_flag"] is False


def test_games_create_all_options(runner: CliRunner) -> None:
    """Test `schedule games create` with all options provided."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        location="Polar Ice",
        broadcast_provider="LIVEBARN",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[OWNERSHIP, mock_created],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--opposing-division-id",
                "81420",
                "--game-number",
                "TEST-123",
                "--game-type",
                "playoff",
                "--location",
                "Polar Ice",
                "--scorekeeper-name",
                "Jane Doe",
                "--scorekeeper-phone",
                "555-1234",
                "--broadcaster",
                "LIVEBARN",
                "--time-zone-name",
                "America/New_York",
                "--time-zone-offset",
                "-240",
                "--date",
                "2026-08-20",
                "--start",
                "12:00",
                "--end",
                "13:15",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args[1]
        assert kwargs["opposing_division"] == "81420"
        assert kwargs["association_id"] == "38"
        assert kwargs["league_id"] == "1148580"
        assert kwargs["game_type"] == "playoff"
        assert kwargs["location"] == "Polar Ice"
        assert kwargs["scorekeeper_name"] == "Jane Doe"
        assert kwargs["scorekeeper_phone"] == "555-1234"
        assert kwargs["broadcast_provider"] == "LIVEBARN"
        assert kwargs["time_zone_name"] == "America/New_York"
        assert kwargs["time_zone_offset"] == -240


def test_games_create_missing_required(runner: CliRunner) -> None:
    """Test `schedule games create` missing required options."""
    res = runner.invoke(
        cli,
        [
            "schedule",
            "games",
            "create",
            "-t",
            "525015",
            "--season-id",
            "15020",
        ],
    )
    assert res.exit_code == 2
    assert "Missing option" in res.output


def test_games_create_envvars(runner: CliRunner) -> None:
    """Test `schedule games create` with GAMESHEET_TEAM_ID and GAMESHEET_SEASON_ID envvars."""
    mock_created = CreatedGameResult(success=True, game_number="TEST-123")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[OWNERSHIP, mock_created],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "--opposing-team-id",
                "523675",
                "--division-id",
                "81419",
                "--opposing-division-id",
                "81419",
                "--game-number",
                "TEST-123",
                "--game-type",
                "regular_season",
                "--start",
                "2026-08-20 12:00",
                "--duration",
                "75",
            ],
            env={
                "GAMESHEET_TEAM_ID": "525015",
                "GAMESHEET_SEASON_ID": "15020",
            },
        )
        assert result.exit_code == 0
        args = mock_action.call_args[0]
        assert args[2] == "525015"
        assert args[3] == "15020"


def test_games_create_json_format(runner: CliRunner) -> None:
    """Test `schedule games create -F json`."""
    mock_created = CreatedGameResult(
        success=True,
        game_number="TEST-123",
        team_id=525015,
        opposing_team_id=523675,
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[OWNERSHIP, mock_created],
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "create",
                "-t",
                "525015",
                "--opposing-team-id",
                "523675",
                "--season-id",
                "15020",
                "--division-id",
                "81419",
                "--opposing-division-id",
                "81419",
                "--game-number",
                "TEST-123",
                "--game-type",
                "regular_season",
                "--start",
                "2026-08-20 12:00",
                "--duration",
                "75",
                "-F",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["success"] is True
        assert data[0]["game_number"] == "TEST-123"


def test_games_delete_force(runner: CliRunner) -> None:
    """Test `schedule games delete --force`."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=mock_res,
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
                "--force",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully deleted game 2962920" in result.output
        mock_action.assert_called_once()


def test_games_delete_prompt_confirm_and_abort(runner: CliRunner) -> None:
    """Test `schedule games delete` interactive confirmation and abortion."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        # Confirm
        res1 = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
            ],
            input="y\n",
        )
        assert res1.exit_code == 0
        assert "Successfully deleted game 2962920" in res1.output

        # Abort
        res2 = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "delete",
                "-g",
                "2962920",
            ],
            input="n\n",
        )
        assert res2.exit_code == 1
        assert "Aborted" in res2.output


def test_games_delete_json_and_aliases(runner: CliRunner) -> None:
    """Test `schedule games del/rm/remove` aliases and json formatting."""
    mock_res = ScheduleDeleteResult(success=True, message="Game deleted successfully", id="2962920")
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            return_value=mock_res,
        ),
    ):
        for alias in ("del", "rm", "remove"):
            result = runner.invoke(
                cli,
                [
                    "schedule",
                    "games",
                    alias,
                    "-g",
                    "2962920",
                    "--force",
                    "-F",
                    "json",
                ],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data[0]["success"] is True


def test_games_update_basic(runner: CliRunner) -> None:
    """Test `schedule games update` updates location, number, scorekeeper."""
    mock_game = {
        "id": 2962945,
        "team_id": 525015,
        "opposing_team_id": 523675,
        "season_id": 15020,
        "division_id": 81419,
        "opposing_division": 81419,
        "association_id": 38,
        "league_id": 1148580,
        "home_flag": True,
        "game_number": "OLD-1",
        "game_type": "regular_season",
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
        "location": "Old Rink",
        "scorekeeper_name": "Old SK",
        "scorekeeper_phone": "555-0000",
        "broadcast_provider": "LIVEBARN",
    }
    mock_updated = UpdatedGameResult(
        success=True,
        id=2962945,
        game_number="NEW-100",
        location="New Arena",
        scorekeeper_name="New SK",
        date_time="2026-08-24T15:00",
        end_time="16:15",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962945",
                "--game-number",
                "NEW-100",
                "--location",
                "New Arena",
                "--scorekeeper-name",
                "New SK",
            ],
        )
        assert result.exit_code == 0
        assert "NEW-100" in result.output
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["game_number"] == "NEW-100"
        assert kwargs["location"] == "New Arena"
        assert kwargs["scorekeeper_name"] == "New SK"
        assert kwargs["team_id"] == "525015"


def test_games_update_datetime_resolution(runner: CliRunner) -> None:
    """Test `schedule games update` with datetime calculation using duration."""
    mock_game = {
        "id": 2962946,
        "team_id": 525015,
        "opposing_team_id": 523675,
        "season_id": 15020,
        "division_id": 81419,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(
        success=True,
        id=2962946,
        date_time="2026-08-25T18:00",
        end_time="19:30",
    )
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962946",
                "--start",
                "2026-08-25 18:00",
                "--duration",
                "90",
            ],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["date_time"] == "2026-08-25T18:00"
        assert kwargs["end_time"] == "19:30"


def test_games_update_aliases(runner: CliRunner) -> None:
    """Test `schedule games set` and `schedule games edit` aliases."""
    mock_game = {
        "id": 2962947,
        "team_id": 525015,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962947)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[mock_game, mock_updated, mock_game, mock_updated],
        ),
    ):
        res1 = runner.invoke(cli, ["schedule", "games", "set", "-g", "2962947"])
        assert res1.exit_code == 0
        res2 = runner.invoke(cli, ["schedule", "games", "edit", "-g", "2962947"])
        assert res2.exit_code == 0


def test_games_update_game_type(runner: CliRunner) -> None:
    """Test `schedule games update` with valid and invalid game-type."""
    mock_game = {
        "id": 2962948,
        "team_id": 525015,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962948)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "update", "-g", "2962948", "--game-type", "exhibition"],
        )
        assert result.exit_code == 0
        kwargs = mock_action.call_args_list[1][1]
        assert kwargs["game_type"] == "exhibition"

    # Invalid game type raises click.UsageError
    res_inv = runner.invoke(
        cli,
        ["schedule", "games", "update", "-g", "2962948", "--game-type", "invalid_type"],
    )
    assert res_inv.exit_code != 0


def test_games_update_no_t_in_date_time(runner: CliRunner) -> None:
    """Test `schedule games update` when current game date_time has no T."""
    mock_game = {
        "id": 2962950,
        "team_id": 525015,
        "date_time": "2026-08-24",
        "end_time": "16:15",
    }
    mock_updated = UpdatedGameResult(success=True, id=2962950)
    with (
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.build_authenticated_session",
            return_value=MagicMock(),
        ),
        patch(
            "gamesheet_sdk.teams.cli.commands.schedule.game_runner.run_action_or_exit",
            side_effect=[mock_game, mock_updated],
        ),
    ):
        result = runner.invoke(
            cli,
            [
                "schedule",
                "games",
                "update",
                "-g",
                "2962950",
            ],
        )
        assert result.exit_code == 0
