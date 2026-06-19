"""Teams command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
    run_team_create,
    run_team_update,
)
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
    team_create_options,
    team_update_options,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.teams import delete_team as _delete_team_action
from gamesheet_sdk.teams import get_team as _get_team_action
from gamesheet_sdk.teams import list_teams as _list_teams_action

if TYPE_CHECKING:
    from rich_click import Context


@click.group(
    "teams",
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
def teams_group() -> None:
    """Manage teams within a season.

    Invoking ``teams`` with no sub-command runs ``list`` by default.
    """


@teams_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the team.",
)
@click.option(
    "--team-id",
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
    season_id: str,
    team_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific team.

    The team and season IDs can be provided via command-line options or environment variables
    (GAMESHEET_TEAM_ID, GAMESHEET_SEASON_ID). Requires a saved session from `gamesheet-sdk-py login`. The
    output displays team metadata as key-value pairs, with each field on its own row.
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    # Convert to dict for rendering
    team = run_action_or_exit(session, _get_team_action, season_id, team_id)
    render_get_command(team, output_format, output_path, fields_spec)


@teams_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list teams for.",
)
@common_output_options
@list_columns_option
@click.pass_context
def teams_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all teams in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    teams = run_action_or_exit(session, _list_teams_action, season_id)
    render_list_command(teams, output_format, output_path, columns_spec)


@teams_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to create the team in.",
)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Team name/title.",
)
@click.option(
    "--division-id",
    type=str,
    required=True,
    help="Division ID the team belongs to.",
)
@team_create_options
@common_output_options
@click.pass_context
def teams_create_command(
    ctx: Context,
    season_id: str,
    title: str,
    division_id: str,
    external_id: str | None,
    logo_path: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new team in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    run_team_create(
        ctx,
        season_id,
        title,
        division_id,
        external_id,
        logo_path,
        output_format,
        output_path,
    )


@teams_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the team.",
)
@click.option(
    "--team-id",
    type=str,
    required=True,
    help="Team ID to update.",
)
@team_update_options
@common_output_options
@click.pass_context
def teams_update_command(
    ctx: Context,
    season_id: str,
    team_id: str,
    title: str | None,
    division_id: str | None,
    external_id: str | None,
    logo_path: str | None,
    *,
    remove_logo: bool,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing team.

    Requires authentication (run 'gamesheet-sdk-py login' first). At least one field must be provided for
    update.
    """
    run_team_update(
        ctx,
        season_id,
        team_id,
        title,
        division_id,
        external_id,
        logo_path,
        remove_logo=remove_logo,
        output_format=output_format,
        output_path=output_path,
    )


@teams_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the team.",
)
@click.option(
    "--team-id",
    type=str,
    required=True,
    help="Team ID to delete.",
)
@click.pass_context
def teams_delete_command(
    ctx: Context,
    season_id: str,
    team_id: str,
) -> None:
    """Delete a team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    run_action_or_exit(session, _delete_team_action, season_id, team_id)
    click.secho(f"Team {team_id} deleted successfully.", fg="green")


# Teams roster nested group
@teams_group.group(
    "roster",
    cls=ResourceGroup,
    default="players",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to manage roster for.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to manage roster for.",
)
@click.pass_context
def teams_roster_group(ctx: Context, season_id: str, team_id: str) -> None:
    """Manage roster (players and coaches) for a specific team.

    Invoking ``roster`` with no sub-command runs ``players`` by default. The --season-id and --team-id options
    are required and apply to all sub-commands.
    """
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id, "team_id": team_id}


# Teams roster players sub-group
@teams_roster_group.group(
    "players",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def teams_roster_players_group() -> None:
    """Manage players for this team.

    Invoking ``players`` with no sub-command runs ``list`` by default.
    """


@teams_roster_players_group.command("list")
def teams_roster_players_list_command() -> None:
    """List all players for this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players list is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("get")
def teams_roster_players_get_command() -> None:
    """Get a specific player for this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players get is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("create")
def teams_roster_players_create_command() -> None:
    """Add a player to this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players create is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("update")
def teams_roster_players_update_command() -> None:
    """Update a player on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players update is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("delete")
@confirm_destructive("player")
def teams_roster_players_delete_command() -> None:
    """Remove a player from this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players delete is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("penalty-report")
def teams_roster_players_penalty_report_command() -> None:
    """Get penalty report for a player on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


# Teams roster coaches sub-group
@teams_roster_group.group(
    "coaches",
    cls=ResourceGroup,
    default="list",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def teams_roster_coaches_group() -> None:
    """Manage coaches for this team.

    Invoking ``coaches`` with no sub-command runs ``list`` by default.
    """


@teams_roster_coaches_group.command("list")
def teams_roster_coaches_list_command() -> None:
    """List all coaches for this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches list is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("get")
def teams_roster_coaches_get_command() -> None:
    """Get a specific coach for this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches get is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("create")
def teams_roster_coaches_create_command() -> None:
    """Add a coach to this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches create is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("update")
def teams_roster_coaches_update_command() -> None:
    """Update a coach on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches update is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("delete")
@confirm_destructive("coach")
def teams_roster_coaches_delete_command() -> None:
    """Remove a coach from this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches delete is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("penalty-report")
def teams_roster_coaches_penalty_report_command() -> None:
    """Get penalty report for a coach on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)
