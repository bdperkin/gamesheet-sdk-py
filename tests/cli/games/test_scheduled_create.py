# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for scheduled games create CLI command."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli


def test_timezone_name_tzlocal_with_key() -> None:
    """Test _get_local_timezone_name with tzlocal library (has .key attribute)."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Mock tzlocal module with a timezone that has .key attribute
    mock_tz = MagicMock()
    mock_tz.key = "America/New_York"
    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.return_value = mock_tz

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = _get_local_timezone_name()
        assert result == "America/New_York"


def test_timezone_name_tzlocal_without_key() -> None:
    """Test _get_local_timezone_name with tzlocal library (no .key attribute)."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Mock tzlocal module with a timezone that lacks .key attribute but has __str__
    # pylint: disable-next=too-few-public-methods
    class MockTZ:
        """Mock timezone object without .key attribute."""

        def __str__(self) -> str:
            return "America/Chicago"

    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.return_value = MockTZ()

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = _get_local_timezone_name()
        assert result == "America/Chicago"


def test_timezone_name_etc_localtime_symlink() -> None:
    """Test _get_local_timezone_name reading /etc/localtime symlink."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Remove tzlocal from sys.modules to trigger ImportError
    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("pathlib.Path.is_symlink", return_value=True),
        patch("os.readlink", return_value="/usr/share/zoneinfo/America/Los_Angeles"),
    ):
        result = _get_local_timezone_name()
        assert result == "America/Los_Angeles"


def test_timezone_name_fallback_utc_import_error() -> None:
    """Test _get_local_timezone_name falls back to UTC when tzlocal import fails."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Remove tzlocal to trigger ImportError, Windows to skip /etc/localtime
    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "nt"),
    ):
        result = _get_local_timezone_name()
        assert result == "UTC"


def test_timezone_name_fallback_utc_oserror() -> None:
    """Test _get_local_timezone_name falls back to UTC on OSError."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Mock tzlocal to raise OSError
    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.side_effect = OSError("Permission denied")

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = _get_local_timezone_name()
        assert result == "UTC"


def test_timezone_offset_standard_time() -> None:
    """Test _get_local_timezone_offset during standard time."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_offset

    # Mock time module for EST (UTC-5, -18000 seconds)
    with (
        patch("time.daylight", 0),  # No DST
        patch("time.timezone", 18000),  # UTC-5 in seconds
    ):
        result = _get_local_timezone_offset()
        assert result == -300  # -5 hours in minutes


def test_timezone_offset_daylight_saving_time() -> None:
    """Test _get_local_timezone_offset during daylight saving time."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_offset

    # Mock time module for EDT (UTC-4, -14400 seconds)
    mock_localtime = MagicMock()
    mock_localtime.tm_isdst = 1  # DST active

    with (
        patch("time.daylight", 1),  # DST supported
        patch("time.localtime", return_value=mock_localtime),
        patch("time.altzone", 14400),  # UTC-4 in seconds
    ):
        result = _get_local_timezone_offset()
        assert result == -240  # -4 hours in minutes


def test_scheduled_create_with_defaults(runner: CliRunner) -> None:
    """Test scheduled game create command with default timezone values."""
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.games.run_action_or_exit") as mock_run,
        patch(
            "gamesheet_sdk.cli.commands.games._get_local_timezone_name",
        ) as mock_tz_name,
        patch(
            "gamesheet_sdk.cli.commands.games._get_local_timezone_offset",
        ) as mock_tz_offset,
        patch("gamesheet_sdk.cli.commands.games.render_get_command"),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_tz_name.return_value = "America/Toronto"
        mock_tz_offset.return_value = -240
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {
                "id": "game-123",
                "status": "scheduled",
            },
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-456",
                "scheduled",
                "create",
                "--scheduled-start-time",
                "2026-07-15T19:00:00-04:00",
                "--scheduled-end-time",
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
                "Arena A Ice 1",
                "--scorekeeper-name",
                "John Doe",
                "--scorekeeper-phone",
                "555-1234",
                "--game-type",
                "regular_season",
                "--number",
                "101",
            ],
        )

        assert not result.exit_code
        mock_tz_name.assert_called_once()
        mock_tz_offset.assert_called_once()
        # Verify run_action_or_exit was called with the create action
        assert mock_run.call_count == 1
        # Verify timezone defaults were used (check args to run_action_or_exit)
        args = mock_run.call_args[0]
        assert args[13] == "America/Toronto"  # time_zone_name (index 13)
        assert args[14] == -240  # time_zone_offset (index 14)


def test_scheduled_create_with_explicit_timezone(runner: CliRunner) -> None:
    """Test scheduled game create command with explicit timezone values."""
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.games.run_action_or_exit") as mock_run,
        patch(
            "gamesheet_sdk.cli.commands.games._get_local_timezone_name",
        ) as mock_tz_name,
        patch(
            "gamesheet_sdk.cli.commands.games._get_local_timezone_offset",
        ) as mock_tz_offset,
        patch("gamesheet_sdk.cli.commands.games.render_get_command"),
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {
                "id": "game-789",
                "status": "scheduled",
            },
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-789",
                "scheduled",
                "create",
                "--scheduled-start-time",
                "2026-07-20T14:00:00-07:00",
                "--scheduled-end-time",
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

        assert not result.exit_code
        # Verify defaults were NOT called since explicit values provided
        mock_tz_name.assert_not_called()
        mock_tz_offset.assert_not_called()
        # Verify run_action_or_exit was called
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        assert args[13] == "America/Vancouver"  # explicit time_zone_name (index 13)
        assert args[14] == -420  # explicit time_zone_offset (index 14)


def test_timezone_name_etc_localtime_not_symlink() -> None:
    """Test _get_local_timezone_name when /etc/localtime is not a symlink."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Remove tzlocal, /etc/localtime exists but is NOT a symlink
    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("pathlib.Path.is_symlink", return_value=False),
    ):
        result = _get_local_timezone_name()
        assert result == "UTC"


def test_timezone_name_etc_localtime_no_zoneinfo() -> None:
    """Test _get_local_timezone_name when symlink doesn't contain zoneinfo."""
    from gamesheet_sdk.cli.commands.games import _get_local_timezone_name

    # Remove tzlocal, symlink doesn't contain "zoneinfo/"
    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("pathlib.Path.is_symlink", return_value=True),
        patch("os.readlink", return_value="/some/other/path"),
    ):
        result = _get_local_timezone_name()
        assert result == "UTC"


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
            # Missing all required fields
        ],
    )

    # Should fail with non-zero exit code
    assert result.exit_code
    # Error message should indicate missing options
    assert "Missing option" in result.output or "Error" in result.output


def test_scheduled_create_with_optional_broadcaster_and_labels(runner: CliRunner) -> None:
    """Test scheduled game create command with optional broadcaster and team labels."""
    with (
        patch("gamesheet_sdk.cli.commands.games.build_authenticated_session"),
        patch("gamesheet_sdk.cli.commands.games.run_action_or_exit") as mock_run,
        patch("gamesheet_sdk.cli.commands.games._get_local_timezone_name", return_value="America/Toronto"),
        patch("gamesheet_sdk.cli.commands.games._get_local_timezone_offset", return_value=-240),
        patch("gamesheet_sdk.cli.commands.games.render_get_command"),
        patch("gamesheet_sdk.cli.helpers.load_refresh_token", return_value="refresh-tok"),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_run.return_value = MagicMock(
            model_dump=lambda **_kw: {
                "id": "game-555",
                "status": "scheduled",
            },
        )

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-999",
                "scheduled",
                "create",
                "--scheduled-start-time",
                "2026-08-01T18:00:00-04:00",
                "--scheduled-end-time",
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

        assert not result.exit_code
        # Verify run_action_or_exit was called
        assert mock_run.call_count == 1
        args = mock_run.call_args[0]
        # Check broadcaster and labels were passed
        # Args after session & action: season_id, start, end, home_team, home_div, visitor_team,
        # visitor_div, location, sk_name, sk_phone, game_type, tz_name, tz_offset, number,
        # broadcaster, home_label, visitor_label
        # Indices: 2=season, 3=start, ..., 15=number, 16=broadcaster, 17=home_label, 18=visitor_label
        assert args[16] == "livebarn"  # broadcaster
        assert args[17] == "Home Stars"  # home_label
        assert args[18] == "Away Comets"  # visitor_label
