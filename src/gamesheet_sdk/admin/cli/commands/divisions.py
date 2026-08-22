# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Divisions command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.admin.cli.commands.teams import (
    teams_create_command,
    teams_delete_command,
    teams_get_command,
    teams_update_command,
)
from gamesheet_sdk.admin.cli.constants import (
    HELP_SEASON_ID_FOR_DIVISION,
)
from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared import (
    columns_option,
    common_output_options,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.admin.divisions import (
    Division,
)
from gamesheet_sdk.admin.divisions import (
    create_division as _create_division_action,
)
from gamesheet_sdk.admin.divisions import (
    delete_division as _delete_division_action,
)
from gamesheet_sdk.admin.divisions import (
    get_division as _get_division_action,
)
from gamesheet_sdk.admin.divisions import (
    list_division_teams as _list_division_teams_action,
)
from gamesheet_sdk.admin.divisions import (
    list_divisions as _list_divisions_action,
)
from gamesheet_sdk.admin.divisions import (
    update_division as _update_division_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive

if TYPE_CHECKING:
    from gamesheet_sdk.common.auth.session import AuthenticatedSession
    from gamesheet_sdk.common.config import Config


@click.group(
    "divisions",
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
def divisions_group() -> None:
    """Manage divisions within a season.

    Invoking ``divisions`` with no sub-command runs ``list`` by default.
    """


@divisions_group.command("get")
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID to retrieve details for.",
)
@common_output_options
@columns_option
@click.pass_context
def divisions_get_command(
    ctx: Context,
    division_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""Get detailed information about a specific division.

    The division ID can be provided via --division-id or the GAMESHEET_DIVISION_ID environment variable.
    Requires a saved session from ``gamesheet-admin login``. The output displays division metadata as
    key-value pairs, with each field on its own row.\f

    Args:
        ctx (Context): Click context object containing config
        division_id (str): The division identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    division = run_action_or_exit(session, _get_division_action, division_id)
    render_get_command(division, output_format, output_path, columns_spec)


@divisions_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list divisions for.",
)
@common_output_options
@columns_option
@click.pass_context
def divisions_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all divisions in the specified season.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)

    def _list_with_counts(sess: AuthenticatedSession, sid: str) -> list[Division]:
        return _list_divisions_action(sess, sid, include_team_counts=True)

    divisions = run_action_or_exit(session, _list_with_counts, season_id)
    render_list_command(divisions, output_format, output_path, columns_spec)


@divisions_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID in which to create the division.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Division name/title.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Optional external identifier for integration with third-party systems.",
)
@common_output_options
@click.pass_context
def divisions_create_command(
    ctx: Context,
    season_id: str,
    title: str,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    r"""Create a new division in the specified season.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
        title (str): Division name/title
        external_id (str | None): Optional external identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)

    def _create_with_kwargs(
        sess: AuthenticatedSession,
        sid: str,
        div_title: str,
    ) -> Division:
        return _create_division_action(sess, sid, div_title, external_id=external_id)

    division = run_action_or_exit(session, _create_with_kwargs, season_id, title)
    render_list_command([division], output_format, output_path)
    if output_path is None:
        click.secho(
            f"\nDivision '{division.title}' created successfully (ID: {division.id})",
            fg="green",
        )


@divisions_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help=HELP_SEASON_ID_FOR_DIVISION,
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID to update.",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="New division name/title.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="New external identifier.",
)
@common_output_options
@click.pass_context
def divisions_update_command(
    ctx: Context,
    season_id: str,
    division_id: str,
    title: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    r"""Update an existing division.

    At least one of --title or --external-id must be provided. Requires authentication (run 'gamesheet-admin
    login' first).\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
        division_id (str): The division identifier to update
        title (str | None): Optional new division name/title
        external_id (str | None): Optional new external identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

    Raises:
        Exit: If neither title nor external_id is provided

    """
    if title is None is external_id:
        click.secho(
            "Error: At least one of --title or --external-id must be provided.",
            fg="red",
            err=True,
        )
        raise Exit(1)

    config: Config = ctx.obj
    session = build_authenticated_session(config)

    def _update_with_kwargs(
        sess: AuthenticatedSession,
        sid: str,
        div_id: str,
    ) -> Division:
        return _update_division_action(
            sess,
            sid,
            div_id,
            title=title,
            external_id=external_id,
        )

    division = run_action_or_exit(session, _update_with_kwargs, season_id, division_id)
    render_list_command([division], output_format, output_path)
    if output_path is None:
        click.secho(
            f"\nDivision '{division.title}' updated successfully (ID: {division.id})",
            fg="green",
        )


@divisions_group.group(
    "teams",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def divisions_teams_group() -> None:
    """Manage teams within a division.

    Invoking ``teams`` with no sub-command runs ``list`` by default.
    """


@divisions_teams_group.command("list")
@click.option(
    "--division-id",
    type=str,
    envvar="GAMESHEET_DIVISION_ID",
    required=True,
    help="Division ID to list teams for.",
)
@common_output_options
@columns_option
@click.pass_context
def divisions_teams_list_command(
    ctx: Context,
    division_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all teams in the specified division.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        division_id (str): The division identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    division_teams = run_action_or_exit(session, _list_division_teams_action, division_id)
    render_list_command(division_teams, output_format, output_path, columns_spec)


divisions_teams_group.add_command(teams_get_command, name="get")
divisions_teams_group.add_command(teams_create_command, name="create")
divisions_teams_group.add_command(teams_update_command, name="update")
divisions_teams_group.add_command(teams_delete_command, name="delete")


@divisions_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help=HELP_SEASON_ID_FOR_DIVISION,
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID to delete.",
)
@confirm_destructive("division")
@click.pass_context
def divisions_delete_command(
    ctx: Context,
    season_id: str,
    division_id: str,
) -> None:
    r"""Delete a division.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        season_id (str): The season identifier
        division_id (str): The division identifier to delete

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    run_action_or_exit(session, _delete_division_action, season_id, division_id)
    click.secho(f"Division {division_id} deleted successfully.", fg="green")
