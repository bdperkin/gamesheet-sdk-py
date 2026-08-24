# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Roster players command group."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import rich_click as click
import yaml
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
    columns_option,
    common_output_options,
    player_update_options,
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.admin.roster import (
    assign_player as _assign_player_action,
)
from gamesheet_sdk.admin.roster import (
    create_player as _create_player_action,
)
from gamesheet_sdk.admin.roster import (
    delete_player as _delete_player_action,
)
from gamesheet_sdk.admin.roster import (
    get_player as _get_player_action,
)
from gamesheet_sdk.admin.roster import (
    list_players as _list_players_action,
)
from gamesheet_sdk.admin.roster import (
    unassign_player as _unassign_player_action,
)
from gamesheet_sdk.admin.roster import (
    update_player as _update_player_action,
)
from gamesheet_sdk.common.cli.core import ResourceGroup, confirm_destructive
from gamesheet_sdk.common.output import write_output

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


# Players sub-group
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
@columns_option
@click.pass_context
def players_get_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""Get detailed information about a specific player.

    The player ID can be provided via --player-id or the GAMESHEET_PLAYER_ID environment variable. The season
    ID is inherited from the parent roster command. Requires a saved session from ``gamesheet-admin login``.
    The output displays player metadata as key-value pairs, with each field on its own row.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    player = run_action_or_exit(session, _get_player_action, season_id, player_id)
    render_get_command(player, output_format, output_path, columns_spec)


@players_group.command("list")
@common_output_options
@columns_option
@click.pass_context
def players_list_command(
    ctx: Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    r"""List all players in the specified season.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        columns_spec (str | None): Optional comma-separated list of columns to display

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
    r"""Create a new player in the season.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        first_name (str): Player's first name
        last_name (str): Player's last name
        external_id (str | None): Optional external identifier
        jersey (str | None): Optional jersey number
        position (str | None): Optional player position
        status (str | None): Optional player status
        designation (str | None): Optional player designation
        team_id (str | None): Optional team ID to assign player to
        biography (str | None): Optional player biography
        height (str | None): Optional player height
        weight (str | None): Optional player weight
        shot_hand (str | None): Optional shooting hand
        birthdate (str | None): Optional birthdate
        hometown (str | None): Optional hometown
        country (str | None): Optional country
        province (str | None): Optional province/state
        drafted_by (str | None): Optional drafted by team
        committed_to (str | None): Optional committed to team
        photo_path (str | None): Optional path to player photo
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    # pylint: disable=duplicate-code
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
    # pylint: enable=duplicate-code


@players_group.command("update")
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
def players_update_command(
    ctx: Context,
    player_id: str,
    output_format: str,
    output_path: str | None,
    **player_kwargs: Any,
) -> None:
    r"""Update an existing player.

    Requires authentication (run 'gamesheet-admin login' first). At least one field must be provided for
    update.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier to update
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path
        **player_kwargs (Any): Player attributes to update

    """
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
        player_id,
        **player_kwargs,
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
    r"""Delete a player from the season.

    Requires authentication (run 'gamesheet-admin login' first). This operation is destructive and cannot be
    undone. Use --force to skip confirmation prompt.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier to delete

    """
    ctx_data = ctx.obj
    config: Config = ctx_data["config"]
    season_id: str = ctx_data["season_id"]
    session = build_authenticated_session(config)
    run_roster_delete(
        _delete_player_action,
        session,
        "player",
        player_id,
        session,
        season_id,
        player_id,
    )


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
    r"""Get penalty report for a player.

    Retrieves penalty statistics, incidents, and infraction history for the specified player.\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): Player ID to retrieve penalty report for
        output_format (str): Output format (json, yaml, etc.)
        output_path (str | None): Optional path to write output file

    """
    config: Config = ctx.obj["config"]
    season_id: str = ctx.obj["season_id"]
    # pylint: disable=duplicate-code
    with build_authenticated_session(config) as session:
        report = roster.get_player_penalty_report(session, season_id, player_id)
        if output_format == "json":
            output_text = json.dumps(report, indent=2)
        elif output_format == "yaml":
            output_text = yaml.dump(report, default_flow_style=False)
        else:
            output_text = json.dumps(report, indent=2)

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
    r"""Assign an existing player to a team's roster.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        team_id (str): The team identifier
        jersey (str | None): Optional jersey number
        position (str | None): Optional position
        status (str | None): Optional status
        designation (str | None): Optional designation
        output_format (str): Output format for rendering
        output_path (str | None): Optional output file path

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
    # pylint: enable=duplicate-code


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
    r"""Unassign a player from a team's roster.

    Requires authentication (run 'gamesheet-admin login' first).\f

    Args:
        ctx (Context): Click context object containing config
        player_id (str): The player identifier
        team_id (str): The team identifier

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
