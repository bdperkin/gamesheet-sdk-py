"""Games command group with nested sub-commands."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.games import get_game as _get_game_action
from gamesheet_sdk.games import list_brackets as _list_brackets_action
from gamesheet_sdk.games import list_completed as _list_completed_action
from gamesheet_sdk.games import list_scheduled as _list_scheduled_action
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output


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
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--fields",
    "-f",
    "fields_spec",
    default=None,
    help=("Comma-separated list of field names to include (default: all fields the API returns)."),
)
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
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    data = run_action_or_exit(session, _get_game_action, season_id, game_id).model_dump(
        mode="json",
    )
    # If fields are specified, filter to only those fields
    if fields_spec:
        fields = parse_columns_spec(fields_spec)
        if fields:
            data = {k: v for k, v in data.items() if k in fields}
    # For tabular formats, convert to a list of key-value rows
    if output_format not in ("json", "yaml"):
        rows = [{"field": k, "value": v} for k, v in data.items()]
        rendered = render(rows, fmt=output_format, columns=None)
    else:
        # For data formats, output the whole object
        rendered = render([data], fmt=output_format, columns=None)
    write_output(rendered, output_path, fmt=output_format)


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
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def scheduled_get_command(
    ctx: Context,
    game_id: int,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get detailed information about a scheduled game.

    Delegates to the main games get command.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(ctx, config)
    data = run_action_or_exit(session, _get_game_action, season_id, game_id).model_dump(mode="json")
    if output_format not in ("json", "yaml"):
        rows = [{"field": k, "value": v} for k, v in data.items()]
        rendered = render(rows, fmt=output_format, columns=None)
    else:
        rendered = render([data], fmt=output_format, columns=None)
    write_output(rendered, output_path, fmt=output_format)


@scheduled_group.command("list")
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def scheduled_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all scheduled games in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    # Extract config and season_id from context (set by games_group)
    # ctx.obj is always a dict set by games_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(ctx, config)
    games = run_action_or_exit(session, _list_scheduled_action, season_id)
    rows = [game.model_dump(mode="json") for game in games]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@scheduled_group.command("create")
def scheduled_create_command() -> None:
    """Create a new scheduled game.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.games module.
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
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def completed_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all completed games in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    # Extract config and season_id from context (set by games_group)
    # ctx.obj is always a dict set by games_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(ctx, config)
    games = run_action_or_exit(session, _list_completed_action, season_id)
    rows = [game.model_dump(mode="json") for game in games]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


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
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def brackets_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all bracket games in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    # Extract config and season_id from context (set by games_group)
    # ctx.obj is always a dict set by games_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(ctx, config)
    games = run_action_or_exit(session, _list_brackets_action, season_id)
    rows = [game.model_dump(mode="json") for game in games]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
