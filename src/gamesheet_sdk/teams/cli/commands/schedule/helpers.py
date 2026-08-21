# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Datetime resolution helpers for schedule CLI commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

import rich_click as click
from click.exceptions import ClickException, Exit

from gamesheet_sdk.common.cli.datetime_helpers import (
    get_local_timezone_offset,
    parse_flexible_datetime,
    resolve_create_times,
    resolve_update_times,
    validate_no_input_conflict,
)
from gamesheet_sdk.common.cli.rendering import render_get_command
from gamesheet_sdk.teams.schedule import (
    _fetch_and_normalize_game_dict,
    _fetch_and_verify_occurrence_dict,
    validate_game_type,
)
from gamesheet_sdk.teams.schedule import (
    build_rrule as _build_rrule_action,
)
from gamesheet_sdk.teams.schedule import (
    update_calendar_occurrence as _update_calendar_occurrence_action,
)
from gamesheet_sdk.teams.schedule import (
    update_game as _update_game_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.teams.schedule import CalendarEventCreated, UpdatedGameResult
    from gamesheet_sdk.teams.session import TeamsAuthenticatedSession

F = TypeVar("F", bound=Callable[..., object])

ISO_MINUTE_STR_LEN = 16


def _extract_date_prefix(raw: str | None) -> str | None:
    if not raw:
        return None

    try:
        dt = parse_flexible_datetime(raw)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, ClickException):
        if "T" in raw:
            return raw.split("T", maxsplit=1)[0]

        if " " in raw:
            return raw.split(" ", maxsplit=1)[0]

        return None


def _build_raw_start(
    date_time: str | None,
    date: str | None,
    time: str | None,
    fallback_date: str | None = None,
) -> str | None:
    if date_time:
        return date_time

    if date and time:
        return f"{date} {time}"

    if time and (" " in time or "T" in time):
        return time

    if date:
        return date

    if time:
        return f"{fallback_date} {time}" if fallback_date else time

    return None


def _build_raw_end(
    date_time: str | None,
    date: str | None,
    time: str | None,
    date_prefix: str | None,
) -> str | None:
    if date_time:
        return date_time

    if date and time:
        return f"{date} {time}"

    if time and (" " in time or "T" in time):
        return time

    if date:
        return date

    if time:
        return f"{date_prefix} {time}" if date_prefix else time

    return None


def resolve_schedule_create_times(
    start_date_time: str | None,
    start_date: str | None,
    start_time: str | None,
    end_date_time: str | None,
    end_date: str | None,
    end_time: str | None,
    duration: str | int | None,
    *,
    all_day: bool = False,
    is_practice: bool = False,
) -> tuple[str, str]:
    """Resolve create command datetime inputs into formatted start and end strings.

    Args:
        start_date_time (str | None): Optional combined start datetime string.
        start_date (str | None): Optional start date string.
        start_time (str | None): Optional start time string.
        end_date_time (str | None): Optional combined end datetime string.
        end_date (str | None): Optional end date string.
        end_time (str | None): Optional end time string.
        duration (str | int | None): Optional duration in minutes.
        all_day (bool): Whether event is all day.
        is_practice (bool): Whether event is a practice.

    Returns:
        tuple[str, str]: Formatted start and end ISO strings.

    Raises:
        UsageError: If invalid combinations of date and time arguments are provided.

    """
    if all_day:
        if start_date_time:
            msg = "Cannot combine --all-day with --start-datetime."
            raise click.UsageError(msg)

        start_date_str = start_date or start_time
        if not start_date_str:
            entity = "practices" if is_practice else "events"
            msg = f"--date/--start-date is required for all-day {entity}."
            raise click.UsageError(msg)

        return start_date_str, ""

    validate_no_input_conflict(start_date_time, start_date, start_time, "start")
    validate_no_input_conflict(end_date_time, end_date, end_time, "end")

    start_raw = _build_raw_start(start_date_time, start_date, start_time)
    date_prefix = _extract_date_prefix(start_raw) or start_date
    end_raw = _build_raw_end(end_date_time, end_date, end_time, date_prefix)

    duration_int = int(duration) if duration is not None else None

    start_iso, end_iso = resolve_create_times(start_raw, end_raw, duration_int)
    start_dt = parse_flexible_datetime(start_iso)
    end_dt = parse_flexible_datetime(end_iso)

    return start_dt.strftime("%Y-%m-%dT%H:%M"), end_dt.strftime("%H:%M")


def resolve_occurrence_update_times(
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
    """Resolve occurrence update datetime inputs.

    Returns:
        tuple[str | None, str | None]: Resolved (start_iso, end_iso) datetime strings.

    """
    validate_no_input_conflict(start_date_time, start_date, start_time, "start")
    validate_no_input_conflict(end_date_time, end_date, end_time, "end")

    start_prefix = _extract_date_prefix(current_start)
    start_raw = _build_raw_start(start_date_time, start_date, start_time, start_prefix)

    end_prefix = (
        _extract_date_prefix(start_raw)
        or _extract_date_prefix(current_end)
        or _extract_date_prefix(current_start)
    )
    end_raw = _build_raw_end(end_date_time, end_date, end_time, end_prefix)

    duration_int = int(duration) if duration is not None else None

    if not start_raw and not end_raw and duration_int is None:
        return None, None

    return resolve_update_times(start_raw, end_raw, duration_int, current_start, current_end)


def _normalize_game_iso(
    raw_start: str,
    raw_end: str,
) -> tuple[str, str]:
    if "T" not in raw_start:
        iso_start = f"{raw_start}T00:00:00Z" if raw_start else "2026-01-01T00:00:00Z"
    elif not raw_start.endswith("Z"):
        iso_start = f"{raw_start}:00Z" if len(raw_start) == ISO_MINUTE_STR_LEN else f"{raw_start}Z"
    else:
        iso_start = raw_start

    if "T" in raw_end:
        iso_end = raw_end if raw_end.endswith("Z") else f"{raw_end}Z"
    elif raw_start and "T" in raw_start:
        date_part = raw_start.split("T", maxsplit=1)[0]
        iso_end = f"{date_part}T{raw_end}:00Z" if raw_end else iso_start
    else:
        iso_end = f"2026-01-01T{raw_end}:00Z" if raw_end else iso_start

    return iso_start, iso_end


def resolve_game_update_times(
    start_date_time: str | None,
    start_date: str | None,
    start_time: str | None,
    end_date_time: str | None,
    end_date: str | None,
    end_time: str | None,
    duration: str | int | None,
    current_date_time: str | None,
    current_end_time: str | None,
) -> tuple[str | None, str | None]:
    """Resolve game update datetime inputs.

    Returns:
        tuple[str | None, str | None]: Resolved (start_iso, end_time_iso) strings.

    """
    validate_no_input_conflict(start_date_time, start_date, start_time, "start")
    validate_no_input_conflict(end_date_time, end_date, end_time, "end")

    raw_start = current_date_time or ""
    raw_end = current_end_time or ""
    iso_start, iso_end = _normalize_game_iso(raw_start, raw_end)

    start_prefix = _extract_date_prefix(raw_start)
    start_raw = _build_raw_start(start_date_time, start_date, start_time, start_prefix)

    end_prefix = (
        _extract_date_prefix(start_raw) or _extract_date_prefix(raw_end) or _extract_date_prefix(raw_start)
    )
    end_raw = _build_raw_end(end_date_time, end_date, end_time, end_prefix)

    duration_int = int(duration) if duration is not None else None

    if not start_raw and not end_raw and duration_int is None:
        return None, None

    start_iso, end_iso = resolve_update_times(start_raw, end_raw, duration_int, iso_start, iso_end)
    start_dt = parse_flexible_datetime(start_iso)
    end_dt = parse_flexible_datetime(end_iso)

    return start_dt.strftime("%Y-%m-%dT%H:%M"), end_dt.strftime("%H:%M")


def validate_update_scope(*, update_future: bool, update_single: bool) -> None:
    """Reject mutually exclusive occurrence update scope flags.

    Called from the command body ahead of ``build_authenticated_session`` so a usage error is reported as
    such even when no session is stored, rather than surfacing as a login failure.

    Args:
        update_future (bool): Update this and future occurrences flag.
        update_single (bool): Update only this occurrence flag.

    Raises:
        UsageError: If both flags are specified.

    """
    if update_future and update_single:
        msg = "Cannot specify both --future and --single."
        raise click.UsageError(msg)


def confirm_delete_or_abort(event_type: str, event_id: str, *, force: bool) -> None:
    """Confirm a destructive delete before any authenticated work happens.

    Called from the command body ahead of ``build_authenticated_session`` so that declining costs no
    login round trip, and so an aborted delete reports ``Aborted.`` rather than a session error.

    Args:
        event_type (str): Event type name shown in the prompt.
        event_id (str): Event identifier shown in the prompt.
        force (bool): Skip the confirmation prompt.

    Raises:
        Exit: If the user declines the confirmation.

    """
    if force:
        return

    if not click.confirm(f"Are you sure you want to delete {event_type} '{event_id}'?", default=False):
        click.echo("Aborted.", err=True)
        raise Exit(1)


def prompt_delete_scope(
    run_action: Callable[..., Any],
    session: TeamsAuthenticatedSession,
    event_id: str,
    event_type: str,
    timeout: float | None,
    *,
    force: bool = False,
    scope_flags: list[bool] | None = None,
    all_occurrences: bool = False,
    delete_future: bool = False,
) -> tuple[bool, bool]:
    """Resolve recurring delete scope and confirm destruction interactively.

    Args:
        run_action (Callable[..., Any]): Helper to execute actions.
        session (TeamsAuthenticatedSession): Authenticated session.
        event_id (str): Event identifier.
        event_type (str): Event type name.
        timeout (float | None): Optional timeout in seconds.
        force (bool): Skip confirmation prompt.
        scope_flags (list[bool] | None): Scope flags provided on CLI.
        all_occurrences (bool): Delete all occurrences flag.
        delete_future (bool): Delete future occurrences flag.

    Returns:
        tuple[bool, bool]: Tuple of (resolved_all, resolved_future).

    """
    flags = scope_flags or []
    if force or any(flags):
        return all_occurrences, delete_future

    occ_raw = run_action(
        session,
        _fetch_and_verify_occurrence_dict,
        event_id,
        event_type=event_type,
        timeout=timeout,
    )
    resolved_all = all_occurrences
    resolved_future = delete_future
    if bool(occ_raw.get("rrule")):
        prompt_text = "Delete scope: [1] This occurrence only, [2] This and future, [3] All occurrences"
        choice = click.prompt(
            prompt_text,
            type=click.Choice(["1", "2", "3"]),
            default="1",
        )
        if choice == "3":
            resolved_all = True
        elif choice == "2":
            resolved_future = True

    return resolved_all, resolved_future


def prompt_update_scope(
    occ: dict[str, Any],
    *,
    update_future: bool = False,
    update_single: bool = False,
) -> bool:
    """Prompt interactively for update scope if recurring and scope not explicitly given.

    Returns:
        bool: True if future occurrences should also be updated.

    """
    effective_future = update_future
    if not update_future and not update_single and bool(occ.get("rrule")):
        prompt_text = "Update scope: [1] This occurrence only, [2] This and future occurrences"
        choice = click.prompt(
            prompt_text,
            type=click.Choice(["1", "2"]),
            default="1",
        )
        if choice == "2":
            effective_future = True

    return effective_future


def handle_game_update(
    run_action: Callable[..., Any],
    session: TeamsAuthenticatedSession,
    event_id: str,
    *,
    game_type: str | None,
    start_date_time: str | None,
    end_time: str | None,
    start: str | None,
    end: str | None,
    date: str | None,
    duration: str | None,
    team_id: str | None,
    season_id: str | None,
    division_id: str | None,
    opposing_team_id: str | None,
    opposing_division: str | None,
    association_id: str | None,
    league_id: str | None,
    home_flag: bool | None,
    game_number: str | None,
    location_name: str | None,
    scorekeeper_name: str | None,
    scorekeeper_phone: str | None,
    broadcast_provider: str | None,
    timezone: str | None,
    timeout: float | None,
) -> UpdatedGameResult:
    """Execute game update action with datetime resolution.

    Returns:
        UpdatedGameResult: Result of updating the game.

    """
    if game_type is not None:
        validate_game_type(game_type)

    game_dict = run_action(
        session,
        _fetch_and_normalize_game_dict,
        event_id,
        timeout=timeout,
    )
    current_start = game_dict.get("date_time") or game_dict.get("startDate")
    current_end = game_dict.get("end_time") or game_dict.get("endTime")

    resolved_start_dt, resolved_end_time = resolve_game_update_times(
        start_date_time=start_date_time,
        start_date=date,
        start_time=start,
        end_date_time=None,
        end_date=None,
        end_time=end or end_time,
        duration=duration,
        current_date_time=current_start,
        current_end_time=current_end,
    )

    tz_name = timezone
    tz_offset = get_local_timezone_offset() if timezone is not None else None

    return run_action(
        session,
        _update_game_action,
        event_id,
        team_id=team_id,
        season_id=season_id,
        division_id=division_id,
        opposing_team_id=opposing_team_id,
        opposing_division=opposing_division,
        association_id=association_id,
        league_id=league_id,
        home_flag=home_flag,
        date_time=resolved_start_dt,
        end_time=resolved_end_time,
        game_number=game_number,
        game_type=game_type,
        location=location_name,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        timeout=timeout,
    )


def handle_occurrence_update(
    run_action: Callable[..., Any],
    session: TeamsAuthenticatedSession,
    event_id: str,
    event_type: str | None,
    *,
    title: str | None,
    notes: str | None,
    location_name: str | None,
    start_date_time: str | None,
    end_time: str | None,
    start: str | None,
    end: str | None,
    date: str | None,
    duration: str | None,
    repeat: str | None,
    repeat_interval: int,
    repeat_by_day: str | None,
    repeat_until: str | None,
    rrule: str | None,
    update_future: bool,
    update_single: bool,
    timeout: float | None,
) -> CalendarEventCreated:
    """Execute calendar occurrence update with scope prompt and datetime resolution.

    Returns:
        CalendarEventCreated: Result of creating/updating the occurrence.

    """
    occ = run_action(
        session,
        _fetch_and_verify_occurrence_dict,
        event_id,
        event_type=event_type,
        timeout=timeout,
    )
    current_start = occ.get("startDate") or occ.get("start_date") or ""
    current_end = occ.get("endDate") or occ.get("end_date") or ""

    start_iso, end_iso = resolve_occurrence_update_times(
        start_date_time=start_date_time,
        start_date=date,
        start_time=start,
        end_date_time=None,
        end_date=None,
        end_time=end or end_time,
        duration=duration,
        current_start=current_start,
        current_end=current_end,
    )

    effective_rrule = rrule
    if effective_rrule is None and repeat is not None:
        effective_rrule = _build_rrule_action(
            repeat,
            interval=repeat_interval,
            by_day=repeat_by_day,
            until=repeat_until,
        )

    effective_future = prompt_update_scope(
        occ,
        update_future=update_future,
        update_single=update_single,
    )

    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title

    if notes is not None:
        payload["notes"] = notes

    if location_name is not None:
        payload["locationName"] = location_name
        payload["location_name"] = location_name

    if start_iso is not None:
        payload["startDate"] = start_iso
        payload["start_date"] = start_iso

    if end_iso is not None:
        payload["endDate"] = end_iso
        payload["end_date"] = end_iso

    if effective_rrule is not None:
        payload["rrule"] = effective_rrule

    return run_action(
        session,
        _update_calendar_occurrence_action,
        event_id,
        payload,
        update_future=effective_future,
        timeout=timeout,
    )


def handle_occurrence_delete(
    run_action: Callable[..., Any],
    session: TeamsAuthenticatedSession,
    item_id: str,
    item_type: str | None,
    delete_action: Callable[..., Any],
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    force: bool,
    scope_flags: list[bool] | None,
    all_occurrences: bool,
    delete_future: bool,
    timeout: float | None,
    use_result_message: bool = True,
) -> None:
    """Execute calendar occurrence deletion with scope prompt and rendering.

    Args:
        run_action (Callable[..., Any]): Runner for API actions.
        session (TeamsAuthenticatedSession): Authenticated session.
        item_id (str): ID of event/occurrence to delete.
        item_type (str | None): Event type label ('event', 'practice', etc.).
        delete_action (Callable[..., Any]): Delete API action callable.
        output_format (str): Output format string ('plain', 'json', 'yaml').
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional fields spec string.
        force (bool): Bypass confirmation prompt.
        scope_flags (bool): Whether scope flags were supplied.
        all_occurrences (bool): Delete all occurrences flag.
        delete_future (bool): Delete future occurrences flag.
        timeout (float | None): Optional request timeout.
        use_result_message (bool): Whether to display result.message if present.

    """
    resolved_all, resolved_future = prompt_delete_scope(
        run_action,
        session,
        item_id,
        item_type or "event",
        timeout,
        force=force,
        scope_flags=scope_flags,
        all_occurrences=all_occurrences,
        delete_future=delete_future,
    )

    result = run_action(
        session,
        delete_action,
        item_id,
        delete_future=resolved_future,
        all_occurrences=resolved_all,
        timeout=timeout,
    )
    if output_format in {"json", "yaml"}:
        render_get_command(result, output_format, output_path, fields_spec)
    elif use_result_message and result and hasattr(result, "message") and result.message:
        click.echo(result.message)
    else:
        label = item_type or "event"
        click.echo(f"Successfully deleted {label} {item_id}")


def occurrence_update_options(func: F) -> F:
    """Add common occurrence update CLI options to a command.

    Args:
        func (F): The Click command function to decorate.

    Returns:
        F: Decorated command function with occurrence update options.

    """
    options = [
        click.option("--title", type=str, default=None, help="Updated event title."),
        click.option(
            "--start-date-time",
            type=str,
            default=None,
            help="Start date and time (ISO format or flexible string).",
        ),
        click.option(
            "--end-time",
            type=str,
            default=None,
            help="End time (e.g. '14:30' or '2:30 PM').",
        ),
        click.option(
            "--start",
            type=str,
            default=None,
            help="Flexible start datetime input.",
        ),
        click.option(
            "--end",
            type=str,
            default=None,
            help="Flexible end datetime or time input.",
        ),
        click.option(
            "--date",
            type=str,
            default=None,
            help="Event date (e.g. '2026-08-20').",
        ),
        click.option(
            "--duration",
            type=str,
            default=None,
            help="Event duration (e.g. '1h', '90m', '1.5h').",
        ),
        click.option(
            "--location",
            "--location-name",
            "location_name",
            type=str,
            default=None,
            help="Updated venue or location name.",
        ),
        click.option(
            "--notes",
            type=str,
            default=None,
            help="Updated event notes or description.",
        ),
        click.option(
            "--repeat",
            type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
            default=None,
            help="Repeat frequency for recurring events.",
        ),
        click.option(
            "--repeat-interval",
            "--interval",
            "repeat_interval",
            type=int,
            default=1,
            show_default=True,
            help="Interval for repeating events (e.g. 2 for every 2 weeks).",
        ),
        click.option(
            "--repeat-by-day",
            "--by-day",
            "--byday",
            "repeat_by_day",
            type=str,
            default=None,
            help="Days of the week for weekly recurrence (e.g. 'TU,TH', 'mon,wed').",
        ),
        click.option(
            "--repeat-until",
            "--until",
            "repeat_until",
            type=str,
            default=None,
            help="End date for recurrence (e.g. '2027-03-22').",
        ),
        click.option(
            "--rrule",
            type=str,
            default=None,
            help="Raw RRULE recurrence string (overrides --repeat flags).",
        ),
        click.option(
            "--future",
            "update_future",
            is_flag=True,
            default=False,
            help="Update this and all future occurrences.",
        ),
        click.option(
            "--single",
            "update_single",
            is_flag=True,
            default=False,
            help="Update only this single occurrence.",
        ),
    ]
    for opt in reversed(options):
        func = opt(func)

    return func


def run_occurrence_update(
    run_action: Callable[..., Any],
    session: TeamsAuthenticatedSession,
    event_id: str,
    event_type: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    title: str | None = None,
    notes: str | None = None,
    location_name: str | None = None,
    start_date_time: str | None = None,
    end_time: str | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
    duration: str | None = None,
    repeat: str | None = None,
    repeat_interval: int = 1,
    repeat_by_day: str | None = None,
    repeat_until: str | None = None,
    rrule: str | None = None,
    update_future: bool = False,
    update_single: bool = False,
    timeout: float | None = None,
    **_extra_kwargs: Any,
) -> None:
    """Validate arguments and execute calendar occurrence update.

    Args:
        run_action (Callable[..., Any]): Runner for API actions.
        session (TeamsAuthenticatedSession): Authenticated session.
        event_id (str): Event or occurrence ID to update.
        event_type (str | None): Event type ('event', 'practice', etc.).
        output_format (str): Output format string ('plain', 'json', 'yaml').
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional fields spec string.
        title (str | None): Optional updated title.
        notes (str | None): Optional updated notes.
        location_name (str | None): Optional updated location name.
        start_date_time (str | None): Optional start datetime string.
        end_time (str | None): Optional end time string.
        start (str | None): Optional flexible start input.
        end (str | None): Optional flexible end input.
        date (str | None): Optional date string.
        duration (str | None): Optional duration string.
        repeat (str | None): Optional repeat frequency.
        repeat_interval (int): Repeat interval.
        repeat_by_day (str | None): Optional repeat by day string.
        repeat_until (str | None): Optional repeat until date string.
        rrule (str | None): Optional RRULE string.
        update_future (bool): Update future occurrences flag.
        update_single (bool): Update single occurrence flag.
        timeout (float | None): Optional request timeout.

    """
    validate_update_scope(update_future=update_future, update_single=update_single)

    updated_occ = handle_occurrence_update(
        run_action,
        session,
        event_id,
        event_type,
        title=title,
        notes=notes,
        location_name=location_name,
        start_date_time=start_date_time,
        end_time=end or end_time,
        start=start,
        end=end,
        date=date,
        duration=duration,
        repeat=repeat,
        repeat_interval=repeat_interval,
        repeat_by_day=repeat_by_day,
        repeat_until=repeat_until,
        rrule=rrule,
        update_future=update_future,
        update_single=update_single,
        timeout=timeout,
    )
    render_get_command(updated_occ, output_format, output_path, fields_spec)
