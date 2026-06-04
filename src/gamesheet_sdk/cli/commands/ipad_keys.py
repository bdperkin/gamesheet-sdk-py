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

    This command group provides access to iPad keys (also known as Scoring Access Keys), which are credentials
    used by the GameSheet iPad app to authenticate and submit live game scoring data. Keys are season-specific
    and enable authorized devices to record scores, penalties, game stats, and other real-time events during
    games.

    Invoking ``ipad-keys`` with no sub-command runs ``get`` by default.

    :returns: None. This is a Click command group that delegates to sub-commands.
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

    Requires a saved session from ``gamesheet-sdk-py login`` -- the bearer token is read out of the browser
    storage state on disk and attached to the HTTP request. No browser is launched.

    The command retrieves all iPad keys (Scoring Access Keys) configured for the specified season. These
    keys are used by the GameSheet iPad app for live game scoring, enabling authorized devices to submit
    scores, penalties, statistics, and other real-time game events. Each key includes an ID, the actual
    access key value, an optional description, and creation timestamp.

    The season ID can be provided via ``--season-id`` or the ``GAMESHEET_SEASON_ID`` environment variable.

    :param ctx: Click context object containing the application :class:`~gamesheet_sdk.config.Config` in
        ``ctx.obj``.
    :param season_id: Season ID to retrieve iPad keys for. Must be a valid GameSheet season identifier.
    :param output_format: Output format name (json, yaml, csv, tsv, or any tabulate format like simple, grid,
        etc.). Defaults to ``simple``.
    :param output_path: Optional file path to write output. If ``None``, writes to stdout.
    :param columns_spec: Optional comma-separated list of column names to include in output (e.g.,
        ``"id,value,description,created_at"``). If ``None``, includes default columns: id, value, description,
        created_at.
    :returns: None. Writes formatted output to stdout or the specified file.
    :raises click.exceptions.Exit: If no saved session exists (exit code 1), authentication fails, the season
        ID is invalid, or the API returns an error.

    Examples:
        Get all iPad keys for a season in default format::

            $ gamesheet-sdk-py ipad-keys get --season-id 12345

        Get iPad keys in JSON format::

            $ gamesheet-sdk-py ipad-keys get --season-id 12345 --format json

        Get iPad keys with only id and value columns::

            $ gamesheet-sdk-py ipad-keys --season-id 12345 --columns id,value

        Save iPad keys to a CSV file::

            $ gamesheet-sdk-py ipad-keys get --season-id 12345 --format csv --output keys.csv

        Use environment variable for season ID::

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
