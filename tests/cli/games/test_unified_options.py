# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the admin side of the unified game option set.

Covers the pieces that only exist because ``gamesheet-admin games`` and ``gamesheet-teams schedule games``
now share one option vocabulary: ``--season-id`` accepted in two positions, the promoted ``games <verb>``
shortcuts, the teams-only options being warned about rather than rejected, and the relative team-naming
spelling reaching the season-schedule payload.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from gamesheet_sdk.admin.cli.commands.games import SCHEDULED_VERBS, games_group
from gamesheet_sdk.admin.cli.commands.games_scheduled import scheduled_group
from gamesheet_sdk.admin.cli.main import cli

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from click.testing import CliRunner

_AUTH = (
    "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
    "gamesheet_sdk.admin.cli.helpers.load_access_token",
)
_RUNNER = "gamesheet_sdk.admin.cli.shared.game_runner"

_CREATE_ARGS = [
    "--start-datetime",
    "2026-07-15T19:00:00",
    "--duration",
    "1h15m",
    "--home-team-id",
    "team-1",
    "--home-division-id",
    "div-1",
    "--visitor-team-id",
    "team-2",
    "--visitor-division-id",
    "div-2",
    "--game-type",
    "regular_season",
    "--number",
    "101",
]


def _patched() -> AbstractContextManager[Any]:
    """Patch the session plumbing so no command reaches the network.

    Returns:
        AbstractContextManager[Any]: A patch context manager usable with ``with``.

    """
    return patch.multiple(
        _RUNNER,
        build_authenticated_session=MagicMock(),
        run_action_or_exit=MagicMock(
            return_value=MagicMock(model_dump=lambda **_kw: {"id": "game-1"}),
        ),
    )


def test_promoted_verbs_are_the_scheduled_commands() -> None:
    """``games <verb>`` and ``games scheduled <verb>`` are literally the same command object."""
    assert games_group.commands["scheduled"] is scheduled_group
    for verb in SCHEDULED_VERBS:
        assert games_group.commands[verb] is scheduled_group.commands[verb]


@pytest.mark.parametrize(
    "argv",
    [
        ["games", "--season-id", "s-1", "scheduled", "create"],
        ["games", "scheduled", "create", "--season-id", "s-1"],
        ["games", "create", "--season-id", "s-1"],
        ["games", "--season-id", "s-1", "create"],
    ],
    ids=["group-option", "subcommand-option", "promoted-verb", "promoted-verb-group-option"],
)
def test_season_id_is_accepted_in_either_position(runner: CliRunner, argv: list[str]) -> None:
    """A teams-style command line, with --season-id after the verb, works here too."""
    with (
        _patched(),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
        patch(f"{_RUNNER}.render_get_command"),
        patch(f"{_RUNNER}._create_scheduled_game_action"),
    ):
        result = runner.invoke(cli, [*argv, *_CREATE_ARGS])

    assert not result.exit_code, result.output


def test_missing_season_id_is_a_usage_error(runner: CliRunner) -> None:
    """With no season in either position the command reports a usage error, not a login failure."""
    result = runner.invoke(cli, ["games", "create", *_CREATE_ARGS])
    assert result.exit_code == 2
    assert "--season-id" in result.output


def test_relative_team_naming_reaches_the_json_api_payload(runner: CliRunner) -> None:
    """``--team-id``/``--opposing-team-id`` plus ``--visitor`` resolve to the right absolute pair."""
    with (
        patch(f"{_RUNNER}.build_authenticated_session"),
        patch(f"{_RUNNER}.run_action_or_exit") as mock_run,
        patch(f"{_RUNNER}.render_get_command"),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
    ):
        result = runner.invoke(
            cli,
            [
                "games",
                "create",
                "--season-id",
                "s-1",
                "--start-datetime",
                "2026-07-15T19:00:00",
                "--duration",
                "75",
                "--team-id",
                "team-2",
                "--division-id",
                "div-2",
                "--opposing-team-id",
                "team-1",
                "--opposing-division-id",
                "div-1",
                "--visitor",
                "--game-type",
                "regular_season",
                "--number",
                "101",
            ],
        )

    assert not result.exit_code, result.output
    # Positional order: session, action, season, start, end, then the four absolute identifiers.
    args = mock_run.call_args[0]
    assert args[5] == "team-1"
    assert args[6] == "div-1"
    assert args[7] == "team-2"
    assert args[8] == "div-2"


def test_conflicting_team_spellings_are_rejected(runner: CliRunner) -> None:
    """Naming the home team twice with different values fails before any request."""
    result = runner.invoke(
        cli,
        [
            "games",
            "create",
            "--season-id",
            "s-1",
            "--start-datetime",
            "2026-07-15T19:00:00",
            "--duration",
            "75",
            "--home-team-id",
            "team-1",
            "--team-id",
            "team-9",
            "--visitor-team-id",
            "team-2",
            "--home-division-id",
            "div-1",
            "--visitor-division-id",
            "div-2",
            "--game-type",
            "regular_season",
            "--number",
            "101",
        ],
        env={"COLUMNS": "200"},
    )
    assert result.exit_code == 2
    assert "both name the same team but disagree" in result.output


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["games", "list", "--season-id", "s-1", "--team-id", "t-1"], "--team-id"),
        (["games", "list", "--season-id", "s-1", "--month", "2026-08"], "--month"),
        (["games", "list", "--season-id", "s-1", "--event-data"], "--event-data"),
    ],
    ids=["team-id", "month", "event-data"],
)
def test_teams_only_list_options_warn_but_do_not_fail(
    runner: CliRunner,
    argv: list[str],
    expected: str,
) -> None:
    """Teams-gateway filters are accepted for portability and reported as ignored."""
    with (
        patch(f"{_RUNNER}.build_authenticated_session"),
        patch(f"{_RUNNER}.run_action_or_exit", return_value=[]),
        patch(f"{_RUNNER}.render_list_command"),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
    ):
        result = runner.invoke(cli, argv)

    assert not result.exit_code, result.output
    assert f"{expected} is not supported by `gamesheet-admin`" in result.output


def test_default_month_does_not_warn(runner: CliRunner) -> None:
    """``--month all`` narrows nothing, so it is not worth a warning."""
    with (
        patch(f"{_RUNNER}.build_authenticated_session"),
        patch(f"{_RUNNER}.run_action_or_exit", return_value=[]),
        patch(f"{_RUNNER}.render_list_command"),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
    ):
        result = runner.invoke(cli, ["games", "list", "--season-id", "s-1", "--month", "all"])

    assert not result.exit_code, result.output
    assert "--month" not in result.output


def test_availability_warns_on_get(runner: CliRunner) -> None:
    """``--availability`` has no season-schedule equivalent and is reported as ignored."""
    with (
        patch(f"{_RUNNER}.build_authenticated_session"),
        patch(f"{_RUNNER}.run_action_or_exit", return_value=MagicMock(model_dump=lambda **_kw: {})),
        patch(f"{_RUNNER}.render_get_command"),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
    ):
        result = runner.invoke(
            cli,
            ["games", "get", "--season-id", "s-1", "-g", "g-1", "--availability"],
        )

    assert not result.exit_code, result.output
    assert "--availability is not supported by `gamesheet-admin`" in result.output


def test_delete_renders_a_result_object_for_data_formats(runner: CliRunner) -> None:
    """``-F json`` on delete emits a machine-readable result, matching gamesheet-teams."""
    with (
        patch(f"{_RUNNER}.build_authenticated_session"),
        patch(f"{_RUNNER}.run_action_or_exit", return_value=None),
        patch(_AUTH[0], return_value="refresh-tok"),
        patch(_AUTH[1], return_value="bearer-tok"),
    ):
        result = runner.invoke(
            cli,
            ["games", "delete", "--season-id", "s-1", "--id", "g-9", "-f", "-F", "json"],
        )

    assert not result.exit_code, result.output
    payload = json.loads(result.output)
    assert payload[0]["success"] is True
    assert payload[0]["id"] == "g-9"


def test_update_rejects_conflicting_time_options_before_authenticating(runner: CliRunner) -> None:
    """A bad option combination reports as a usage error rather than as a missing session."""
    result = runner.invoke(
        cli,
        [
            "games",
            "update",
            "--season-id",
            "s-1",
            "-g",
            "g-1",
            "--start-datetime",
            "2026-07-15T19:00:00",
            "--start-date",
            "2026-07-15",
        ],
    )
    assert result.exit_code == 2
    assert "Cannot combine" in result.output
