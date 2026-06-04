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

import click

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

    This command group provides operations for interacting with leagues in the GameSheet platform. A league
    represents a subdivision of an association, typically organized by division, age group, or skill level.

    Invoking ``leagues`` with no sub-command runs ``list`` by default.

    :returns: None. This is a Click group command that serves as a container for sub-commands.
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
    type=click.Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=click.Path(dir_okay=False, writable=True),
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
    ctx: click.Context,
    association_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all leagues in the specified association.

    Requires a saved session from ``gamesheet-sdk-py login`` -- the bearer token is read out of the browser
    storage state on disk and attached to the HTTP request. No browser is launched.

    The command retrieves all leagues belonging to the specified association and renders them in the
    specified output format. The association ID can be provided via the ``--association-id`` option or the
    ``GAMESHEET_ASSOCIATION_ID`` environment variable. By default, output is written to stdout in simple
    table format, but can be redirected to a file and rendered in various data or human-readable formats.

    :param ctx: Click context object containing the application :class:`~gamesheet_sdk.config.Config` in
        ``ctx.obj``.
    :param association_id: Association ID to list leagues for. Can be provided via CLI option or
        ``GAMESHEET_ASSOCIATION_ID`` environment variable.
    :param output_format: Output format name (json, yaml, csv, tsv, or any tabulate format like simple, grid,
        etc.). Defaults to ``simple``.
    :param output_path: Optional file path to write output. If ``None``, writes to stdout.
    :param columns_spec: Optional comma-separated list of column names to include in output (e.g.,
        ``"id,name,season_count"``). If ``None``, includes all columns returned by the API.
    :returns: None. Writes formatted output to stdout or the specified file.
    :raises click.exceptions.Exit: If no saved session exists (exit code 1), authentication fails, the
        association ID is not provided, or the API returns an error.

    Examples:
        List all leagues in an association in default format::

            $ gamesheet-sdk-py leagues list --association-id ABC123

        List leagues in JSON format::

            $ gamesheet-sdk-py leagues list --association-id ABC123 --format json

        List leagues with only id and name columns::

            $ gamesheet-sdk-py leagues list --association-id ABC123 --columns id,name

        Save leagues to a YAML file::

            $ gamesheet-sdk-py leagues list --association-id ABC123 --format yaml --output leagues.yaml

        Use environment variable for association ID::

            $ export GAMESHEET_ASSOCIATION_ID=ABC123
            $ gamesheet-sdk-py leagues list
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    leagues = run_action_or_exit(session, _list_leagues_action, association_id)
    rows = [league.model_dump(mode="json") for league in leagues]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
