# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Scheduled games CLI commands."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli import constants as cli_constants
from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared import (
    common_output_options,
    get_fields_option,
    get_local_timezone_name,
    get_local_timezone_offset,
    list_columns_option,
    render_get_command,
    render_list_command,
    resolve_create_times,
    resolve_datetime_input,
    resolve_update_times,
    validate_no_input_conflict,
)
from gamesheet_sdk.admin.games import (
    create_scheduled_game as _create_scheduled_game_action,
    delete_scheduled_game as _delete_scheduled_game_action,
    get_scheduled_game as _get_scheduled_game_action,
    list_scheduled as _list_scheduled_action,
    update_scheduled_game as _update_scheduled_game_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.common.config import Config


@click.group(
    "scheduled",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def scheduled_group() -> None:
    """Manage scheduled games.

    Invoking ``scheduled`` with no sub-command runs ``list`` by default.
    """


@scheduled_group.command("get")
@click.option(
    "--game-id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Game ID to retrieve.",
)
@common_output_options
@get_fields_option
@click.pass_context
def scheduled_get_command(
    ctx: Context,
    game_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a scheduled game.

    Uses the JSON:API /api/seasons/{id}/schedule/{game_id} endpoint for richer structured data.\f
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: The game identifier
    :type game_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param fields_spec: Optional comma-separated list of fields to display
    :type fields_spec: str | None
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    game = run_action_or_exit(session, _get_scheduled_game_action, season_id, game_id)
    render_get_command(game, output_format, output_path, fields_spec)


@scheduled_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def scheduled_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all scheduled games in the specified season.

    Requires authentication (run 'gamesheet-admin login' first).\f
    :param ctx: Click context object containing config
    :type ctx: Context
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param columns_spec: Optional comma-separated list of columns to display
    :type columns_spec: str | None
    """
    # Extract config and season_id from context (set by games_group)
    # ctx.obj is always a dict set by games_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(config)
    games = run_action_or_exit(session, _list_scheduled_action, season_id)
    render_list_command(games, output_format, output_path, columns_spec)


@scheduled_group.command("create")
@click.option(
    "--start-datetime",
    type=str,
    default=None,
    help=(
        f"Start date and time. {cli_constants.FLEXIBLE_DATETIME_HELP} "
        "Mutually exclusive with --start-date/--start-time."
    ),
)
@click.option(
    "--end-datetime",
    type=str,
    default=None,
    help=(
        f"End date and time. {cli_constants.FLEXIBLE_DATETIME_HELP} "
        "Mutually exclusive with --end-date/--end-time."
    ),
)
@click.option(
    "--start-date",
    type=str,
    default=None,
    help=f"Start {cli_constants.SPLIT_DATE_HELP} Use with --start-time.",
)
@click.option(
    "--start-time",
    "start_time_str",
    type=str,
    default=None,
    help=f"Start {cli_constants.SPLIT_TIME_HELP} Use with --start-date.",
)
@click.option(
    "--end-date",
    type=str,
    default=None,
    help=f"End {cli_constants.SPLIT_DATE_HELP} Use with --end-time.",
)
@click.option(
    "--end-time",
    "end_time_str",
    type=str,
    default=None,
    help=f"End {cli_constants.SPLIT_TIME_HELP} Use with --end-date.",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help=cli_constants.DURATION_HELP,
)
@click.option(
    "--home-team-id",
    type=str,
    required=True,
    help="Home team identifier.",
)
@click.option(
    "--home-division-id",
    type=str,
    required=True,
    help="Home team division identifier.",
)
@click.option(
    "--visitor-team-id",
    type=str,
    required=True,
    help="Visitor team identifier.",
)
@click.option(
    "--visitor-division-id",
    type=str,
    required=True,
    help="Visitor team division identifier.",
)
@click.option(
    "--location",
    type=str,
    default="",
    help=(
        "Game location/venue (optional). Format: '<location_name> <surface_name>' "
        "(case-insensitive). Validated against API."
    ),
)
@click.option(
    "--scorekeeper-name",
    type=str,
    default="",
    help="Scorekeeper's full name (optional).",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    default="",
    help="Scorekeeper's phone number (optional).",
)
@click.option(
    "--game-type",
    type=str,
    required=True,
    help="Game type. Valid: playoff, exhibition, tournament, regular_season.",
)
@click.option(
    "--time-zone-name",
    type=str,
    default=None,
    help=f"{cli_constants.IANA_TIMEZONE_HELP_TEXT}. Defaults to system timezone.",
)
@click.option(
    "--time-zone-offset",
    type=int,
    default=None,
    help=f"{cli_constants.TIMEZONE_OFFSET_HELP_TEXT}. Defaults to system timezone offset.",
)
@click.option(
    "--number",
    type=str,
    required=True,
    help="Game number.",
)
@click.option(
    "--broadcaster",
    type=str,
    default="",
    help="Broadcast provider key (optional, case-insensitive, e.g., LIVEBARN). Validated against API.",
)
@click.option(
    "--home-label",
    type=str,
    default="",
    help="Home team label override (optional).",
)
@click.option(
    "--visitor-label",
    type=str,
    default="",
    help="Visitor team label override (optional).",
)
@common_output_options
@click.pass_context
# pylint: disable-next=too-many-arguments,too-many-locals,too-many-positional-arguments
def scheduled_create_command(
    ctx: Context,
    start_datetime: str | None,
    end_datetime: str | None,
    start_date: str | None,
    start_time_str: str | None,
    end_date: str | None,
    end_time_str: str | None,
    duration: int | None,
    home_team_id: str,
    home_division_id: str,
    visitor_team_id: str,
    visitor_division_id: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    game_type: str,
    time_zone_name: str | None,
    time_zone_offset: int | None,
    number: str,
    broadcaster: str,
    home_label: str,
    visitor_label: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). Provide any two of
    ``--start-datetime`` (or ``--start-date`` + ``--start-time``), ``--end-datetime``
    (or ``--end-date`` + ``--end-time``), and ``--duration`` to automatically calculate
    the third. If time zone options are not specified, they default to the local system
    timezone.\f

    :param ctx: Click context object containing config
    :type ctx: Context
    :param start_datetime: Start date and time (flexible format)
    :type start_datetime: str | None
    :param end_datetime: End date and time (flexible format)
    :type end_datetime: str | None
    :param start_date: Start date component
    :type start_date: str | None
    :param start_time_str: Start time component
    :type start_time_str: str | None
    :param end_date: End date component
    :type end_date: str | None
    :param end_time_str: End time component
    :type end_time_str: str | None
    :param duration: Game duration in minutes
    :type duration: int | None
    :param home_team_id: Home team identifier
    :type home_team_id: str
    :param home_division_id: Home team division identifier
    :type home_division_id: str
    :param visitor_team_id: Visitor team identifier
    :type visitor_team_id: str
    :param visitor_division_id: Visitor team division identifier
    :type visitor_division_id: str
    :param location: Game location/venue
    :type location: str
    :param scorekeeper_name: Scorekeeper's full name
    :type scorekeeper_name: str
    :param scorekeeper_phone: Scorekeeper's phone number
    :type scorekeeper_phone: str
    :param game_type: Game type
    :type game_type: str
    :param time_zone_name: IANA time zone name (optional, defaults to system)
    :type time_zone_name: str | None
    :param time_zone_offset: Time zone offset in minutes (optional, defaults to system)
    :type time_zone_offset: int | None
    :param number: Game number
    :type number: str
    :param broadcaster: Broadcast provider name
    :type broadcaster: str
    :param home_label: Home team label override
    :type home_label: str
    :param visitor_label: Visitor team label override
    :type visitor_label: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    validate_no_input_conflict(start_datetime, start_date, start_time_str, "start")
    validate_no_input_conflict(end_datetime, end_date, end_time_str, "end")

    start_raw = resolve_datetime_input(
        start_datetime,
        start_date,
        start_time_str,
        "start",
    )
    end_raw = resolve_datetime_input(end_datetime, end_date, end_time_str, "end")

    scheduled_start_time, scheduled_end_time = resolve_create_times(
        start_raw,
        end_raw,
        duration,
    )

    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)

    if time_zone_name is None:
        time_zone_name = get_local_timezone_name()
    if time_zone_offset is None:
        time_zone_offset = get_local_timezone_offset()
    game = run_action_or_exit(
        session,
        _create_scheduled_game_action,
        season_id,
        scheduled_start_time,
        scheduled_end_time,
        home_team_id,
        home_division_id,
        visitor_team_id,
        visitor_division_id,
        location,
        scorekeeper_name,
        scorekeeper_phone,
        game_type,
        time_zone_name,
        time_zone_offset,
        number,
        broadcaster,
        home_label,
        visitor_label,
    )
    render_get_command(game, output_format, output_path)


@scheduled_group.command("update")
@click.option(
    "--game-id",
    type=str,
    required=True,
    help="Game ID to update.",
)
@click.option(
    "--start-datetime",
    type=str,
    default=None,
    help=(
        f"Start date and time. {cli_constants.FLEXIBLE_DATETIME_HELP} "
        "Mutually exclusive with --start-date/--start-time."
    ),
)
@click.option(
    "--end-datetime",
    type=str,
    default=None,
    help=(
        f"End date and time. {cli_constants.FLEXIBLE_DATETIME_HELP} "
        "Mutually exclusive with --end-date/--end-time."
    ),
)
@click.option(
    "--start-date",
    type=str,
    default=None,
    help=f"Start {cli_constants.SPLIT_DATE_HELP} Use with --start-time.",
)
@click.option(
    "--start-time",
    "start_time_str",
    type=str,
    default=None,
    help=f"Start {cli_constants.SPLIT_TIME_HELP} Use with --start-date.",
)
@click.option(
    "--end-date",
    type=str,
    default=None,
    help=f"End {cli_constants.SPLIT_DATE_HELP} Use with --end-time.",
)
@click.option(
    "--end-time",
    "end_time_str",
    type=str,
    default=None,
    help=f"End {cli_constants.SPLIT_TIME_HELP} Use with --end-date.",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help=cli_constants.DURATION_HELP,
)
@click.option(
    "--home-team-id",
    type=str,
    help="Home team identifier.",
)
@click.option(
    "--home-division-id",
    type=str,
    help="Home team division identifier.",
)
@click.option(
    "--visitor-team-id",
    type=str,
    help="Visitor team identifier.",
)
@click.option(
    "--visitor-division-id",
    type=str,
    help="Visitor team division identifier.",
)
@click.option(
    "--location",
    type=str,
    help=(
        "Game location/venue. Format: '<location_name> <surface_name>' "
        "(case-insensitive). Validated against API."
    ),
)
@click.option(
    "--scorekeeper-name",
    type=str,
    help="Scorekeeper's full name.",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    help="Scorekeeper's phone number.",
)
@click.option(
    "--game-type",
    type=str,
    help="Game type. Valid: playoff, exhibition, tournament, regular_season.",
)
@click.option(
    "--time-zone-name",
    type=str,
    help=cli_constants.IANA_TIMEZONE_HELP_TEXT,
)
@click.option(
    "--time-zone-offset",
    type=int,
    help=cli_constants.TIMEZONE_OFFSET_HELP_TEXT,
)
@click.option(
    "--number",
    type=str,
    help="Game number.",
)
@click.option(
    "--broadcaster",
    type=str,
    help="Broadcast provider key (case-insensitive, e.g., LIVEBARN). Validated against API.",
)
@click.option(
    "--home-label",
    type=str,
    help="Home team label override.",
)
@click.option(
    "--visitor-label",
    type=str,
    help="Visitor team label override.",
)
@common_output_options
@click.pass_context
# pylint: disable-next=too-many-arguments,too-many-locals,too-many-positional-arguments
def scheduled_update_command(
    ctx: Context,
    game_id: str,
    start_datetime: str | None,
    end_datetime: str | None,
    start_date: str | None,
    start_time_str: str | None,
    end_date: str | None,
    end_time_str: str | None,
    duration: int | None,
    home_team_id: str | None,
    home_division_id: str | None,
    visitor_team_id: str | None,
    visitor_division_id: str | None,
    location: str | None,
    scorekeeper_name: str | None,
    scorekeeper_phone: str | None,
    game_type: str | None,
    time_zone_name: str | None,
    time_zone_offset: int | None,
    number: str | None,
    broadcaster: str | None,
    home_label: str | None,
    visitor_label: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update a scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). Only specified fields are updated;
    unspecified fields retain their current values. You may provide any combination of
    ``--start-datetime`` (or ``--start-date`` + ``--start-time``), ``--end-datetime``
    (or ``--end-date`` + ``--end-time``), and ``--duration`` to automatically calculate
    missing time fields.\f

    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: Game identifier
    :type game_id: str
    :param start_datetime: Start date and time (flexible format)
    :type start_datetime: str | None
    :param end_datetime: End date and time (flexible format)
    :type end_datetime: str | None
    :param start_date: Start date component
    :type start_date: str | None
    :param start_time_str: Start time component
    :type start_time_str: str | None
    :param end_date: End date component
    :type end_date: str | None
    :param end_time_str: End time component
    :type end_time_str: str | None
    :param duration: Game duration in minutes
    :type duration: int | None
    :param home_team_id: Home team identifier
    :type home_team_id: str | None
    :param home_division_id: Home team division identifier
    :type home_division_id: str | None
    :param visitor_team_id: Visitor team identifier
    :type visitor_team_id: str | None
    :param visitor_division_id: Visitor team division identifier
    :type visitor_division_id: str | None
    :param location: Game location/venue
    :type location: str | None
    :param scorekeeper_name: Scorekeeper's full name
    :type scorekeeper_name: str | None
    :param scorekeeper_phone: Scorekeeper's phone number
    :type scorekeeper_phone: str | None
    :param game_type: Game type
    :type game_type: str | None
    :param time_zone_name: IANA time zone name
    :type time_zone_name: str | None
    :param time_zone_offset: Time zone offset in minutes
    :type time_zone_offset: int | None
    :param number: Game number
    :type number: str | None
    :param broadcaster: Broadcast provider name
    :type broadcaster: str | None
    :param home_label: Home team label override
    :type home_label: str | None
    :param visitor_label: Visitor team label override
    :type visitor_label: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    validate_no_input_conflict(start_datetime, start_date, start_time_str, "start")
    validate_no_input_conflict(end_datetime, end_date, end_time_str, "end")

    start_raw = resolve_datetime_input(
        start_datetime,
        start_date,
        start_time_str,
        "start",
    )
    end_raw = resolve_datetime_input(end_datetime, end_date, end_time_str, "end")

    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    current_game = run_action_or_exit(
        session,
        _get_scheduled_game_action,
        season_id,
        game_id,
    )
    attrs = current_game.data.attributes
    rels = current_game.data.relationships

    scheduled_start_time, scheduled_end_time = resolve_update_times(
        start_raw,
        end_raw,
        duration,
        attrs.scheduled_start_time,
        attrs.scheduled_end_time,
    )

    updated_game = run_action_or_exit(
        session,
        _update_scheduled_game_action,
        season_id,
        game_id,
        scheduled_start_time,
        scheduled_end_time,
        home_team_id or rels.home_team.data.id,
        home_division_id or rels.home_division.data.id,
        visitor_team_id or rels.visitor_team.data.id,
        visitor_division_id or rels.visitor_division.data.id,
        location or attrs.location,
        scorekeeper_name or attrs.scorekeeper.name,
        scorekeeper_phone or attrs.scorekeeper.phone,
        game_type or attrs.game_type,
        time_zone_name or attrs.time_zone_name,
        time_zone_offset if time_zone_offset is not None else -240,
        number or attrs.number,
        attrs.status,
        broadcaster if broadcaster is not None else attrs.data.broadcaster,
        home_label if home_label is not None else attrs.data.home_label,
        visitor_label if visitor_label is not None else attrs.data.visitor_label,
    )
    render_get_command(updated_game, output_format, output_path)


@scheduled_group.command("delete")
@click.option(
    "--game-id",
    type=str,
    required=True,
    help="Game ID to delete.",
)
@confirm_destructive("this scheduled game")
@click.pass_context
def scheduled_delete_command(
    ctx: Context,
    game_id: str,
) -> None:
    """Delete a scheduled game.

    Requires authentication (run 'gamesheet-admin login' first). This operation is destructive and requires
    confirmation unless --force is specified.\f
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: Game identifier
    :type game_id: str
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    run_action_or_exit(session, _delete_scheduled_game_action, season_id, game_id)
    click.secho(f"Successfully deleted scheduled game {game_id}", fg="green")
