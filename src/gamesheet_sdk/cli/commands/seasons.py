"""Seasons command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.seasons import get_season as _get_season_action
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
    "--starts-after",
    type=str,
    default=None,
    help="Filter seasons starting after this date (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--ends-before",
    type=str,
    default=None,
    help="Filter seasons ending before this date (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--status",
    type=Choice(["archived", "active", "all"], case_sensitive=False),
    default=None,
    help="Filter by season status.",
)
@click.option(
    "--stats-year",
    type=str,
    default=None,
    help="Filter by statistics year (e.g., '2026-2027').",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Filter by season title (free-form text search).",
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
    *,
    starts_after: str | None,
    ends_before: str | None,
    status: str | None,
    stats_year: str | None,
    title: str | None,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List the seasons in the specified league.

    The league ID can be provided via --league-id or the GAMESHEET_LEAGUE_ID environment variable. Requires a
    saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the browser storage state
    on disk and attached to the HTTP request. No browser is launched.

    Optional filters can be applied to narrow the results:
    --starts-after, --ends-before, --status, --stats-year, and --title.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    seasons = run_action_or_exit(
        session,
        lambda s: _list_seasons_action(
            s,
            league_id,
            starts_after=starts_after,
            ends_before=ends_before,
            status=status,
            stats_year=stats_year,
            title=title,
        ),
    )
    rows = [season.model_dump(mode="json") for season in seasons]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)


@seasons_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve details for.",
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
def seasons_get_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific season.

    The season ID can be provided via --season-id or the GAMESHEET_SEASON_ID environment variable. Requires a
    saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the browser storage state
    on disk and attached to the HTTP request. No browser is launched. The output displays season metadata as
    key-value pairs, with each field on its own row. Complex nested fields (like settings, flagging_criteria)
    are displayed as JSON.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    data = run_action_or_exit(session, _get_season_action, season_id).model_dump(
        mode="json",
    )
    # If fields are specified, filter to only those fields
    if fields_spec:
        fields = parse_columns_spec(fields_spec)
        if fields:  # pragma: no cover - edge case: fields list is always non-empty when spec is provided
            data = {k: v for k, v in data.items() if k in fields}
    # For tabular formats, convert to a list of key-value rows
    if output_format not in ("json", "yaml"):
        rows = [{"field": k, "value": v} for k, v in data.items()]
        rendered = render(rows, fmt=output_format, columns=None)
    else:
        # For data formats, output the whole object
        rendered = render([data], fmt=output_format, columns=None)
    write_output(rendered, output_path, fmt=output_format)
