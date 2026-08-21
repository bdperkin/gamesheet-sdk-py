# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Start/end/duration resolution shared by the admin and teams game commands.

Both CLIs accept the same seven time options (``--start-datetime``/``--start-date-time``/``--start``,
``--end-datetime``/``--end-date-time``/``--end``, ``--start-date``/``--date``, ``--start-time``,
``--end-date``, ``--end-time``, ``--duration``) and resolve them identically here. Only the final wire format
differs: ``gamesheet-admin`` sends the ISO 8601 pair returned by these helpers verbatim, while
``gamesheet-teams`` reformats it into its ``YYYY-MM-DDTHH:MM`` + ``HH:MM`` pair.

A bare ``--end-time`` (no ``--end-date``) inherits the resolved start date, which is what makes
``--date 2026-07-04 --start-time 7pm --end-time 9pm`` mean the same thing on both CLIs.
"""

from __future__ import annotations

import re
from typing import Final

import rich_click as click
from click.exceptions import ClickException

from gamesheet_sdk.common.cli.datetime_helpers import (
    get_local_timezone_name,
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_update_times,
    validate_no_input_conflict,
)

MINUTES_PER_HOUR: Final[int] = 60

#: ``1h``, ``15m``, ``1h15m``, ``1.5h``, ``90 min`` — either part may be omitted, but not both.
_HM_DURATION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:(?P<hours>\d+(?:\.\d+)?)\s*h(?:ours?|rs?|r)?)?"
    r"\s*(?:(?P<minutes>\d+(?:\.\d+)?)\s*m(?:in(?:ute)?s?)?)?$",
    re.IGNORECASE,
)
#: ``1:15`` — hours and minutes separated by a colon.
_COLON_DURATION_RE: Final[re.Pattern[str]] = re.compile(r"^(?P<hours>\d+):(?P<minutes>[0-5]?\d)$")

#: ``12``, ``12:00``, ``12:00:30``, ``7pm``, ``7:00 PM`` — a time of day carrying no date.
_BARE_TIME_RE: Final[re.Pattern[str]] = re.compile(
    r"^\d{1,2}(?::\d{2}){0,2}\s*(?:[ap]\.?m\.?)?$",
    re.IGNORECASE,
)


def is_bare_time(value: str | None) -> bool:
    """Return whether a value is a time of day with no date attached.

    ``--start`` / ``--end`` are the flexible spellings and accept either form. Recognizing the bare-time case
    is what lets ``--date 2026-08-20 --start 12:00 --end 13:15`` keep working: the time-only value is folded
    into the split date/time slot instead of colliding with ``--date``.

    Args:
        value (str | None): The supplied value.

    Returns:
        bool: ``True`` when the value looks like a time of day and nothing else.

    """
    return bool(value) and _BARE_TIME_RE.match(str(value).strip()) is not None


def _split_bare_time(date_time: str | None, time: str | None) -> tuple[str | None, str | None]:
    """Reclassify a bare time given as ``--start``/``--end`` into the time slot.

    Args:
        date_time (str | None): The combined value.
        time (str | None): The split time value.

    Returns:
        tuple[str | None, str | None]: The ``(date_time, time)`` pair after reclassification.

    """
    if time is None and is_bare_time(date_time):
        return None, date_time

    return date_time, time


def _duration_from_match(match: re.Match[str]) -> int:
    """Convert a matched hours/minutes pair into whole minutes.

    Args:
        match (re.Match[str]): A match exposing ``hours`` and ``minutes`` groups.

    Returns:
        int: Total duration in minutes, rounded to the nearest minute.

    """
    hours = float(match.group("hours") or 0)
    minutes = float(match.group("minutes") or 0)
    return round(hours * MINUTES_PER_HOUR + minutes)


def _match_duration(text: str) -> re.Match[str] | None:
    """Match a suffixed or colon-separated duration, rejecting an all-empty match.

    Args:
        text (str): The stripped duration string.

    Returns:
        re.Match[str] | None: The match, or ``None`` when the value names no hours and no minutes.

    """
    match = _COLON_DURATION_RE.match(text) or _HM_DURATION_RE.match(text)
    if match is None or not (match.group("hours") or match.group("minutes")):
        return None

    return match


def _parse_duration_text(text: str) -> int:
    """Parse a non-empty duration string.

    Args:
        text (str): The stripped duration string.

    Returns:
        int: Duration in whole minutes.

    Raises:
        UsageError: If the value cannot be interpreted as a duration.

    """
    if text.lstrip("-").isdigit():
        return int(text)

    match = _match_duration(text)
    if match is None:
        msg = f"Cannot parse duration '{text}'. Use minutes ('75'), '1h15m', '90m', '1.5h', or '1:15'."
        raise click.UsageError(msg)

    return _duration_from_match(match)


def parse_duration_minutes(raw: str | int | None) -> int | None:
    """Parse a duration in any of the spellings both CLIs accept.

    ``gamesheet-admin`` historically took an integer count of minutes and ``gamesheet-teams`` a suffixed
    string; both spellings now work everywhere. A value that cannot be interpreted raises
    :class:`click.UsageError` from :func:`_parse_duration_text`.

    Args:
        raw (str | int | None): Duration as minutes (``75``), a suffixed string (``'1h15m'``, ``'90m'``,
            ``'1.5h'``), a ``H:MM`` string (``'1:15'``), or ``None``.

    Returns:
        int | None: Duration in whole minutes, or ``None`` when ``raw`` is ``None`` or blank.

    """
    if raw is None:
        return None

    if isinstance(raw, int):
        return raw

    text = raw.strip()
    if not text:
        return None

    return _parse_duration_text(text)


def _split_date_prefix(raw: str) -> str | None:
    """Recover a date prefix by splitting on the ISO ``T`` or a space.

    Args:
        raw (str): An unparsable datetime-ish string.

    Returns:
        str | None: The leading token, or ``None`` when there is no separator.

    """
    for separator in ("T", " "):
        if separator in raw:
            return raw.split(separator, maxsplit=1)[0]

    return None


def extract_date_prefix(raw: str | None) -> str | None:
    """Return the ``YYYY-MM-DD`` prefix of a datetime string, if one can be recovered.

    Args:
        raw (str | None): A datetime-ish string, or ``None``.

    Returns:
        str | None: The date portion, or ``None`` when it cannot be determined.

    """
    if not raw:
        return None

    try:
        return parse_flexible_datetime(raw).strftime("%Y-%m-%d")
    except (ValueError, TypeError, ClickException):
        return _split_date_prefix(raw)


def _time_with_fallback_date(time: str | None, fallback_date: str | None) -> str | None:
    """Pair a bare time with a fallback date when one is available.

    Args:
        time (str | None): Bare time component.
        fallback_date (str | None): Date to pair it with.

    Returns:
        str | None: The paired string, the bare time, or ``None``.

    """
    if not time:
        return None

    return f"{fallback_date} {time}" if fallback_date else time


def _merge_without_combined(
    date: str | None,
    time: str | None,
    fallback_date: str | None,
) -> str | None:
    """Combine the remaining parts once no combined value is in play.

    Args:
        date (str | None): Date part.
        time (str | None): Time part.
        fallback_date (str | None): Date to pair a bare time with.

    Returns:
        str | None: The merged string, or ``None`` if no part was supplied.

    """
    if time and (" " in time or "T" in time):
        return time

    if date:
        return date

    return _time_with_fallback_date(time, fallback_date)


def _merge_date_and_time(
    date_time: str | None,
    date: str | None,
    time: str | None,
    fallback_date: str | None,
) -> str | None:
    """Combine a date part and a time part into one datetime string.

    Args:
        date_time (str | None): Combined value, which wins outright when present.
        date (str | None): Date part.
        time (str | None): Time part.
        fallback_date (str | None): Date to pair a bare time with.

    Returns:
        str | None: The merged string, or ``None`` if no part was supplied.

    """
    date_time, time = _split_bare_time(date_time, time)
    if date_time:
        return date_time

    if date and time:
        return f"{date} {time}"

    return _merge_without_combined(date, time, fallback_date)


def build_raw_start(
    date_time: str | None,
    date: str | None,
    time: str | None,
    fallback_date: str | None = None,
) -> str | None:
    """Merge the three start spellings into a single parseable string.

    Args:
        date_time (str | None): Combined ``--start-datetime`` value.
        date (str | None): ``--start-date`` / ``--date`` value.
        time (str | None): ``--start-time`` value.
        fallback_date (str | None): Date to pair a bare time with (the game's current date, on update).

    Returns:
        str | None: A string for :func:`parse_flexible_datetime`, or ``None`` if nothing was supplied.

    """
    return _merge_date_and_time(date_time, date, time, fallback_date)


def build_raw_end(
    date_time: str | None,
    date: str | None,
    time: str | None,
    date_prefix: str | None,
) -> str | None:
    """Merge the three end spellings into a single parseable string.

    A bare ``--end-time`` is paired with ``date_prefix`` — normally the resolved start date — so an end time
    without an explicit end date lands on the same day as the start.

    Args:
        date_time (str | None): Combined ``--end-datetime`` value.
        date (str | None): ``--end-date`` value.
        time (str | None): ``--end-time`` value.
        date_prefix (str | None): Date to pair a bare time with.

    Returns:
        str | None: A string for :func:`parse_flexible_datetime`, or ``None`` if nothing was supplied.

    """
    return _merge_date_and_time(date_time, date, time, date_prefix)


def _validate_one_end(
    date_time: str | None,
    date: str | None,
    time: str | None,
    label: str,
) -> None:
    """Reject a conflicting combination for one end of the window.

    Args:
        date_time (str | None): Combined value.
        date (str | None): Date part.
        time (str | None): Time part.
        label (str): ``'start'`` or ``'end'``, for the error message.

    Raises:
        UsageError: If two times were given for the same end of the window.

    """
    if is_bare_time(date_time):
        if time:
            msg = f"Cannot combine --{label} with --{label}-time; both name the {label} time of day."
            raise click.UsageError(msg)

        return

    validate_no_input_conflict(date_time, date, time, label)


def validate_game_time_inputs(
    start_date_time: str | None,
    start_date: str | None,
    start_time: str | None,
    end_date_time: str | None,
    end_date: str | None,
    end_time: str | None,
) -> None:
    """Reject combining a ``--*-datetime`` option with its split counterparts.

    A combined value that is only a time of day is exempt, because ``--start`` / ``--end`` are the flexible
    spellings and ``--date 2026-08-20 --start 12:00`` has to keep meaning what it did before the two CLIs
    shared one option set. Two *times* for the same end of the window are still a conflict.

    Args:
        start_date_time (str | None): Combined start value.
        start_date (str | None): Start date part.
        start_time (str | None): Start time part.
        end_date_time (str | None): Combined end value.
        end_date (str | None): End date part.
        end_time (str | None): End time part.

    """
    _validate_one_end(start_date_time, start_date, start_time, "start")
    _validate_one_end(end_date_time, end_date, end_time, "end")


def resolve_game_window(
    start_date_time: str | None,
    start_date: str | None,
    start_time: str | None,
    end_date_time: str | None,
    end_date: str | None,
    end_time: str | None,
    duration: str | int | None,
) -> tuple[str, str]:
    """Resolve create-time inputs into an ISO 8601 start/end pair.

    Exactly two of start, end, and duration are required; the third is calculated. Supplying all three is
    allowed as long as they agree.

    Args:
        start_date_time (str | None): Combined start value.
        start_date (str | None): Start date part.
        start_time (str | None): Start time part.
        end_date_time (str | None): Combined end value.
        end_date (str | None): End date part.
        end_time (str | None): End time part.
        duration (str | int | None): Duration in any accepted spelling.

    Returns:
        tuple[str, str]: ``(start, end)`` as ``YYYY-MM-DDTHH:MM:SSZ`` strings.

    """
    validate_game_time_inputs(start_date_time, start_date, start_time, end_date_time, end_date, end_time)

    start_raw = build_raw_start(start_date_time, start_date, start_time)
    date_prefix = extract_date_prefix(start_raw) or start_date
    end_raw = build_raw_end(end_date_time, end_date, end_time, date_prefix)

    return resolve_create_times(start_raw, end_raw, parse_duration_minutes(duration))


def _end_date_prefix(start_raw: str | None, current_start: str, current_end: str) -> str | None:
    """Pick the date a bare end time should land on during an update.

    Args:
        start_raw (str | None): The resolved new start, if the update moves it.
        current_start (str): The game's current start, ISO 8601.
        current_end (str): The game's current end, ISO 8601.

    Returns:
        str | None: The best available date, preferring the new start over the current window.

    """
    return (
        extract_date_prefix(start_raw)
        or extract_date_prefix(current_end)
        or extract_date_prefix(current_start)
    )


def resolve_game_window_update(
    start_date_time: str | None,
    start_date: str | None,
    start_time: str | None,
    end_date_time: str | None,
    end_date: str | None,
    end_time: str | None,
    duration: str | int | None,
    current_start: str,
    current_end: str,
) -> tuple[str | None, str | None]:
    """Resolve update-time inputs against the game's current window.

    Partial input is allowed: one new value updates that field and preserves the other, two or more trigger a
    recalculation, and no time input at all leaves the window untouched.

    Args:
        start_date_time (str | None): Combined start value.
        start_date (str | None): Start date part.
        start_time (str | None): Start time part.
        end_date_time (str | None): Combined end value.
        end_date (str | None): End date part.
        end_time (str | None): End time part.
        duration (str | int | None): Duration in any accepted spelling.
        current_start (str): The game's current start, ISO 8601.
        current_end (str): The game's current end, ISO 8601.

    Returns:
        tuple[str | None, str | None]: The new ``(start, end)`` pair, or ``(None, None)`` when no time option
            was supplied.

    """
    validate_game_time_inputs(start_date_time, start_date, start_time, end_date_time, end_date, end_time)

    start_raw = build_raw_start(
        start_date_time,
        start_date,
        start_time,
        extract_date_prefix(current_start),
    )
    end_prefix = _end_date_prefix(start_raw, current_start, current_end)
    end_raw = build_raw_end(end_date_time, end_date, end_time, end_prefix)
    duration_minutes = parse_duration_minutes(duration)

    if not start_raw and not end_raw and duration_minutes is None:
        return None, None

    return resolve_update_times(start_raw, end_raw, duration_minutes, current_start, current_end)


def resolve_time_zone(name: str | None, offset: int | None) -> tuple[str, int]:
    """Fill in whichever of the time zone name and offset was not supplied.

    Both CLIs fall back to the system time zone, which is what ``create`` already did on either side. It is
    also what ``gamesheet-admin games update`` now does instead of assuming a hardcoded ``-240``.

    Args:
        name (str | None): ``--time-zone-name`` / ``--timezone``, or ``None``.
        offset (int | None): ``--time-zone-offset``, or ``None``.

    Returns:
        tuple[str, int]: The resolved ``(name, offset)`` pair.

    """
    resolved_name = name if name is not None else get_local_timezone_name()
    resolved_offset = offset if offset is not None else get_local_timezone_offset()
    return resolved_name, resolved_offset


__all__ = [
    "build_raw_end",
    "build_raw_start",
    "extract_date_prefix",
    "is_bare_time",
    "parse_duration_minutes",
    "resolve_game_window",
    "resolve_game_window_update",
    "resolve_time_zone",
    "validate_game_time_inputs",
]
