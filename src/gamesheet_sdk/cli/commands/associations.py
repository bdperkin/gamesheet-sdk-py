"""Associations command group.

This module provides the CLI interface for managing GameSheet associations, which represent the
top-level organizational unit in the GameSheet platform. An association corresponds to a league
operator (hockey association, tournament series, district body, etc.).

The command group provides sub-commands for listing associations accessible to the authenticated user.
When invoked without a sub-command, it defaults to the ``list`` operation.

Examples:
    List all associations in simple table format::

        $ gamesheet-sdk-py associations

    List associations in JSON format::

        $ gamesheet-sdk-py associations list --format json

    List associations with selected columns only::

        $ gamesheet-sdk-py associations list --columns id,title,created_at

    Save associations to a file::

        $ gamesheet-sdk-py associations list --format yaml --output associations.yaml
"""

from __future__ import annotations

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.associations import get_association as _get_association_action
from gamesheet_sdk.associations import list_associations as _list_associations_action
from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output


@click.group(
    "associations",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        # standard CRUD verb aliases included if they are used when
        # sub-commands are added.
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def associations_group() -> None:
    """Manage GameSheet associations.

    Invoking ``associations`` with no sub-command runs ``list`` by default.
    """


@associations_group.command("get")
@click.option(
    "--association-id",
    type=str,
    envvar="GAMESHEET_ASSOCIATION_ID",
    required=True,
    help="Association ID to retrieve details for.",
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
def associations_get_command(
    ctx: Context,
    association_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific association.

    The association ID can be provided via --association-id or the GAMESHEET_ASSOCIATION_ID environment
    variable. Requires a saved session from `gamesheet-sdk-py login` -- the bearer token is read out of the
    browser storage state on disk and attached to the HTTP request. No browser is launched. The output
    displays association metadata as key-value pairs, with each field on its own row.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    data = run_action_or_exit(session, _get_association_action, association_id).model_dump(mode="json")
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


@associations_group.command("list")
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
def associations_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all associations on your GameSheet account.

    Requires authentication (run 'gamesheet-sdk-py login' first). Retrieves all
    associations accessible by your account and displays them in the specified
    output format.

    Examples:
        List all associations in default format:

            $ gamesheet-sdk-py associations list

        List associations in JSON format:

            $ gamesheet-sdk-py associations list --format json

        List associations with only id and title columns:

            $ gamesheet-sdk-py associations list --columns id,title

        Save associations to a YAML file:

            $ gamesheet-sdk-py associations list --format yaml --output assocs.yaml
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    associations = run_action_or_exit(session, _list_associations_action)
    rows = [assoc.model_dump(mode="json") for assoc in associations]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
