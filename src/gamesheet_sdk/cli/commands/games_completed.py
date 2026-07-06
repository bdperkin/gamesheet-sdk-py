# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Completed games CLI commands."""

from __future__ import annotations

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
    Game,
    download_completed_game_pdf as _download_completed_game_pdf_action,
    get_completed_game as _get_completed_game_action,
    get_game as _get_game_action,
    list_completed as _list_completed_action,
)


@click.group(
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
