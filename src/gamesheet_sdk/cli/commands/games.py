# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Games command group with nested sub-commands."""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli.core import ResourceGroup
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.games import (
    get_game as _get_game_action,
    list_brackets as _list_brackets_action,
    list_completed as _list_completed_action,
    list_scheduled as _list_scheduled_action,
)


@click.group(
    "games",
    cls=ResourceGroup,
    default="completed",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
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


@games_group.command("get")
@click.option(
    "--game-id",
    type=int,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Game ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
def games_get_command(
    ctx: Context,
    game_id: int,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific game.

    The game ID can be provided via --game-id or the GAMESHEET_GAME_ID environment variable. The season ID is
    inherited from the parent games command. Requires a saved session from `gamesheet-sdk-py login`. The
    output displays game metadata as key-value pairs, with each field on its own row.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: The game identifier
    :type game_id: int
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
    game = run_action_or_exit(session, _get_game_action, season_id, game_id)
    render_get_command(game, output_format, output_path, fields_spec)


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
    type=int,
    envvar="GAMESHEET_GAME_ID",
    required=True,
    help="Game ID to retrieve.",
)
@common_output_options
@click.pass_context
def scheduled_get_command(
    ctx: Context,
    game_id: int,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get detailed information about a scheduled game.

    Delegates to the main games get command.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param game_id: The game identifier
    :type game_id: int
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    game = run_action_or_exit(session, _get_game_action, season_id, game_id)
    render_get_command(game, output_format, output_path)


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
def scheduled_create_command() -> None:
    """Create a new scheduled game.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.games module.

    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    click.secho(
        "Error: games scheduled create is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@scheduled_group.command("update")
def scheduled_update_command() -> None:
    """Update a scheduled game.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.games module.

    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    click.secho(
        "Error: games scheduled update is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@scheduled_group.command("delete")
def scheduled_delete_command() -> None:
    """Delete a scheduled game.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.games module.

    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    click.secho(
        "Error: games scheduled delete is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


# Completed games sub-group
@games_group.group(
    "completed",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def completed_group() -> None:
    """Manage completed games.

    Invoking ``completed`` with no sub-command runs ``list`` by default.
    """


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


@brackets_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def brackets_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all bracket games in the specified season.

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
    games = run_action_or_exit(session, _list_brackets_action, season_id)
    render_list_command(games, output_format, output_path, columns_spec)
