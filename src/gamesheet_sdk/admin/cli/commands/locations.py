# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Locations command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

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
from gamesheet_sdk.admin.games import (
    get_location as _get_location_action,
    list_locations as _list_locations_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup
from gamesheet_sdk.common.config import Config


@click.group(
    "locations",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def locations_group() -> None:
    """Manage game locations and venues.

    View available locations/venues and their surfaces for scheduling games.
    """


@locations_group.command("list", aliases=["ls"])
@list_columns_option
@common_output_options
@click.pass_context
def locations_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all available locations.

    Returns the list of locations/venues from the GameSheet API. Each location includes the venue name,
    surface/rink name, and geographic information.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Comma-separated list of columns to display
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    locations = run_action_or_exit(session, _list_locations_action)
    render_list_command(locations, output_format, output_path, columns_spec)


@locations_group.command("get", aliases=["show", "view"])
@click.option(
    "--location-id",
    type=str,
    required=True,
    help="Location UUID to retrieve.",
)
@get_fields_option
@common_output_options
@click.pass_context
def locations_get_command(
    ctx: Context,
    location_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Get a specific location by ID.

    Retrieve detailed information about a specific location using its UUID. The location ID can be found using
    the 'list' command.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        location_id (str): The location UUID
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        fields_spec (str | None): Comma-separated list of fields to display
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    location = run_action_or_exit(session, _get_location_action, location_id)
    render_get_command(location, output_format, output_path, fields_spec)
