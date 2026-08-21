# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Datetime parsing and resolution helpers for CLI commands."""

from __future__ import annotations

import datetime
import logging
import os
import time
from pathlib import Path

import rich_click as click
from dateutil import parser as dateutil_parser

from gamesheet_sdk.common.constants import DEFAULT_TIMEZONE

_LOGGER = logging.getLogger(__name__)

MIN_REQUIRED_INPUTS = 2


def _detect_timezone() -> str | None:
    """Attempt to detect the local timezone name from tzlocal or /etc/localtime.

    Returns:
        str | None: The detected timezone name if found, else None.

    """
    try:
        import tzlocal  # noqa: PLC0415

        tz = tzlocal.get_localzone()
    except (ImportError, AttributeError):
        pass
    else:
        return str(tz.key) if hasattr(tz, "key") else str(tz)

    if os.name != "nt":
        localtime = Path("/etc/localtime")
        if localtime.is_symlink():
            target = str(localtime.readlink())
            if "zoneinfo/" in target:
                return target.split("zoneinfo/", 1)[1]

    return None


def get_local_timezone_name() -> str:
    """Get the local system timezone name (IANA format).

    Returns the timezone name like 'America/New_York', 'UTC', etc. Falls back to 'UTC' if unable to determine.

    Returns:
        str: IANA timezone name

    """
    try:
        tz = _detect_timezone()
        if tz:
            return tz
    except (OSError, ValueError, IndexError) as exc:
        _LOGGER.debug(
            "Failed to detect timezone, falling back to %s: %s",
            DEFAULT_TIMEZONE,
            exc,
        )

    return DEFAULT_TIMEZONE


def get_local_timezone_offset() -> int:
    """Get the local timezone offset in minutes from UTC.

    Returns the offset as a signed integer (negative for west of UTC, positive for east). For example, EDT
    (UTC-4) returns -240.

    Returns:
        int: Timezone offset in minutes

    """
    offset_seconds = -time.altzone if time.daylight and time.localtime().tm_isdst else -time.timezone

    return offset_seconds // 60


def parse_flexible_datetime(raw: str) -> datetime.datetime:
    """Parse a flexible datetime string into a naive datetime.datetime preserving face values.

    Uses ``dateutil.parser.parse`` for flexible input. Any timezone information is stripped — the returned
    datetime.datetime contains the literal hour/minute/second the user typed. This matches GameSheet's API
    behavior, which stores and displays time values as-is without timezone conversion.

    Args:
        raw (str): A human-readable datetime string

    Returns:
        datetime.datetime: A timezone-naive datetime.datetime with the face-value time

    Raises:
        UsageError: If the string cannot be parsed

    """
    try:
        dt = dateutil_parser.parse(raw)
    except (ValueError, OverflowError) as exc:
        msg = f"Cannot parse datetime '{raw}': {exc}"
        raise click.UsageError(msg) from exc

    return dt.replace(tzinfo=None)


def _format_utc_iso(dt: datetime.datetime) -> str:
    """Format a datetime.datetime as ISO 8601 with trailing Z for the GameSheet API.

    The trailing ``Z`` is required by the API format but does **not** imply UTC — GameSheet displays the face-
    value time as-is.

    Args:
        dt (datetime.datetime): A datetime.datetime (typically naive, face-value)

    Returns:
        str: ISO 8601 string like ``2026-07-04T12:00:00Z``

    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_no_input_conflict(
    combined: str | None,
    date_part: str | None,
    time_part: str | None,
    label: str,
) -> None:
    """Raise if combined and split inputs are both provided.

    Args:
        combined (str | None): The ``--start-datetime`` or ``--end-datetime`` value
        date_part (str | None): The ``--start-date`` or ``--end-date`` value
        time_part (str | None): The ``--start-time`` or ``--end-time`` value
        label (str): ``"start"`` or ``"end"``, for error messages

    Raises:
        UsageError: If combined and any split input coexist

    """
    if combined and (date_part or time_part):
        msg = f"Cannot combine --{label}-datetime with --{label}-date/--{label}-time."
        raise click.UsageError(msg)


def resolve_datetime_input(
    combined: str | None,
    date_part: str | None,
    time_part: str | None,
    label: str,
) -> str | None:
    """Merge split date+time inputs into one string, or return combined.

    Args:
        combined (str | None): The ``--start-datetime`` or ``--end-datetime`` value
        date_part (str | None): The ``--start-date`` or ``--end-date`` value
        time_part (str | None): The ``--start-time`` or ``--end-time`` value
        label (str): ``"start"`` or ``"end"``, for error messages

    Returns:
        str | None: A merged datetime string or None

    Raises:
        UsageError: If only one of date/time is provided

    """
    if combined:
        return combined

    if date_part and time_part:
        return f"{date_part} {time_part}"

    if date_part or time_part:
        msg = f"Both --{label}-date and --{label}-time are required when using split inputs."
        raise click.UsageError(msg)

    return None


def validate_end_after_start(start_dt: datetime.datetime, end_dt: datetime.datetime) -> None:
    """Raise if end is not strictly after start.

    Args:
        start_dt (datetime.datetime): Start datetime.datetime (UTC)
        end_dt (datetime.datetime): End datetime.datetime (UTC)

    Raises:
        UsageError: If end <= start

    """
    if end_dt <= start_dt:
        msg = f"End time ({end_dt.isoformat()}) must be after start time ({start_dt.isoformat()})."
        raise click.UsageError(msg)


def _resolve_all_three(
    start_raw: str,
    end_raw: str,
    duration: int,
) -> tuple[str, str]:
    """Validate consistency when all 3 are given.

    Args:
        start_raw (str): Raw start datetime string
        end_raw (str): Raw end datetime string
        duration (int): Duration in minutes

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    Raises:
        UsageError: If start + duration != end (within 59s tolerance)

    """
    start_dt = parse_flexible_datetime(start_raw)
    end_dt = parse_flexible_datetime(end_raw)
    validate_end_after_start(start_dt, end_dt)
    expected_end = start_dt + datetime.timedelta(minutes=duration)
    if abs(end_dt - expected_end) >= datetime.timedelta(minutes=1):
        msg = f"Inconsistent inputs: start ({start_raw}) + duration ({duration}min) != end ({end_raw})."
        raise click.UsageError(msg)

    return _format_utc_iso(start_dt), _format_utc_iso(end_dt)


def _resolve_start_and_end(
    start_raw: str,
    end_raw: str,
) -> tuple[str, str]:
    """Resolve from start + end.

    Args:
        start_raw (str): Raw start datetime string
        end_raw (str): Raw end datetime string

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    """
    start_dt = parse_flexible_datetime(start_raw)
    end_dt = parse_flexible_datetime(end_raw)
    validate_end_after_start(start_dt, end_dt)
    return _format_utc_iso(start_dt), _format_utc_iso(end_dt)


def _resolve_start_and_duration(
    start_raw: str,
    duration: int,
) -> tuple[str, str]:
    """Resolve from start + duration to compute end.

    Args:
        start_raw (str): Raw start datetime string
        duration (int): Duration in minutes

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    """
    start_dt = parse_flexible_datetime(start_raw)
    end_dt = start_dt + datetime.timedelta(minutes=duration)
    return _format_utc_iso(start_dt), _format_utc_iso(end_dt)


def _resolve_end_and_duration(
    end_raw: str,
    duration: int,
) -> tuple[str, str]:
    """Resolve from end + duration to compute start.

    Args:
        end_raw (str): Raw end datetime string
        duration (int): Duration in minutes

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    """
    end_dt = parse_flexible_datetime(end_raw)
    start_dt = end_dt - datetime.timedelta(minutes=duration)
    return _format_utc_iso(start_dt), _format_utc_iso(end_dt)


def _resolve_with_all_inputs(
    start_raw: str | None,
    end_raw: str | None,
    duration: int | None,
) -> tuple[str, str]:
    """Dispatch to the correct compute function based on which inputs are present.

    Args:
        start_raw (str | None): Raw start string or None
        end_raw (str | None): Raw end string or None
        duration (int | None): Duration in minutes or None

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    Raises:
        UsageError: If fewer than 2 of 3 inputs are provided.

    """
    if start_raw and end_raw and duration is not None:
        return _resolve_all_three(start_raw, end_raw, duration)

    if start_raw and end_raw:
        return _resolve_start_and_end(start_raw, end_raw)

    if start_raw is not None and duration is not None:
        return _resolve_start_and_duration(start_raw, duration)

    if end_raw is not None and duration is not None:
        return _resolve_end_and_duration(end_raw, duration)

    msg = "At least 2 of --start-datetime, --end-datetime, --duration are required."
    raise click.UsageError(msg)


def resolve_create_times(
    start_raw: str | None,
    end_raw: str | None,
    duration: int | None,
) -> tuple[str, str]:
    """Resolve start/end for create: exactly 2 of 3 required.

    Args:
        start_raw (str | None): Raw start datetime string, or None
        end_raw (str | None): Raw end datetime string, or None
        duration (int | None): Duration in minutes, or None

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    Raises:
        UsageError: If fewer than 2 of 3 are provided, or if all 3 are inconsistent, or end <= start

    """
    given = (start_raw is not None) + (end_raw is not None) + (duration is not None)
    if given < MIN_REQUIRED_INPUTS:
        msg = "At least 2 of --start-datetime, --end-datetime, --duration are required."
        raise click.UsageError(msg)

    return _resolve_with_all_inputs(start_raw, end_raw, duration)


def _resolve_single_update(
    start_raw: str | None,
    end_raw: str | None,
    duration: int | None,
    current_start: str,
    current_end: str,
) -> tuple[str, str]:
    """Handle update with exactly 1 new time input.

    Args:
        start_raw (str | None): New start string or None
        end_raw (str | None): New end string or None
        duration (int | None): Duration in minutes or None
        current_start (str): Current game start (ISO 8601)
        current_end (str): Current game end (ISO 8601)

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    Raises:
        UsageError: If duration is missing when neither start nor end is provided.

    """
    if start_raw:
        start_dt = parse_flexible_datetime(start_raw)
        end_dt = parse_flexible_datetime(current_end)
        validate_end_after_start(start_dt, end_dt)
        return _format_utc_iso(start_dt), current_end

    if end_raw:
        start_dt = parse_flexible_datetime(current_start)
        end_dt = parse_flexible_datetime(end_raw)
        validate_end_after_start(start_dt, end_dt)
        return current_start, _format_utc_iso(end_dt)

    if duration is None:
        msg = "Duration is required."
        raise click.UsageError(msg)

    start_dt = parse_flexible_datetime(current_start)
    end_dt = start_dt + datetime.timedelta(minutes=duration)
    return _format_utc_iso(start_dt), _format_utc_iso(end_dt)


def resolve_update_times(
    start_raw: str | None,
    end_raw: str | None,
    duration: int | None,
    current_start: str,
    current_end: str,
) -> tuple[str, str]:
    """Resolve start/end for update: partial inputs OK.

    Uses current game values as fallback when the user provides fewer than 2 inputs.

    Args:
        start_raw (str | None): New start datetime string, or None
        end_raw (str | None): New end datetime string, or None
        duration (int | None): Duration in minutes, or None
        current_start (str): Current game start time (ISO 8601)
        current_end (str): Current game end time (ISO 8601)

    Returns:
        tuple[str, str]: ``(start_utc_iso, end_utc_iso)`` tuple

    """
    given = (start_raw is not None) + (end_raw is not None) + (duration is not None)
    if not given:
        return current_start, current_end

    if given >= MIN_REQUIRED_INPUTS:
        return _resolve_with_all_inputs(start_raw, end_raw, duration)

    return _resolve_single_update(
        start_raw,
        end_raw,
        duration,
        current_start,
        current_end,
    )
