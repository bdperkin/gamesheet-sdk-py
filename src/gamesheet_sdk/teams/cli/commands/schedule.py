# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Schedule CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.cli.decorators import (
    common_output_options,
    list_columns_option,
)
from gamesheet_sdk.common.cli.rendering import render_list_command
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
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
        "list": ("ls",),
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


@click.group(
    "events",
    cls=ResourceGroup,
    default="list",
    aliases={
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


@click.group(
    "games",
    cls=ResourceGroup,
    default="list",
    aliases={
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


@click.group(
    "practices",
    cls=ResourceGroup,
    default="list",
    aliases={
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


@schedule_group.command("subscribe")
def schedule_subscribe_command() -> None:
    r"""Subscribe to team calendar.

    Generate calendar subscription feed URL.\f

    NOT YET IMPLEMENTED - Calendar subscription support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: schedule subscribe is not yet implemented. "
        "Calendar subscription support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


schedule_group.add_command(events_group)
schedule_group.add_command(games_group)
schedule_group.add_command(practices_group)
