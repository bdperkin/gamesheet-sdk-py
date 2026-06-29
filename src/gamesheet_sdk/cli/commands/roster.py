# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster command group with nested sub-commands."""

from __future__ import annotations

from click.exceptions import Exit
import rich_click as click
from rich_click import Context

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
from gamesheet_sdk.roster import (
    assign_coach as _assign_coach_action,
    assign_player as _assign_player_action,
    create_coach as _create_coach_action,
    create_player as _create_player_action,
    delete_coach as _delete_coach_action,
    delete_player as _delete_player_action,
    get_coach as _get_coach_action,
    get_player as _get_player_action,
    list_coaches as _list_coaches_action,
    list_players as _list_players_action,
    unassign_coach as _unassign_coach_action,
    unassign_player as _unassign_player_action,
    update_coach as _update_coach_action,
    update_player as _update_player_action,
)


@click.group(
    "roster",
    cls=ResourceGroup,
    default="players",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
        "assign": ("register", "enlist", "place"),
        "unassign": ("drop", "release", "deregister"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to manage roster for.",
)
@click.pass_context
def roster_group(ctx: Context, season_id: str) -> None:
    """Manage roster (players and coaches) within a season.

    Invoking ``roster`` with no sub-command runs ``players`` by default. The --season-id option is required
    and applies to all sub-commands.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param season_id: The season identifier
    :type season_id: str
    """
    # Store season_id in context for sub-commands to access
    # ctx.obj is a Config object from the root CLI - wrap it in a dict
    config = ctx.obj
    ctx.obj = {"config": config, "season_id": season_id}


# Players sub-group
@roster_group.group(
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
def players_group() -> None:
    """Manage players.

    Invoking ``players`` with no sub-command runs ``list`` by default.
    """


@players_group.command("get")
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
def players_get_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific player.

    The player ID can be provided via --player-id or the GAMESHEET_PLAYER_ID environment variable. The season
    ID is inherited from the parent roster command. Requires a saved session from `gamesheet-sdk-py login`.
    The output displays player metadata as key-value pairs, with each field on its own row.
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
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    player = run_action_or_exit(session, _get_player_action, season_id, player_id)
    render_get_command(player, output_format, output_path, fields_spec)


@players_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def players_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all players in the specified season.

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
    # Extract config and season_id from context (set by roster_group)
    # ctx.obj is always a dict set by roster_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(config)
    players = run_action_or_exit(session, _list_players_action, season_id)
    render_list_command(players, output_format, output_path, columns_spec)


@players_group.command("create")
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
    "--team-id",
    type=str,
    help="Optional team ID to associate the player with.",
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
def players_create_command(
    ctx: Context,
    first_name: str,
    last_name: str,
    external_id: str | None,
    jersey: str | None,
    position: str | None,
    status: str | None,
    designation: str | None,
    team_id: str | None,
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
    """Create a new player in the season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    :param ctx: Click context object containing config
    :type ctx: Context
    :param first_name: Player's first name
    :type first_name: str
    :param last_name: Player's last name
    :type last_name: str
    :param external_id: Optional external identifier
    :type external_id: str | None
    :param jersey: Optional jersey number
    :type jersey: str | None
    :param position: Optional player position
    :type position: str | None
    :param status: Optional player status
    :type status: str | None
    :param designation: Optional player designation
    :type designation: str | None
    :param team_id: Optional team ID to assign player to
    :type team_id: str | None
    :param biography: Optional player biography
    :type biography: str | None
    :param height: Optional player height
    :type height: str | None
    :param weight: Optional player weight
    :type weight: str | None
    :param shot_hand: Optional shooting hand
    :type shot_hand: str | None
    :param birthdate: Optional birthdate
    :type birthdate: str | None
    :param hometown: Optional hometown
    :type hometown: str | None
    :param country: Optional country
    :type country: str | None
    :param province: Optional province/state
    :type province: str | None
    :param drafted_by: Optional drafted by team
    :type drafted_by: str | None
    :param committed_to: Optional committed to team
    :type committed_to: str | None
    :param photo_path: Optional path to player photo
    :type photo_path: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: On authentication or API errors.
    """
    ctx_data = ctx.obj
    from gamesheet_sdk.cli.helpers import run_roster_create_with_output

    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    run_roster_create_with_output(
        _create_player_action,
        session,
        "player",
        output_format,
        output_path,
        session,
        season_id,
        first_name,
        last_name,
        external_id=external_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
        team_id=team_id,
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
    )


@players_group.command("update")
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
def players_update_command(
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
    """Update an existing player.

    Requires authentication (run 'gamesheet-sdk-py login' first). At least one field must be provided for
    update.
    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier to update
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
    :param photo_path: Optional path to updated player photo
    :type photo_path: str | None
    :param remove_photo: Remove the player's photo
    :type remove_photo: bool
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: On authentication or API errors.
    """
    from gamesheet_sdk.cli.helpers import run_roster_update_with_output

    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    run_roster_update_with_output(
        _update_player_action,
        session,
        "player",
        output_format,
        output_path,
        session,
        season_id,
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


@players_group.command("delete")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to delete.",
)
@confirm_destructive("player")
@click.pass_context
def players_delete_command(ctx: Context, player_id: str) -> None:
    """Delete a player from the season.

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
    session = build_authenticated_session(config)
    try:
        with session:
            _delete_player_action(session, season_id, player_id)
    except Exception as exc:
        click.secho(f"Error deleting player: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho(f"Player {player_id} deleted successfully.", fg="green")


@players_group.command("penalty-report")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to retrieve penalty report for.",
)
@common_output_options
@click.pass_context
def players_penalty_report_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get penalty report for a player.

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
    import json

    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    with build_authenticated_session(config) as session:
        from gamesheet_sdk.roster import get_player_penalty_report

        report = get_player_penalty_report(session, season_id, player_id)
        if output_format == "json":
            output_text = json.dumps(report, indent=2)
        elif output_format == "yaml":
            import yaml

            output_text = yaml.dump(report, default_flow_style=False)
        else:
            output_text = json.dumps(report, indent=2)
        from gamesheet_sdk.output import write_output

        write_output(output_text, output_path, fmt=output_format)


@players_group.command("assign")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to assign.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to assign to.",
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
def players_assign_command(
    ctx: Context,
    player_id: str,
    team_id: str,
    jersey: str | None,
    position: str | None,
    status: str | None,
    designation: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Assign an existing player to a team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
    :param team_id: The team identifier
    :type team_id: str
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
    config, season_id = ctx.obj["config"], ctx.obj["season_id"]
    session = build_authenticated_session(config)
    run_roster_assign_with_output(
        _assign_player_action,
        session,
        "player",
        player_id,
        team_id,
        output_format,
        output_path,
        session,
        season_id,
        player_id,
        team_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )


@players_group.command("unassign")
@click.option(
    "--player-id",
    type=str,
    envvar="GAMESHEET_PLAYER_ID",
    required=True,
    help="Player ID to unassign.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to unassign from.",
)
@click.pass_context
def players_unassign_command(ctx: Context, player_id: str, team_id: str) -> None:
    """Unassign a player from a team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param player_id: The player identifier
    :type player_id: str
    :param team_id: The team identifier
    :type team_id: str
    """
    config, season_id = ctx.obj["config"], ctx.obj["season_id"]
    session = build_authenticated_session(config)
    run_roster_unassign(
        _unassign_player_action,
        session,
        "player",
        player_id,
        team_id,
        session,
        season_id,
        player_id,
        team_id,
    )


# Coaches sub-group
@roster_group.group(
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
def coaches_group() -> None:
    """Manage coaches.

    Invoking ``coaches`` with no sub-command runs ``list`` by default.
    """


@coaches_group.command("get")
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
def coaches_get_command(
    ctx: Context,
    coach_id: str,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None,
) -> None:
    """Get detailed information about a specific coach.

    The coach ID can be provided via --coach-id or the GAMESHEET_COACH_ID environment variable. The season ID
    is inherited from the parent roster command. Requires a saved session from `gamesheet-sdk-py login`. The
    output displays coach metadata as key-value pairs, with each field on its own row.
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
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    coach = run_action_or_exit(session, _get_coach_action, season_id, coach_id)
    render_get_command(coach, output_format, output_path, fields_spec)


@coaches_group.command("list")
@common_output_options
@list_columns_option
@click.pass_context
def coaches_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all coaches in the specified season.

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
    # Extract config and season_id from context (set by roster_group)
    # ctx.obj is always a dict set by roster_group with "config" and "season_id" keys
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    session = build_authenticated_session(config)
    coaches = run_action_or_exit(session, _list_coaches_action, season_id)
    render_list_command(coaches, output_format, output_path, columns_spec)


@coaches_group.command("create")
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
@click.option(
    "--team-id",
    type=str,
    help="Optional team ID to associate the coach with.",
)
@common_output_options
@click.pass_context
def coaches_create_command(
    ctx: Context,
    first_name: str,
    last_name: str,
    external_id: str | None,
    position: str | None,
    team_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new coach in the season.

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
    :param team_id: The team identifier
    :type team_id: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    :raises Exit: Always raised (exit code 1) because this command is not yet implemented.
    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    try:
        with session:
            coach = _create_coach_action(
                session,
                season_id,
                first_name,
                last_name,
                external_id=external_id,
                position=position,
                team_id=team_id,
            )
    except Exception as exc:
        click.secho(f"Error creating coach: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    render_get_command(coach, output_format, output_path, None)
    click.secho(f"Coach {coach.id} created successfully.", fg="green")


@coaches_group.command("update")
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
    "--position",
    type=click.Choice(COACH_POSITIONS, case_sensitive=False),
    help="Updated position.",
)
@common_output_options
@click.pass_context
def coaches_update_command(
    ctx: Context,
    coach_id: str,
    first_name: str | None,
    last_name: str | None,
    external_id: str | None,
    position: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing coach.

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

    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    run_roster_update_with_output(
        _update_coach_action,
        session,
        "coach",
        output_format,
        output_path,
        session,
        season_id,
        coach_id,
        first_name=first_name,
        last_name=last_name,
        external_id=external_id,
        position=position,
    )


@coaches_group.command("delete")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to delete.",
)
@confirm_destructive("coach")
@click.pass_context
def coaches_delete_command(ctx: Context, coach_id: str) -> None:
    """Delete a coach from the season.

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
    session = build_authenticated_session(config)
    try:
        with session:
            _delete_coach_action(session, season_id, coach_id)
    except Exception as exc:
        click.secho(f"Error deleting coach: {exc}", fg="red", err=True)
        raise Exit(1) from exc
    click.secho(f"Coach {coach_id} deleted successfully.", fg="green")


@coaches_group.command("penalty-report")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to retrieve penalty report for.",
)
@common_output_options
@click.pass_context
def coaches_penalty_report_command(
    ctx: Context,
    coach_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get penalty report for a coach.

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
    import json

    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    with build_authenticated_session(config) as session:
        from gamesheet_sdk.roster import get_coach_penalty_report

        report = get_coach_penalty_report(session, season_id, coach_id)
        if output_format == "json":
            output_text = json.dumps(report, indent=2)
        elif output_format == "yaml":
            import yaml

            output_text = yaml.dump(report, default_flow_style=False)
        else:
            output_text = json.dumps(report, indent=2)
        from gamesheet_sdk.output import write_output

        write_output(output_text, output_path, fmt=output_format)


@coaches_group.command("assign")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to assign.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to assign to.",
)
@click.option(
    "--position",
    type=click.Choice(COACH_POSITIONS, case_sensitive=False),
    help="Optional position.",
)
@common_output_options
@click.pass_context
def coaches_assign_command(
    ctx: Context,
    coach_id: str,
    team_id: str,
    position: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Assign an existing coach to a team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    :param team_id: The team identifier
    :type team_id: str
    :param position: Optional position
    :type position: str | None
    :param output_format: Output format for rendering
    :type output_format: str
    :param output_path: Optional output file path
    :type output_path: str | None
    """
    config, season_id = ctx.obj["config"], ctx.obj["season_id"]
    session = build_authenticated_session(config)
    run_roster_assign_with_output(
        _assign_coach_action,
        session,
        "coach",
        coach_id,
        team_id,
        output_format,
        output_path,
        session,
        season_id,
        coach_id,
        team_id,
        position=position,
    )


@coaches_group.command("unassign")
@click.option(
    "--coach-id",
    type=str,
    envvar="GAMESHEET_COACH_ID",
    required=True,
    help="Coach ID to unassign.",
)
@click.option(
    "--team-id",
    type=str,
    envvar="GAMESHEET_TEAM_ID",
    required=True,
    help="Team ID to unassign from.",
)
@click.pass_context
def coaches_unassign_command(ctx: Context, coach_id: str, team_id: str) -> None:
    """Unassign a coach from a team's roster.

    :param ctx: Click context object containing config
    :type ctx: Context
    :param coach_id: The coach identifier
    :type coach_id: str
    :param team_id: The team identifier
    :type team_id: str
    """
    config, season_id = ctx.obj["config"], ctx.obj["season_id"]
    session = build_authenticated_session(config)
    run_roster_unassign(
        _unassign_coach_action,
        session,
        "coach",
        coach_id,
        team_id,
        session,
        season_id,
        coach_id,
        team_id,
    )
