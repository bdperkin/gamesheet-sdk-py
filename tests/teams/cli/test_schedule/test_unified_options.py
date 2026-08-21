# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the teams side of the unified game option set.

Covers the pieces that only exist because ``gamesheet-teams schedule games`` and ``gamesheet-admin games`` now
share one option vocabulary: the admin-only label options being warned about rather than rejected, the
absolute team-naming spelling mapping onto the gateway's relative one, and ``--association-id`` /
``--league-id`` being derived from ``--season-id`` instead of asked for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.teams.cli.main import cli
from gamesheet_sdk.teams.schedule import CreatedGameResult, UpdatedGameResult
from gamesheet_sdk.teams.seasons import SeasonOwnership

if TYPE_CHECKING:
    from click.testing import CliRunner

_RUNNER = "gamesheet_sdk.teams.cli.commands.schedule.game_runner"
OWNERSHIP = SeasonOwnership(association_id="38", league_id="1148580")

_CREATE_ARGS = [
    "schedule",
    "games",
    "create",
    "--season-id",
    "15020",
    "--start",
    "2026-08-20 12:00",
    "--duration",
    "75",
    "--game-type",
    "regular_season",
    "--number",
    "TEST-1",
]


def test_absolute_team_naming_maps_onto_the_gateway_payload(runner: CliRunner) -> None:
    """``--home-team-id``/``--visitor-team-id`` produce the right team_id + home_flag pair."""
    created = CreatedGameResult(success=True, game_number="TEST-1")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[OWNERSHIP, created]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                *_CREATE_ARGS,
                "--home-team-id",
                "10",
                "--home-division-id",
                "1",
                "--visitor-team-id",
                "20",
                "--visitor-division-id",
                "2",
                "--visitor",
            ],
        )

    assert result.exit_code == 0, result.output
    args = mock_action.call_args[0]
    # Positional order: session, action, then team, season, division, opposing team, start, end.
    kwargs = mock_action.call_args[1]
    assert args[2] == "20"
    assert args[4] == "2"
    assert args[5] == "10"
    assert kwargs["opposing_division"] == "1"
    assert kwargs["home_flag"] is False


def test_association_and_league_are_derived_from_the_season(runner: CliRunner) -> None:
    """The two gateway-only identifiers come from a season lookup, not from the command line."""
    created = CreatedGameResult(success=True, game_number="TEST-1")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[OWNERSHIP, created]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            [
                *_CREATE_ARGS,
                "-t",
                "10",
                "--division-id",
                "1",
                "--opposing-team-id",
                "20",
                "--opposing-division-id",
                "2",
            ],
        )

    assert result.exit_code == 0, result.output
    lookup_args = mock_action.call_args_list[0][0]
    assert lookup_args[2] == "15020"
    kwargs = mock_action.call_args[1]
    assert kwargs["association_id"] == "38"
    assert kwargs["league_id"] == "1148580"


def test_admin_only_labels_warn_but_do_not_fail(runner: CliRunner) -> None:
    """``--home-label``/``--visitor-label`` have no gateway field and are reported as ignored."""
    created = CreatedGameResult(success=True, game_number="TEST-1")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[OWNERSHIP, created]),
    ):
        result = runner.invoke(
            cli,
            [
                *_CREATE_ARGS,
                "-t",
                "10",
                "--division-id",
                "1",
                "--opposing-team-id",
                "20",
                "--opposing-division-id",
                "2",
                "--home-label",
                "Blue",
                "--visitor-label",
                "White",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "--home-label is not supported by `gamesheet-teams`" in result.output
    assert "--visitor-label is not supported by `gamesheet-teams`" in result.output


def test_update_maps_absolute_names_using_the_games_current_side(runner: CliRunner) -> None:
    """On an away game, ``--home-team-id`` names the opponent, not the acting team."""
    game = {
        "id": 42,
        "team_id": 525015,
        "home_flag": False,
        "date_time": "2026-08-24T15:00",
        "end_time": "16:15",
    }
    updated = UpdatedGameResult(success=True, id=42, message="ok")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[game, updated]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "update", "-g", "42", "--home-team-id", "999"],
        )

    assert result.exit_code == 0, result.output
    kwargs = mock_action.call_args[1]
    assert kwargs["opposing_team_id"] == "999"
    assert kwargs["team_id"] == "525015"
    assert kwargs["home_flag"] is None


def test_update_without_a_side_defaults_home_when_the_gateway_omits_it(runner: CliRunner) -> None:
    """A game dict with no home_flag falls back to treating the acting team as home."""
    game = {"id": 42, "team_id": 525015, "date_time": "2026-08-24T15:00", "end_time": "16:15"}
    updated = UpdatedGameResult(success=True, id=42, message="ok")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[game, updated]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "update", "-g", "42", "--home-team-id", "999"],
        )

    assert result.exit_code == 0, result.output
    assert mock_action.call_args[1]["team_id"] == "999"


def test_update_rederives_association_when_the_season_changes(runner: CliRunner) -> None:
    """Naming a new ``--season-id`` on update also refreshes association and league."""
    game = {"id": 42, "team_id": 525015, "date_time": "2026-08-24T15:00", "end_time": "16:15"}
    updated = UpdatedGameResult(success=True, id=42, message="ok")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[game, OWNERSHIP, updated]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "update", "-g", "42", "--season-id", "15020"],
        )

    assert result.exit_code == 0, result.output
    kwargs = mock_action.call_args[1]
    assert kwargs["association_id"] == "38"
    assert kwargs["league_id"] == "1148580"


def test_update_time_zone_is_left_alone_unless_named(runner: CliRunner) -> None:
    """An update that says nothing about the time zone sends neither field."""
    game = {"id": 42, "team_id": 525015, "date_time": "2026-08-24T15:00", "end_time": "16:15"}
    updated = UpdatedGameResult(success=True, id=42, message="ok")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[game, updated]) as mock_action,
    ):
        result = runner.invoke(cli, ["schedule", "games", "update", "-g", "42", "--location", "Rink"])

    assert result.exit_code == 0, result.output
    kwargs = mock_action.call_args[1]
    assert kwargs["time_zone_name"] is None
    assert kwargs["time_zone_offset"] is None


def test_update_time_zone_is_completed_when_only_the_name_is_named(runner: CliRunner) -> None:
    """Naming just the zone fills in the offset from the system, as ``create`` does."""
    game = {"id": 42, "team_id": 525015, "date_time": "2026-08-24T15:00", "end_time": "16:15"}
    updated = UpdatedGameResult(success=True, id=42, message="ok")
    with (
        patch(f"{_RUNNER}.build_authenticated_session", return_value=MagicMock()),
        patch(f"{_RUNNER}.run_action_or_exit", side_effect=[game, updated]) as mock_action,
    ):
        result = runner.invoke(
            cli,
            ["schedule", "games", "update", "-g", "42", "--timezone", "America/Denver"],
        )

    assert result.exit_code == 0, result.output
    kwargs = mock_action.call_args[1]
    assert kwargs["time_zone_name"] == "America/Denver"
    assert isinstance(kwargs["time_zone_offset"], int)


def test_update_rejects_conflicting_time_options_before_authenticating(runner: CliRunner) -> None:
    """A bad option combination reports as a usage error rather than as a missing session."""
    result = runner.invoke(
        cli,
        [
            "schedule",
            "games",
            "update",
            "-g",
            "42",
            "--start-datetime",
            "2026-08-24 15:00",
            "--start-date",
            "2026-08-24",
        ],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output
