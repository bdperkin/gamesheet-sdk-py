# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Scheduled games CLI commands for GameSheet teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.core import (
    ResourceGroup,
)
from gamesheet_sdk.common.cli.datetime_helpers import (
    get_local_timezone_name,
    get_local_timezone_offset,
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
    resolve_game_update_times,
    resolve_schedule_create_times,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.schedule import (
    _fetch_and_normalize_game_dict,
    validate_game_type,
)
from gamesheet_sdk.teams.schedule import (
    create_game as _create_game_action,
)
from gamesheet_sdk.teams.schedule import (
    delete_game as _delete_game_action,
)
from gamesheet_sdk.teams.schedule import (
    get_game as _get_game_action,
)
from gamesheet_sdk.teams.schedule import (
    list_games as _list_games_action,
)
from gamesheet_sdk.teams.schedule import (
    update_game as _update_game_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "games",
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
def games_group() -> None:
    """Manage scheduled games.

    Invoking ``games`` with no sub-command runs ``list`` by default.
    """


@games_group.command(
    "create",
    aliases=("add", "new"),
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Home team ID.",
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID for the game.",
)
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID for the team.",
)
@click.option(
    "--opposing-team-id",
    type=str,
    required=True,
    help="Opposing team ID.",
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
    help="End time (e.g. '13:15' or '1:15 PM').",
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
    help="Game date (e.g. '2026-08-20').",
)
@click.option(
    "--duration",
    type=str,
    default=None,
    help="Game duration (e.g. '1h15m', '75m').",
)
@click.option(
    "--home/--visitor",
    "home_flag",
    default=True,
    show_default=True,
    help="Whether this team is the home team.",
)
@click.option(
    "--opposing-division-id",
    "--opposing-division",
    "opposing_division",
    type=str,
    default=None,
    help="Opposing division ID (defaults to division-id).",
)
@click.option(
    "--association-id",
    type=str,
    default="0",
    show_default=True,
    help="Association ID.",
)
@click.option(
    "--league-id",
    type=str,
    default="0",
    show_default=True,
    help="League ID.",
)
@click.option(
    "--game-number",
    "--number",
    "game_number",
    type=str,
    default="",
    help="Game number / identifier.",
)
@click.option(
    "--game-type",
    type=str,
    default="regular_season",
    show_default=True,
    help="Game type (e.g. regular_season, playoff, exhibition, tournament).",
)
@click.option(
    "--location",
    type=str,
    default="",
    help="Game venue or location.",
)
@click.option(
    "--scorekeeper-name",
    type=str,
    default="",
    help="Scorekeeper full name.",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    default="",
    help="Scorekeeper phone number.",
)
@click.option(
    "--broadcast-provider",
    "--broadcaster",
    "broadcast_provider",
    type=str,
    default="",
    help="Broadcast provider identifier.",
)
@click.option(
    "--time-zone-name",
    "--timezone",
    "timezone",
    type=str,
    default=None,
    help="Timezone name (defaults to local timezone).",
)
@click.option(
    "--time-zone-offset",
    type=int,
    default=None,
    help="Timezone offset in minutes.",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_create_command(  # noqa: PLR0913
    ctx: Context,
    *,
    team_id: str,
    season_id: str,
    division_id: str,
    opposing_team_id: str,
    start_date_time: str | None,
    end_time: str | None,
    start: str | None,
    end: str | None,
    date: str | None,
    duration: str | None,
    home_flag: bool,
    opposing_division: str | None,
    association_id: str,
    league_id: str,
    game_number: str,
    game_type: str,
    location: str,
    scorekeeper_name: str,
    scorekeeper_phone: str,
    broadcast_provider: str,
    timezone: str | None,
    time_zone_offset: int | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Create a new scheduled game.

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
        all_day=False,
        is_practice=False,
    )

    tz_name = timezone if timezone is not None else get_local_timezone_name()
    tz_offset = time_zone_offset if time_zone_offset is not None else get_local_timezone_offset()

    session = build_authenticated_session(config)
    created = run_action_or_exit(
        session,
        _create_game_action,
        team_id,
        season_id,
        division_id,
        opposing_team_id,
        resolved_start_dt,
        resolved_end_time,
        home_flag=home_flag,
        opposing_division=opposing_division,
        association_id=association_id,
        league_id=league_id,
        game_number=game_number,
        game_type=game_type,
        location=location,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        timeout=config.timeout,
    )
    render_get_command(created, output_format, output_path, fields_spec)


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
    include_event_data: bool,
) -> None:
    """List scheduled games for a team.

    Selected via ``--team-id`` / ``-t`` or the ``GAMESHEET_TEAM_ID`` environment variable.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    games = run_action_or_exit(
        session,
        _list_games_action,
        team_id,
        month=month,
        include_event_data=include_event_data,
        timeout=config.timeout,
    )
    render_list_command(
        games,
        output_format,
        output_path,
        columns_spec,
    )


@games_group.command("get")
@click.option(
    "--game-id",
    "-g",
    "--id",
    "game_id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Scheduled game identifier.",
)
@click.option(
    "--availability",
    "--include-availability",
    "include_availability",
    is_flag=True,
    default=False,
    help="Include player/coach availability for the game.",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    default=None,
    help="Team ID (required when fetching availability if not present in game).",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_get_command(
    ctx: Context,
    game_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    include_availability: bool,
    team_id: str | None,
) -> None:
    """Show details for a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game_detail = run_action_or_exit(
        session,
        _get_game_action,
        game_id,
        include_availability=include_availability,
        team_id=team_id,
        timeout=config.timeout,
    )
    render_get_command(game_detail, output_format, output_path, fields_spec)


@games_group.command(
    "delete",
    aliases=("del", "rm", "remove"),
)
@click.option(
    "--game-id",
    "-g",
    "--id",
    "game_id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Scheduled game identifier.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompts.",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_delete_command(
    ctx: Context,
    game_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
    *,
    force: bool = False,
) -> None:
    """Delete a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``.
    """
    config: Config = ctx.obj
    confirm_delete_or_abort("game", game_id, force=force)

    session = build_authenticated_session(config)
    result = run_action_or_exit(
        session,
        _delete_game_action,
        game_id,
        timeout=config.timeout,
    )
    if output_format in {"json", "yaml"}:
        render_get_command(result, output_format, output_path, fields_spec)
    else:
        click.echo(f"Successfully deleted game {game_id}")


@games_group.command(
    "update",
    aliases=("set", "edit"),
)
@click.option(
    "--game-id",
    "-g",
    "--id",
    "game_id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Identifier of the scheduled game to update.",
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
    help="End time (e.g. '13:15' or '1:15 PM').",
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
    help="Game date (e.g. '2026-08-20').",
)
@click.option(
    "--duration",
    type=str,
    default=None,
    help="Game duration (e.g. '1h15m', '75m').",
)
@click.option(
    "--team-id",
    "-t",
    type=str,
    default=None,
    help="Home team ID.",
)
@click.option(
    "--season-id",
    type=str,
    default=None,
    help="Season ID.",
)
@click.option(
    "--division-id",
    type=str,
    default=None,
    help="Division ID.",
)
@click.option(
    "--opposing-team-id",
    type=str,
    default=None,
    help="Opposing team ID.",
)
@click.option(
    "--opposing-division",
    type=str,
    default=None,
    help="Opposing division ID.",
)
@click.option(
    "--association-id",
    type=str,
    default=None,
    help="Association ID.",
)
@click.option(
    "--league-id",
    type=str,
    default=None,
    help="League ID.",
)
@click.option(
    "--home/--away",
    "home_flag",
    default=None,
    help="Whether this team is the home team.",
)
@click.option(
    "--game-number",
    type=str,
    default=None,
    help="Game number / identifier.",
)
@click.option(
    "--game-type",
    type=str,
    default=None,
    help="Game type (e.g. regular_season, playoff, exhibition, tournament).",
)
@click.option(
    "--location",
    type=str,
    default=None,
    help="Game venue or location.",
)
@click.option(
    "--scorekeeper-name",
    type=str,
    default=None,
    help="Scorekeeper full name.",
)
@click.option(
    "--scorekeeper-phone",
    type=str,
    default=None,
    help="Scorekeeper phone number.",
)
@click.option(
    "--broadcast-provider",
    type=str,
    default=None,
    help="Broadcast provider identifier.",
)
@click.option(
    "--timezone",
    type=str,
    default=None,
    help="Timezone name (defaults to local timezone).",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_update_command(  # noqa: PLR0913
    ctx: Context,
    game_id: str,
    *,
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
    game_type: str | None,
    location: str | None,
    scorekeeper_name: str | None,
    scorekeeper_phone: str | None,
    broadcast_provider: str | None,
    timezone: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Update a scheduled game.

    Selected via ``--game-id`` / ``-g`` / ``--id`` or ``GAMESHEET_GAME_ID``.
    """
    config: Config = ctx.obj
    if game_type is not None:
        validate_game_type(game_type)

    session = build_authenticated_session(config)
    game_dict = run_action_or_exit(
        session,
        _fetch_and_normalize_game_dict,
        game_id,
        timeout=config.timeout,
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

    raw_tid = game_dict.get("team_id") or game_dict.get("teamId")
    effective_team_id = (
        int(team_id) if team_id is not None else (int(raw_tid) if raw_tid is not None else None)
    )

    result = run_action_or_exit(
        session,
        _update_game_action,
        game_id,
        team_id=effective_team_id,
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
        location=location,
        scorekeeper_name=scorekeeper_name,
        scorekeeper_phone=scorekeeper_phone,
        broadcast_provider=broadcast_provider,
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        timeout=config.timeout,
    )
    render_get_command(result, output_format, output_path, fields_spec)


__all__ = [
    "games_create_command",
    "games_delete_command",
    "games_get_command",
    "games_group",
    "games_list_command",
    "games_update_command",
]
