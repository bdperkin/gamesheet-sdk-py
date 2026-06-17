"""Roster command group with nested sub-commands."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import (
    ResourceGroup,
    confirm_destructive,
    parse_columns_spec,
)
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.roster import get_coach as _get_coach_action
from gamesheet_sdk.roster import get_player as _get_player_action
from gamesheet_sdk.roster import list_coaches as _list_coaches_action
from gamesheet_sdk.roster import list_players as _list_players_action


@click.group(
    "roster",
    cls=ResourceGroup,
    default="players",
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
    help="Season ID to manage roster for.",
)
@click.pass_context
def roster_group(ctx: Context, season_id: str) -> None:
    """Manage roster (players and coaches) within a season.

    Invoking ``roster`` with no sub-command runs ``players`` by default. The --season-id option is required
    and applies to all sub-commands.
    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Players sub-group
@roster_group.group(
    "players",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def players_group() -> None:
    """Manage players.

    Invoking ``players`` with no sub-command runs ``list`` by default.
    """


@players_group.command("get")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to retrieve details for.",
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
def players_get_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific player.

    The player ID can be provided via --player-id or the GAMESHEET_PLAYER_ID environment variable. The season
    ID is inherited from the parent roster command. Requires a saved session from `gamesheet-sdk-py login`.
    The output displays player metadata as key-value pairs, with each field on its own row.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    data = run_action_or_exit(
        session,
        _get_player_action,
        season_id,
        player_id,
    ).model_dump(mode="json")
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


@players_group.command("list")
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
def players_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all players in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    # Extract config and season_id from context (set by roster_group)
    # ctx.obj is always a dict set by roster_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(ctx, config)
    players = run_action_or_exit(session, _list_players_action, season_id)
    rows = [player.model_dump(mode="json") for player in players]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@players_group.command("create")
def players_create_command() -> None:
    """Create a new player.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster players create is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@players_group.command("update")
def players_update_command() -> None:
    """Update a player.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster players update is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@players_group.command("delete")
@confirm_destructive("player")
def players_delete_command() -> None:
    """Delete a player.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster players delete is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@players_group.command("penalty-report")
def players_penalty_report_command() -> None:
    """Get penalty report for a player.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster players penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


# Coaches sub-group
@roster_group.group(
    "coaches",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def coaches_group() -> None:
    """Manage coaches.

    Invoking ``coaches`` with no sub-command runs ``list`` by default.
    """


@coaches_group.command("get")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to retrieve details for.",
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
def coaches_get_command(
    ctx: Context,
    coach_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific coach.

    The coach ID can be provided via --coach-id or the GAMESHEET_COACH_ID environment variable. The season ID
    is inherited from the parent roster command. Requires a saved session from `gamesheet-sdk-py login`. The
    output displays coach metadata as key-value pairs, with each field on its own row.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    data = run_action_or_exit(
        session,
        _get_coach_action,
        season_id,
        coach_id,
    ).model_dump(mode="json")
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


@coaches_group.command("list")
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
def coaches_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all coaches in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    # Extract config and season_id from context (set by roster_group)
    # ctx.obj is always a dict set by roster_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(ctx, config)
    coaches = run_action_or_exit(session, _list_coaches_action, season_id)
    rows = [coach.model_dump(mode="json") for coach in coaches]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@coaches_group.command("create")
def coaches_create_command() -> None:
    """Create a new coach.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster coaches create is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@coaches_group.command("update")
def coaches_update_command() -> None:
    """Update a coach.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster coaches update is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@coaches_group.command("delete")
@confirm_destructive("coach")
def coaches_delete_command() -> None:
    """Delete a coach.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster coaches delete is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@coaches_group.command("penalty-report")
def coaches_penalty_report_command() -> None:
    """Get penalty report for a coach.

    NOT YET IMPLEMENTED - Backend function needs to be added to gamesheet_sdk.roster module.
    """
    click.secho(
        "Error: roster coaches penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)
