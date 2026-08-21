# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games create CLI command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from gamesheet_sdk.admin.cli.main import cli
from tests.fixtures.constants import (
    TEST_ACCESS_TOKEN,
    TEST_LOCATION_NAME,
    TEST_REFRESH_TOKEN,
    TEST_SCOREKEEPER_NAME,
    TEST_SCOREKEEPER_PHONE,
    TEST_SURFACE_NAME,
    TEST_TIMEZONE_NAME,
    TEST_TIMEZONE_OFFSET,
)

if TYPE_CHECKING:
    from click.testing import CliRunner

_CREATE_MOCKS = (
    "gamesheet_sdk.admin.cli.shared.game_runner.build_authenticated_session",
    "gamesheet_sdk.admin.cli.shared.game_runner.run_action_or_exit",
    "gamesheet_sdk.common.cli.game_times.get_local_timezone_name",
    "gamesheet_sdk.common.cli.game_times.get_local_timezone_offset",
    "gamesheet_sdk.admin.cli.shared.game_runner.render_get_command",
    "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
    "gamesheet_sdk.admin.cli.helpers.load_access_token",
)


def test_scheduled_create_with_defaults(runner: CliRunner) -> None:
    """Test scheduled game create command with default timezone values."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2]) as mock_tz_name,
        patch(_CREATE_MOCKS[3]) as mock_tz_offset,
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
    ):
        mock_tz_name.return_value = TEST_TIMEZONE_NAME
        mock_tz_offset.return_value = TEST_TIMEZONE_OFFSET
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-123", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-456",
                "scheduled",
                "create",
                "--start-datetime",
                "2026-07-15T19:00:00-04:00",
                "--end-datetime",
                "2026-07-15T21:00:00-04:00",
                "--home-team-id",
                "team-1",
                "--home-division-id",
                "div-1",
                "--visitor-team-id",
                "team-2",
                "--visitor-division-id",
                "div-2",
                "--location",
                f"{TEST_LOCATION_NAME} {TEST_SURFACE_NAME}",
                "--scorekeeper-name",
                TEST_SCOREKEEPER_NAME,
                "--scorekeeper-phone",
                TEST_SCOREKEEPER_PHONE,
                "--game-type",
                "regular_season",
                "--number",
                "101",
            ],
        )

        assert not result.exit_code, result.output
        mock_tz_name.assert_called_once()
        mock_tz_offset.assert_called_once()
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[13] == TEST_TIMEZONE_NAME
        assert args[14] == TEST_TIMEZONE_OFFSET


def test_scheduled_create_with_explicit_timezone(runner: CliRunner) -> None:
    """Test scheduled game create command with explicit timezone values."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2]) as mock_tz_name,
        patch(_CREATE_MOCKS[3]) as mock_tz_offset,
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-789", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-789",
                "scheduled",
                "create",
                "--start-datetime",
                "2026-07-20T14:00:00-07:00",
                "--end-datetime",
                "2026-07-20T16:00:00-07:00",
                "--home-team-id",
                "team-3",
                "--home-division-id",
                "div-3",
                "--visitor-team-id",
                "team-4",
                "--visitor-division-id",
                "div-4",
                "--location",
                "Arena B",
                "--scorekeeper-name",
                "Jane Smith",
                "--scorekeeper-phone",
                "555-5678",
                "--game-type",
                "playoff",
                "--number",
                "202",
                "--time-zone-name",
                "America/Vancouver",
                "--time-zone-offset",
                "-420",
            ],
        )

        assert not result.exit_code, result.output
        mock_tz_name.assert_not_called()
        mock_tz_offset.assert_not_called()
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[13] == "America/Vancouver"
        assert args[14] == -420


def test_scheduled_create_missing_required_fields(runner: CliRunner) -> None:
    """Test scheduled game create command fails with missing required fields."""
    result = runner.invoke(
        cli,
        [
            "games",
            "--season-id",
            "season-456",
            "scheduled",
            "create",
        ],
    )

    assert result.exit_code
    assert "Missing option" in result.output or "Error" in result.output


def test_scheduled_create_with_optional_broadcaster_and_labels(
    runner: CliRunner,
) -> None:
    """Test scheduled game create command with optional broadcaster and team labels."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2], return_value=TEST_TIMEZONE_NAME),
        patch(_CREATE_MOCKS[3], return_value=TEST_TIMEZONE_OFFSET),
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-555", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-999",
                "scheduled",
                "create",
                "--start-datetime",
                "2026-08-01T18:00:00-04:00",
                "--end-datetime",
                "2026-08-01T20:00:00-04:00",
                "--home-team-id",
                "team-10",
                "--home-division-id",
                "div-10",
                "--visitor-team-id",
                "team-20",
                "--visitor-division-id",
                "div-20",
                "--location",
                "Main Arena Ice 1",
                "--scorekeeper-name",
                "Alice Johnson",
                "--scorekeeper-phone",
                "555-9999",
                "--game-type",
                "exhibition",
                "--number",
                "500",
                "--broadcaster",
                "livebarn",
                "--home-label",
                "Home Stars",
                "--visitor-label",
                "Away Comets",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[16] == "livebarn"
        assert args[17] == "Home Stars"
        assert args[18] == "Away Comets"


def test_create_with_split_date_time(runner: CliRunner) -> None:
    """Test create command with split --start-date + --start-time and --end-date + --end-time."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2], return_value=TEST_TIMEZONE_NAME),
        patch(_CREATE_MOCKS[3], return_value=TEST_TIMEZONE_OFFSET),
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
        patch(
            "gamesheet_sdk.admin.cli.shared.datetime_helpers.get_local_timezone_offset",
            return_value=-240,
        ),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-split", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-split",
                "scheduled",
                "create",
                "--start-date",
                "2026-07-15",
                "--start-time",
                "19:00",
                "--end-date",
                "2026-07-15",
                "--end-time",
                "21:00",
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
                "301",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[3].endswith("Z")
        assert args[4].endswith("Z")


def test_create_with_start_and_duration(runner: CliRunner) -> None:
    """Test create command with --start-datetime + --duration computes end."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2], return_value=TEST_TIMEZONE_NAME),
        patch(_CREATE_MOCKS[3], return_value=TEST_TIMEZONE_OFFSET),
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-dur", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-dur",
                "scheduled",
                "create",
                "--start-datetime",
                "2026-07-15T23:00:00Z",
                "--duration",
                "120",
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
                "401",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[3] == "2026-07-15T23:00:00Z"
        assert args[4] == "2026-07-16T01:00:00Z"


def test_create_with_end_and_duration(runner: CliRunner) -> None:
    """Test create command with --end-datetime + --duration computes start."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2], return_value=TEST_TIMEZONE_NAME),
        patch(_CREATE_MOCKS[3], return_value=TEST_TIMEZONE_OFFSET),
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-end-dur", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-end-dur",
                "scheduled",
                "create",
                "--end-datetime",
                "2026-07-16T01:00:00Z",
                "--duration",
                "120",
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
                "501",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[3] == "2026-07-04T23:00:00Z" or args[3].endswith("Z")
        assert args[4] == "2026-07-16T01:00:00Z"


def test_create_conflict_start_options_raises(runner: CliRunner) -> None:
    """Test error when --start-datetime and --start-date both provided."""
    result = runner.invoke(
        cli,
        [
            "games",
            "--season-id",
            "season-456",
            "scheduled",
            "create",
            "--start-datetime",
            "2026-07-15T19:00:00Z",
            "--start-date",
            "2026-07-15",
            "--end-datetime",
            "2026-07-15T21:00:00Z",
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
            "601",
        ],
    )

    assert result.exit_code
    assert "Cannot combine" in result.output


def test_create_conflict_end_options_raises(runner: CliRunner) -> None:
    """Test error when --end-datetime and --end-date both provided."""
    result = runner.invoke(
        cli,
        [
            "games",
            "--season-id",
            "season-456",
            "scheduled",
            "create",
            "--start-datetime",
            "2026-07-15T19:00:00Z",
            "--end-datetime",
            "2026-07-15T21:00:00Z",
            "--end-date",
            "2026-07-15",
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
            "701",
        ],
    )

    assert result.exit_code
    assert "Cannot combine" in result.output


def test_create_insufficient_options_raises(runner: CliRunner) -> None:
    """Test error when only one of start/end/duration provided."""
    result = runner.invoke(
        cli,
        [
            "games",
            "--season-id",
            "season-456",
            "scheduled",
            "create",
            "--start-datetime",
            "2026-07-15T19:00:00Z",
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
            "801",
        ],
    )

    assert result.exit_code
    assert "At least 2" in result.output


def test_create_natural_language_date(runner: CliRunner) -> None:
    """Test create command with natural language date input."""
    with (
        patch(_CREATE_MOCKS[0]),
        patch(_CREATE_MOCKS[1]) as mock_run,
        patch(_CREATE_MOCKS[2], return_value=TEST_TIMEZONE_NAME),
        patch(_CREATE_MOCKS[3], return_value=TEST_TIMEZONE_OFFSET),
        patch(_CREATE_MOCKS[4]),
        patch(_CREATE_MOCKS[5], return_value=TEST_REFRESH_TOKEN),
        patch(_CREATE_MOCKS[6], return_value=TEST_ACCESS_TOKEN),
        patch(
            "gamesheet_sdk.admin.cli.shared.datetime_helpers.get_local_timezone_offset",
            return_value=-240,
        ),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {"id": "game-nat", "status": "scheduled"},
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-nat",
                "scheduled",
                "create",
                "--start-datetime",
                "July 15 2026 7:00pm",
                "--duration",
                "120",
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
                "901",
            ],
        )

        assert not result.exit_code, result.output
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[3].endswith("Z")
        assert args[4].endswith("Z")
