# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams command for the GameSheet teams dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit
from rich_click import Context

from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.common.cli.decorators import (
    common_output_options,
    get_fields_option,
    list_columns_option,
)
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.teams import (
    archive_team as _archive_team_action,
)
from gamesheet_sdk.teams.teams import (
    delete_team as _delete_team_action,
)
from gamesheet_sdk.teams.teams import (
    get_team as _get_team_action,
)
from gamesheet_sdk.teams.teams import (
    list_teams as _list_teams_action,
)
from gamesheet_sdk.teams.teams import (
    restore_team as _restore_team_action,
)
from gamesheet_sdk.teams.teams import (
    update_team as _update_team_action,
)

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


@click.group(
    "teams",
    cls=ResourceGroup,
    default="list",
    aliases={
        "delete": ("rm", "remove"),
        "get": ("show", "view"),
        "list": ("ls",),
        "restore": ("unarchive",),
        "update": ("set", "edit"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def teams_group() -> None:
    """View and update teams from the teams API.

    Invoking ``teams`` with no sub-command runs ``list`` by default.
    """


@teams_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def teams_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all teams available to the authenticated user.

    Focuses on member ID, team ID, relationship, status, onboarding completion timestamp, team name,
    age category, club ID, joined timestamp, and stats year.\f

    Args:
        ctx (Context): Click context object containing config.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        columns_spec (str | None): Optional comma-separated list of columns to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    teams = run_action_or_exit(
        session,
        _list_teams_action,
        timeout=config.timeout,
    )
    render_list_command(teams, output_format, output_path, columns_spec)


@teams_group.command("get")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_get_command(
    ctx: Context,
    team_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Get detailed metadata for a specific team.

    Retrieves all attributes and configuration for the selected team.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    team = run_action_or_exit(
        session,
        _get_team_action,
        team_id,
        timeout=config.timeout,
    )
    render_get_command(team, output_format, output_path, fields_spec)


@teams_group.command("update")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to update.",
)
@click.option(
    "--team-name",
    "--name",
    type=str,
    default=None,
    help="New name for the team.",
)
@click.option(
    "--skill",
    type=str,
    default=None,
    help="Skill level of the team (e.g., rec, AAA).",
)
@click.option(
    "--team-logo",
    "--logo",
    type=str,
    default=None,
    help="Path to a local image file or URL for the team logo.",
)
@click.option(
    "--age-category",
    type=str,
    default=None,
    help="Age category of the team (e.g., U18, 12U).",
)
@click.option(
    "--province",
    type=str,
    default=None,
    help="Province or state code (e.g., VA, ON).",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_update_command(
    ctx: Context,
    team_id: str,
    team_name: str | None,
    skill: str | None,
    team_logo: str | None,
    age_category: str | None,
    province: str | None,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Update an existing team's metadata.

    Requires authentication (run 'gamesheet-teams login' first). At least one field must be provided for
    update.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier to update.
        team_name (str | None): Optional new team name.
        skill (str | None): Optional new skill level.
        team_logo (str | None): Optional local image path or logo URL.
        age_category (str | None): Optional new age category.
        province (str | None): Optional new province/state code.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    if all(v is None for v in (team_name, skill, team_logo, age_category, province)):
        click.secho(
            "Error: At least one field must be provided for update. "
            "Use --name/--team-name, --skill, --logo/--team-logo, --age-category, or --province.",
            fg="red",
            err=True,
        )
        raise Exit(1)

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    team = run_action_or_exit(
        session,
        _update_team_action,
        team_id,
        team_name=team_name,
        skill=skill,
        team_logo=team_logo,
        age_category=age_category,
        province=province,
        timeout=config.timeout,
    )
    render_get_command(team, output_format, output_path, fields_spec)


@teams_group.command("archive")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to archive.",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_archive_command(
    ctx: Context,
    team_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Archive a team.

    Archiving a team will remove it from active lists and prevent members from interacting with it,
    but all data will be preserved and it can be unarchived at any time.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier to archive.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    team = run_action_or_exit(
        session,
        _archive_team_action,
        team_id,
        timeout=config.timeout,
    )
    render_get_command(team, output_format, output_path, fields_spec)


@teams_group.command("restore")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to restore.",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_restore_command(
    ctx: Context,
    team_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    r"""Restore an archived team back to active lists.

    Restoring a team will add it back to active lists and allow members to interact with it.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier to restore.
        output_format (str): Output format for rendering.
        output_path (str | None): Optional output file path.
        fields_spec (str | None): Optional comma-separated list of fields to display.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    team = run_action_or_exit(
        session,
        _restore_team_action,
        team_id,
        timeout=config.timeout,
    )
    render_get_command(team, output_format, output_path, fields_spec)


@teams_group.command("delete")
@click.option(
    "--team-id",
    "-t",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to delete.",
)
@confirm_destructive("team")
@click.pass_context
def teams_delete_command(
    ctx: Context,
    team_id: str,
) -> None:
    r"""Delete a team.

    Permanently deletes a team.\f

    Args:
        ctx (Context): Click context object containing config.
        team_id (str): Team identifier to delete.

    """
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    run_action_or_exit(
        session,
        _delete_team_action,
        team_id,
        timeout=config.timeout,
    )
    click.secho(f"Team {team_id} deleted successfully.", fg="green")
