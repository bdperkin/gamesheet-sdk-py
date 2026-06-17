"""Leagues command group.

This module provides the CLI interface for managing GameSheet leagues, which represent organizational
units within an association. A league typically corresponds to a specific division, age group, or
competition tier within the broader association structure.
The command group provides sub-commands for listing leagues within a specified association. When invoked
without a sub-command, it defaults to the ``list`` operation.
Examples:
    List all leagues in an association in simple table format::
        $ gamesheet-sdk-py leagues --association-id ABC123
    List leagues in JSON format::
        $ gamesheet-sdk-py leagues list --association-id ABC123 --format json
    List leagues with selected columns only::
        $ gamesheet-sdk-py leagues list --association-id ABC123 --columns id,name,season_count
    Save leagues to a file::
        $ gamesheet-sdk-py leagues list --association-id ABC123 --format yaml --output leagues.yaml
    Use environment variable for association ID::
        $ export GAMESHEET_ASSOCIATION_ID=ABC123
        $ gamesheet-sdk-py leagues
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click

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
from gamesheet_sdk.leagues import get_league as _get_league_action
from gamesheet_sdk.leagues import list_leagues as _list_leagues_action

if TYPE_CHECKING:
    from rich_click import Context


@click.group(
    "leagues",
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
def leagues_group() -> None:
    """Manage GameSheet leagues within an association.

    A league represents a subdivision of an association, typically organized by division, age group, or skill
    level. Invoking 'leagues' with no sub-command runs 'list' by default.
    """


@leagues_group.command("get")
@click.option(
    "--association-id",
    type=str,
    envvar="GAMESHEET_ASSOCIATION_ID",
    required=True,
    help="Association ID containing the league.",
)
@click.option(
    "--league-id",
    type=str,
    envvar="GAMESHEET_LEAGUE_ID",
    required=True,
    help="League ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def leagues_get_command(
    ctx: Context,
    association_id: str,
    league_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific league.

    The league and association IDs can be provided via command-line options or environment variables
    (GAMESHEET_LEAGUE_ID, GAMESHEET_ASSOCIATION_ID). Requires a saved session from `gamesheet-sdk-py login`.
    The output displays league metadata as key-value pairs, with each field on its own row.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    league = run_action_or_exit(session, _get_league_action, association_id, league_id)
    render_get_command(league, output_format, output_path, fields_spec)


@leagues_group.command("list")
@click.option(
    "--association-id",
    type=str,
    envvar="GAMESHEET_ASSOCIATION_ID",
    required=True,
    help="Association ID to list leagues for.",
)
@common_output_options
@list_columns_option
@click.pass_context
def leagues_list_command(
    ctx: Context,
    association_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all leagues in the specified association.

    Requires authentication (run 'gamesheet-sdk-py login' first). Retrieves all
    leagues belonging to the specified association and displays them in the
    specified output format.
    The association ID can be provided via --association-id or the
    GAMESHEET_ASSOCIATION_ID environment variable.
    Examples:
        List all leagues in an association in default format:
            $ gamesheet-sdk-py leagues list --association-id ABC123
        List leagues in JSON format:
            $ gamesheet-sdk-py leagues list --association-id ABC123 --format json
        List leagues with only id and name columns:
            $ gamesheet-sdk-py leagues list --association-id ABC123 --columns id,name
        Save leagues to a YAML file:
            $ gamesheet-sdk-py leagues list --association-id ABC123 --format yaml --output leagues.yaml
        Use environment variable for association ID:
            $ export GAMESHEET_ASSOCIATION_ID=ABC123
            $ gamesheet-sdk-py leagues list
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    leagues = run_action_or_exit(session, _list_leagues_action, association_id)
    render_list_command(leagues, output_format, output_path, columns_spec)
