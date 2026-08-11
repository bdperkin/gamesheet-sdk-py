# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""IPad keys command group.

This module provides the CLI interface for managing GameSheet iPad / Scoring Access Keys, which are
credentials used by the GameSheet iPad app for live game scoring. Keys are scoped to a specific season and
enable authorized devices to submit scores, penalties, and other game events in real-time. The command group
provides sub-commands for retrieving all iPad keys configured for a season. When invoked without a
sub-command, it defaults to the ``get`` operation.

Examples:
    Get all iPad keys for a season in simple table format::
        $ gamesheet-admin ipad-keys --season-id <season_id>
    Get iPad keys in JSON format::
        $ gamesheet-admin ipad-keys get --season-id <season_id> --format json
    Get iPad keys with selected columns only::
        $ gamesheet-admin ipad-keys --season-id <season_id> --columns id,value,description
    Save iPad keys to a file::
        $ gamesheet-admin ipad-keys get --season-id <season_id> --format yaml --output keys.yaml
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared import (
    common_output_options,
    list_columns_option,
    render_list_command,
)
from gamesheet_sdk.admin.ipad_keys import list_ipad_keys as _list_ipad_keys_action
from gamesheet_sdk.common.cli.core import ResourceGroup

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


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
    are season-specific and enable authorized devices to record scores, penalties, and game stats. Invoking
    'ipad-keys' with no sub-command runs 'get' by default.
    """


@ipad_keys_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to retrieve iPad keys for.",
)
@common_output_options
@list_columns_option
@click.pass_context
def ipad_keys_get_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""Get iPad / Scoring Access Keys for a specific season.

    Requires authentication (run 'gamesheet-admin login' first). Retrieves all iPad keys configured for the
    specified season. These keys are used by the GameSheet iPad app for live game scoring. The season ID can
    be provided via --season-id or the GAMESHEET_SEASON_ID environment variable. .. rubric:: Examples

        Get all iPad keys for a season in default format:
    .. code-block:: bash

        $ gamesheet-admin ipad-keys get --season-id 12345

        Get iPad keys in JSON format:
    .. code-block:: bash

        $ gamesheet-admin ipad-keys get --season-id 12345 --format json

        Get iPad keys with only id and value columns:
    .. code-block:: bash

        $ gamesheet-admin ipad-keys --season-id 12345 --columns id,value

        Save iPad keys to a CSV file:
    .. code-block:: bash

        $ gamesheet-admin ipad-keys get --season-id 12345 --format csv --output keys.csv

        Use environment variable for season ID:
    .. code-block:: bash

        $ export GAMESHEET_SEASON_ID=12345

    .. code-block:: bash

        $ gamesheet-admin ipad-keys\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    keys = run_action_or_exit(session, _list_ipad_keys_action, season_id)
    render_list_command(keys, output_format, output_path, columns_spec)
