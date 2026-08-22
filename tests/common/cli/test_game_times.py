# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the start/end/duration helpers shared by both game command trees."""

from __future__ import annotations

import pytest
import rich_click as click

from gamesheet_sdk.common.cli.game_times import (
    build_raw_end,
    build_raw_start,
    extract_date_prefix,
    is_bare_time,
    parse_duration_minutes,
    resolve_game_window,
    resolve_game_window_update,
    resolve_time_zone,
    validate_game_time_inputs,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        (75, 75),
        ("75", 75),
        ("  90  ", 90),
        ("", None),
        ("   ", None),
        ("90m", 90),
        ("90 min", 90),
        ("90 minutes", 90),
        ("1h", 60),
        ("1hr", 60),
        ("1 hour", 60),
        ("1h15m", 75),
        ("1h 15m", 75),
        ("1.5h", 90),
        ("1:15", 75),
        ("0:45", 45),
        ("2H30M", 150),
    ],
)
def test_parse_duration_minutes_accepts_both_spellings(raw: str | int | None, expected: int | None) -> None:
    """Both the admin integer-minutes form and the teams suffixed form parse to the same minutes."""
    assert parse_duration_minutes(raw) == expected


@pytest.mark.parametrize("raw", ["abc", "1h15x", "--", "1:99"])
def test_parse_duration_minutes_rejects_garbage(raw: str) -> None:
    """Unparsable durations raise a usage error rather than silently becoming zero."""
    with pytest.raises(click.UsageError, match="Cannot parse duration"):
        parse_duration_minutes(raw)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        ("12", True),
        ("12:00", True),
        ("12:00:30", True),
        ("7pm", True),
        ("7:00 PM", True),
        ("7 p.m.", True),
        ("2026-08-20", False),
        ("2026-08-20 12:00", False),
        ("2026-08-20T12:00", False),
    ],
)
def test_is_bare_time(value: str | None, expected: bool) -> None:
    """A bare time of day is distinguished from anything carrying a date."""
    assert is_bare_time(value) is expected


def test_extract_date_prefix_parses_and_falls_back() -> None:
    """The date prefix comes from a real parse when possible and a split otherwise."""
    assert extract_date_prefix(None) is None
    assert extract_date_prefix("") is None
    assert extract_date_prefix("2026-08-20T15:00:00Z") == "2026-08-20"
    assert extract_date_prefix("bad-dateTinvalid") == "bad-date"
    assert extract_date_prefix("bad-date invalid") == "bad-date"
    assert extract_date_prefix("completelyinvalid") is None


def test_build_raw_start_and_end_merge_parts() -> None:
    """Split date/time parts merge, and a bare end time inherits the start date."""
    assert build_raw_start(None, None, None) is None
    assert build_raw_start("2026-08-20 12:00", None, None) == "2026-08-20 12:00"
    assert build_raw_start(None, "2026-08-20", "12:00") == "2026-08-20 12:00"
    assert build_raw_start(None, "2026-08-20", None) == "2026-08-20"
    assert build_raw_start(None, None, "12:00") == "12:00"
    assert build_raw_start(None, None, "12:00", "2026-08-20") == "2026-08-20 12:00"
    assert build_raw_start(None, None, "2026-08-20 12:00") == "2026-08-20 12:00"
    assert build_raw_end(None, None, "13:15", "2026-08-20") == "2026-08-20 13:15"
    assert build_raw_end(None, "2026-08-21", "13:15", "2026-08-20") == "2026-08-21 13:15"


def test_bare_time_in_the_flexible_slot_is_treated_as_a_time() -> None:
    """``--date X --start 12:00`` keeps working now that ``--start`` aliases ``--start-datetime``."""
    validate_game_time_inputs("12:00", "2026-08-20", None, "13:15", None, None)
    start, end = resolve_game_window("12:00", "2026-08-20", None, "13:15", None, None, None)
    assert start == "2026-08-20T12:00:00Z"
    assert end == "2026-08-20T13:15:00Z"


def test_two_times_for_the_same_end_is_a_usage_error() -> None:
    """A bare ``--start`` still conflicts with ``--start-time``; both name the time of day."""
    with pytest.raises(click.UsageError, match="Cannot combine --start with --start-time"):
        validate_game_time_inputs("12:00", None, "13:00", None, None, None)

    with pytest.raises(click.UsageError, match="Cannot combine --end with --end-time"):
        validate_game_time_inputs(None, None, None, "12:00", None, "13:00")


def test_datetime_with_split_parts_is_a_usage_error() -> None:
    """A combined value that carries a date still conflicts with the split spellings."""
    with pytest.raises(click.UsageError, match="Cannot combine --start-datetime"):
        validate_game_time_inputs("2026-08-20 12:00", "2026-08-20", None, None, None, None)


def test_resolve_game_window_calculates_the_missing_value() -> None:
    """Any two of start, end, and duration determine the third."""
    start, end = resolve_game_window("2026-08-20 12:00", None, None, None, None, None, "1h15m")
    assert (start, end) == ("2026-08-20T12:00:00Z", "2026-08-20T13:15:00Z")

    start, end = resolve_game_window(None, None, None, "2026-08-20 13:15", None, None, 75)
    assert (start, end) == ("2026-08-20T12:00:00Z", "2026-08-20T13:15:00Z")


def test_resolve_game_window_update_leaves_an_untouched_window_alone() -> None:
    """An update naming no time option reports ``(None, None)`` so the caller keeps the current window."""
    assert resolve_game_window_update(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "2026-08-20T12:00:00Z",
        "2026-08-20T13:15:00Z",
    ) == (None, None)


def test_resolve_game_window_update_applies_a_partial_change() -> None:
    """A lone new start moves the start and preserves the end."""
    start, end = resolve_game_window_update(
        None,
        None,
        "11:00",
        None,
        None,
        None,
        None,
        "2026-08-20T12:00:00Z",
        "2026-08-20T13:15:00Z",
    )
    assert start == "2026-08-20T11:00:00Z"
    assert end == "2026-08-20T13:15:00Z"


def test_resolve_time_zone_falls_back_to_the_system() -> None:
    """An explicit name or offset wins; anything missing comes from the system."""
    name, offset = resolve_time_zone("America/Denver", -360)
    assert (name, offset) == ("America/Denver", -360)

    name, offset = resolve_time_zone("America/Denver", None)
    assert name == "America/Denver"
    assert isinstance(offset, int)

    name, offset = resolve_time_zone(None, None)
    assert isinstance(name, str)
    assert isinstance(offset, int)
