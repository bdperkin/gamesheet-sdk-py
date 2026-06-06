"""Seasons command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.seasons import list_seasons as _list_seasons_action


@click.group(
    "seasons",
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
def seasons_group() -> None:
    """Manage seasons within a league.

    Invoking ``seasons`` with no sub-command runs ``list`` by default.
    """


@seasons_group.command("list")
@click.option(
    "--league-id",
    type=str,
    envvar="GAMESHEET_LEAGUE_ID",
    required=True,
    help="League ID to list seasons for.",
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
def seasons_list_command(
    ctx: Context,
    league_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List the seasons in the specified league.

    The league ID can be provided via --league-id or the GAMESHEET_LEAGUE_ID environment variable. Requires a
    saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the browser storage state
    on disk and attached to the HTTP request. No browser is launched.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    seasons = run_action_or_exit(session, _list_seasons_action, league_id)
    rows = [season.model_dump(mode="json") for season in seasons]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
