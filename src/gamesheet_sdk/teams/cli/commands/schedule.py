# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup, parse_columns_spec
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
        "get": ("show", "view"),
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def events_group() -> None:
    """Manage team calendar events.

    Invoking ``events`` with no sub-command runs ``list`` by default.
    """


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
        "get": ("show", "view"),
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def games_group() -> None:
    """Manage team games.

    Invoking ``games`` with no sub-command runs ``list`` by default.
    """


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
        "get": ("show", "view"),
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def practices_group() -> None:
    """Manage team practices.

    Invoking ``practices`` with no sub-command runs ``list`` by default.
    """


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
