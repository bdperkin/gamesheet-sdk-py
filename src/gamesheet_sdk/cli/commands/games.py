# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Games command group with nested sub-commands."""

from __future__ import annotations

import logging

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli import constants as cli_constants
from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.constants import DEFAULT_TIMEZONE
from gamesheet_sdk.games import (
    Game,
    create_scheduled_game as _create_scheduled_game_action,
    delete_scheduled_game as _delete_scheduled_game_action,
    download_completed_game_pdf as _download_completed_game_pdf_action,
    get_completed_game as _get_completed_game_action,
    get_game as _get_game_action,
    get_scheduled_game as _get_scheduled_game_action,
    list_completed as _list_completed_action,
    list_scheduled as _list_scheduled_action,
    update_scheduled_game as _update_scheduled_game_action,
)

_LOGGER = logging.getLogger(__name__)


def _get_local_timezone_name() -> str:
    """Get the local system timezone name (IANA format).

    Returns the timezone name like 'America/New_York', 'UTC', etc. Falls back to 'UTC' if unable to determine.

    :returns: IANA timezone name
    :rtype: str
    """
    try:
        # Try to get timezone using tzlocal library if available
        try:
            import tzlocal

            tz = tzlocal.get_localzone()
        except (ImportError, AttributeError):
            pass
        else:
            return str(tz.key) if hasattr(tz, "key") else str(tz)
        # Fallback: try to read /etc/localtime symlink on Unix systems
        import os
        from pathlib import Path

        if os.name != "nt":  # Unix-like systems
            localtime = Path("/etc/localtime")
            if localtime.is_symlink():
                target = os.readlink(localtime)
                # Extract timezone name from path like /usr/share/zoneinfo/America/New_York
                if "zoneinfo/" in target:
                    return target.split("zoneinfo/", 1)[1]
    except (OSError, ValueError, IndexError) as exc:
        _LOGGER.debug("Failed to detect timezone, falling back to %s: %s", DEFAULT_TIMEZONE, exc)
    # Default fallback
    return DEFAULT_TIMEZONE


def _get_local_timezone_offset() -> int:
    """Get the local timezone offset in minutes from UTC.

    Returns the offset as a signed integer (negative for west of UTC, positive for east). For example, EDT
    (UTC-4) returns -240, IST (UTC+5:30) returns 330.

    :returns: Timezone offset in minutes
    :rtype: int
    """
    import time

    # Get the current UTC offset in seconds, then convert to minutes
    # time.timezone is offset for standard time, time.altzone for DST
    if time.daylight and time.localtime().tm_isdst:
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone
    return offset_seconds // 60


@click.group(
    "games",
    cls=ResourceGroup,
    default="completed",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to manage games for.",
)
@click.pass_context
def games_group(ctx: Context, season_id: str) -> None:
    """Manage games within a season.

    Invoking ``games`` with no sub-command runs ``completed`` by default. The --season-id option is required
    and applies to all sub-commands.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Scheduled games sub-group
@games_group.group(
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

    Uses the JSON:API /api/seasons/{id}/schedule/{game_id} endpoint for richer structured data.
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

    Requires authentication (run 'gamesheet-sdk-py login' first).
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
    "--scheduled-start-time",
    type=str,
    required=True,
    help=f"Scheduled start time. {cli_constants.ISO_8601_HELP_TEXT}",
)
@click.option(
    "--scheduled-end-time",
    type=str,
    required=True,
    help=f"Scheduled end time. {cli_constants.ISO_8601_HELP_TEXT}",
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
# pylint: disable-next=too-many-positional-arguments
def scheduled_create_command(
    ctx: Context,
    scheduled_start_time: str,
    scheduled_end_time: str,
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

    Requires authentication (run 'gamesheet-sdk-py login' first). If time zone options are not
    specified, they default to the local system timezone.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param scheduled_start_time: Scheduled start time (ISO 8601 format)
    :type scheduled_start_time: str
    :param scheduled_end_time: Scheduled end time (ISO 8601 format)
    :type scheduled_end_time: str
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
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)

    # Use system timezone if not specified
    if time_zone_name is None:
        time_zone_name = _get_local_timezone_name()
    if time_zone_offset is None:
        time_zone_offset = _get_local_timezone_offset()
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
    "--scheduled-start-time",
    type=str,
    help=f"Scheduled start time. {cli_constants.ISO_8601_HELP_TEXT}",
)
@click.option(
    "--scheduled-end-time",
    type=str,
    help=f"Scheduled end time. {cli_constants.ISO_8601_HELP_TEXT}",
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
# pylint: disable-next=too-many-positional-arguments
def scheduled_update_command(  # noqa: R701
    ctx: Context,
    game_id: str,
    scheduled_start_time: str | None,
    scheduled_end_time: str | None,
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

    Requires authentication (run 'gamesheet-sdk-py login' first). Only specified fields are updated;
    unspecified fields retain their current values.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: Game identifier
    :type game_id: str
    :param scheduled_start_time: Scheduled start time
    :type scheduled_start_time: str | None
    :param scheduled_end_time: Scheduled end time
    :type scheduled_end_time: str | None
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
    updated_game = run_action_or_exit(
        session,
        _update_scheduled_game_action,
        season_id,
        game_id,
        scheduled_start_time or attrs.scheduled_start_time,
        scheduled_end_time or attrs.scheduled_end_time,
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
        attrs.status,  # Status is not editable via CLI - always use current value
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

    Requires authentication (run 'gamesheet-sdk-py login' first). This operation is destructive and requires
    confirmation unless --force is specified.
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


# Completed games sub-group
@games_group.group(
    "completed",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
        "get": ("show", "view"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def completed_group() -> None:
    """Manage completed games.

    Invoking ``completed`` with no sub-command runs ``list`` by default.
    """


@completed_group.command("get")
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
def completed_get_command(
    ctx: Context,
    game_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a completed game.

    Returns full game details including rosters, goals, shots, penalties, and statistics.
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
    game = run_action_or_exit(session, _get_completed_game_action, season_id, game_id)
    render_get_command(game, output_format, output_path, fields_spec)


@completed_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def completed_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all completed games in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
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
    games = run_action_or_exit(session, _list_completed_action, season_id)
    render_list_command(games, output_format, output_path, columns_spec)


def _build_scoresheet_filename(game: Game) -> str:
    """Build a descriptive filename for a scoresheet PDF from game data.

    Format: {date}-scoresheet-{id}-{visitor}-vs-{home}-{game_number}.pdf
    All text is converted to lowercase and spaces/special chars are replaced with underscores.

    :param game: The game object with details
    :type game: Game
    :returns: A filesystem-safe filename
    :rtype: str
    """

    def sanitize(text: str | None) -> str:
        """Convert text to lowercase and replace spaces/special chars with underscores."""
        if not text:
            return "unknown"
        # Convert to lowercase, replace spaces/special chars with underscores,
        # collapse multiple underscores, and strip leading/trailing underscores
        import re

        return re.sub(r"_+", "_", re.sub(r"[^\w\-]", "_", text.lower())).strip("_")

    date = game.date
    game_id = game.id
    visitor_title = sanitize(game.visitor.title)
    visitor_division = sanitize(game.visitor.division_title)
    home_title = sanitize(game.home.title)
    home_division = sanitize(game.home.division_title)
    game_number = sanitize(game.game_number)
    return (
        f"{date}-scoresheet-{game_id}-{visitor_title}-{visitor_division}-vs-"
        f"{home_title}-{home_division}-{game_number}.pdf"
    )


@completed_group.command("download")
@click.option(
    "--game-id",
    type=str,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Game ID to download scoresheet for.",
)
@click.option(
    "--output-path",
    "-o",
    type=str,
    help=(
        "File path where the PDF scoresheet will be saved. "
        "If not specified, generates a filename from game details."
    ),
)
@click.pass_context
def completed_download_command(
    ctx: Context,
    game_id: str,
    output_path: str | None,
) -> None:
    """Download the PDF scoresheet for a completed game.

    Requires authentication (run 'gamesheet-sdk-py login' first). If --output-path is not specified,
    the filename is automatically generated from game details in the format:
    {date}-scoresheet-{id}-{visitor}-vs-{home}-{game_number}.pdf
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: The game identifier
    :type game_id: str
    :param output_path: File path where the PDF will be saved (optional)
    :type output_path: str | None
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)

    # If no output path specified, generate one from game details
    if output_path is None:
        game = run_action_or_exit(session, _get_game_action, season_id, int(game_id))
        output_path = _build_scoresheet_filename(game)

    run_action_or_exit(
        session,
        _download_completed_game_pdf_action,
        game_id,
        output_path,
    )
    click.secho(f"Successfully downloaded scoresheet to {output_path}", fg="green")


# Brackets games sub-group
@games_group.group(
    "brackets",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def brackets_group() -> None:
    """Manage bracket games.

    Invoking ``brackets`` with no sub-command runs ``list`` by default.
    """


@brackets_group.command("list", aliases=["ls"])
@list_columns_option
@common_output_options
def brackets_list_command(
    # pylint: disable-next=unused-argument
    output_format: str,  # noqa: U100
    # pylint: disable-next=unused-argument
    output_path: str | None,  # noqa: U100
    # pylint: disable-next=unused-argument
    columns_spec: str | None,  # noqa: U100
) -> None:
    """List all bracket games in the specified season.

    NOT YET IMPLEMENTED - Bracket games support is planned for a future release.

    :param output_format: Output format (ignored - command not implemented).
    :type output_format: str
    :param output_path: Output file path (ignored - command not implemented).
    :type output_path: str | None
    :param columns_spec: Columns specification (ignored - command not implemented).
    :type columns_spec: str | None
    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    click.secho(
        "Error: games brackets list is not yet implemented. "
        "Bracket games support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)
