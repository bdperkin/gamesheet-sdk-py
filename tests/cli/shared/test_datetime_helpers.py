# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for datetime parsing and resolution helpers."""

from __future__ import annotations

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import rich_click as click

from gamesheet_sdk.admin.cli.shared.datetime_helpers import (
    _format_utc_iso,
    _resolve_single_update,
    _resolve_with_all_inputs,
    get_local_timezone_name,
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_datetime_input,
    resolve_update_times,
    validate_end_after_start,
    validate_no_input_conflict,
)
from tests.fixtures.constants import (
    TEST_ERROR_PERMISSION_DENIED,
)

# ---------------------------------------------------------------------------
# get_local_timezone_name (moved from test_scheduled_create.py)
# ---------------------------------------------------------------------------


def test_timezone_name_tzlocal_with_key() -> None:
    """Test get_local_timezone_name with tzlocal library (has .key attribute)."""
    mock_tz = MagicMock()
    mock_tz.key = "America/New_York"
    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.return_value = mock_tz

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = get_local_timezone_name()
        assert result == "America/New_York"


def test_timezone_name_tzlocal_without_key() -> None:
    """Test get_local_timezone_name with tzlocal library (no .key attribute)."""

    class MockTZ:
        """Mock timezone object without .key attribute."""

        def __str__(self: MockTZ) -> str:
            return "America/Chicago"

    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.return_value = MockTZ()

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = get_local_timezone_name()
        assert result == "America/Chicago"


def test_timezone_name_etc_localtime_symlink() -> None:
    """Test get_local_timezone_name reading /etc/localtime symlink."""
    mock_path = MagicMock()
    mock_path.is_symlink.return_value = True
    mock_path.readlink.return_value = "/usr/share/zoneinfo/America/Los_Angeles"

    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("gamesheet_sdk.common.cli.datetime_helpers.Path", return_value=mock_path),
    ):
        result = get_local_timezone_name()
        assert result == "America/Los_Angeles"


def test_timezone_name_fallback_utc_import_error() -> None:
    """Test get_local_timezone_name falls back to UTC when tzlocal import fails."""
    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "nt"),
    ):
        result = get_local_timezone_name()
        assert result == "UTC"


def test_timezone_name_fallback_utc_oserror() -> None:
    """Test get_local_timezone_name falls back to UTC on OSError."""
    mock_tzlocal = MagicMock()
    mock_tzlocal.get_localzone.side_effect = OSError(TEST_ERROR_PERMISSION_DENIED)

    with patch.dict(sys.modules, {"tzlocal": mock_tzlocal}):
        result = get_local_timezone_name()
        assert result == "UTC"


def test_timezone_name_etc_localtime_not_symlink() -> None:
    """Test get_local_timezone_name when /etc/localtime is not a symlink."""
    mock_path = MagicMock()
    mock_path.is_symlink.return_value = False

    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("gamesheet_sdk.common.cli.datetime_helpers.Path", return_value=mock_path),
    ):
        result = get_local_timezone_name()
        assert result == "UTC"


def test_timezone_name_etc_localtime_no_zoneinfo() -> None:
    """Test get_local_timezone_name when symlink doesn't contain zoneinfo."""
    mock_path = MagicMock()
    mock_path.is_symlink.return_value = True

    with (
        patch.dict(sys.modules, {"tzlocal": None}),
        patch("os.name", "posix"),
        patch("gamesheet_sdk.common.cli.datetime_helpers.Path", return_value=mock_path),
        patch("os.readlink", return_value="/some/other/path"),
    ):
        result = get_local_timezone_name()
        assert result == "UTC"


# ---------------------------------------------------------------------------
# get_local_timezone_offset (moved from test_scheduled_create.py)
# ---------------------------------------------------------------------------


def test_timezone_offset_standard_time() -> None:
    """Test get_local_timezone_offset during standard time."""
    with (
        patch("time.daylight", 0),
        patch("time.timezone", 18000),
    ):
        result = get_local_timezone_offset()
        assert result == -300


def test_timezone_offset_daylight_saving_time() -> None:
    """Test get_local_timezone_offset during daylight saving time."""
    mock_localtime = MagicMock()
    mock_localtime.tm_isdst = 1

    with (
        patch("time.daylight", 1),
        patch("time.localtime", return_value=mock_localtime),
        patch("time.altzone", 14400),
    ):
        result = get_local_timezone_offset()
        assert result == -240


# ---------------------------------------------------------------------------
# parse_flexible_datetime
# ---------------------------------------------------------------------------


def test_parse_iso8601_with_timezone() -> None:
    """Test parsing ISO 8601 with explicit timezone strips tz, keeps face value."""
    result = parse_flexible_datetime("2026-07-04T19:00:00-04:00")
    assert result == datetime(2026, 7, 4, 19, 0, 0)
    assert result.tzinfo is None


def test_parse_iso8601_utc() -> None:
    """Test parsing ISO 8601 with Z strips tz, keeps face value."""
    result = parse_flexible_datetime("2026-07-04T19:00:00Z")
    assert result == datetime(2026, 7, 4, 19, 0, 0)
    assert result.tzinfo is None


def test_parse_date_and_time_no_timezone() -> None:
    """Test parsing date+time without timezone keeps face value."""
    result = parse_flexible_datetime("2026-07-04 19:00")
    assert result == datetime(2026, 7, 4, 19, 0, 0)
    assert result.tzinfo is None


def test_parse_natural_format() -> None:
    """Test parsing natural language date format keeps face value."""
    result = parse_flexible_datetime("July 4 2026 7:00pm")
    assert result == datetime(2026, 7, 4, 19, 0, 0)
    assert result.tzinfo is None


def test_parse_strips_explicit_timezone() -> None:
    """Test that explicit timezone offset is stripped, keeping face-value time."""
    result = parse_flexible_datetime("2026-07-04T19:00:00+05:30")
    assert result == datetime(2026, 7, 4, 19, 0, 0)
    assert result.tzinfo is None


def test_parse_invalid_string_raises() -> None:
    """Test that unparsable strings raise UsageError."""
    with pytest.raises(click.UsageError, match="Cannot parse datetime"):
        parse_flexible_datetime("not-a-date")


def test_parse_empty_string_raises() -> None:
    """Test that empty strings raise UsageError."""
    with pytest.raises(click.UsageError, match="Cannot parse datetime"):
        parse_flexible_datetime("")


def test_parse_date_only_assumes_midnight() -> None:
    """Test parsing date-only string assumes midnight."""
    result = parse_flexible_datetime("2026-07-04")
    assert result == datetime(2026, 7, 4, 0, 0, 0)
    assert result.tzinfo is None


# ---------------------------------------------------------------------------
# _format_utc_iso
# ---------------------------------------------------------------------------


def test_format_utc_iso_trailing_z() -> None:
    """Test output format has trailing Z."""
    dt = datetime(2026, 7, 4, 23, 0, 0)
    assert _format_utc_iso(dt) == "2026-07-04T23:00:00Z"


def test_format_utc_iso_no_microseconds() -> None:
    """Test output format strips microseconds."""
    dt = datetime(2026, 7, 4, 23, 0, 0, 123456)
    assert _format_utc_iso(dt) == "2026-07-04T23:00:00Z"


# ---------------------------------------------------------------------------
# validate_no_input_conflict
# ---------------------------------------------------------------------------


def test_conflict_combined_with_date() -> None:
    """Test error when combined and date_part both provided."""
    with pytest.raises(click.UsageError, match="Cannot combine"):
        validate_no_input_conflict("2026-07-04T19:00", "2026-07-04", None, "start")


def test_conflict_combined_with_time() -> None:
    """Test error when combined and time_part both provided."""
    with pytest.raises(click.UsageError, match="Cannot combine"):
        validate_no_input_conflict("2026-07-04T19:00", None, "19:00", "end")


def test_no_conflict_combined_only() -> None:
    """Test no error when only combined is provided."""
    validate_no_input_conflict("2026-07-04T19:00", None, None, "start")


def test_no_conflict_split_only() -> None:
    """Test no error when only split parts are provided."""
    validate_no_input_conflict(None, "2026-07-04", "19:00", "start")


def test_no_conflict_none() -> None:
    """Test no error when nothing is provided."""
    validate_no_input_conflict(None, None, None, "start")


# ---------------------------------------------------------------------------
# resolve_datetime_input
# ---------------------------------------------------------------------------


def test_resolve_returns_combined_when_provided() -> None:
    """Test combined value is returned directly."""
    result = resolve_datetime_input("2026-07-04T19:00", None, None, "start")
    assert result == "2026-07-04T19:00"


def test_resolve_merges_date_and_time() -> None:
    """Test date + time parts are merged."""
    result = resolve_datetime_input(None, "2026-07-04", "19:00", "start")
    assert result == "2026-07-04 19:00"


def test_resolve_returns_none_when_nothing() -> None:
    """Test None returned when nothing provided."""
    result = resolve_datetime_input(None, None, None, "start")
    assert result is None


def test_resolve_raises_if_only_date() -> None:
    """Test error when only date provided without time."""
    with pytest.raises(click.UsageError, match="Both --start-date and --start-time"):
        resolve_datetime_input(None, "2026-07-04", None, "start")


def test_resolve_raises_if_only_time() -> None:
    """Test error when only time provided without date."""
    with pytest.raises(click.UsageError, match="Both --end-date and --end-time"):
        resolve_datetime_input(None, None, "19:00", "end")


# ---------------------------------------------------------------------------
# validate_end_after_start
# ---------------------------------------------------------------------------


def test_valid_end_after_start() -> None:
    """Test no error when end is after start."""
    start = datetime(2026, 7, 4, 19, 0)
    end = datetime(2026, 7, 4, 21, 0)
    validate_end_after_start(start, end)


def test_end_equals_start_raises() -> None:
    """Test error when end equals start."""
    dt = datetime(2026, 7, 4, 19, 0)
    with pytest.raises(click.UsageError, match="must be after"):
        validate_end_after_start(dt, dt)


def test_end_before_start_raises() -> None:
    """Test error when end is before start."""
    start = datetime(2026, 7, 4, 21, 0)
    end = datetime(2026, 7, 4, 19, 0)
    with pytest.raises(click.UsageError, match="must be after"):
        validate_end_after_start(start, end)


# ---------------------------------------------------------------------------
# resolve_create_times
# ---------------------------------------------------------------------------


def test_create_start_and_end_given() -> None:
    """Test resolving with start + end (timezone stripped, face values kept)."""
    start, end = resolve_create_times(
        "2026-07-04T19:00:00-04:00",
        "2026-07-04T21:00:00-04:00",
        None,
    )
    assert start == "2026-07-04T19:00:00Z"
    assert end == "2026-07-04T21:00:00Z"


def test_create_start_and_duration_given() -> None:
    """Test resolving with start + duration computes end."""
    start, end = resolve_create_times(
        "2026-07-04T23:00:00Z",
        None,
        120,
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_create_end_and_duration_given() -> None:
    """Test resolving with end + duration computes start."""
    start, end = resolve_create_times(
        None,
        "2026-07-05T01:00:00Z",
        120,
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_create_all_three_consistent() -> None:
    """Test all 3 given and consistent passes."""
    start, end = resolve_create_times(
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
        120,
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_create_all_three_inconsistent() -> None:
    """Test all 3 given but inconsistent raises error."""
    with pytest.raises(click.UsageError, match="Inconsistent inputs"):
        resolve_create_times(
            "2026-07-04T23:00:00Z",
            "2026-07-05T01:00:00Z",
            60,
        )


def test_create_fewer_than_two_raises() -> None:
    """Test only 1 given raises error."""
    with pytest.raises(click.UsageError, match="At least 2"):
        resolve_create_times("2026-07-04T23:00:00Z", None, None)


def test_create_none_given_raises() -> None:
    """Test 0 given raises error."""
    with pytest.raises(click.UsageError, match="At least 2"):
        resolve_create_times(None, None, None)


def test_create_end_before_start_raises() -> None:
    """Test end before start raises error."""
    with pytest.raises(click.UsageError, match="must be after"):
        resolve_create_times(
            "2026-07-05T01:00:00Z",
            "2026-07-04T23:00:00Z",
            None,
        )


def test_create_output_format_is_utc_iso() -> None:
    """Test output strings end with Z (UTC ISO 8601)."""
    start, end = resolve_create_times(
        "2026-07-04T19:00:00-04:00",
        "2026-07-04T21:00:00-04:00",
        None,
    )
    assert start.endswith("Z")
    assert end.endswith("Z")


def test_create_duration_60_minutes() -> None:
    """Test 1-hour game calculated correctly."""
    start, end = resolve_create_times(
        "2026-07-04T23:00:00Z",
        None,
        60,
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T00:00:00Z"


# ---------------------------------------------------------------------------
# resolve_update_times
# ---------------------------------------------------------------------------


def test_update_no_changes_returns_current() -> None:
    """Test no changes returns current values."""
    start, end = resolve_update_times(
        None,
        None,
        None,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_update_only_start_changed() -> None:
    """Test only start updated, end kept."""
    start, end = resolve_update_times(
        "2026-07-04T22:00:00Z",
        None,
        None,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T22:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_update_only_end_changed() -> None:
    """Test only end updated, start kept."""
    start, end = resolve_update_times(
        None,
        "2026-07-05T02:00:00Z",
        None,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T02:00:00Z"


def test_update_only_duration_recomputes_end() -> None:
    """Test only duration recomputes end from current start."""
    start, end = resolve_update_times(
        None,
        None,
        90,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T00:30:00Z"


def test_update_start_and_end_given() -> None:
    """Test both new start and end resolves normally."""
    start, end = resolve_update_times(
        "2026-07-04T22:00:00Z",
        "2026-07-05T00:00:00Z",
        None,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T22:00:00Z"
    assert end == "2026-07-05T00:00:00Z"


def test_update_start_and_duration_given() -> None:
    """Test new start + duration computes new end."""
    start, end = resolve_update_times(
        "2026-07-04T22:00:00Z",
        None,
        60,
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
    )
    assert start == "2026-07-04T22:00:00Z"
    assert end == "2026-07-04T23:00:00Z"


def test_update_new_start_after_current_end_raises() -> None:
    """Test error when new start is after current end."""
    with pytest.raises(click.UsageError, match="must be after"):
        resolve_update_times(
            "2026-07-05T02:00:00Z",
            None,
            None,
            "2026-07-04T23:00:00Z",
            "2026-07-05T01:00:00Z",
        )


def test_update_all_three_consistent() -> None:
    """Test all 3 given and consistent passes."""
    start, end = resolve_update_times(
        "2026-07-04T23:00:00Z",
        "2026-07-05T01:00:00Z",
        120,
        "2026-07-04T20:00:00Z",
        "2026-07-04T22:00:00Z",
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_update_end_and_duration_given() -> None:
    """Test new end + duration computes new start."""
    start, end = resolve_update_times(
        None,
        "2026-07-05T01:00:00Z",
        120,
        "2026-07-04T20:00:00Z",
        "2026-07-04T22:00:00Z",
    )
    assert start == "2026-07-04T23:00:00Z"
    assert end == "2026-07-05T01:00:00Z"


def test_resolve_with_all_inputs_insufficient_inputs_raises() -> None:
    """Test error when _resolve_with_all_inputs receives fewer than 2 inputs."""
    with pytest.raises(click.UsageError, match="At least 2 of"):
        _resolve_with_all_inputs(None, None, None)


def test_resolve_single_update_missing_duration_raises() -> None:
    """Test error when _resolve_single_update receives no inputs and duration=None."""
    with pytest.raises(click.UsageError, match="Duration is required"):
        _resolve_single_update(None, None, None, "2026-07-04T20:00:00Z", "2026-07-04T22:00:00Z")
