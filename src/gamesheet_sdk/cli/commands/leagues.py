"""Leagues command group."""

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
    """Manage leagues within an association.

    Invoking ``leagues`` with no sub-command runs ``list`` by default.
    """


@leagues_group.command("list")
@click.argument("association-id", type=str, metavar="ASSOCIATION_ID")
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
    """List the leagues in the specified association.

    Requires a saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the browser
    storage state on disk and attached to the HTTP request. No browser is launched.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    leagues = run_action_or_exit(session, _list_leagues_action, association_id)
    rows = [league.model_dump(mode="json") for league in leagues]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
