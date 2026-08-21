# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Team practices CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.core import (
    ResourceGroup,
)
from gamesheet_sdk.common.cli.decorators import (
    common_output_options,
    get_fields_option,
    list_columns_option,
)
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.helpers import (
    confirm_delete_or_abort,
    handle_occurrence_delete,
    occurrence_update_options,
    resolve_schedule_create_times,
    run_occurrence_update,
    validate_update_scope,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.schedule import (
    build_rrule as _build_rrule_action,
)
from gamesheet_sdk.teams.schedule import (
    create_practice as _create_practice_action,
)
from gamesheet_sdk.teams.schedule import (
    delete_practice as _delete_practice_action,
)
from gamesheet_sdk.teams.schedule import (
    get_practice as _get_practice_action,
)
from gamesheet_sdk.teams.schedule import (
    list_practices as _list_practices_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "practices",
    cls=ResourceGroup,
    default="list",
    aliases={
        "create": ("add", "new"),
        "delete": ("del", "rm", "remove"),
        "get": ("show", "view"),
        "list": ("ls",),
        "update": ("set", "edit"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def practices_group() -> None:
    """Manage team practices.

    Invoking ``practices`` with no sub-command runs ``list`` by default.
    """


@practices_group.command(
    "create",
    aliases=("add", "new"),
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID for the practice.",
)
@click.option(
    "--title",
    type=str,
    default="Practice",
    show_default=True,
    help="Practice title.",
)
@click.option(
    "--start-date-time",
    type=str,
    default=None,
    help="Start date and time (ISO format or flexible string).",
)
@click.option(
    "--end-time",
    type=str,
    default=None,
    help="End time (e.g. '14:30' or '2:30 PM').",
)
@click.option(
    "--start",
    type=str,
    default=None,
    help="Flexible start datetime input.",
)
@click.option(
    "--end",
    type=str,
    default=None,
    help="Flexible end datetime or time input.",
)
@click.option(
    "--date",
    type=str,
    default=None,
    help="Practice date (e.g. '2026-08-20').",
)
@click.option(
    "--duration",
    type=str,
    default=None,
    help="Practice duration (e.g. '1h', '90m', '1.5h').",
)
@click.option(
    "--all-day",
    is_flag=True,
    default=False,
    help="Mark as an all-day practice.",
)
@click.option(
    "--location",
    type=str,
    default="",
    help="Venue or location name/address.",
)
@click.option(
    "--notes",
    type=str,
    default="",
    help="Practice notes or description.",
)
@click.option(
    "--timezone",
    type=str,
    default=None,
    help="Timezone name (defaults to local timezone).",
)
@click.option(
    "--repeat",
    type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
    default=None,
    help="Repeat frequency for recurring practices.",
)
@click.option(
    "--repeat-interval",
    "--interval",
    "repeat_interval",
    type=int,
    default=1,
    show_default=True,
    help="Interval for repeating practices (e.g. 2 for every 2 weeks).",
)
@click.option(
    "--repeat-by-day",
    "--by-day",
    "--byday",
    "repeat_by_day",
    type=str,
    default=None,
    help="Days of the week for weekly recurrence (e.g. 'TU,TH', 'mon,wed').",
)
@click.option(
    "--repeat-until",
    "--until",
    "repeat_until",
    type=str,
    default=None,
    help="End date for recurrence (e.g. '2027-03-22').",
)
@click.option(
    "--rrule",
    type=str,
    default=None,
    help="Raw RRULE recurrence string (overrides --repeat flags).",
)
@common_output_options
@get_fields_option
@click.pass_context
def practices_create_command(
    ctx: Context,
    team_id: str,
    title: str,
    start_date_time: str | None,
    end_time: str | None,
    start: str | None,
    end: str | None,
    date: str | None,
    duration: str | None,
    location: str,
    notes: str,
    timezone: str | None,
    repeat: str | None,
    repeat_interval: int,
    repeat_by_day: str | None,
    repeat_until: str | None,
    rrule: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    all_day: bool = False,
) -> None:
    """Create a new team practice.

    Supports flexible start/end datetime resolution.
    """
    config: Config = ctx.obj
    resolved_start_dt, resolved_end_time = resolve_schedule_create_times(
        start_date_time=start_date_time,
        start_date=date,
        start_time=start,
        end_date_time=None,
        end_date=None,
        end_time=end or end_time,
        duration=duration,
        all_day=all_day,
        is_practice=True,
    )

    effective_rrule = rrule
    if effective_rrule is None and repeat is not None:
        effective_rrule = _build_rrule_action(
            repeat,
            interval=repeat_interval,
            by_day=repeat_by_day,
        )

    session = build_authenticated_session(config)
    created = run_action_or_exit(
        session,
        _create_practice_action,
        team_id,
        resolved_start_dt,
        resolved_end_time,
        title=title,
        timezone=timezone,
        location=location,
        notes=notes,
        all_day=all_day,
        rrule=effective_rrule,
        repeat_until=repeat_until,
        timeout=config.timeout,
    )
    render_get_command(created, output_format, output_path, fields_spec)


@practices_group.command("list")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve practices for.",
)
@click.option(
    "--month",
    type=str,
    default="all",
    show_default=True,
    help="Month filter for calendar events (e.g. 'all', '2026-08').",
)
@click.option(
    "--event-data",
    "--include-event-data",
    "include_event_data",
    is_flag=True,
    default=False,
    help="Include detailed eventData in the output.",
)
@common_output_options
@list_columns_option
@click.pass_context
def practices_list_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_event_data: bool,
) -> None:
    """List practices for a team.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    practices = run_action_or_exit(
        session,
        _list_practices_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(
        practices,
        output_format,
        output_path,
        columns_spec,
    )


@practices_group.command("get")
@click.option(
    "--practice-id",
    "-p",
    "--id",
    "practice_id",
    type=str,
    envvar="GAMESHEET_PRACTICE_ID",
    required=True,
    help="Practice occurrence identifier.",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include player/coach availability for the practice.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    default=None,
    help="Team ID (required when fetching availability if not present in practice).",
)
@common_output_options
@get_fields_option
@click.pass_context
def practices_get_command(
    ctx: Context,
    practice_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool,
    team_id: str | None,
) -> None:
    """Show details for a practice occurrence.

    Selected via ``--practice-id`` / ``-p`` / ``--id`` or ``GAMESHEET_PRACTICE_ID``.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    practice_detail = run_action_or_exit(
        session,
        _get_practice_action,
        practice_id,
        include_availability=include_availability,
        team_id=team_id,
        timeout=config.timeout,
    )
    render_get_command(practice_detail, output_format, output_path, fields_spec)


@practices_group.command(
    "delete",
    aliases=("del", "rm", "remove"),
)
@click.option(
    "--practice-id",
    "-p",
    "--id",
    "practice_id",
    type=str,
    envvar="GAMESHEET_PRACTICE_ID",
    required=True,
    help="Identifier of the practice or occurrence to delete.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompts.",
)
@click.option(
    "--all",
    "all_occurrences",
    is_flag=True,
    default=False,
    help="Delete all occurrences of the practice series (via /api/calendar/events).",
)
@click.option(
    "--future",
    "delete_future",
    is_flag=True,
    default=False,
    help="Delete this occurrence and all future occurrences.",
)
@click.option(
    "--single",
    "delete_single",
    is_flag=True,
    default=False,
    help="Delete only this single occurrence.",
)
@common_output_options
@get_fields_option
@click.pass_context
def practices_delete_command(
    ctx: Context,
    practice_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    force: bool = False,
    all_occurrences: bool = False,
    delete_future: bool = False,
    delete_single: bool = False,
) -> None:
    """Delete a practice series or occurrence.

    Selected via ``--practice-id`` / ``-p`` / ``--id`` or ``GAMESHEET_PRACTICE_ID``.

    Raises:
        UsageError: If conflicting scope options are provided.

    """
    config: Config = ctx.obj
    scope_flags = [all_occurrences, delete_future, delete_single]
    if sum(1 for f in scope_flags if f) > 1:
        msg = "Cannot combine --all, --future, and --single."
        raise click.UsageError(msg)

    confirm_delete_or_abort("practice", practice_id, force=force)

    session = build_authenticated_session(config)
    handle_occurrence_delete(
        run_action_or_exit,
        session,
        practice_id,
        "practice",
        _delete_practice_action,
        output_format,
        output_path,
        fields_spec,
        force=force,
        scope_flags=scope_flags,
        all_occurrences=all_occurrences,
        delete_future=delete_future,
        timeout=config.timeout,
        use_result_message=False,
    )


@practices_group.command(
    "update",
    aliases=("set", "edit"),
)
@click.option(
    "--practice-id",
    "-p",
    "--id",
    "practice_id",
    type=str,
    envvar="GAMESHEET_PRACTICE_ID",
    required=True,
    help="Practice ID to update.",
)
@occurrence_update_options
@common_output_options
@get_fields_option
@click.pass_context
def practices_update_command(
    ctx: Context,
    practice_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    **update_kwargs: Any,
) -> None:
    """Update a practice occurrence.

    Selected via ``--practice-id`` / ``-p`` / ``--id`` or ``GAMESHEET_PRACTICE_ID``.
    """
    config: Config = ctx.obj
    validate_update_scope(
        update_future=bool(update_kwargs.get("update_future")),
        update_single=bool(update_kwargs.get("update_single")),
    )

    session = build_authenticated_session(config)
    run_occurrence_update(
        run_action_or_exit,
        session,
        practice_id,
        "practice",
        output_format,
        output_path,
        fields_spec,
        timeout=config.timeout,
        **update_kwargs,
    )


__all__ = [
    "practices_create_command",
    "practices_delete_command",
    "practices_get_command",
    "practices_group",
    "practices_list_command",
    "practices_update_command",
]
