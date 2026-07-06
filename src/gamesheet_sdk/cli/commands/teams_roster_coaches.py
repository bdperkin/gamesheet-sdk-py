# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams roster coaches command group."""

from __future__ import annotations

from typing import Any

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli.constants import (
    COACH_POSITIONS,
    HELP_COACH_FIRST_NAME,
    HELP_COACH_LAST_NAME,
    HELP_UPDATED_EXTERNAL_ID,
    HELP_UPDATED_FIRST_NAME,
    HELP_UPDATED_LAST_NAME,
)
from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
    run_roster_assign_with_output,
    run_roster_unassign,
)
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
    render_penalty_report,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.roster import (
    assign_team_coach as _assign_team_coach_action,
    create_team_coach as _create_team_coach_action,
    delete_team_coach as _delete_team_coach_action,
    get_team_coach as _get_team_coach_action,
    list_team_coaches as _list_team_coaches_action,
    unassign_team_coach as _unassign_team_coach_action,
    update_team_coach as _update_team_coach_action,
)


# Teams roster coaches sub-group
@click.group(
    "coaches",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
        "assign": ("register", "enlist", "place"),
        "unassign": ("drop", "release", "deregister"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def teams_roster_coaches_group() -> None:
    """Manage coaches for this team.

    Invoking ``coaches`` with no sub-command runs ``list`` by default.
    """


@teams_roster_coaches_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def teams_roster_coaches_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all coaches for this team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param columns_spec: Optional comma-separated list of columns to display
    :type columns_spec: str | None
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    coaches = run_action_or_exit(session, _list_team_coaches_action, season_id, team_id)
    render_list_command(coaches, output_format, output_path, columns_spec)


@teams_roster_coaches_group.command("get")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_roster_coaches_get_command(
    ctx: Context,
    coach_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific coach on this team.

    The coach ID can be provided via --coach-id or the GAMESHEET_COACH_ID environment variable. The season ID
    and team ID are inherited from the parent roster command. Requires authentication (run 'gamesheet-sdk-py
    login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :param fields_spec: Optional comma-separated list of fields to display
    :type fields_spec: str | None
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    coach = run_action_or_exit(
        session,
        _get_team_coach_action,
        season_id,
        team_id,
        coach_id,
    )
    render_get_command(coach, output_format, output_path, fields_spec)


@teams_roster_coaches_group.command("create")
@click.option(
    "--first-name",
    type=str,
    required=True,
    help=HELP_COACH_FIRST_NAME,
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help=HELP_COACH_LAST_NAME,
)
@click.option(
    "--external-id",
    type=str,
    help="Optional external identifier for the coach.",
)
@click.option(
    "--position",
    type=click.Choice(COACH_POSITIONS, case_sensitive=False),
    help="Optional position.",
)
@common_output_options
@click.pass_context
def teams_roster_coaches_create_command(
    ctx: Context,
    first_name: str,
    last_name: str,
    external_id: str | None,
    position: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Add a coach to this team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param first_name: Optional updated first name
    :type first_name: str
    :param last_name: Optional updated last name
    :type last_name: str
    :param external_id: Optional updated external identifier
    :type external_id: str | None
    :param position: Optional position
    :type position: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    try:
        with session:
            coach = _create_team_coach_action(
                session,
                season_id,
                team_id,
                first_name,
                last_name,
                external_id=external_id,
                position=position,
            )
    except Exception as exc:
        click.secho(f"Error creating coach: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(coach, output_format, output_path, None)
    click.secho(f"Coach {coach.id} added to team {team_id} successfully.", fg="green")


@teams_roster_coaches_group.command("update")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to update.",
)
@click.option(
    "--first-name",
    type=str,
    help=HELP_UPDATED_FIRST_NAME,
)
@click.option(
    "--last-name",
    type=str,
    help=HELP_UPDATED_LAST_NAME,
)
@click.option(
    "--external-id",
    type=str,
    help=HELP_UPDATED_EXTERNAL_ID,
)
@click.option(
    "--position",
    type=click.Choice(COACH_POSITIONS, case_sensitive=False),
    help="Updated position.",
)
@common_output_options
@click.pass_context
def teams_roster_coaches_update_command(
    ctx: Context,
    coach_id: str,
    first_name: str | None,
    last_name: str | None,
    external_id: str | None,
    position: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update a coach on this team.

    Requires authentication (run 'gamesheet-sdk-py login' first). At least one field must be provided for
    update.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    :param first_name: Optional updated first name
    :type first_name: str | None
    :param last_name: Optional updated last name
    :type last_name: str | None
    :param external_id: Optional updated external identifier
    :type external_id: str | None
    :param position: Optional position
    :type position: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    from gamesheet_sdk.cli.helpers import run_roster_update_with_output

    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    run_roster_update_with_output(
        _update_team_coach_action,
        session,
        "coach",
        output_format,
        output_path,
        session,
        season_id,
        team_id,
        coach_id,
        first_name=first_name,
        last_name=last_name,
        external_id=external_id,
        position=position,
    )


@teams_roster_coaches_group.command("delete")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to delete.",
)
@confirm_destructive("coach")
@click.pass_context
def teams_roster_coaches_delete_command(ctx: Context, coach_id: str) -> None:
    """Delete a coach from the team's roster and the season.

    Requires authentication (run 'gamesheet-sdk-py login' first). This operation is destructive and cannot be
    undone. Use --force to skip confirmation prompt.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier to delete
    :type coach_id: str
    :raises Exit: On authentication or API errors.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    team_id: str = ctx_data["team_id"]
    session = build_authenticated_session(config)
    try:
        with session:
            _delete_team_coach_action(session, season_id, team_id, coach_id)
    except Exception as exc:
        click.secho(f"Error deleting coach: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho(f"Coach {coach_id} deleted successfully.", fg="green")


@teams_roster_coaches_group.command("penalty-report")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to retrieve penalty report for.",
)
@common_output_options
@click.pass_context
def teams_roster_coaches_penalty_report_command(
    ctx: Context,
    coach_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get penalty report for a coach on this team.

    Retrieves penalty statistics, incidents, and infraction history for the specified coach.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: Coach ID to retrieve penalty report for
    :type coach_id: str
    :param output_format: Output format (json, yaml, etc.)
    :type output_format: str
    :param output_path: Optional path to write output file
    :type output_path: str | None
    """
    ctx_data: dict[str, Any] = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    with build_authenticated_session(config) as session:
        from gamesheet_sdk.roster import get_coach_penalty_report

        report = get_coach_penalty_report(session, season_id, coach_id)
        render_penalty_report(report, output_format, output_path)


@teams_roster_coaches_group.command("assign")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to assign.",
)
@click.option(
    "--position",
    type=click.Choice(COACH_POSITIONS, case_sensitive=False),
    help="Optional position.",
)
@common_output_options
@click.pass_context
def teams_roster_coaches_assign_command(
    ctx: Context,
    coach_id: str,
    position: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Assign an existing coach to this team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    :param position: Optional position
    :type position: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    config, season_id, team_id = (
        ctx.obj["config"],
        ctx.obj["season_id"],
        ctx.obj["team_id"],
    )
    session = build_authenticated_session(config)
    run_roster_assign_with_output(
        _assign_team_coach_action,
        session,
        "coach",
        coach_id,
        team_id,
        output_format,
        output_path,
        session,
        season_id,
        team_id,
        coach_id,
        position=position,
    )


@teams_roster_coaches_group.command("unassign")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to unassign.",
)
@click.pass_context
def teams_roster_coaches_unassign_command(ctx: Context, coach_id: str) -> None:
    """Unassign a coach from this team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    """
    config, season_id, team_id = (
        ctx.obj["config"],
        ctx.obj["season_id"],
        ctx.obj["team_id"],
    )
    session = build_authenticated_session(config)
    run_roster_unassign(
        _unassign_team_coach_action,
        session,
        "coach",
        coach_id,
        team_id,
        session,
        season_id,
        team_id,
        coach_id,
    )
