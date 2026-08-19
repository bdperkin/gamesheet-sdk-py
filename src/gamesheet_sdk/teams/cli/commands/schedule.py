# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.common.cli.datetime_helpers import (
    parse_flexible_datetime,
    resolve_create_times,
    resolve_datetime_input,
    validate_no_input_conflict,
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
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.schedule import (
    build_rrule as _build_rrule_action,
)
from gamesheet_sdk.teams.schedule import (
    create_event as _create_event_action,
)
from gamesheet_sdk.teams.schedule import (
    create_game as _create_game_action,
)
from gamesheet_sdk.teams.schedule import (
    create_practice as _create_practice_action,
)
from gamesheet_sdk.teams.schedule import (
    get_calendar_subscription as _get_calendar_subscription_action,
)
from gamesheet_sdk.teams.schedule import (
    get_event as _get_event_action,
)
from gamesheet_sdk.teams.schedule import (
    get_game as _get_game_action,
)
from gamesheet_sdk.teams.schedule import (
    get_practice as _get_practice_action,
)
from gamesheet_sdk.teams.schedule import (
    get_schedule_event as _get_schedule_event_action,
)
from gamesheet_sdk.teams.schedule import (
    list_events as _list_events_action,
)
from gamesheet_sdk.teams.schedule import (
    list_games as _list_games_action,
)
from gamesheet_sdk.teams.schedule import (
    list_practices as _list_practices_action,
)
from gamesheet_sdk.teams.schedule import (
    list_schedule as _list_schedule_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "schedule",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "subscribe": ("sub",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def schedule_group() -> None:
    """Manage team schedules, calendar events, practices, and games.

    Invoking ``schedule`` with no sub-command runs ``list`` by default.
    """


@schedule_group.command("list")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve schedule for.",
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
def schedule_list_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_event_data: bool = False,
) -> None:
    r"""List all schedule events for the specified team.

    Focuses on eventDate, eventLocation, eventTime, eventTitle, id, and type.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.
        include_event_data (bool): Whether to include detailed eventData (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    events = run_action_or_exit(
        session,
        _list_schedule_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(events, output_format, output_path, columns_spec)


@schedule_group.command("get")
@click.option(
    "--event-id",
    "--id",
    "-e",
    "event_id",
    type=str,
    envvar="GAMESHEET_EVENT_ID",
    required=True,
    help="Event occurrence ID to retrieve details for.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=False,
    default=None,
    help="Team ID (used for fetching availability if requested).",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include availability information in the output.",
)
@common_output_options
@get_fields_option
@click.pass_context
def schedule_get_command(
    ctx: Context,
    event_id: str,
    team_id: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool = False,
) -> None:
    r"""Get detailed metadata for a schedule event occurrence.

    Retrieves all attributes and data for the selected calendar event.\f

    Args:
        ctx (Context): Click context object containing config.
        event_id (str): Event occurrence identifier.
        team_id (str | None): Optional team identifier for availability.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.
        include_availability (bool): Whether to include availability (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    event = run_action_or_exit(
        session,
        _get_schedule_event_action,
        event_id,
        team_id=team_id,
        include_availability=include_availability,
        timeout=config.timeout,
    )
    render_get_command(event, output_format, output_path, fields_spec)


@click.group(
    "events",
    cls=ResourceGroup,
    default="list",
    aliases={
        "create": ("add", "new"),
        "get": ("show", "view"),
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def events_group() -> None:
    """Manage team calendar events.

    Invoking ``events`` with no sub-command runs ``list`` by default.
    """


@events_group.command(
    "create",
    aliases=("add", "new"),
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID for the event.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Event title.",
)
@click.option(
    "--start-datetime",
    type=str,
    default=None,
    help="Start date and time. Mutually exclusive with --start-date/--start-time.",
)
@click.option(
    "--end-datetime",
    type=str,
    default=None,
    help="End date and time. Mutually exclusive with --end-date/--end-time.",
)
@click.option(
    "--start-date",
    type=str,
    default=None,
    help="Start date (YYYY-MM-DD). Use with --start-time.",
)
@click.option(
    "--start-time",
    "start_time_str",
    type=str,
    default=None,
    help="Start time (HH:MM or HH:MM:SS, 24h). Use with --start-date.",
)
@click.option(
    "--end-date",
    type=str,
    default=None,
    help="End date (YYYY-MM-DD). Use with --end-time.",
)
@click.option(
    "--end-time",
    "end_time_str",
    type=str,
    default=None,
    help="End time (HH:MM or HH:MM:SS, 24h). Use with --end-date.",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help="Event duration in minutes. Used to calculate end time from start time.",
)
@click.option(
    "--all-day",
    is_flag=True,
    default=False,
    help="Mark event as all-day.",
)
@click.option(
    "--location",
    type=str,
    default="",
    help="Event location / venue / address.",
)
@click.option(
    "--notes",
    "--description",
    "notes",
    type=str,
    default="",
    help="Event notes / description.",
)
@click.option(
    "--timezone",
    "--time-zone-name",
    "timezone",
    type=str,
    default=None,
    help="Timezone name. Defaults to system timezone.",
)
@click.option(
    "--repeat",
    "--freq",
    "--frequency",
    "frequency",
    type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
    default=None,
    help="Recurrence frequency for repeating events.",
)
@click.option(
    "--interval",
    type=int,
    default=1,
    show_default=True,
    help="Recurrence interval (e.g. every 2 weeks).",
)
@click.option(
    "--by-day",
    "--byday",
    "--days",
    "by_day",
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
    help="Recurrence end date (YYYY-MM-DD).",
)
@click.option(
    "--rrule",
    type=str,
    default=None,
    help="Explicit RRULE string (e.g. 'FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH').",
)
@common_output_options
@get_fields_option
@click.pass_context
def events_create_command(
    ctx: Context,
    team_id: str,
    title: str,
    start_datetime: str | None,
    end_datetime: str | None,
    start_date: str | None,
    start_time_str: str | None,
    end_date: str | None,
    end_time_str: str | None,
    duration: int | None,
    *,
    all_day: bool = False,
    location: str = "",
    notes: str = "",
    timezone: str | None = None,
    frequency: str | None = None,
    interval: int = 1,
    by_day: str | None = None,
    repeat_until: str | None = None,
    rrule: str | None = None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Create a new calendar event.

    Provide any two of ``--start-datetime`` (or ``--start-date`` + ``--start-time``),
    ``--end-datetime`` (or ``--end-date`` + ``--end-time``), and ``--duration`` to
    automatically calculate the third. For all-day events, use ``--all-day`` and provide
    ``--start-date`` or ``--start-datetime``.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        title (str): Event title.
        start_datetime (str | None): Start date and time.
        end_datetime (str | None): End date and time.
        start_date (str | None): Start date component.
        start_time_str (str | None): Start time component.
        end_date (str | None): End date component.
        end_time_str (str | None): End time component.
        duration (int | None): Event duration in minutes.
        all_day (bool): Whether event is all day (default: False).
        location (str): Event location / venue.
        notes (str): Event notes / description.
        timezone (str | None): Timezone name (defaults to system timezone).
        frequency (str | None): Recurrence frequency ('daily', 'weekly', 'monthly').
        interval (int): Recurrence interval (default: 1).
        by_day (str | None): Days of the week for weekly recurrence.
        repeat_until (str | None): Recurrence end date (YYYY-MM-DD).
        rrule (str | None): Direct RRULE string.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    if all_day:
        if start_datetime and start_date:
            msg = "Cannot combine --start-datetime with --start-date/--start-time."
            raise click.UsageError(msg)

        start_raw = start_datetime or start_date
        if not start_raw:
            msg = "--start-datetime or --start-date is required for all-day events."
            raise click.UsageError(msg)

        start_dt = parse_flexible_datetime(start_raw)
        formatted_start = start_dt.strftime("%Y-%m-%d")
        formatted_end = ""
    else:
        validate_no_input_conflict(start_datetime, start_date, start_time_str, "start")
        validate_no_input_conflict(end_datetime, end_date, end_time_str, "end")

        start_raw = resolve_datetime_input(start_datetime, start_date, start_time_str, "start")
        end_raw = resolve_datetime_input(end_datetime, end_date, end_time_str, "end")

        scheduled_start, scheduled_end = resolve_create_times(start_raw, end_raw, duration)
        start_dt = parse_flexible_datetime(scheduled_start)
        end_dt = parse_flexible_datetime(scheduled_end)
        formatted_start = start_dt.strftime("%Y-%m-%dT%H:%M")
        formatted_end = end_dt.strftime("%H:%M")

    effective_rrule = rrule or _build_rrule_action(frequency, interval=interval, by_day=by_day)

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    event = run_action_or_exit(
        session,
        _create_event_action,
        team_id,
        title,
        formatted_start,
        formatted_end,
        event_type="event",
        timezone=timezone,
        location=location,
        notes=notes,
        all_day=all_day,
        rrule=effective_rrule,
        repeat_until=repeat_until,
        timeout=config.timeout,
    )
    render_get_command(event, output_format, output_path, fields_spec)


@events_group.command("list")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve events for.",
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
def events_list_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_event_data: bool = False,
) -> None:
    r"""List calendar events for the specified team.

    Focuses on eventDate, eventLocation, eventTime, eventTitle, id, and type.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.
        include_event_data (bool): Whether to include detailed eventData (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    events = run_action_or_exit(
        session,
        _list_events_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(events, output_format, output_path, columns_spec)


@events_group.command("get")
@click.option(
    "--event-id",
    "--id",
    "-e",
    "event_id",
    type=str,
    envvar="GAMESHEET_EVENT_ID",
    required=True,
    help="Event occurrence ID to retrieve details for.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=False,
    default=None,
    help="Team ID (used for fetching availability if requested).",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include availability information in the output.",
)
@common_output_options
@get_fields_option
@click.pass_context
def events_get_command(
    ctx: Context,
    event_id: str,
    team_id: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool = False,
) -> None:
    r"""Get detailed metadata for a calendar event occurrence.

    Retrieves all attributes and data for the selected event.\f

    Args:
        ctx (Context): Click context object containing config.
        event_id (str): Event occurrence identifier.
        team_id (str | None): Optional team identifier for availability.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.
        include_availability (bool): Whether to include availability (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    event = run_action_or_exit(
        session,
        _get_event_action,
        event_id,
        team_id=team_id,
        include_availability=include_availability,
        timeout=config.timeout,
    )
    render_get_command(event, output_format, output_path, fields_spec)


@click.group(
    "games",
    cls=ResourceGroup,
    default="list",
    aliases={
        "create": ("add", "new"),
        "get": ("show", "view"),
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def games_group() -> None:
    """Manage team games.

    Invoking ``games`` with no sub-command runs ``list`` by default.
    """


@games_group.command(
    "create",
    aliases=("add", "new"),
)
@click.option(
    "--team-id",
    "-t",
    "--home-team-id",
    "team_id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team identifier.",
)
@click.option(
    "--opposing-team-id",
    "--visitor-team-id",
    "--opponent-id",
    "opposing_team_id",
    type=str,
    required=True,
    help="Opposing team identifier.",
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season identifier.",
)
@click.option(
    "--division-id",
    "--home-division-id",
    "division_id",
    type=str,
    required=True,
    help="Division identifier.",
)
@click.option(
    "--opposing-division-id",
    "--opposing-division",
    "--visitor-division-id",
    "opposing_division",
    type=str,
    default=None,
    help="Opposing team division identifier (defaults to --division-id).",
)
@click.option(
    "--association-id",
    type=str,
    default="0",
    help="Association identifier (optional).",
)
@click.option(
    "--league-id",
    type=str,
    default="0",
    help="League identifier (optional).",
)
@click.option(
    "--home/--visitor",
    "--home-flag/--away",
    "home_flag",
    default=True,
    show_default=True,
    help="Specify whether the team is the home or visitor/away team.",
)
@click.option(
    "--number",
    "-n",
    "--game-number",
    "number",
    type=str,
    required=True,
    help="Game number.",
)
@click.option(
    "--game-type",
    type=str,
    default="regular_season",
    show_default=True,
    help="Game type (regular_season, playoff, exhibition, tournament).",
)
@click.option(
    "--start-datetime",
    type=str,
    default=None,
    help="Start date and time. Mutually exclusive with --start-date/--start-time.",
)
@click.option(
    "--end-datetime",
    type=str,
    default=None,
    help="End date and time. Mutually exclusive with --end-date/--end-time.",
)
@click.option(
    "--start-date",
    type=str,
    default=None,
    help="Start date (YYYY-MM-DD). Use with --start-time.",
)
@click.option(
    "--start-time",
    "start_time_str",
    type=str,
    default=None,
    help="Start time (HH:MM or HH:MM:SS, 24h). Use with --start-date.",
)
@click.option(
    "--end-date",
    type=str,
    default=None,
    help="End date (YYYY-MM-DD). Use with --end-time.",
)
@click.option(
    "--end-time",
    "end_time_str",
    type=str,
    default=None,
    help="End time (HH:MM or HH:MM:SS, 24h). Use with --end-date.",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help="Game duration in minutes. Used to calculate end time from start time.",
)
@click.option(
    "--location",
    type=str,
    default="",
    help="Game venue / location name.",
)
@click.option(
    "--scorekeeper-name",
    type=str,
    default="",
    help="Scorekeeper full name (optional).",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    default="",
    help="Scorekeeper phone number (optional).",
)
@click.option(
    "--broadcaster",
    "--broadcast-provider",
    "broadcast_provider",
    type=str,
    default="",
    help="Broadcast provider (e.g. LIVEBARN).",
)
@click.option(
    "--time-zone-name",
    "--timezone",
    "time_zone_name",
    type=str,
    default=None,
    help="IANA timezone name. Defaults to system timezone.",
)
@click.option(
    "--time-zone-offset",
    type=int,
    default=None,
    help="Timezone offset in minutes. Defaults to system timezone offset.",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_create_command(  # noqa: PLR0913
    ctx: Context,
    team_id: str,
    opposing_team_id: str,
    season_id: str,
    division_id: str,
    opposing_division: str | None,
    association_id: str,
    league_id: str,
    number: str,
    game_type: str,
    start_datetime: str | None,
    end_datetime: str | None,
    start_date: str | None,
    start_time_str: str | None,
    end_date: str | None,
    end_time_str: str | None,
    duration: int | None,
    *,
    home_flag: bool = True,
    location: str = "",
    scorekeeper_name: str = "",
    scorekeeper_phone: str = "",
    broadcast_provider: str = "",
    time_zone_name: str | None = None,
    time_zone_offset: int | None = None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Create a new scheduled game.

    Provide any two of ``--start-datetime`` (or ``--start-date`` + ``--start-time``),
    ``--end-datetime`` (or ``--end-date`` + ``--end-time``), and ``--duration`` to
    automatically calculate the third.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        opposing_team_id (str): Opposing team identifier.
        season_id (str): Season identifier.
        division_id (str): Division identifier.
        opposing_division (str | None): Opposing team division identifier.
        association_id (str): Association identifier.
        league_id (str): League identifier.
        number (str): Game number.
        game_type (str): Game type (regular_season, playoff, exhibition, tournament).
        start_datetime (str | None): Start date and time.
        end_datetime (str | None): End date and time.
        start_date (str | None): Start date component.
        start_time_str (str | None): Start time component.
        end_date (str | None): End date component.
        end_time_str (str | None): End time component.
        duration (int | None): Game duration in minutes.
        home_flag (bool): Whether home team (default: True).
        location (str): Game venue / location name.
        scorekeeper_name (str): Scorekeeper full name.
        scorekeeper_phone (str): Scorekeeper phone number.
        broadcast_provider (str): Broadcast provider name.
        time_zone_name (str | None): Timezone name (defaults to system timezone).
        time_zone_offset (int | None): Timezone offset in minutes (defaults to system offset).
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    validate_no_input_conflict(start_datetime, start_date, start_time_str, "start")
    validate_no_input_conflict(end_datetime, end_date, end_time_str, "end")

    start_raw = resolve_datetime_input(start_datetime, start_date, start_time_str, "start")
    end_raw = resolve_datetime_input(end_datetime, end_date, end_time_str, "end")

    scheduled_start, scheduled_end = resolve_create_times(start_raw, end_raw, duration)
    start_dt = parse_flexible_datetime(scheduled_start)
    end_dt = parse_flexible_datetime(scheduled_end)
    formatted_start = start_dt.strftime("%Y-%m-%dT%H:%M")
    formatted_end = end_dt.strftime("%H:%M")

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game = run_action_or_exit(
        session,
        _create_game_action,
        team_id,
        season_id,
        division_id,
        opposing_team_id,
        formatted_start,
        formatted_end,
        home_flag=home_flag,
        opposing_division=opposing_division,
        association_id=association_id,
        league_id=league_id,
        game_number=number,
        game_type=game_type,
        location=location,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
        time_zone_name=time_zone_name,
        time_zone_offset=time_zone_offset,
        timeout=config.timeout,
    )
    render_get_command(game, output_format, output_path, fields_spec)


@games_group.command("list")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve games for.",
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
def games_list_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_event_data: bool = False,
) -> None:
    r"""List scheduled games for the specified team.

    Focuses on eventDate, eventLocation, eventTime, eventTitle, id, and type.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.
        include_event_data (bool): Whether to include detailed eventData (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    events = run_action_or_exit(
        session,
        _list_games_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(events, output_format, output_path, columns_spec)


@games_group.command("get")
@click.option(
    "--game-id",
    "--event-id",
    "--id",
    "-e",
    "event_id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Game occurrence ID to retrieve details for.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=False,
    default=None,
    help="Team ID (used for fetching availability if requested).",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include availability information in the output.",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_get_command(
    ctx: Context,
    event_id: str,
    team_id: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool = False,
) -> None:
    r"""Get detailed metadata for a game occurrence.

    Retrieves all attributes and data for the selected game.\f

    Args:
        ctx (Context): Click context object containing config.
        event_id (str): Game occurrence identifier.
        team_id (str | None): Optional team identifier for availability.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.
        include_availability (bool): Whether to include availability (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game = run_action_or_exit(
        session,
        _get_game_action,
        event_id,
        team_id=team_id,
        include_availability=include_availability,
        timeout=config.timeout,
    )
    render_get_command(game, output_format, output_path, fields_spec)


@click.group(
    "practices",
    cls=ResourceGroup,
    default="list",
    aliases={
        "create": ("add", "new"),
        "get": ("show", "view"),
        "list": ("ls",),
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
    "--start-datetime",
    type=str,
    default=None,
    help="Start date and time. Mutually exclusive with --start-date/--start-time.",
)
@click.option(
    "--end-datetime",
    type=str,
    default=None,
    help="End date and time. Mutually exclusive with --end-date/--end-time.",
)
@click.option(
    "--start-date",
    type=str,
    default=None,
    help="Start date (YYYY-MM-DD). Use with --start-time.",
)
@click.option(
    "--start-time",
    "start_time_str",
    type=str,
    default=None,
    help="Start time (HH:MM or HH:MM:SS, 24h). Use with --start-date.",
)
@click.option(
    "--end-date",
    type=str,
    default=None,
    help="End date (YYYY-MM-DD). Use with --end-time.",
)
@click.option(
    "--end-time",
    "end_time_str",
    type=str,
    default=None,
    help="End time (HH:MM or HH:MM:SS, 24h). Use with --end-date.",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help="Practice duration in minutes. Used to calculate end time from start time.",
)
@click.option(
    "--all-day",
    is_flag=True,
    default=False,
    help="Mark practice as all-day.",
)
@click.option(
    "--location",
    type=str,
    default="",
    help="Practice location / venue / address.",
)
@click.option(
    "--notes",
    "--description",
    "notes",
    type=str,
    default="",
    help="Practice notes / description.",
)
@click.option(
    "--timezone",
    "--time-zone-name",
    "timezone",
    type=str,
    default=None,
    help="Timezone name. Defaults to system timezone.",
)
@click.option(
    "--repeat",
    "--freq",
    "--frequency",
    "frequency",
    type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
    default=None,
    help="Recurrence frequency for repeating practices.",
)
@click.option(
    "--interval",
    type=int,
    default=1,
    show_default=True,
    help="Recurrence interval (e.g. every 2 weeks).",
)
@click.option(
    "--by-day",
    "--byday",
    "--days",
    "by_day",
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
    help="Recurrence end date (YYYY-MM-DD).",
)
@click.option(
    "--rrule",
    type=str,
    default=None,
    help="Explicit RRULE string (e.g. 'FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH').",
)
@common_output_options
@get_fields_option
@click.pass_context
def practices_create_command(
    ctx: Context,
    team_id: str,
    title: str,
    start_datetime: str | None,
    end_datetime: str | None,
    start_date: str | None,
    start_time_str: str | None,
    end_date: str | None,
    end_time_str: str | None,
    duration: int | None,
    *,
    all_day: bool = False,
    location: str = "",
    notes: str = "",
    timezone: str | None = None,
    frequency: str | None = None,
    interval: int = 1,
    by_day: str | None = None,
    repeat_until: str | None = None,
    rrule: str | None = None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Create a new team practice.

    Provide any two of ``--start-datetime`` (or ``--start-date`` + ``--start-time``),
    ``--end-datetime`` (or ``--end-date`` + ``--end-time``), and ``--duration`` to
    automatically calculate the third. For all-day practices, use ``--all-day`` and provide
    ``--start-date`` or ``--start-datetime``.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        title (str): Practice title (default: 'Practice').
        start_datetime (str | None): Start date and time.
        end_datetime (str | None): End date and time.
        start_date (str | None): Start date component.
        start_time_str (str | None): Start time component.
        end_date (str | None): End date component.
        end_time_str (str | None): End time component.
        duration (int | None): Practice duration in minutes.
        all_day (bool): Whether practice is all day (default: False).
        location (str): Practice location / venue.
        notes (str): Practice notes / description.
        timezone (str | None): Timezone name (defaults to system timezone).
        frequency (str | None): Recurrence frequency ('daily', 'weekly', 'monthly').
        interval (int): Recurrence interval (default: 1).
        by_day (str | None): Days of the week for weekly recurrence.
        repeat_until (str | None): Recurrence end date (YYYY-MM-DD).
        rrule (str | None): Direct RRULE string.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    if all_day:
        if start_datetime and start_date:
            msg = "Cannot combine --start-datetime with --start-date/--start-time."
            raise click.UsageError(msg)

        start_raw = start_datetime or start_date
        if not start_raw:
            msg = "--start-datetime or --start-date is required for all-day practices."
            raise click.UsageError(msg)

        start_dt = parse_flexible_datetime(start_raw)
        formatted_start = start_dt.strftime("%Y-%m-%d")
        formatted_end = ""
    else:
        validate_no_input_conflict(start_datetime, start_date, start_time_str, "start")
        validate_no_input_conflict(end_datetime, end_date, end_time_str, "end")

        start_raw = resolve_datetime_input(start_datetime, start_date, start_time_str, "start")
        end_raw = resolve_datetime_input(end_datetime, end_date, end_time_str, "end")

        scheduled_start, scheduled_end = resolve_create_times(start_raw, end_raw, duration)
        start_dt = parse_flexible_datetime(scheduled_start)
        end_dt = parse_flexible_datetime(scheduled_end)
        formatted_start = start_dt.strftime("%Y-%m-%dT%H:%M")
        formatted_end = end_dt.strftime("%H:%M")

    effective_rrule = rrule or _build_rrule_action(frequency, interval=interval, by_day=by_day)

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    practice = run_action_or_exit(
        session,
        _create_practice_action,
        team_id,
        formatted_start,
        formatted_end,
        title=title,
        timezone=timezone,
        location=location,
        notes=notes,
        all_day=all_day,
        rrule=effective_rrule,
        repeat_until=repeat_until,
        timeout=config.timeout,
    )
    render_get_command(practice, output_format, output_path, fields_spec)


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
    include_event_data: bool = False,
) -> None:
    r"""List practices for the specified team.

    Focuses on eventDate, eventLocation, eventTime, eventTitle, id, and type.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        month (str): Month filter for calendar events.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.
        include_event_data (bool): Whether to include detailed eventData (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    events = run_action_or_exit(
        session,
        _list_practices_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(events, output_format, output_path, columns_spec)


@practices_group.command("get")
@click.option(
    "--practice-id",
    "--event-id",
    "--id",
    "-e",
    "event_id",
    type=str,
    envvar="GAMESHEET_PRACTICE_ID",
    required=True,
    help="Practice occurrence ID to retrieve details for.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=False,
    default=None,
    help="Team ID (used for fetching availability if requested).",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include availability information in the output.",
)
@common_output_options
@get_fields_option
@click.pass_context
def practices_get_command(
    ctx: Context,
    event_id: str,
    team_id: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool = False,
) -> None:
    r"""Get detailed metadata for a practice occurrence.

    Retrieves all attributes and data for the selected practice.\f

    Args:
        ctx (Context): Click context object containing config.
        event_id (str): Practice occurrence identifier.
        team_id (str | None): Optional team identifier for availability.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.
        include_availability (bool): Whether to include availability (default: False).

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    practice = run_action_or_exit(
        session,
        _get_practice_action,
        event_id,
        team_id=team_id,
        include_availability=include_availability,
        timeout=config.timeout,
    )
    render_get_command(practice, output_format, output_path, fields_spec)


@schedule_group.command("export")
def schedule_export_command() -> None:
    r"""Export and download scoresheets.

    Download team scoresheets and game data.\f

    NOT YET IMPLEMENTED - Scoresheet export support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule export is not yet implemented. "
        "Scoresheet export support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@schedule_group.command(
    "subscribe",
    aliases=("sub",),
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to generate calendar subscription URLs for.",
)
@click.option(
    "--apple",
    "--apple-calendar",
    "apple_calendar",
    is_flag=True,
    default=False,
    help="Include Apple Calendar subscription URL.",
)
@click.option(
    "--google",
    "--google-calendar",
    "google_calendar",
    is_flag=True,
    default=False,
    help="Include Google Calendar subscription URL.",
)
@click.option(
    "--webcal",
    "--calendar-url",
    "calendar_url",
    is_flag=True,
    default=False,
    help="Include generic calendar subscription feed URL.",
)
@common_output_options
@list_columns_option
def schedule_subscribe_command(
    team_id: str,
    *,
    apple_calendar: bool,
    google_calendar: bool,
    calendar_url: bool,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """Generate calendar subscription feed URLs for a team.

    Provides subscription URLs for Apple Calendar, Google Calendar, and generic calendar feeds (webcal).
    """
    selected_columns: list[str] = []
    parsed_columns = parse_columns_spec(columns_spec)
    if parsed_columns is not None:
        alias_map = {
            "apple": "appleCalendar",
            "apple calendar": "appleCalendar",
            "apple_calendar": "appleCalendar",
            "applecalendar": "appleCalendar",
            "calendar url": "calendarUrl",
            "calendar_url": "calendarUrl",
            "calendarurl": "calendarUrl",
            "google": "googleCalendar",
            "google calendar": "googleCalendar",
            "google_calendar": "googleCalendar",
            "googlecalendar": "googleCalendar",
            "url": "calendarUrl",
            "webcal": "calendarUrl",
        }
        selected_columns = [alias_map.get(c.lower(), c) for c in parsed_columns]
    else:
        if apple_calendar:
            selected_columns.append("appleCalendar")

        if google_calendar:
            selected_columns.append("googleCalendar")

        if calendar_url:
            selected_columns.append("calendarUrl")

    effective_columns_spec = ",".join(selected_columns) if selected_columns else None
    subscription = _get_calendar_subscription_action(team_id)
    render_list_command([subscription], output_format, output_path, effective_columns_spec)


schedule_group.add_command(events_group)
schedule_group.add_command(games_group)
schedule_group.add_command(practices_group)
