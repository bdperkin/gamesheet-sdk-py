"""Season detail command group."""

from __future__ import annotations

import click

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.seasons import get_season as _get_season_action


@click.group(
    "season",
    cls=ResourceGroup,
    default="get",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def season_group() -> None:
    """Manage an individual GameSheet season.

    Invoking ``season`` with no sub-command runs ``get`` by default.
    """


@season_group.command("get")
@click.argument("season-id", type=str, metavar="SEASON_ID")
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
    "--fields",
    "-f",
    "fields_spec",
    default=None,
    help=("Comma-separated list of field names to include (default: all fields the API returns)."),
)
@click.pass_context
def season_get_command(
    ctx: click.Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific season.

    Requires a saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the browser
    storage state on disk and attached to the HTTP request. No browser is launched. The output displays season
    metadata as key-value pairs, with each field on its own row. Complex nested fields (like settings,
    flagging_criteria) are displayed as JSON.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    season_detail = run_action_or_exit(session, _get_season_action, season_id)
    # Convert to dict for rendering
    data = season_detail.model_dump(mode="json")  # noqa: FURB184
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
