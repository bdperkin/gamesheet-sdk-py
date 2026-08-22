# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule top-level CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.core import (
    ResourceGroup,
    parse_columns_spec,
)
from gamesheet_sdk.common.cli.decorators import (
    columns_option,
    common_output_options,
)
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.events import events_group
from gamesheet_sdk.teams.cli.commands.schedule.games import games_group
from gamesheet_sdk.teams.cli.commands.schedule.helpers import (
    confirm_delete_or_abort,
    handle_game_update,
    handle_occurrence_delete,
    run_occurrence_update,
    validate_update_scope,
)
from gamesheet_sdk.teams.cli.commands.schedule.practices import practices_group
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.schedule import (
    delete_event as _delete_event_action,
)
from gamesheet_sdk.teams.schedule import (
    delete_game as _delete_game_action,
)
from gamesheet_sdk.teams.schedule import (
    get_calendar_subscription as _get_calendar_subscription_action,
)
from gamesheet_sdk.teams.schedule import (
    get_schedule_event as _get_schedule_event_action,
)
from gamesheet_sdk.teams.schedule import (
    list_schedule as _list_schedule_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config
    from gamesheet_sdk.teams.session import TeamsAuthenticatedSession


@click.group(
    "schedule",
    cls=ResourceGroup,
    default="list",
    aliases={
        "delete": ("del", "rm", "remove"),
        "get": ("show", "view"),
        "list": ("ls",),
        "subscribe": ("sub",),
        "update": ("set", "edit"),
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
@columns_option
@click.pass_context
def schedule_list_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_event_data: bool,
) -> None:
    """List calendar events, games, and practices for a team.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.
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
    render_list_command(
        events,
        output_format,
        output_path,
        columns_spec,
    )


@schedule_group.command("get")
@click.option(
    "--event-id",
    "-e",
    "--id",
    "event_id",
    type=str,
    envvar="GAMESHEET_EVENT_ID",
    required=True,
    help="Calendar event occurrence identifier or game ID.",
)
@click.option(
    "--type",
    "event_type",
    type=click.Choice(["event", "game", "practice"], case_sensitive=False),
    default=None,
    help="Type of event ('event', 'game', 'practice').",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include player/coach availability for the event.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    default=None,
    help="Team ID (required when fetching availability if not present in event).",
)
@common_output_options
@columns_option
@click.pass_context
def schedule_get_command(
    ctx: Context,
    event_id: str,
    event_type: str | None,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    include_availability: bool,
    team_id: str | None,
) -> None:
    """Show details for a calendar event occurrence or scheduled game.

    Selected via ``--event-id`` / ``-e`` / ``--id`` or ``GAMESHEET_EVENT_ID``.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    event_detail = run_action_or_exit(
        session,
        _get_schedule_event_action,
        event_id,
        event_type=event_type,
        include_availability=include_availability,
        team_id=team_id,
        timeout=config.timeout,
    )
    render_get_command(event_detail, output_format, output_path, columns_spec)


def _handle_game_delete(
    session: TeamsAuthenticatedSession,
    event_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    timeout: float | None,
) -> None:
    result = run_action_or_exit(
        session,
        _delete_game_action,
        event_id,
        timeout=timeout,
    )
    if output_format in {"json", "yaml"}:
        render_get_command(result, output_format, output_path, columns_spec)
    elif result and hasattr(result, "message") and result.message:
        click.echo(result.message)
    else:
        click.echo(f"Successfully deleted game {event_id}")


@schedule_group.command(
    "delete",
    aliases=("del", "rm", "remove"),
)
@click.option(
    "--event-id",
    "-e",
    "--id",
    "event_id",
    type=str,
    envvar="GAMESHEET_EVENT_ID",
    required=True,
    help="Calendar event identifier or game ID to delete.",
)
@click.option(
    "--type",
    "event_type",
    type=click.Choice(["event", "game", "practice"], case_sensitive=False),
    default=None,
    help="Type of event ('event', 'game', 'practice').",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompts.",
)
@click.option(
    "--all",
    "all_occurrences",
    is_flag=True,
    default=False,
    help="Delete all occurrences of the event series (via /api/calendar/events).",
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
@columns_option
@click.pass_context
def schedule_delete_command(
    ctx: Context,
    event_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    event_type: str | None = None,
    force: bool = False,
    all_occurrences: bool = False,
    delete_future: bool = False,
    delete_single: bool = False,
) -> None:
    """Delete a calendar event, occurrence, practice, or game.

    Selected via ``--event-id`` / ``-e`` / ``--id`` or ``GAMESHEET_EVENT_ID``.

    Raises:
        UsageError: If conflicting scope options are provided.

    """
    config: Config = ctx.obj
    is_game = (event_type is not None and event_type.lower() == "game") or (
        event_type is None and (isinstance(event_id, int) or str(event_id).isdigit())
    )

    scope_flags = [all_occurrences, delete_future, delete_single]
    if sum(1 for f in scope_flags if f) > 1:
        msg = "Cannot combine --all, --future, and --single."
        raise click.UsageError(msg)

    confirm_delete_or_abort("game" if is_game else (event_type or "event"), event_id, force=force)

    session = build_authenticated_session(config)

    if is_game:
        _handle_game_delete(
            session,
            event_id,
            output_format,
            output_path,
            columns_spec,
            config.timeout,
        )
        return

    handle_occurrence_delete(
        run_action_or_exit,
        session,
        event_id,
        event_type or "event",
        _delete_event_action,
        output_format,
        output_path,
        columns_spec,
        force=force,
        scope_flags=scope_flags,
        all_occurrences=all_occurrences,
        delete_future=delete_future,
        timeout=config.timeout,
    )


@schedule_group.command(
    "update",
    aliases=("set", "edit"),
)
@click.option(
    "--event-id",
    "-e",
    "--id",
    "event_id",
    type=str,
    envvar="GAMESHEET_EVENT_ID",
    required=True,
    help="Identifier of the event, occurrence, or game to update.",
)
@click.option(
    "--type",
    "event_type",
    type=click.Choice(["event", "game", "practice"], case_sensitive=False),
    default=None,
    help="Type of event ('event', 'game', 'practice').",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Updated title (for events/practices).",
)
@click.option(
    "--start-datetime",
    "--start-date-time",
    "start_date_time",
    type=str,
    default=None,
    help="Start date and time (ISO format or flexible string).",
)
@click.option(
    "--end-datetime",
    "--end-date-time",
    "end_time",
    type=str,
    default=None,
    help="End time (e.g. '14:30' or '2:30 PM').",
)
@click.option(
    "--start-time",
    "--start",
    "start",
    type=str,
    default=None,
    help="Flexible start datetime input.",
)
@click.option(
    "--end-time",
    "--end",
    "end",
    type=str,
    default=None,
    help="Flexible end datetime or time input.",
)
@click.option(
    "--start-date",
    "--date",
    "date",
    type=str,
    default=None,
    help="Date (e.g. '2026-08-20').",
)
@click.option(
    "--duration",
    type=str,
    default=None,
    help="Duration in minutes (e.g. '60', '1h', '90m').",
)
@click.option(
    "--location",
    "--location-name",
    "location_name",
    type=str,
    default=None,
    help="Location or facility name.",
)
@click.option(
    "--notes",
    type=str,
    default=None,
    help="Notes or description (events/practices only).",
)
@click.option(
    "--repeat",
    type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
    default=None,
    help="Repeat frequency for recurring events/practices.",
)
@click.option(
    "--repeat-interval",
    "--interval",
    "repeat_interval",
    type=int,
    default=1,
    show_default=True,
    help="Interval for repeating events/practices (e.g. 2 for every 2 weeks).",
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
    help="Raw RRULE string for custom recurrence (events/practices only).",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    default=None,
    help="Updated home team ID (games only).",
)
@click.option(
    "--season-id",
    "-s",
    type=str,
    default=None,
    help="Updated season ID (games only).",
)
@click.option(
    "--division-id",
    "-d",
    type=str,
    default=None,
    help="Updated division ID (games only).",
)
@click.option(
    "--opposing-team-id",
    "--opponent",
    "opposing_team_id",
    type=str,
    default=None,
    help="Updated opposing / visitor team ID (games only).",
)
@click.option(
    "--opposing-division",
    type=str,
    default=None,
    help="Updated opposing division name (games only).",
)
@click.option(
    "--association-id",
    "-a",
    type=str,
    default=None,
    help="Updated association ID (games only).",
)
@click.option(
    "--league-id",
    "-l",
    type=str,
    default=None,
    help="Updated league ID (games only).",
)
@click.option(
    "--home/--away",
    "home_flag",
    default=None,
    help="Whether this is a home game (games only).",
)
@click.option(
    "--game-number",
    "-n",
    type=str,
    default=None,
    help="Updated game number string (games only).",
)
@click.option(
    "--game-type",
    type=str,
    default=None,
    help="Game type (e.g. 'EX', 'PRE', 'REG', 'PLAYOFF', 'TOURN', 'OTHER') (games only).",
)
@click.option(
    "--scorekeeper-name",
    type=str,
    default=None,
    help="Updated scorekeeper name (games only).",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    default=None,
    help="Updated scorekeeper phone number (games only).",
)
@click.option(
    "--broadcast-provider",
    type=str,
    default=None,
    help="Updated broadcast provider (games only).",
)
@click.option(
    "--timezone",
    type=str,
    default=None,
    help="Timezone for the game (e.g. 'America/New_York') (games only).",
)
@click.option(
    "--future",
    "update_future",
    is_flag=True,
    default=False,
    help="Update this and all future occurrences (events/practices only).",
)
@click.option(
    "--single",
    "update_single",
    is_flag=True,
    default=False,
    help="Update only this single occurrence (events/practices only).",
)
@common_output_options
@columns_option
@click.pass_context
def schedule_update_command(  # noqa: PLR0913
    ctx: Context,
    event_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    event_type: str | None = None,
    title: str | None = None,
    start_date_time: str | None = None,
    end_time: str | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
    duration: str | None = None,
    location_name: str | None = None,
    notes: str | None = None,
    repeat: str | None = None,
    repeat_interval: int = 1,
    repeat_by_day: str | None = None,
    repeat_until: str | None = None,
    rrule: str | None = None,
    team_id: str | None = None,
    season_id: str | None = None,
    division_id: str | None = None,
    opposing_team_id: str | None = None,
    opposing_division: str | None = None,
    association_id: str | None = None,
    league_id: str | None = None,
    home_flag: bool | None = None,
    game_number: str | None = None,
    game_type: str | None = None,
    scorekeeper_name: str | None = None,
    scorekeeper_phone: str | None = None,
    broadcast_provider: str | None = None,
    timezone: str | None = None,
    update_future: bool = False,
    update_single: bool = False,
) -> None:
    """Update a calendar event occurrence, practice, or scheduled game.

    Selected via ``--event-id`` / ``-e`` / ``--id`` or ``GAMESHEET_EVENT_ID``.
    """
    config: Config = ctx.obj
    is_game = (event_type is not None and event_type.lower() == "game") or (
        event_type is None and (isinstance(event_id, int) or str(event_id).isdigit())
    )

    if not is_game:
        validate_update_scope(update_future=update_future, update_single=update_single)

    session = build_authenticated_session(config)

    if is_game:
        result = handle_game_update(
            run_action_or_exit,
            session,
            event_id,
            game_type=game_type,
            start_date_time=start_date_time,
            end_time=end_time,
            start=start,
            end=end,
            date=date,
            duration=duration,
            team_id=team_id,
            season_id=season_id,
            division_id=division_id,
            opposing_team_id=opposing_team_id,
            opposing_division=opposing_division,
            association_id=association_id,
            league_id=league_id,
            home_flag=home_flag,
            game_number=game_number,
            location_name=location_name,
            scorekeeper_name=scorekeeper_name,
            scorekeeper_phone=scorekeeper_phone,
            broadcast_provider=broadcast_provider,
            timezone=timezone,
            timeout=config.timeout,
        )
        render_get_command(result, output_format, output_path, columns_spec)
        return

    run_occurrence_update(
        run_action_or_exit,
        session,
        event_id,
        event_type,
        output_format,
        output_path,
        columns_spec,
        title=title,
        notes=notes,
        location_name=location_name,
        start_date_time=start_date_time,
        end_time=end_time,
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
        timeout=config.timeout,
    )


@schedule_group.command("export")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to export calendar data for.",
)
@click.option(
    "--month",
    type=str,
    default="all",
    show_default=True,
    help="Month filter for calendar events (e.g. 'all', '2026-08').",
)
@common_output_options
@columns_option
@click.pass_context
def schedule_export_command(
    ctx: Context,
    team_id: str,
    month: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """Export schedule and calendar events to JSON or CSV.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    events = run_action_or_exit(
        session,
        _list_schedule_action,
        team_id,
        month=month,
        include_event_data=True,
        timeout=config.timeout,
    )
    render_list_command(
        events,
        output_format,
        output_path,
        columns_spec,
    )


@schedule_group.command(
    "subscribe",
    aliases=("feed", "urls"),
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to get subscription URLs for.",
)
@click.option(
    "--apple-calendar",
    "--apple",
    "apple_calendar",
    is_flag=True,
    default=False,
    help="Output only the Apple Calendar subscription URL.",
)
@click.option(
    "--google-calendar",
    "--google",
    "google_calendar",
    is_flag=True,
    default=False,
    help="Output only the Google Calendar subscription URL.",
)
@click.option(
    "--calendar-url",
    "--url",
    "--webcal",
    "calendar_url",
    is_flag=True,
    default=False,
    help="Output only the generic calendar feed URL.",
)
@common_output_options
@columns_option
@click.pass_context
def schedule_subscribe_command(
    _ctx: Context,
    team_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
    *,
    apple_calendar: bool = False,
    google_calendar: bool = False,
    calendar_url: bool = False,
) -> None:
    """Get calendar subscription URLs for Apple Calendar, Google Calendar, and webcal.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.
    """
    selected_columns: list[str] = []
    parsed_columns = parse_columns_spec(columns_spec)
    if parsed_columns is not None:
        alias_map = {
            "apple_calendar": "appleCalendar",
            "applecalendar": "appleCalendar",
            "apple": "appleCalendar",
            "google": "googleCalendar",
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


# Register sub-groups from separate modules
schedule_group.add_command(events_group)
schedule_group.add_command(games_group)
schedule_group.add_command(practices_group)


__all__ = [
    "schedule_delete_command",
    "schedule_export_command",
    "schedule_get_command",
    "schedule_group",
    "schedule_list_command",
    "schedule_subscribe_command",
    "schedule_update_command",
]
