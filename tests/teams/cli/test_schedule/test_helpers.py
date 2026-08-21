# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for schedule CLI datetime helpers."""

from __future__ import annotations

import pytest
import rich_click as click

from gamesheet_sdk.teams.cli.commands.schedule.helpers import (
    _extract_date_prefix,
    resolve_game_update_times,
    resolve_occurrence_update_times,
    resolve_schedule_create_times,
)


def test_extract_date_prefix_none_and_valid() -> None:
    """Test _extract_date_prefix with None, ISO strings, and fallback parsing."""
    assert _extract_date_prefix(None) is None
    assert _extract_date_prefix("") is None
    assert _extract_date_prefix("2026-08-20T15:00:00Z") == "2026-08-20"
    assert _extract_date_prefix("2026-08-20 15:00") == "2026-08-20"


def test_extract_date_prefix_fallbacks() -> None:
    """Test fallback splitting when parse_flexible_datetime fails."""
    assert _extract_date_prefix("bad-dateTinvalid-time") == "bad-date"
    assert _extract_date_prefix("bad-date invalid-time") == "bad-date"
    assert _extract_date_prefix("completelyinvalid") is None


def test_resolve_schedule_create_times_all_day() -> None:
    """Test resolve_schedule_create_times with all_day=True."""
    # Conflict with start_date_time
    with pytest.raises(click.UsageError, match="Cannot combine --all-day with --start-datetime"):
        resolve_schedule_create_times(
            start_date_time="2026-08-20T10:00",
            start_date=None,
            start_time=None,
            end_date_time=None,
            end_date=None,
            end_time=None,
            duration=None,
            all_day=True,
        )

    # Missing date for events
    with pytest.raises(click.UsageError, match="--date/--start-date is required for all-day events"):
        resolve_schedule_create_times(
            start_date_time=None,
            start_date=None,
            start_time=None,
            end_date_time=None,
            end_date=None,
            end_time=None,
            duration=None,
            all_day=True,
            is_practice=False,
        )

    # Missing date for practices
    with pytest.raises(click.UsageError, match="--date/--start-date is required for all-day practices"):
        resolve_schedule_create_times(
            start_date_time=None,
            start_date=None,
            start_time=None,
            end_date_time=None,
            end_date=None,
            end_time=None,
            duration=None,
            all_day=True,
            is_practice=True,
        )

    # Success with start_date
    res_start, res_end = resolve_schedule_create_times(
        start_date_time=None,
        start_date="2026-08-20",
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration=None,
        all_day=True,
    )
    assert res_start == "2026-08-20"
    assert not res_end


def test_resolve_schedule_create_times_branches() -> None:
    """Test start and end branches in resolve_schedule_create_times."""
    # start_date_time branch
    st, et = resolve_schedule_create_times(
        start_date_time="2026-08-20T10:00",
        start_date=None,
        start_time=None,
        end_date_time="2026-08-20T11:30",
        end_date=None,
        end_time=None,
        duration=None,
    )
    assert st == "2026-08-20T10:00"
    assert et == "11:30"

    # start_date and start_time branch + duration
    st, et = resolve_schedule_create_times(
        start_date_time=None,
        start_date="2026-08-20",
        start_time="10:00",
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration="60",
    )
    assert st == "2026-08-20T10:00"
    assert et == "11:00"

    # start_time with space/T + end_date and end_time
    st, et = resolve_schedule_create_times(
        start_date_time=None,
        start_date=None,
        start_time="2026-08-20 14:00",
        end_date_time=None,
        end_date="2026-08-20",
        end_time="15:30",
        duration=None,
    )
    assert st == "2026-08-20T14:00"
    assert et == "15:30"

    # start_date only + end_time only (using date_prefix)
    st, et = resolve_schedule_create_times(
        start_date_time=None,
        start_date="2026-08-20 09:00",
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="10:00",
        duration=None,
    )
    assert st == "2026-08-20T09:00"
    assert et == "10:00"

    # start_time only + end_date only
    st, et = resolve_schedule_create_times(
        start_date_time=None,
        start_date=None,
        start_time="2026-08-20T08:00",
        end_date_time=None,
        end_date="2026-08-20T09:30",
        end_time=None,
        duration=None,
    )
    assert st == "2026-08-20T08:00"
    assert et == "09:30"

    # start_time only with no space/T
    st, et = resolve_schedule_create_times(
        start_date_time=None,
        start_date=None,
        start_time="10:00",
        end_date_time=None,
        end_date=None,
        end_time="11:00",
        duration=None,
    )
    assert st is not None
    assert et == "11:00"

    # end_time with space/T
    st, et = resolve_schedule_create_times(
        start_date_time="2026-08-20T18:00",
        start_date=None,
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="2026-08-20 19:30",
        duration=None,
    )
    assert st == "2026-08-20T18:00"
    assert et == "19:30"


def test_resolve_occurrence_update_times_branches() -> None:
    """Test all branches of resolve_occurrence_update_times."""
    # No inputs
    assert resolve_occurrence_update_times(
        start_date_time=None,
        start_date=None,
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    ) == (None, None)

    # start_date_time + end_date_time
    st, et = resolve_occurrence_update_times(
        start_date_time="2026-08-21T10:00:00Z",
        start_date=None,
        start_time=None,
        end_date_time="2026-08-21T12:00:00Z",
        end_date=None,
        end_time=None,
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-21T10:00:00Z"
    assert et == "2026-08-21T12:00:00Z"

    # start_date + start_time + duration
    st, et = resolve_occurrence_update_times(
        start_date_time=None,
        start_date="2026-08-21",
        start_time="10:00",
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration="90",
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-21T10:00:00Z"
    assert et == "2026-08-21T11:30:00Z"

    # start_time only with current_start date prefix + end_date and end_time
    st, et = resolve_occurrence_update_times(
        start_date_time=None,
        start_date=None,
        start_time="12:00",
        end_date_time=None,
        end_date="2026-08-20",
        end_time="13:30",
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-20T12:00:00Z"
    assert et == "2026-08-20T13:30:00Z"

    # start_date only + end_time only
    st, et = resolve_occurrence_update_times(
        start_date_time=None,
        start_date="2026-08-22",
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="15:00",
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-22T00:00:00Z"
    assert et == "2026-08-22T15:00:00Z"

    # start_time with space/T + end_date only
    st, et = resolve_occurrence_update_times(
        start_date_time=None,
        start_date=None,
        start_time="2026-08-23 10:00",
        end_date_time=None,
        end_date="2026-08-23 11:30",
        end_time=None,
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-23T10:00:00Z"
    assert et == "2026-08-23T11:30:00Z"

    # end_time with space/T
    st, et = resolve_occurrence_update_times(
        start_date_time="2026-08-24T10:00:00Z",
        start_date=None,
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="2026-08-24 11:45",
        duration=None,
        current_start="2026-08-20T10:00:00Z",
        current_end="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-24T10:00:00Z"
    assert et == "2026-08-24T11:45:00Z"

    # start_time without current_start date prefix fallback
    st, et = resolve_occurrence_update_times(
        start_date_time=None,
        start_date=None,
        start_time="14:00",
        end_date_time=None,
        end_date=None,
        end_time="15:00",
        duration=None,
        current_start="",
        current_end="",
    )
    # Both start_raw and end_raw are time-only strings without date prefix
    assert st is not None
    assert et is not None


def test_resolve_game_update_times_branches() -> None:
    """Test all branches of resolve_game_update_times."""
    # No inputs
    assert resolve_game_update_times(
        start_date_time=None,
        start_date=None,
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration=None,
        current_date_time="2026-08-20T10:00",
        current_end_time="11:00",
    ) == (None, None)

    # raw_start with no T and raw_end with no T
    st, et = resolve_game_update_times(
        start_date_time="2026-08-21T10:00",
        start_date=None,
        start_time=None,
        end_date_time="2026-08-21T12:00",
        end_date=None,
        end_time=None,
        duration=None,
        current_date_time="2026-08-20",
        current_end_time="11:00",
    )
    assert st == "2026-08-21T10:00"
    assert et == "12:00"

    # raw_start len != 16 and not ending with Z (e.g. 2026-08-20T10:00:00)
    st, et = resolve_game_update_times(
        start_date_time=None,
        start_date="2026-08-22",
        start_time="10:00",
        end_date_time=None,
        end_date=None,
        end_time=None,
        duration=60,
        current_date_time="2026-08-20T10:00:00",
        current_end_time="2026-08-20T11:00:00Z",
    )
    assert st == "2026-08-22T10:00"
    assert et == "11:00"

    # raw_start already ending with Z and raw_end ending without Z
    st, et = resolve_game_update_times(
        start_date_time=None,
        start_date=None,
        start_time="2026-08-23 14:00",
        end_date_time=None,
        end_date="2026-08-23",
        end_time="15:30",
        duration=None,
        current_date_time="2026-08-20T10:00:00Z",
        current_end_time="2026-08-20T11:00",
    )
    assert st == "2026-08-23T14:00"
    assert et == "15:30"

    # raw_start empty and raw_end empty
    st, et = resolve_game_update_times(
        start_date_time=None,
        start_date="2026-08-24",
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="16:00",
        duration=None,
        current_date_time=None,
        current_end_time=None,
    )
    assert st is not None
    assert et == "16:00"

    # start_time only with raw_start date_prefix + end_date only
    st, et = resolve_game_update_times(
        start_date_time=None,
        start_date=None,
        start_time="18:00",
        end_date_time=None,
        end_date="2026-08-25 19:30",
        end_time=None,
        duration=None,
        current_date_time="2026-08-25T10:00",
        current_end_time="11:00",
    )
    assert st == "2026-08-25T18:00"
    assert et == "19:30"

    # end_time with space/T
    st, et = resolve_game_update_times(
        start_date_time="2026-08-26T10:00",
        start_date=None,
        start_time=None,
        end_date_time=None,
        end_date=None,
        end_time="2026-08-26 11:30",
        duration=None,
        current_date_time="2026-08-26T10:00",
        current_end_time="11:00",
    )
    assert st == "2026-08-26T10:00"
    assert et == "11:30"
