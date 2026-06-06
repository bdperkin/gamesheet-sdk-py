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

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.leagues import list_leagues as _list_leagues_action
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output


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
    level.

    Invoking 'leagues' with no sub-command runs 'list' by default.
    """


@leagues_group.command("list")
@click.option(
    "--association-id",
    type=str,
    envvar="GAMESHEET_ASSOCIATION_ID",
    required=True,
    help="Association ID to list leagues for.",
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
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
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
    rows = [league.model_dump(mode="json") for league in leagues]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
