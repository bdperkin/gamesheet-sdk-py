"""Teams roster command group - player and coach management for teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.roster import create_team_coach as _create_team_coach_action
from gamesheet_sdk.roster import create_team_player as _create_team_player_action
from gamesheet_sdk.roster import get_team_coach as _get_team_coach_action
from gamesheet_sdk.roster import get_team_player as _get_team_player_action
from gamesheet_sdk.roster import list_team_coaches as _list_team_coaches_action
from gamesheet_sdk.roster import list_team_players as _list_team_players_action

if TYPE_CHECKING:
    from rich_click import Context


# Teams roster nested group
@click.group(
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


def register_teams_roster_group(teams_group: click.Group) -> None:
    """Register the teams roster sub-group with the teams group.

    :param teams_group: The main teams group to attach roster commands to.
    """
    teams_group.add_command(teams_roster_group)


# Teams roster players sub-group
@teams_roster_group.group(
    "players",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def teams_roster_players_group() -> None:
    """Manage players for this team.

    Invoking ``players`` with no sub-command runs ``list`` by default.
    """


@teams_roster_players_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def teams_roster_players_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all players for this team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    players = run_action_or_exit(session, _list_team_players_action, season_id, team_id)
    render_list_command(players, output_format, output_path, columns_spec)


@teams_roster_players_group.command("get")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to retrieve details for.",
)
@common_output_options
@get_fields_option
@click.pass_context
def teams_roster_players_get_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific player on this team.

    The player ID can be provided via --player-id or the GAMESHEET_PLAYER_ID environment variable. The season
    ID and team ID are inherited from the parent roster command. Requires authentication (run 'gamesheet-sdk-
    py login' first).
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    player = run_action_or_exit(session, _get_team_player_action, season_id, team_id, player_id)
    render_get_command(player, output_format, output_path, fields_spec)


@teams_roster_players_group.command("create")
@click.option(
    "--first-name",
    type=str,
    required=True,
    help="Player's first name.",
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help="Player's last name.",
)
@click.option(
    "--external-id",
    type=str,
    help="Optional external identifier for the player.",
)
@click.option(
    "--jersey",
    type=str,
    help="Optional jersey number.",
)
@click.option(
    "--position",
    type=click.Choice(
        [
            "Forward",
            "Left Wing",
            "Right Wing",
            "Centre",
            "Pusher (Sled)",
            "Defence",
            "Goalie",
        ],
        case_sensitive=False,
    ),
    help="Optional position.",
)
@click.option(
    "--status",
    type=click.Choice(["Regular", "Affiliated"], case_sensitive=False),
    help="Optional status.",
)
@click.option(
    "--designation",
    type=click.Choice(["Captain", "Alternate Captain"], case_sensitive=False),
    help="Optional designation (Captain or Alternate Captain).",
)
@common_output_options
@click.pass_context
def teams_roster_players_create_command(
    ctx: Context,
    first_name: str,
    last_name: str,
    external_id: str | None,
    jersey: str | None,
    position: str | None,
    status: str | None,
    designation: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Add a player to this team.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    try:
        with session:
            player = _create_team_player_action(
                session,
                season_id,
                team_id,
                first_name,
                last_name,
                external_id=external_id,
                jersey=jersey,
                position=position,
                status=status,
                designation=designation,
            )
    except Exception as exc:
        click.secho(f"Error creating player: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(player, output_format, output_path, None)
    click.secho(f"Player {player.id} added to team {team_id} successfully.", fg="green")


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
    aliases={
        "list": ("ls",),
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
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
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
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    coach = run_action_or_exit(session, _get_team_coach_action, season_id, team_id, coach_id)
    render_get_command(coach, output_format, output_path, fields_spec)


@teams_roster_coaches_group.command("create")
@click.option(
    "--first-name",
    type=str,
    required=True,
    help="Coach's first name.",
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help="Coach's last name.",
)
@click.option(
    "--external-id",
    type=str,
    help="Optional external identifier for the coach.",
)
@click.option(
    "--position",
    type=click.Choice(
        [
            "Head Coach",
            "Assistant Coach",
            "Head Coach at Large",
            "Assistant Coach at Large",
            "Assistant Trainer",
            "Manager",
            "Trainer",
            "Trainer at Large",
        ],
        case_sensitive=False,
    ),
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
    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
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
