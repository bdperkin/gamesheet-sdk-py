"""Teams roster command group - player and coach management for teams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.cli.constants import (
    COACH_POSITIONS,
    PLAYER_DESIGNATION,
    PLAYER_POSITIONS,
    PLAYER_STATUS,
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
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.roster import assign_team_coach as _assign_team_coach_action
from gamesheet_sdk.roster import assign_team_player as _assign_team_player_action
from gamesheet_sdk.roster import create_team_coach as _create_team_coach_action
from gamesheet_sdk.roster import create_team_player as _create_team_player_action
from gamesheet_sdk.roster import get_team_coach as _get_team_coach_action
from gamesheet_sdk.roster import get_team_player as _get_team_player_action
from gamesheet_sdk.roster import list_team_coaches as _list_team_coaches_action
from gamesheet_sdk.roster import list_team_players as _list_team_players_action
from gamesheet_sdk.roster import unassign_team_coach as _unassign_team_coach_action
from gamesheet_sdk.roster import unassign_team_player as _unassign_team_player_action

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
        "assign": ("register", "enlist", "place"),
        "unassign": ("drop", "release", "deregister"),
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
    type=click.Choice(PLAYER_POSITIONS, case_sensitive=False),
    help="Optional position.",
)
@click.option(
    "--status",
    type=click.Choice(PLAYER_STATUS, case_sensitive=False),
    help="Optional status.",
)
@click.option(
    "--designation",
    type=click.Choice(PLAYER_DESIGNATION, case_sensitive=False),
    help="Optional designation (Captain or Alternate Captain).",
)
@click.option(
    "--biography",
    type=str,
    help="Optional biography text.",
)
@click.option(
    "--height",
    type=str,
    help='Optional height (e.g., "6\'2\\"").',
)
@click.option(
    "--weight",
    type=str,
    help='Optional weight (e.g., "185").',
)
@click.option(
    "--shot-hand",
    type=click.Choice(["left", "right"], case_sensitive=False),
    help="Optional shooting hand.",
)
@click.option(
    "--birthdate",
    type=str,
    help="Optional birthdate (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--hometown",
    type=str,
    help="Optional hometown.",
)
@click.option(
    "--country",
    type=str,
    help='Optional country code (e.g., "US", "CA").',
)
@click.option(
    "--province",
    type=str,
    help="Optional province/state.",
)
@click.option(
    "--drafted-by",
    type=str,
    help="Optional drafted by team name.",
)
@click.option(
    "--committed-to",
    type=str,
    help="Optional committed to institution.",
)
@click.option(
    "--photo",
    "photo_path",
    type=click.Path(exists=True, dir_okay=False),
    help="Optional path to a local photo image file.",
)
@common_output_options
@click.pass_context
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
def teams_roster_players_create_command(
    ctx: Context,
    first_name: str,
    last_name: str,
    external_id: str | None,
    jersey: str | None,
    position: str | None,
    status: str | None,
    designation: str | None,
    biography: str | None,
    height: str | None,
    weight: str | None,
    shot_hand: str | None,
    birthdate: str | None,
    hometown: str | None,
    country: str | None,
    province: str | None,
    drafted_by: str | None,
    committed_to: str | None,
    photo_path: str | None,
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
                biography=biography,
                height=height,
                weight=weight,
                shot_hand=shot_hand,
                birthdate=birthdate,
                hometown=hometown,
                country=country,
                province=province,
                drafted_by=drafted_by,
                committed_to=committed_to,
                photo_path=photo_path,
            )
    except Exception as exc:
        click.secho(f"Error creating player: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(player, output_format, output_path, None)
    click.secho(f"Player {player.id} added to team {team_id} successfully.", fg="green")


@teams_roster_players_group.command("update")
def teams_roster_players_update_command() -> None:  # pragma: no cover
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
def teams_roster_players_delete_command() -> None:  # pragma: no cover
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
def teams_roster_players_penalty_report_command() -> None:  # pragma: no cover
    """Get penalty report for a player on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster players penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_players_group.command("assign")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to assign.",
)
@click.option("--jersey", type=str, help="Optional jersey number.")
@click.option(
    "--position",
    type=click.Choice(
        ["Forward", "Left Wing", "Right Wing", "Centre", "Pusher (Sled)", "Defence", "Goalie"],
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
    help="Optional designation.",
)
@common_output_options
@click.pass_context
def teams_roster_players_assign_command(
    ctx: Context,
    player_id: str,
    jersey: str | None,
    position: str | None,
    status: str | None,
    designation: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Assign an existing player to this team's roster."""
    config, season_id, team_id = ctx.obj["config"], ctx.obj["season_id"], ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    run_roster_assign_with_output(
        _assign_team_player_action,
        session,
        "player",
        player_id,
        team_id,
        output_format,
        output_path,
        session,
        season_id,
        team_id,
        player_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )


@teams_roster_players_group.command("unassign")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to unassign.",
)
@click.pass_context
def teams_roster_players_unassign_command(ctx: Context, player_id: str) -> None:
    """Unassign a player from this team's roster."""
    config, season_id, team_id = ctx.obj["config"], ctx.obj["season_id"], ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
    run_roster_unassign(
        _unassign_team_player_action,
        session,
        "player",
        player_id,
        team_id,
        session,
        season_id,
        team_id,
        player_id,
    )


# Teams roster coaches sub-group
@teams_roster_group.group(
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
def teams_roster_coaches_update_command() -> None:  # pragma: no cover
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
def teams_roster_coaches_delete_command() -> None:  # pragma: no cover
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
def teams_roster_coaches_penalty_report_command() -> None:  # pragma: no cover
    """Get penalty report for a coach on this team.

    NOT YET IMPLEMENTED - Backend function needs to be added.
    """
    click.secho(
        "Error: teams roster coaches penalty-report is not yet implemented. Backend support needed.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@teams_roster_coaches_group.command("assign")
@click.option("--coach-id", type=str, envvar="GAMESHEET_COACH_ID", required=True, help="Coach ID to assign.")
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
    """Assign an existing coach to this team's roster."""
    config, season_id, team_id = ctx.obj["config"], ctx.obj["season_id"], ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
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
    """Unassign a coach from this team's roster."""
    config, season_id, team_id = ctx.obj["config"], ctx.obj["season_id"], ctx.obj["team_id"]
    session = build_authenticated_session(ctx, config)
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
