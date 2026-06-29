# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Referees command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.cli.shared import (
    common_output_options,
    list_columns_option,
    render_list_command,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.referees import (
    create_referee as _create_referee_action,
    delete_referee as _delete_referee_action,
    get_referee as _get_referee_action,
    get_referee_report as _get_referee_report_action,
    list_referees as _list_referees_action,
    update_referee as _update_referee_action,
)


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


@referees_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to retrieve.",
)
@common_output_options
@click.pass_context
def referees_get_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get a single referee by ID.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param referee_id: The referee identifier
    :type referee_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    referee = run_action_or_exit(session, _get_referee_action, season_id, referee_id)
    render_list_command([referee], output_format, output_path)


@referees_group.command("report")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to retrieve report for.",
)
@common_output_options
@click.pass_context
def referees_report_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get a comprehensive referee report with statistics and games.

    Retrieves career statistics, games officiated, and penalty details. Requires authentication (run
    'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param referee_id: The referee identifier
    :type referee_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    report = run_action_or_exit(
        session,
        _get_referee_report_action,
        season_id,
        referee_id,
    )
    render_list_command([report], output_format, output_path)


@referees_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to create the referee in.",
)
@click.option(
    "--first-name",
    type=str,
    required=True,
    help="Referee's first name.",
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help="Referee's last name.",
)
@click.option(
    "--email-address",
    type=str,
    default=None,
    help="Optional email address for the referee.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Optional external identifier for the referee.",
)
@common_output_options
@click.pass_context
def referees_create_command(
    ctx: Context,
    season_id: str,
    first_name: str,
    last_name: str,
    email_address: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new referee in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param first_name: Referee's first name
    :type first_name: str
    :param last_name: Referee's last name
    :type last_name: str
    :param email_address: Optional email address for the referee
    :type email_address: str | None
    :param external_id: Optional external identifier for the referee
    :type external_id: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    referee = run_action_or_exit(
        session,
        _create_referee_action,
        season_id,
        first_name,
        last_name,
        email_address,
        external_id,
    )
    render_list_command([referee], output_format, output_path)


@referees_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to update.",
)
@click.option(
    "--first-name",
    type=str,
    default=None,
    help="Updated first name.",
)
@click.option(
    "--last-name",
    type=str,
    default=None,
    help="Updated last name.",
)
@click.option(
    "--email-address",
    type=str,
    default=None,
    help="Updated email address.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Updated external identifier.",
)
@common_output_options
@click.pass_context
def referees_update_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    first_name: str | None,
    last_name: str | None,
    email_address: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing referee in the specified season.

    At least one field must be provided to update. Requires authentication (run 'gamesheet-sdk-py login'
    first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param referee_id: The referee identifier to update
    :type referee_id: str
    :param first_name: Optional updated first name
    :type first_name: str | None
    :param last_name: Optional updated last name
    :type last_name: str | None
    :param email_address: Optional updated email address
    :type email_address: str | None
    :param external_id: Optional updated external identifier
    :type external_id: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises click.UsageError: If no fields are provided for update
    """
    # Validate that at least one field is provided
    if not any([first_name, last_name, email_address, external_id]):
        msg = (
            "At least one field must be provided to update. "
            "Use --first-name, --last-name, --email-address, or --external-id."
        )
        raise click.UsageError(msg)
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    referee = run_action_or_exit(
        session,
        _update_referee_action,
        season_id,
        referee_id,
        first_name,
        last_name,
        email_address,
        external_id,
    )
    render_list_command([referee], output_format, output_path)


@referees_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to delete.",
)
@confirm_destructive("referee")
@click.pass_context
def referees_delete_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
) -> None:
    """Delete a referee.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param referee_id: The referee identifier to delete
    :type referee_id: str
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    run_action_or_exit(session, _delete_referee_action, season_id, referee_id)
    click.secho(f"Referee {referee_id} deleted successfully.", fg="green")


@referees_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list referees for.",
)
@common_output_options
@list_columns_option
@click.pass_context
def referees_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all referees in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param columns_spec: Optional comma-separated list of columns to display
    :type columns_spec: str | None
    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    referees = run_action_or_exit(session, _list_referees_action, season_id)
    render_list_command(referees, output_format, output_path, columns_spec)
