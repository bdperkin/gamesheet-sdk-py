"""Referees command group."""

from __future__ import annotations

import rich_click as click

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.referees import list_referees as _list_referees_action


@click.group(
    "referees",
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
def referees_group() -> None:
    """Manage referees within a season.

    Invoking ``referees`` with no sub-command runs ``list`` by default.
    """


@referees_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list referees for.",
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
def referees_list_command(
    ctx: click.Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all referees in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    referees = run_action_or_exit(session, _list_referees_action, season_id)
    rows = [referee.model_dump(mode="json") for referee in referees]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
