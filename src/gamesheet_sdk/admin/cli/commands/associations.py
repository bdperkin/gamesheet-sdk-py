# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Associations command group.

This module provides the CLI interface for managing GameSheet associations, which represent the top-level
organizational unit in the GameSheet platform. An association corresponds to a league operator (hockey
association, tournament series, district body, etc.). The command group provides sub-commands for listing
associations accessible to the authenticated user. When invoked without a sub-command, it defaults to the
``list`` operation.

Examples:
    List all associations in simple table format::
        $ gamesheet-admin associations
    List associations in JSON format::
        $ gamesheet-admin associations list --format json
    List associations with selected columns only::
        $ gamesheet-admin associations list --columns id,title,created_at
    Save associations to a file::
        $ gamesheet-admin associations list --format yaml --output associations.yaml
"""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.associations import (
    get_association as _get_association_action,
    list_associations as _list_associations_action,
)
from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.config import Config


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
    """Manage associations.

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
@common_output_options
@get_fields_option
@click.pass_context
def associations_get_command(
    ctx: Context,
    association_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Get detailed information about a specific association.

    The association ID can be provided via --association-id or the GAMESHEET_ASSOCIATION_ID environment
    variable. Requires a saved session from ``gamesheet-admin login`` -- the bearer token is read out of the
    browser storage state on disk and attached to the HTTP request. No browser is launched. The output
    displays association metadata as key-value pairs, with each field on its own row.\f

    Args:
        ctx (Context): Click context object containing config
        association_id (str): The association identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        fields_spec (str | None): Optional comma-separated list of fields to display
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    association = run_action_or_exit(session, _get_association_action, association_id)
    render_get_command(association, output_format, output_path, fields_spec)


@associations_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def associations_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all associations on your GameSheet account.

    Requires authentication (run 'gamesheet-admin login' first). Retrieves all associations accessible by your
    account and displays them in the specified output format. .. rubric:: Examples

        List all associations in default format:
    .. code-block:: bash

        $ gamesheet-admin associations list

        List associations in JSON format:
    .. code-block:: bash

        $ gamesheet-admin associations list --format json

        List associations with only id and title columns:
    .. code-block:: bash

        $ gamesheet-admin associations list --columns id,title

        Save associations to a YAML file:
    .. code-block:: bash

        $ gamesheet-admin associations list --format yaml --output assocs.yaml\f

    Args:
        ctx (Context): Click context object containing config
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    associations = run_action_or_exit(session, _list_associations_action)
    render_list_command(associations, output_format, output_path, columns_spec)
