# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams roster players command group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin import roster
from gamesheet_sdk.admin.cli.constants import (
    HELP_PLAYER_FIRST_NAME,
    HELP_PLAYER_LAST_NAME,
    PLAYER_DESIGNATION,
    PLAYER_POSITIONS,
    PLAYER_STATUS,
)
from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
    run_roster_assign_with_output,
    run_roster_create_with_output,
    run_roster_delete,
    run_roster_unassign,
    run_roster_update_with_output,
)
from gamesheet_sdk.admin.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    player_update_options,
    render_get_command,
    render_list_command,
    render_penalty_report,
)
from gamesheet_sdk.admin.roster import (
    assign_team_player as _assign_team_player_action,
)
from gamesheet_sdk.admin.roster import (
    create_team_player as _create_team_player_action,
)
from gamesheet_sdk.admin.roster import (
    delete_team_player as _delete_team_player_action,
)
from gamesheet_sdk.admin.roster import (
    get_team_player as _get_team_player_action,
)
from gamesheet_sdk.admin.roster import (
    list_team_players as _list_team_players_action,
)
from gamesheet_sdk.admin.roster import (
    unassign_team_player as _unassign_team_player_action,
)
from gamesheet_sdk.admin.roster import (
    update_team_player as _update_team_player_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


# Teams roster players sub-group
@click.group(
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
    r"""List all players for this team.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
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
    r"""Get detailed information about a specific player on this team.

    The player ID can be provided via --player-id or the GAMESHEET_PLAYER_ID environment variable. The season
    ID and team ID are inherited from the parent roster command. Requires authentication (run 'gamesheet-sdk-
    py login' first).\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        fields_spec (str | None): Optional comma-separated list of fields to display

    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    player = run_action_or_exit(
        session,
        _get_team_player_action,
        season_id,
        team_id,
        player_id,
    )
    render_get_command(player, output_format, output_path, fields_spec)


@teams_roster_players_group.command("create")
@click.option(
    "--first-name",
    type=str,
    required=True,
    help=HELP_PLAYER_FIRST_NAME,
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help=HELP_PLAYER_LAST_NAME,
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
    r"""Add a player to this team.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        first_name (str): Optional updated first name
        last_name (str): Optional updated last name
        external_id (str | None): Optional updated external identifier
        jersey (str | None): Optional jersey number
        position (str | None): Optional position
        status (str | None): Optional status
        designation (str | None): Optional designation
        biography (str | None): Optional updated biography
        height (str | None): Optional updated height
        weight (str | None): Optional updated weight
        shot_hand (str | None): Optional updated shooting hand
        birthdate (str | None): Optional updated birthdate
        hometown (str | None): Optional updated hometown
        country (str | None): Optional updated country
        province (str | None): Optional updated province/state
        drafted_by (str | None): Optional updated drafted by team
        committed_to (str | None): Optional updated committed to team
        photo_path (str | None): Optional updated path to photo
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    run_roster_create_with_output(
        _create_team_player_action,
        session,
        "player",
        output_format,
        output_path,
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
        success_message=f"Player {{id}} added to team {team_id} successfully.",
    )


@teams_roster_players_group.command("update")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to update.",
)
@player_update_options
@common_output_options
@click.pass_context
def teams_roster_players_update_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    **player_kwargs: Any,
) -> None:
    r"""Update a player on this team.

    Requires authentication (run 'gamesheet-admin login' first). At least one field must be provided for
    update.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        **player_kwargs (Any): Player attributes to update

    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    team_id: str = ctx.obj["team_id"]
    session = build_authenticated_session(config)
    run_roster_update_with_output(
        _update_team_player_action,
        session,
        "player",
        output_format,
        output_path,
        session,
        season_id,
        team_id,
        player_id,
        **player_kwargs,
    )


@teams_roster_players_group.command("delete")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to delete.",
)
@confirm_destructive("player")
@click.pass_context
def teams_roster_players_delete_command(ctx: Context, player_id: str) -> None:
    r"""Delete a player from the team's roster and the season.

    Requires authentication (run 'gamesheet-admin login' first). This operation is destructive and cannot be
    undone. Use --force to skip confirmation prompt.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier to delete

    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    team_id: str = ctx_data["team_id"]
    session = build_authenticated_session(config)
    run_roster_delete(
        _delete_team_player_action,
        session,
        "player",
        player_id,
        session,
        season_id,
        team_id,
        player_id,
    )


@teams_roster_players_group.command("penalty-report")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to retrieve penalty report for.",
)
@common_output_options
@click.pass_context
def teams_roster_players_penalty_report_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    r"""Get penalty report for a player on this team.

    Retrieves penalty statistics, incidents, and infraction history for the specified player.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): Player ID to retrieve penalty report for
        output_format (str): Output format (json, yaml, etc.)
        output_path (str | None): Optional path to write output file

    """
    ctx_data: dict[str, Any] = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    with build_authenticated_session(config) as session:
        report = roster.get_player_penalty_report(session, season_id, player_id)
        render_penalty_report(report, output_format, output_path)


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
    r"""Assign an existing player to this team's roster.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        jersey (str | None): Optional jersey number
        position (str | None): Optional position
        status (str | None): Optional status
        designation (str | None): Optional designation
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

    """
    config, season_id, team_id = (
        ctx.obj["config"],
        ctx.obj["season_id"],
        ctx.obj["team_id"],
    )
    session = build_authenticated_session(config)
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
    r"""Unassign a player from this team's roster.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier

    """
    config, season_id, team_id = (
        ctx.obj["config"],
        ctx.obj["season_id"],
        ctx.obj["team_id"],
    )
    session = build_authenticated_session(config)
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
