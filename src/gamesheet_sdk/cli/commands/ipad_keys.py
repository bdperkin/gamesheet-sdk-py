"""IPad keys command group.

This module provides the CLI interface for managing GameSheet iPad / Scoring Access Keys, which are
credentials used by the GameSheet iPad app for live game scoring. Keys are scoped to a specific season
and enable authorized devices to submit scores, penalties, and other game events in real-time.

The command group provides sub-commands for retrieving all iPad keys configured for a season.
When invoked without a sub-command, it defaults to the ``get`` operation.

Examples:
    Get all iPad keys for a season in simple table format::

        $ gamesheet-sdk-py ipad-keys --season-id <season_id>

    Get iPad keys in JSON format::

        $ gamesheet-sdk-py ipad-keys get --season-id <season_id> --format json

    Get iPad keys with selected columns only::

        $ gamesheet-sdk-py ipad-keys --season-id <season_id> --columns id,value,description

    Save iPad keys to a file::

        $ gamesheet-sdk-py ipad-keys get --season-id <season_id> --format yaml --output keys.yaml
"""

from __future__ import annotations

import click

from gamesheet_sdk.cli.core import ResourceGroup, parse_columns_spec
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.ipad_keys import list_ipad_keys as _list_ipad_keys_action
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output


@click.group(
    "ipad-keys",
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
def ipad_keys_group() -> None:
    """Manage iPad / Scoring Access Keys for a season.

    iPad keys (Scoring Access Keys) are credentials used by the GameSheet iPad app for live game scoring. Keys
    are season-specific and enable authorized devices to record scores, penalties, and game stats.

    Invoking 'ipad-keys' with no sub-command runs 'get' by default.
    """


@ipad_keys_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve iPad keys for.",
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
    help=("Comma-separated list of column names to include (default: id, value, description, created_at)."),
)
@click.pass_context
def ipad_keys_get_command(
    ctx: click.Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """Get iPad / Scoring Access Keys for a specific season.

    Requires authentication (run 'gamesheet-sdk-py login' first). Retrieves all
    iPad keys configured for the specified season. These keys are used by the
    GameSheet iPad app for live game scoring.

    The season ID can be provided via --season-id or the GAMESHEET_SEASON_ID
    environment variable.

    Examples:
        Get all iPad keys for a season in default format:

            $ gamesheet-sdk-py ipad-keys get --season-id 12345

        Get iPad keys in JSON format:

            $ gamesheet-sdk-py ipad-keys get --season-id 12345 --format json

        Get iPad keys with only id and value columns:

            $ gamesheet-sdk-py ipad-keys --season-id 12345 --columns id,value

        Save iPad keys to a CSV file:

            $ gamesheet-sdk-py ipad-keys get --season-id 12345 --format csv --output keys.csv

        Use environment variable for season ID:

            $ export GAMESHEET_SEASON_ID=12345
            $ gamesheet-sdk-py ipad-keys
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    keys = run_action_or_exit(session, _list_ipad_keys_action, season_id)
    # Convert to list of dicts for rendering
    rows = [key.model_dump(mode="json") for key in keys]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
