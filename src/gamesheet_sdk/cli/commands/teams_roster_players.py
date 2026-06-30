# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams roster players command group."""

from __future__ import annotations

from typing import Any

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

from gamesheet_sdk.cli.constants import (
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
    render_penalty_report,
)
from gamesheet_sdk.config import Config
from gamesheet_sdk.roster import (
    assign_team_player as _assign_team_player_action,
    create_team_player as _create_team_player_action,
    delete_team_player as _delete_team_player_action,
    get_team_player as _get_team_player_action,
    list_team_players as _list_team_players_action,
    unassign_team_player as _unassign_team_player_action,
    update_team_player as _update_team_player_action,
)


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
    """List all players for this team.

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
    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
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
# pylint: disable-next=too-many-positional-arguments
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
    :param ctx: Click context object containing config
    :type ctx: Context
    :param first_name: Optional updated first name
    :type first_name: str
    :param last_name: Optional updated last name
    :type last_name: str
    :param external_id: Optional updated external identifier
    :type external_id: str | None
    :param jersey: Optional jersey number
    :type jersey: str | None
    :param position: Optional position
    :type position: str | None
    :param status: Optional status
    :type status: str | None
    :param designation: Optional designation
    :type designation: str | None
    :param biography: Optional updated biography
    :type biography: str | None
    :param height: Optional updated height
    :type height: str | None
    :param weight: Optional updated weight
    :type weight: str | None
    :param shot_hand: Optional updated shooting hand
    :type shot_hand: str | None
    :param birthdate: Optional updated birthdate
    :type birthdate: str | None
    :param hometown: Optional updated hometown
    :type hometown: str | None
    :param country: Optional updated country
    :type country: str | None
    :param province: Optional updated province/state
    :type province: str | None
    :param drafted_by: Optional updated drafted by team
    :type drafted_by: str | None
    :param committed_to: Optional updated committed to team
    :type committed_to: str | None
    :param photo_path: Optional updated path to photo
    :type photo_path: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: On authentication or API errors.
    """
    from gamesheet_sdk.cli.helpers import run_roster_create_with_output

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
        # pylint: disable=duplicate-code
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
        # pylint: enable=duplicate-code
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
@click.option(
    "--first-name",
    type=str,
    help="Updated first name.",
)
@click.option(
    "--last-name",
    type=str,
    help="Updated last name.",
)
@click.option(
    "--external-id",
    type=str,
    help="Updated external identifier.",
)
@click.option(
    "--biography",
    type=str,
    help="Updated biography text.",
)
@click.option(
    "--height",
    type=str,
    help="Updated height (e.g., 6'2\").",
)
@click.option(
    "--weight",
    type=str,
    help="Updated weight (e.g., 185).",
)
@click.option(
    "--shot-hand",
    type=click.Choice(["left", "right"], case_sensitive=False),
    help="Updated shooting hand.",
)
@click.option(
    "--birthdate",
    type=str,
    help="Updated birthdate (ISO format: YYYY-MM-DD).",
)
@click.option(
    "--hometown",
    type=str,
    help="Updated hometown.",
)
@click.option(
    "--country",
    type=str,
    help="Updated country code (e.g., US, CA).",
)
@click.option(
    "--province",
    type=str,
    help="Updated province/state.",
)
@click.option(
    "--drafted-by",
    type=str,
    help="Updated drafted by team name.",
)
@click.option(
    "--committed-to",
    type=str,
    help="Updated committed to institution.",
)
@click.option(
    "--photo",
    "photo_path",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a new photo image file.",
)
@click.option(
    "--remove-photo",
    is_flag=True,
    default=False,
    help="Remove the player's photo.",
)
@common_output_options
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def teams_roster_players_update_command(
    ctx: Context,
    player_id: str,
    first_name: str | None,
    last_name: str | None,
    external_id: str | None,
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
    *,
    remove_photo: bool,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update a player on this team.

    Requires authentication (run 'gamesheet-sdk-py login' first). At least one field must be provided for
    update.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
    :param first_name: Optional updated first name
    :type first_name: str | None
    :param last_name: Optional updated last name
    :type last_name: str | None
    :param external_id: Optional updated external identifier
    :type external_id: str | None
    :param biography: Optional updated biography
    :type biography: str | None
    :param height: Optional updated height
    :type height: str | None
    :param weight: Optional updated weight
    :type weight: str | None
    :param shot_hand: Optional updated shooting hand
    :type shot_hand: str | None
    :param birthdate: Optional updated birthdate
    :type birthdate: str | None
    :param hometown: Optional updated hometown
    :type hometown: str | None
    :param country: Optional updated country
    :type country: str | None
    :param province: Optional updated province/state
    :type province: str | None
    :param drafted_by: Optional updated drafted by team
    :type drafted_by: str | None
    :param committed_to: Optional updated committed to team
    :type committed_to: str | None
    :param photo_path: Optional updated path to photo
    :type photo_path: str | None
    :param remove_photo: Remove the photo
    :type remove_photo: bool
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: On authentication or API errors.
    """
    from gamesheet_sdk.cli.helpers import run_roster_update_with_output

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
        # pylint: disable=duplicate-code
        player_id,
        first_name=first_name,
        last_name=last_name,
        external_id=external_id,
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
        remove_photo=remove_photo,
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
    """Delete a player from the team's roster and the season.

    Requires authentication (run 'gamesheet-sdk-py login' first). This operation is destructive and cannot be
    undone. Use --force to skip confirmation prompt.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier to delete
    :type player_id: str
    :raises Exit: On authentication or API errors.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    # pylint: enable=duplicate-code
    team_id: str = ctx_data["team_id"]
    session = build_authenticated_session(config)
    try:
        with session:
            _delete_team_player_action(session, season_id, team_id, player_id)
    except Exception as exc:
        click.secho(f"Error deleting player: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho(f"Player {player_id} deleted successfully.", fg="green")


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
    """Get penalty report for a player on this team.

    Retrieves penalty statistics, incidents, and infraction history for the specified player.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: Player ID to retrieve penalty report for
    :type player_id: str
    :param output_format: Output format (json, yaml, etc.)
    :type output_format: str
    :param output_path: Optional path to write output file
    :type output_path: str | None
    """
    ctx_data: dict[str, Any] = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    with build_authenticated_session(config) as session:
        from gamesheet_sdk.roster import get_player_penalty_report

        report = get_player_penalty_report(session, season_id, player_id)
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
    """Assign an existing player to this team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
    :param jersey: Optional jersey number
    :type jersey: str | None
    :param position: Optional position
    :type position: str | None
    :param status: Optional status
    :type status: str | None
    :param designation: Optional designation
    :type designation: str | None
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
    """Unassign a player from this team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
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
